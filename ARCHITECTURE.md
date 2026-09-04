# Vietnamese Legal AI — Architecture

## 1. System Architecture

```text
┌────────────────────────────────────────────┐
│                  CLIENT                    │
│            Next.js / Streamlit             │
└──────────────────────┬─────────────────────┘
                       │
                       ▼
┌────────────────────────────────────────────┐
│                 FastAPI                    │
└──────────────────────┬─────────────────────┘
                       │
                       ▼
┌────────────────────────────────────────────┐
│              Query Analyzer                │
│                                            │
│  - Date Extraction                         │
│  - Law Number Detection                    │
│  - Article Detection                       │
│  - Query Normalization                     │
└──────────────────────┬─────────────────────┘
                       │
              ┌────────┴─────────┐
              ▼                  ▼
        ┌──────────┐        ┌──────────┐
        │   BM25   │        │ Qwen3    │
        │          │        │Embedding │
        └─────┬────┘        └────┬─────┘
              │                  │
              └────────┬─────────┘
                       ▼
                      RRF
                       │
                       ▼
                Temporal Filter
                       │
                       ▼
              Qwen3 Reranker
                       │
                       ▼
                   Context
                       │
                       ▼
            Fine-tuned Qwen3-4B
                       │
                       ▼
               Citation Validator
                       │
                       ▼
                   Response
```

---

# 2. Legal Corpus Design

## Hierarchy

```text
Văn bản
│
├── Chương
│   ├── Mục
│   ├── Điều
│   │   ├── Khoản
│   │   │   ├── Điểm a
│   │   │   ├── Điểm b
│   │   │   └── Điểm c
```

## Chunking

Không dùng:

```python
text[:1000]
text[1000:2000]
```

Nên chunk theo đơn vị pháp lý tự nhiên:

```text
Điều
Khoản
Điểm
```

Nếu một Điều ngắn:

```text
1 Điều = 1 chunk
```

Nếu dài:

```text
Điều
├── Chunk 1: Khoản 1 + Khoản 2
└── Chunk 2: Khoản 3 + Khoản 4
```

Mỗi chunk phải giữ header:

```text
Tên văn bản
Chương
Điều
Khoản
Nội dung
```

---

# 3. Metadata Schema

```json
{
  "document_id": "...",
  "document_number": "...",
  "title": "...",
  "document_type": "...",
  "issuer": "...",
  "issued_date": "...",
  "effective_from": "...",
  "effective_to": null,
  "status": "effective",
  "chapter": "...",
  "article": "...",
  "clause": "...",
  "point": "...",
  "text": "...",
  "source_url": "...",
  "amended_by": [],
  "replaces": []
}
```

Các field quan trọng nhất cho legal RAG:

```text
document_number
article
clause
point
effective_from
effective_to
status
source_url
```

---

# 4. Temporal Legal Retrieval

Pháp luật thay đổi theo thời gian.

Nếu user hỏi:

```text
Năm 2022 quy định này thế nào?
```

hệ thống không được dùng mặc định văn bản hiện hành năm 2026.

Flow:

```text
Question
↓
Extract reference_date
↓
Retrieve candidates
↓
Filter by effective date
```

Logic:

```text
effective_from <= reference_date

AND

(
    effective_to IS NULL
    OR
    effective_to >= reference_date
)
```

Nếu câu hỏi không có thời điểm:

```text
reference_date = current_date
```

---

# 5. Hybrid Retrieval

## BM25

Tốt cho:

```text
Điều 46
Khoản 2 Điều 15
45/2019/QH14
12/2022/NĐ-CP
```

## Dense Retrieval

Tốt cho query ngữ nghĩa:

```text
Công ty không thanh toán tiền lương sau khi tôi nghỉ việc
thì tôi có quyền gì?
```

## Hybrid

```text
BM25 Top 40
+
Dense Top 40
↓
RRF
↓
Top 30
```

---

# 6. Reciprocal Rank Fusion

```text
RRF(d) = Σ 1 / (k + rank(d))
```

Reference implementation:

```python
def rrf(rankings, k=60):
    scores = {}

    for ranking in rankings:
        for rank, doc_id in enumerate(ranking):
            scores[doc_id] = (
                scores.get(doc_id, 0)
                + 1 / (k + rank + 1)
            )

    return sorted(
        scores.items(),
        key=lambda x: x[1],
        reverse=True
    )
```

