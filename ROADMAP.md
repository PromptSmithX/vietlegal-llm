# Vietnamese Legal AI — High-level Roadmap

Tài liệu này mô tả thứ tự phát triển ở mức tổng quan. Checklist, dependency, deliverable và acceptance gate chính thức nằm trong [PLAN.md](PLAN.md).

## Luồng phát triển

```text
Phase 0  Product và nền tảng
Phase 1  Baseline LLM
Phase 2  Legal corpus
Phase 3  Retrieval
Phase 4  RAG MVP
Phase 5  Evaluation
Phase 6  Fine-tuning có điều kiện
Phase 7  Fine-tuned RAG
Phase 8  API và demo
Phase 9  Production
```

## Phase 0–2: Khóa nền móng

- Hoàn thiện yêu cầu, hợp đồng dữ liệu/API và môi trường tái lập.
- Đo baseline Qwen3-4B trên benchmark cố định.
- Xây corpus Bộ luật Lao động 2019 và văn bản hướng dẫn từ nguồn chính thức.
- Lưu hiệu lực, provenance và version ở cấp provision/chunk.

Kết quả cần đạt: tài liệu nhất quán, benchmark v1 và legal-corpus-v1 đạt data quality gate.

## Phase 3–5: Xây và kiểm chứng RAG

- Kết hợp BM25 và dense retrieval.
- Lọc hiệu lực trước RRF; rerank để lấy Top 5 context.
- Sinh câu trả lời có cấu trúc, validate citation và abstain khi thiếu căn cứ.
- So sánh Base, Dense RAG, Hybrid RAG và Hybrid + Reranker.

Kết quả cần đạt: retrieval/generation vượt các gate trong [Evaluation specification](docs/EVALUATION.md), không có lỗi Critical còn mở.

## Phase 6–7: Fine-tuning có điều kiện

Chỉ fine-tune khi error analysis chứng minh context đúng đã nằm trong Top 5 nhưng base model vẫn lỗi terminology, reasoning, format hoặc abstention.

- Chuẩn bị SFT dataset có provenance và chống leakage.
- QLoRA/LoRA Qwen3-4B.
- So sánh với base model trên cùng benchmark.
- Chỉ nhận adapter nếu cải thiện metric mục tiêu mà không giảm faithfulness/citation/abstention quá ngưỡng.

## Phase 8: MVP chạy end-to-end

- FastAPI stateless theo [API specification](docs/API_SPEC.md).
- Streamlit demo với citation mở được nguồn chính thức.
- Docker Linux, contract/integration/E2E tests và versioned artifacts.

MVP không có tài khoản, authentication, streaming hoặc lưu lịch sử chat.

## Phase 9: Production

- FAISS → Qdrant.
- Transformers → vLLM.
- File metadata → PostgreSQL khi có nhu cầu giao dịch/query đồng thời.
- Streamlit → Next.js.
- Thêm authentication, rate limit, monitoring, backup, rollback và CI/CD.
- Bắt buộc hoàn tất legal/security review trước khi dùng trong nghiệp vụ thực tế.

## Nguyên tắc chuyển phase

- Phase sau không được dùng để che lỗi phase trước.
- Không fine-tune để sửa missing corpus hoặc retrieval kém.
- Không phát hành numeric confidence khi chưa calibration.
- Không ghi đè corpus, index, benchmark hoặc model artifact cũ.
- Mọi phase phải lưu config, version, commit hash và báo cáo evaluation tương ứng.
