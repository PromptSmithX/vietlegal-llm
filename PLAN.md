# Vietnamese Legal AI — Implementation Plan

## Quy ước

Trạng thái hợp lệ: `Not started`, `In progress`, `Blocked`, `Done`.

Mỗi phase chỉ được chuyển sang `Done` khi toàn bộ acceptance gate đạt và artifact đã được lưu với version. Không gắn thời gian thực hiện khi chưa xác định nhân lực, GPU và ngân sách.

## Phase 0 — Product và nền tảng

**Status:** `Done`

**Mục tiêu:** khóa yêu cầu, hợp đồng kỹ thuật và nền tảng phát triển có thể tái lập.

**Phụ thuộc:** không có.

**Đầu vào:** bộ tài liệu thiết kế và các quyết định trong `docs/DECISIONS.md`.

**Công việc:**

- [x] Xác định phạm vi MVP luật lao động và các nội dung ngoài phạm vi.
- [x] Định nghĩa data, RAG, API, evaluation, safety và operations contract.
- [x] Tạo cấu trúc Python package, test và config.
- [x] Khóa dependency và thiết lập lint, type-check, unit test trong CI.
- [x] Tạo `.env.example`; không commit secret.

**Đầu ra:** tài liệu đồng bộ, repository skeleton, dependency lock và CI cơ bản.

**Acceptance gate:** link tài liệu hợp lệ; JSON examples parse được; test skeleton chạy; không còn quyết định MVP bắt buộc chưa được ghi nhận.

## Phase 1 — Baseline LLM

**Status:** `Not started`

**Mục tiêu:** đo năng lực Qwen3-4B nguyên bản trước RAG và fine-tuning.

**Phụ thuộc:** Phase 0.

**Đầu vào:** model `Qwen/Qwen3-4B`, prompt baseline và benchmark v1.

**Công việc:**

- [ ] Xác nhận model revision, license và chat template.
- [ ] Chạy inference smoke test trên môi trường GPU mục tiêu.
- [ ] Tạo 100–300 câu benchmark theo taxonomy evaluation.
- [ ] Lưu prompt, seed, config, output thô và metric baseline.

**Đầu ra:** `legal-eval-v1`, baseline report và inference config có version.

**Acceptance gate:** toàn bộ benchmark chạy lặp lại được; artifact ghi model revision, seed và commit hash; chưa thực hiện fine-tuning.

## Phase 2 — Legal corpus

**Status:** `Not started`

**Mục tiêu:** tạo corpus luật lao động có provenance và hiệu lực ở cấp quy định.

**Phụ thuộc:** Phase 0.

**Đầu vào:** source manifest đã duyệt, raw HTML/PDF từ nguồn chính thức và `docs/DATA_SPEC.md`.

**Công việc:**

- [ ] Lập manifest Bộ luật Lao động 2019 và văn bản trực tiếp hướng dẫn.
- [ ] Tải raw artifact, lưu checksum, timestamp và source metadata.
- [ ] Parse Văn bản → Chương → Mục → Điều → Khoản → Điểm.
- [ ] Chuẩn hóa hiệu lực, quan hệ sửa đổi/thay thế/hợp nhất và stable ID.
- [ ] Chunk theo đơn vị pháp lý và validate schema.
- [ ] Version corpus; không overwrite phiên bản cũ.

**Đầu ra:** `legal-corpus-v1`, raw artifact manifest, parse report và data quality report.

**Acceptance gate:** 100% record có trường bắt buộc và provenance; không trùng stable ID; sample parser đạt ít nhất 98% cấu trúc chính xác qua kiểm tra kỹ thuật; lỗi còn lại được liệt kê.

## Phase 3 — Retrieval

**Status:** `Not started`

**Mục tiêu:** tìm đúng căn cứ cho truy vấn chính xác, ngữ nghĩa và theo thời điểm.

**Phụ thuộc:** Phase 2 và phần retrieval benchmark của Phase 1.

**Đầu vào:** corpus v1, expected citations và retrieval config.

**Công việc:**

- [ ] Xây tokenizer BM25 và sparse index.
- [ ] Sinh normalized embedding và FAISS index.
- [ ] Over-fetch Top 100 mỗi retriever, lọc hiệu lực, RRF Top 30.
- [ ] Rerank và trả Top 5 context.
- [ ] Đánh giá dense, BM25, hybrid và hybrid + reranker.
- [ ] Version index cùng corpus/model/config tương ứng.

**Đầu ra:** retrieval library, index artifacts và comparison report.

**Acceptance gate:** Recall@5 ≥ 0,90 và nDCG@10 ≥ 0,80 trên held-out retrieval set; truy vấn lịch sử không trả chunk ngoài hiệu lực trong Top 5.

## Phase 4 — RAG MVP

**Status:** `Not started`

**Mục tiêu:** tạo pipeline end-to-end với base model, citation hợp lệ và abstention.

**Phụ thuộc:** Phase 3.

**Đầu vào:** retriever đạt gate, base Qwen3-4B và RAG contract.

**Công việc:**