---

# 7. Dense Retrieval

Embedding model:

```text
Qwen/Qwen3-Embedding-0.6B
```

Example:

```python
from sentence_transformers import SentenceTransformer

embedder = SentenceTransformer(
    "Qwen/Qwen3-Embedding-0.6B"
)

vectors = embedder.encode(
    documents,
    normalize_embeddings=True,
    batch_size=16
)
```

---

# 8. FAISS MVP

```python
import faiss
import numpy as np

vectors = np.asarray(vectors, dtype="float32")

index = faiss.IndexFlatIP(
    vectors.shape[1]
)

index.add(vectors)
```

Query:

```python
query_vector = embedder.encode(
    [question],
    normalize_embeddings=True
).astype("float32")

scores, ids = index.search(
    query_vector,
    40
)
```

---

# 9. BM25 MVP

```python
from rank_bm25 import BM25Okapi

tokenized_corpus = [
    doc.lower().split()
    for doc in documents
]

bm25 = BM25Okapi(
    tokenized_corpus
)
```

Sau MVP nên cải thiện tokenizer tiếng Việt.

---

# 10. Reranker

Model:

```text
Qwen/Qwen3-Reranker-0.6B
```

Flow:

```text
Hybrid Top 30
↓
Cross Encoder
↓
Top 5–8
```

---

# 11. RAG Context Format

```text
[C1]

Văn bản:
Bộ luật Lao động

Số:
45/2019/QH14

Điều:
Điều 46

Khoản:
Khoản 1

Hiệu lực:
2021-01-01 → hiện hành

Nội dung:
...

---

[C2]

...
```

Model dùng token citation:

```text
Theo [C1] ...
```

Backend map:

```text
[C1]
→ document_id
→ article
→ source_url
```

Không để LLM tự tạo URL.

---

# 12. RAG Prompt

```text
Bạn là hệ thống hỗ trợ tra cứu pháp luật Việt Nam.

Bạn chỉ được đưa ra kết luận dựa trên
CĂN CỨ PHÁP LUẬT được cung cấp.

Yêu cầu:

1. Không tự tạo Điều, Khoản hoặc tên văn bản.
2. Mỗi kết luận pháp lý phải gắn với căn cứ.
3. Nếu căn cứ không đủ, nói rõ rằng chưa đủ căn cứ.
4. Ưu tiên văn bản có hiệu lực tại thời điểm được hỏi.
5. Không tự tạo URL hoặc nguồn.

Trả lời theo cấu trúc:

Kết luận

Phân tích

Căn cứ pháp lý

Lưu ý
```

---

# 13. Citation Validation

Sau generation:

```text
Generated Answer
↓
Extract [C1], [C2], ...
↓
Validate citation IDs
↓
Map source metadata
↓
Return response
```

Validator cần đảm bảo:

- Citation ID tồn tại.
- Citation thuộc context đã cung cấp.
- Không có URL tự sinh.
- Không có Điều/Khoản không xuất hiện trong context.
- Source trả về từ metadata backend.

---

# 14. Vector Database Migration

MVP:

```text
FAISS
```

Production:

```text
Qdrant
```

Qdrant payload:

```json
{
  "document_number": "45/2019/QH14",
  "title": "Bộ luật Lao động",
  "article": "Điều 46",
  "clause": "Khoản 1",
  "effective_from": "2021-01-01",
  "effective_to": null,
  "status": "effective",
  "source_url": "..."
}
```

---

# 15. Backend API

```text
POST /api/chat
POST /api/search
GET  /api/document/{id}
GET  /api/health
```

Request:

```json
{
  "question": "Tôi nghỉ việc có được trợ cấp thôi việc không?",
  "reference_date": "2026-09-04"
}
```

Response:

```json
{
  "answer": "...",
  "citations": [
    {
      "document": "Bộ luật Lao động",
      "article": "Điều 46",
      "clause": "Khoản 1",
      "source": "..."
    }
  ],
  "confidence": 0.87
}
```

---

# 16. Production Components

```text
Frontend        Next.js
Backend         FastAPI
Generator       vLLM
Vector DB       Qdrant
Metadata DB     PostgreSQL
Container       Docker
Monitoring      Prometheus / Grafana hoặc SaaS
Experiment      W&B / MLflow
Model Storage   Hugging Face Hub
```
