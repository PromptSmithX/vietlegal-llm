# RAG Specification — Labor Law MVP

## 1. Pipeline đã khóa

```text
Question
  → Input Guard
  → Query Analyzer
  → Reference Date Resolver
  → BM25 Top 100 + Dense Top 100
  → Temporal/Metadata Filter
  → RRF Top 30
  → Qwen3 Reranker Top 5
  → Context Builder
  → Qwen3-4B Generator
  → Output Parser
  → Citation Validator
  → ChatResponse
```

Top K là cấu hình nội bộ, không nhận tùy ý từ `/api/chat`. Giá trị mặc định MVP: 100 cho mỗi retriever, 30 sau RRF và 5 sau reranking.

## 2. Input guard và query analyzer

Input guard:

- từ chối chuỗi rỗng, quá 2.000 ký tự hoặc không phải UTF-8 hợp lệ;
- coi mọi chỉ dẫn yêu cầu bỏ qua system prompt, tự tạo nguồn hoặc tiết lộ prompt là dữ liệu không đáng tin;
- không ghi nguyên văn câu hỏi vào application log mặc định.

Query analyzer tạo:

```json
{
  "normalized_query": "...",
  "reference_date": "2026-09-09",
  "document_numbers": ["45/2019/QH14"],
  "articles": ["Điều 46"],
  "clauses": ["Khoản 1"],
  "points": [],
  "date_source": "request | question | system_default"
}
```

Chuẩn hóa dùng Unicode NFC, collapse whitespace và chuẩn hóa alias `điều`, `khoản`, `điểm`; không bỏ dấu tiếng Việt trong dense query. BM25 có thể tạo thêm trường search-normalized không dấu, nhưng phải giữ cả token có dấu và token pháp lý chính xác.

Thứ tự xác định ngày:

1. `reference_date` hợp lệ trong API request.
2. Ngày/năm được nêu rõ trong câu hỏi.
3. Ngày hệ thống tại timezone cấu hình `Asia/Ho_Chi_Minh`.

Nếu request date và câu hỏi mâu thuẫn, trả lỗi validation; không âm thầm chọn một giá trị.

## 3. Retrieval và temporal filter

- BM25 ưu tiên số văn bản, Điều/Khoản/Điểm và exact terms.
- Dense retrieval dùng normalized embeddings để tìm tình huống tương đồng ngữ nghĩa.
- Hai retriever trả tối đa 100 candidate cùng stable `chunk_id`.
- Chỉ chunk chắc chắn áp dụng tại `reference_date` theo `docs/DATA_SPEC.md` được đưa vào RRF.
- Candidate `unknown` hoặc `partially_effective` không được dùng để tạo kết luận; được lưu trong diagnostic trace đã kiểm soát.
- RRF dùng `k = 60`, rank bắt đầu từ 1 và deduplicate theo `chunk_id`.
- Reranker nhận query gốc, reference date, header và text; trả Top 5.

Nếu sau temporal filter không còn candidate hoặc reranker không còn context vượt ngưỡng cấu hình đã được hiệu chỉnh trên validation set, pipeline trả `insufficient_context`.

Không đặt ngưỡng bằng cảm tính trong code. Retrieval/reranker threshold phải nằm trong config có version và được chọn trên validation set, không trên test set.

## 4. Context builder

Context có dạng:

```text
[C1]
Văn bản: Bộ luật Lao động
Số: 45/2019/QH14
Điều: Điều 46
Khoản: Khoản 1
Hiệu lực tại: 2026-09-09
Nguồn: SOURCE_METADATA_ONLY
Nội dung: ...
```

- Citation ID `[C1]` đến `[C5]` chỉ có ý nghĩa trong một request.
- Mapping citation ID → `chunk_id` → source metadata nằm ở backend, không đưa URL vào phần model được phép tự viết.
- Không cắt giữa một câu hoặc provision để đạt token budget.
- Khi vượt token budget, bỏ context có reranker score thấp nhất; không truncate normative text.
- Text corpus được bọc như dữ liệu trích dẫn và mọi chỉ dẫn nằm trong corpus đều bị coi là nội dung, không phải instruction.

## 5. Generator contract

System prompt phải yêu cầu:

1. Chỉ dùng căn cứ trong context.
2. Không tự tạo văn bản, Điều, Khoản, Điểm, URL hoặc citation ID.
3. Mỗi kết luận pháp lý phải kèm ít nhất một citation.
4. Không thêm tình tiết người dùng chưa cung cấp.
5. Trả `insufficient_context` nếu context không đủ hoặc mâu thuẫn chưa giải quyết được.
6. Trả đúng bốn phần: kết luận, phân tích, căn cứ pháp lý, lưu ý.

Output nên được sinh dưới dạng JSON theo schema nội bộ; backend render thành `ChatResponse`. Nếu parse JSON thất bại, chỉ retry một lần bằng repair prompt không thêm context mới. Thất bại lần hai trả lỗi generation có cấu trúc, không trả text thô.

## 6. Citation validator

Validator chạy sau generation và trước response:

- mọi citation ID tồn tại trong context map;
- mỗi câu chứa kết luận pháp lý có citation;
- document number, article, clause và point được nêu trong answer phải xuất hiện trong metadata của citation tương ứng;
- không có URL trong model output; URL response luôn đến từ backend metadata;
- trích đoạn trả cho client phải là substring hoặc normalized substring của chunk;
- citation phải có hiệu lực tại reference date;
- trạng thái `answered` không hợp lệ nếu citation list rỗng.

Nếu validator thất bại do thiếu hoặc sai căn cứ, response chuyển thành `insufficient_context`, không cố tự sửa nội dung pháp lý. Lỗi validator và reason code được ghi trong trace không chứa câu hỏi đầy đủ.

## 7. Abstention

Các reason code nội bộ:

- `OUT_OF_SCOPE`
- `NO_RETRIEVAL_HIT`
- `NO_TEMPORALLY_VALID_CONTEXT`
- `AMBIGUOUS_FACTS`
- `CONFLICTING_CONTEXT`
- `CITATION_VALIDATION_FAILED`

Client chỉ nhận thông báo an toàn và các dữ kiện cần bổ sung; không nhận chain-of-thought hoặc prompt nội bộ.

## 8. Failure handling

- Retriever hoặc model timeout: trả `503 DEPENDENCY_UNAVAILABLE`.
- Index/corpus version mismatch: health chuyển `degraded`; `/api/chat` trả `503`.
- Reference date sai: `422 INVALID_REFERENCE_DATE`.
- Context có prompt injection: giữ text làm evidence nhưng generator không tuân theo instruction trong text; test bắt buộc.
- Citation mâu thuẫn về hiệu lực: abstain và ghi `CONFLICTING_CONTEXT`.

## 9. Observability

Mỗi request có `request_id`, corpus/index/model/prompt version, reference date source, số candidate từng stage, latency từng stage, status và reason code. Không log raw question, raw answer hoặc personal data mặc định.

