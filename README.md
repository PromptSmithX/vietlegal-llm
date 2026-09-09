# Vietnamese Legal AI

Trợ lý nghiên cứu pháp luật Việt Nam sử dụng Retrieval-Augmented Generation (RAG) để tìm căn cứ, kiểm tra hiệu lực theo thời gian và tạo câu trả lời có trích dẫn.

> Trạng thái: **Documentation stage**. Repository hiện chứa đặc tả và kế hoạch; chưa có source code, corpus hoặc model artifact.

## Mục tiêu MVP

MVP tập trung vào Bộ luật Lao động 2019 và các văn bản trực tiếp hướng dẫn. Hệ thống phải:

- hiểu câu hỏi pháp luật bằng tiếng Việt;
- tìm đúng văn bản, Điều, Khoản, Điểm có hiệu lực tại thời điểm được hỏi;
- chỉ kết luận từ context được truy xuất;
- trả citation do backend ánh xạ tới nguồn chính thức;
- từ chối kết luận khi căn cứ chưa đủ;
- không lưu hội thoại hoặc thông tin nhận dạng người dùng.

MVP là công cụ nghiên cứu/demo, không thay thế tư vấn của luật sư hoặc cơ quan có thẩm quyền.

## Nguyên tắc thiết kế

```text
LLM = reasoning và trình bày
RAG = kiến thức pháp luật, hiệu lực và nguồn
Validator = ràng buộc citation và chống căn cứ bịa đặt
```

Fine-tuning không được dùng để ghi nhớ toàn bộ pháp luật. Corpus có version và provenance là nguồn sự thật của hệ thống.

## Thứ tự đọc tài liệu

1. [Product requirements](docs/PRODUCT_REQUIREMENTS.md)
2. [Architecture](ARCHITECTURE.md)
3. [Data specification](docs/DATA_SPEC.md)
4. [RAG specification](docs/RAG_SPEC.md)
5. [API specification](docs/API_SPEC.md)
6. [Evaluation](docs/EVALUATION.md)
7. [Training](TRAINING.md)
8. [Safety and governance](docs/SAFETY_AND_GOVERNANCE.md)
9. [Development and operations](docs/DEVELOPMENT_AND_OPERATIONS.md)
10. [Architecture decisions](docs/DECISIONS.md)
11. [Implementation plan](PLAN.md)
12. [High-level roadmap](ROADMAP.md)

## Kiến trúc mục tiêu

```text
Question
  → Query Analyzer + reference_date
  → BM25 Top 100 + Dense Top 100
  → Temporal/metadata filter
  → Reciprocal Rank Fusion Top 30
  → Legal Reranker Top 5
  → Context Builder
  → Qwen3-4B
  → Citation Validator
  → Structured Answer
```

Chi tiết hành vi từng stage nằm trong [RAG specification](docs/RAG_SPEC.md).

## Tech stack dự kiến

| Layer | MVP | Production |
|---|---|---|
| Generator | Qwen/Qwen3-4B + Transformers | Qwen3-4B + vLLM |
| Fine-tuning | LoRA/QLoRA, TRL, PEFT | Adapter đã qua evaluation gate |
| Sparse retrieval | BM25 | BM25 hoặc search engine tương thích |
| Dense retrieval | Qwen3-Embedding-0.6B + FAISS | Qdrant |
| Reranker | Qwen3-Reranker-0.6B | Model đã benchmark tốt nhất |
| Backend | FastAPI | FastAPI |
| Frontend | Streamlit | Next.js/React |
| Metadata | File artifacts có version | PostgreSQL |
| Runtime | Local + Colab/Kaggle | Docker trên Linux GPU |

## API MVP

```text
POST /api/chat
POST /api/search
GET  /api/documents/{document_id}
GET  /api/health
```

API stateless, không streaming, không authentication trong MVP. Chi tiết request, response và lỗi nằm trong [API specification](docs/API_SPEC.md).

## Bắt đầu triển khai

Thực hiện theo acceptance gate trong [PLAN.md](PLAN.md), bắt đầu từ Phase 0. `ROADMAP.md` chỉ mô tả lộ trình cấp cao; `PLAN.md` là checklist triển khai chính thức.