- [ ] Xây query analyzer và reference-date resolver.
- [ ] Xây context builder với token budget và citation ID ổn định trong request.
- [ ] Áp dụng system prompt chống bịa đặt và prompt injection.
- [ ] Parse structured answer và validate citation/source/legal references.
- [ ] Chuyển sang `insufficient_context` khi retrieval hoặc validation thất bại.

**Đầu ra:** RAG pipeline, trace artifacts đã che dữ liệu nhạy cảm và smoke-test CLI.

**Acceptance gate:** citation ID/source mapping đạt 100%; không URL tự sinh; tất cả scenario bắt buộc có integration test.

## Phase 5 — Evaluation

**Status:** `Not started`

**Mục tiêu:** định lượng chất lượng, phân tích lỗi và quyết định có cần fine-tuning hay không.

**Phụ thuộc:** Phase 4.

**Đầu vào:** benchmark cố định và experiment matrix.

**Công việc:**

- [ ] Chạy Base, Dense RAG, Hybrid RAG và Hybrid + Reranker.
- [ ] Đo retrieval, faithfulness, citation, hallucination và abstention.
- [ ] Phân loại lỗi retrieval, context, prompt, reasoning và validation.
- [ ] Ghi giới hạn của đánh giá chưa có chuyên gia pháp lý.

**Đầu ra:** evaluation report, raw outputs và quyết định `RAG sufficient` hoặc `SFT justified`.

**Acceptance gate:** faithfulness ≥ 0,90; abstention accuracy ≥ 0,85; citation mapping 100%; không có lỗi Critical chưa xử lý.

## Phase 6 — Fine-tuning

**Status:** `Not started`

**Mục tiêu:** cải thiện lỗi reasoning, terminology, answer structure hoặc abstention đã được chứng minh không thuộc retrieval.

**Phụ thuộc:** Phase 5 kết luận `SFT justified`.

**Đầu vào:** SFT dataset có provenance, split chống leakage và Qwen3-4B revision đã khóa.

**Công việc:**

- [ ] Chuẩn hóa prompt/completion và validate dataset.
- [ ] Chạy QLoRA/LoRA experiments có kiểm soát.
- [ ] Lưu adapter, tokenizer, config, dataset version và commit hash.
- [ ] So sánh với base model trên cùng held-out benchmark.

**Đầu ra:** adapter candidates và model evaluation report.

**Acceptance gate:** ít nhất một target metric cải thiện có ý nghĩa; faithfulness, citation và abstention không giảm quá 0,02 tuyệt đối; không có train/eval leakage.

## Phase 7 — Fine-tuned RAG

**Status:** `Not started`

**Mục tiêu:** xác nhận adapter cải thiện toàn hệ thống thay vì chỉ cải thiện model độc lập.

**Phụ thuộc:** Phase 6.

**Đầu vào:** adapter candidate tốt nhất và RAG pipeline đã khóa.

**Công việc:**

- [ ] Tích hợp adapter mà không đổi retrieval config.
- [ ] Chạy lại toàn bộ benchmark và failure scenarios.
- [ ] So sánh paired outputs với Base + Hybrid + Reranker.
- [ ] Chọn hoặc từ chối adapter theo release gate.

**Đầu ra:** final core-model decision và full-system evaluation report.

**Acceptance gate:** cải thiện target metric; đạt toàn bộ gate Phase 3–5; không tăng tỷ lệ citation không được hỗ trợ.

## Phase 8 — API và demo

**Status:** `Not started`

**Mục tiêu:** cung cấp FastAPI stateless và Streamlit demo chạy end-to-end.

**Phụ thuộc:** Phase 4; Phase 7 chỉ bắt buộc nếu adapter được chấp nhận.

**Đầu vào:** API contract, core pipeline và artifact versions.

**Công việc:**

- [ ] Triển khai bốn endpoint và error envelope.
- [ ] Thêm validation, request ID, redacted logging và health checks.
- [ ] Xây Streamlit UI hiển thị bốn phần câu trả lời và citation.
- [ ] Viết OpenAPI, integration/E2E tests và Docker image.

**Đầu ra:** API, demo UI, OpenAPI document và Docker artifact.

**Acceptance gate:** contract tests và E2E scenarios đạt; không lưu chat; citation mở đúng nguồn; container khởi động từ môi trường sạch.

## Phase 9 — Production

**Status:** `Not started`

**Mục tiêu:** production hóa sau khi có thẩm định pháp lý, yêu cầu tải và chính sách vận hành.

**Phụ thuộc:** Phase 8 và phê duyệt quản trị/pháp lý.

**Đầu vào:** capacity target, security review, legal review và SLO đã duyệt.

**Công việc:**

- [ ] Migrate FAISS sang Qdrant và inference sang vLLM.
- [ ] Thêm PostgreSQL khi metadata cần transactional storage.
- [ ] Xây Next.js, authentication, authorization và rate limiting.
- [ ] Thêm monitoring, alerting, backup/restore, CI/CD và rollback.
- [ ] Thiết lập corpus update pipeline và human review workflow.

**Đầu ra:** production release candidate, runbook, dashboards và audit artifacts.

**Acceptance gate:** legal/security review hoàn thành; SLO đạt trong load test; backup/restore và rollback đã diễn tập; không có lỗi Critical hoặc High chưa chấp nhận.
