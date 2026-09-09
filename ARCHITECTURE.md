# Vietnamese Legal AI — Architecture

## 1. System context

```text
┌──────────────────────────────────────────┐
│ Streamlit MVP / Next.js production       │
└───────────────────┬──────────────────────┘
                    │ JSON/HTTP
┌───────────────────▼──────────────────────┐
│ FastAPI                                  │
│ validation · request ID · error contract │
└───────────────────┬──────────────────────┘
                    │
┌───────────────────▼──────────────────────┐
│ RAG Pipeline                             │
│ query · retrieval · context · validation │
└───────┬───────────────┬───────────────┬──┘
        │               │               │
   Corpus/Index     Model runtime    Observability
   FAISS + BM25     Transformers     logs + metrics
   Qdrant prod      vLLM prod        version trace
```

API không truy cập trực tiếp raw corpus. Mọi câu trả lời đi qua RAG pipeline và citation validator.

## 2. Request data flow

```text
Question
  → Input Guard
  → Query Analyzer + Reference Date Resolver
  → BM25 Top 100 ┐
                 ├→ Temporal/Metadata Filter
  → Dense Top 100┘
  → RRF Top 30
  → Qwen3 Reranker Top 5
  → Context Builder
  → Qwen3-4B Generator
  → Structured Output Parser
  → Citation Validator
  → ChatResponse
```

Temporal filter chạy trước RRF. Với FAISS không hỗ trợ metadata pre-filter, hệ thống over-fetch rồi áp allowed-ID mask trước fusion. Các giá trị Top K nằm trong config có version.

## 3. Components

### API layer

- Validate request và unknown fields.
- Sinh request ID; không lưu hội thoại.
- Ánh xạ domain errors thành error envelope.
- Không trả raw model output hoặc internal trace.

### Query analyzer

- Unicode/whitespace normalization.
- Trích số văn bản, Điều/Khoản/Điểm và ngày tham chiếu.
- Phát hiện mâu thuẫn giữa request date và ngày trong câu hỏi.
- Giữ query gốc cho semantic retrieval và audit đã kiểm soát.

### Retrieval

- BM25 cho exact legal references.
- Qwen3-Embedding-0.6B + FAISS cho semantic search.
- Temporal filter theo provision-level validity.
- RRF `k=60`, Top 30; Qwen3-Reranker-0.6B, Top 5.

### Context builder

- Gán `[C1]`–`[C5]` theo request.
- Giữ header, hierarchy, validity và source mapping.
- Tuân thủ token budget mà không cắt giữa provision.
- Xem corpus text là untrusted data.

### Generator

- MVP dùng Qwen/Qwen3-4B nguyên bản.
- Fine-tuned adapter chỉ thay base sau evaluation gate.
- Sinh structured JSON, không sinh URL.

### Citation validator

- Kiểm tra ID thuộc context.
- Kiểm tra legal references khớp metadata.
- Kiểm tra citation có hiệu lực tại reference date.
- Chuyển sang abstention nếu validation không đạt.

## 4. Domain model

```text
LegalDocument 1 ── * DocumentVersion
DocumentVersion 1 ── * LegalProvision
LegalProvision * ── * LegalChunk
LegalChunk 1 ── * RetrievalHit
LegalChunk 1 ── 1..n Citation (theo request)
```

Canonical schema, stable ID, validity và version semantics nằm trong [Data specification](docs/DATA_SPEC.md).

## 5. Temporal model

Ngày áp dụng được xác định theo thứ tự: API request → ngày nêu trong câu hỏi → ngày hệ thống tại `Asia/Ho_Chi_Minh`.

Provision hợp lệ khi:

```text
effective_from <= reference_date
AND (effective_to IS NULL OR reference_date < effective_to)
AND validity_status = effective
```

`partially_effective` hoặc `unknown` không được dùng cho kết luận `answered` nếu chưa xác minh cấp provision.

## 6. Citation boundary

Model chỉ thấy citation token và nội dung context. Backend giữ mapping:

```text
[C1] → chunk_id → provision_ids → document_id → source_url
```

URL, excerpt và source metadata trong API response luôn đến từ backend. Numeric confidence không thuộc API MVP.

## 7. Public interfaces

```text
POST /api/chat
POST /api/search
GET  /api/documents/{document_id}
GET  /api/health
```

Chi tiết schema và lỗi nằm trong [API specification](docs/API_SPEC.md).

## 8. Artifact compatibility

Mỗi runtime phải khóa:

- corpus schema/version;
- index version và embedding revision;
- reranker revision/config;
- generator revision/adapter;
- prompt hash;
- application commit.

Mismatch giữa corpus và index khiến health `degraded` và endpoint sinh câu trả lời fail closed.

## 9. MVP và production boundary

| Concern | MVP | Production |
|---|---|---|
| Vector index | FAISS | Qdrant |
| Generator serving | Transformers | vLLM |
| Metadata | Versioned files | PostgreSQL khi cần |
| UI | Streamlit | Next.js |
| Identity | Không có | Authentication/authorization |
| Chat history | Không lưu | Chỉ thêm sau privacy review |

## 10. Cross-cutting requirements

- Privacy, severity và incident handling: `docs/SAFETY_AND_GOVERNANCE.md`.
- Metrics và acceptance gate: `docs/EVALUATION.md`.
- Runtime, tests, CI và release: `docs/DEVELOPMENT_AND_OPERATIONS.md`.
- Quyết định đã khóa: `docs/DECISIONS.md`.
