# Vietnamese Legal AI — Roadmap

## Tổng quan

```text
PHASE 0  Product Definition
PHASE 1  Baseline LLM
PHASE 2  Legal Corpus
PHASE 3  Retriever
PHASE 4  RAG MVP
PHASE 5  Evaluation
PHASE 6  Fine-tuning
PHASE 7  Fine-tuned LLM + RAG
PHASE 8  Backend + Frontend
PHASE 9  Production
```

---

# PHASE 0 — Định nghĩa sản phẩm

Mục tiêu MVP:

> Trợ lý tra cứu và giải thích pháp luật Việt Nam có căn cứ nguồn.

Hệ thống cần có 5 khả năng:

1. Hiểu câu hỏi pháp luật bằng tiếng Việt.
2. Tìm đúng Điều/Khoản.
3. Phân tích dựa trên căn cứ tìm được.
4. Trích dẫn nguồn.
5. Không bịa nếu không đủ căn cứ.

Output mong muốn:

```text
Kết luận

Phân tích

Căn cứ pháp lý

Lưu ý
```

Nếu context không đủ:

```text
Các căn cứ được truy xuất hiện chưa đủ để đưa ra
kết luận chắc chắn cho trường hợp này.
```

---

# PHASE 1 — Baseline LLM

Base model:

```text
Qwen/Qwen3-4B
```

Việc cần làm:

- Load model trên Colab/Kaggle.
- Test inference.
- Tạo bộ benchmark riêng khoảng 100–300 câu.
- Lưu toàn bộ kết quả baseline.
- Không fine-tune ở phase này.

Nhóm benchmark:

- Legal Definition
- Legal QA
- Legal Reasoning
- Legal Classification
- Legal Basis Retrieval
- Tình huống pháp lý
- Thời hạn
- Mức phạt
- Điều kiện
- Ngoại lệ
- Thẩm quyền
- Unanswerable Questions

---

# PHASE 2 — Legal Corpus

Nguồn ưu tiên:

- Cơ sở dữ liệu quốc gia về pháp luật.
- Nguồn pháp luật chính thức.
- Dataset nghiên cứu chỉ dùng bổ sung.

Các loại văn bản:

- Hiến pháp
- Bộ luật
- Luật
- Nghị quyết
- Nghị định
- Quyết định
- Thông tư
- Thông tư liên tịch

## Data schema

```json
{
  "document_id": "BLLD_2019",
  "document_number": "45/2019/QH14",
  "title": "Bộ luật Lao động",
  "document_type": "Bộ luật",
  "issuer": "Quốc hội",
  "issued_date": "2019-11-20",
  "effective_from": "2021-01-01",
  "effective_to": null,
  "status": "effective",
  "chapter": "Chương III",
  "article": "Điều 46",
  "clause": "Khoản 1",
  "point": null,
  "text": "...",
  "source_url": "...",
  "amended_by": [],
  "replaces": []
}
```

## Parse hierarchy

```text
Văn bản
↓
Chương
↓
Mục
↓
Điều
↓
Khoản
↓
Điểm
```

Không chunk văn bản đơn thuần theo số ký tự.

---

# PHASE 3 — Retriever

Xây theo thứ tự:

1. Dense retrieval
2. FAISS
3. BM25
4. Hybrid search
5. RRF
6. Reranker
7. Evaluation

Architecture:

```text
Query
 ├─ BM25 → Top 40
 └─ Dense → Top 40
        ↓
       RRF
        ↓
     Top 30
        ↓
    Reranker
        ↓
     Top 5
```

Embedding model:

```text
Qwen/Qwen3-Embedding-0.6B
```

Reranker:

```text
Qwen/Qwen3-Reranker-0.6B
```

---

# PHASE 4 — RAG MVP

Pipeline:

```text
Question
↓
Query Analyzer
↓
Temporal Filter
↓
BM25 + Dense
↓
RRF
↓
Reranker
↓
Context Builder
↓
Qwen3-4B
↓
Citation Validator
↓
Answer
```

RAG phase đầu dùng Qwen3-4B nguyên bản.

Không fine-tune trước khi đánh giá RAG baseline.

---

# PHASE 5 — Evaluation

## Retrieval

Đo:

- Recall@1
- Recall@5
- Recall@10
- MRR
- nDCG@10

## Generation

Đo:

- Answer Correctness
- Faithfulness
- Citation Precision
- Citation Recall
- Citation Accuracy
- Hallucination Rate
- Abstention Accuracy

Experiment matrix:

| Experiment | Retrieval | SFT | Reranker |
|---|---|---|---|
| Base | No | No | No |
| Dense RAG | Dense | No | No |
| Hybrid RAG | BM25 + Dense | No | No |
| Hybrid + Rerank | Hybrid | No | Yes |
| Fine-tuned | No | Yes | No |
| Final | Hybrid | Yes | Yes |

---

# PHASE 6 — Fine-tuning

Chỉ bắt đầu khi:

```text
Corpus      ✔
Retriever   ✔
RAG         ✔
Evaluation  ✔
```

Fine-tuning:

```text
Qwen3-4B
+
QLoRA / LoRA
+
SFT
```

Mục tiêu:

- cải thiện hiểu thuật ngữ;
- cải thiện legal reasoning;
- cải thiện cấu trúc câu trả lời;
- giảm hallucination;
- học abstention;
- học phong cách giải thích pháp lý.

Không dùng fine-tuning để ghi nhớ luật.

---

# PHASE 7 — Fine-tuned LLM + RAG

Architecture cuối của core AI:

```text
User
↓
Query Analyzer
↓
BM25 + Dense
↓
RRF
↓
Metadata / Temporal Filter
↓
Reranker
↓
Top Contexts
↓
Fine-tuned Qwen3-4B
↓
Citation Validator
↓
Answer
```

Sau phase này benchmark lại toàn hệ thống.

---

# PHASE 8 — Backend + Frontend

Backend:

```text
FastAPI
```

Endpoints:

```text
POST /api/chat
POST /api/search
GET  /api/document/{id}
GET  /api/health
```

MVP Frontend:

```text
Streamlit
```

Production Frontend:

```text
Next.js / React
```

---

# PHASE 9 — Production

Thay đổi:

```text
FAISS
→
Qdrant
```

```text
Transformers inference
→
vLLM
```

Thêm:

- PostgreSQL
- Docker
- Docker Compose
- Logging
- Monitoring
- Dataset versioning
- Model versioning
- CI/CD

---

# Checklist 30 bước

1. Tạo repository.
2. Tạo Python environment.
3. Load Qwen3-4B.
4. Chạy inference baseline.
5. Tạo 100–300 câu evaluation.
6. Thu thập legal corpus.
7. Parse Văn bản → Chương → Điều → Khoản → Điểm.
8. Chuẩn hóa metadata.
9. Thêm dữ liệu hiệu lực.
10. Build embedding pipeline.
11. Build FAISS.
12. Build BM25.
13. Build Hybrid Retrieval.
14. Thêm RRF.
15. Build reranker.
16. Evaluate retrieval.
17. Build RAG bằng base Qwen.
18. Build citation system.
19. Build temporal filtering.
20. Evaluate RAG.
21. Chuẩn bị SFT dataset.
22. QLoRA Qwen3-4B.
23. Evaluate fine-tuned model.
24. Ghép fine-tuned model + RAG.
25. Evaluate toàn hệ thống.
26. Build FastAPI.
27. Build Streamlit demo.
28. Migrate FAISS → Qdrant.
29. Migrate Transformers → vLLM.
30. Dockerize và deploy.
