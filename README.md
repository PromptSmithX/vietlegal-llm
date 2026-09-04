# Vietnamese Legal AI

## Mục tiêu

Xây dựng một hệ thống AI hỗ trợ tra cứu và giải thích pháp luật Việt Nam có khả năng:

- Hiểu câu hỏi pháp luật bằng tiếng Việt.
- Tìm đúng văn bản, Điều, Khoản, Điểm liên quan.
- Phân tích dựa trên căn cứ pháp luật.
- Trích dẫn nguồn rõ ràng.
- Hạn chế hallucination.
- Nhận biết hiệu lực của văn bản theo thời gian.
- Fine-tune LLM để cải thiện khả năng hiểu và suy luận pháp lý.

## Nguyên tắc thiết kế

> LLM không phải database pháp luật.  
> LLM là reasoning engine.  
> RAG là nơi cung cấp căn cứ pháp luật.

Kiến thức pháp luật cập nhật nên được cung cấp bằng Retrieval-Augmented Generation (RAG), trong khi fine-tuning tập trung vào:

- hiểu thuật ngữ pháp lý;
- hiểu cấu trúc văn bản;
- suy luận tình huống;
- giải thích quy định;
- phân loại;
- viết câu trả lời theo phong cách pháp lý.

## Kiến trúc tổng quát

```text
User Question
      ↓
Query Analyzer
      ↓
BM25 + Dense Retrieval
      ↓
Reciprocal Rank Fusion
      ↓
Temporal / Metadata Filter
      ↓
Legal Reranker
      ↓
Top Contexts
      ↓
Fine-tuned Qwen3-4B
      ↓
Citation Validator
      ↓
Answer
```

## Tech Stack

| Layer | Technology |
|---|---|
| Base LLM | Qwen/Qwen3-4B |
| Fine-tuning | LoRA / QLoRA |
| Training | Transformers + TRL + PEFT |
| Quantization | bitsandbytes |
| Dataset | Hugging Face Datasets |
| Embedding | Qwen/Qwen3-Embedding-0.6B |
| Sparse Retrieval | BM25 |
| Prototype Vector Search | FAISS |
| Production Vector DB | Qdrant |
| Reranker | Qwen/Qwen3-Reranker-0.6B |
| Backend | FastAPI |
| MVP Frontend | Streamlit |
| Production Frontend | Next.js / React |
| Metadata DB | PostgreSQL |
| LLM Serving | vLLM |
| Experiment Tracking | W&B hoặc MLflow |
| Deployment | Docker |

## MVP

MVP được coi là hoàn thành khi hệ thống có thể:

- nhận câu hỏi pháp luật bằng tiếng Việt;
- tìm Điều/Khoản liên quan;
- trả lời dựa trên context;
- dẫn nguồn chính xác;
- không tự tạo Điều/Khoản;
- từ chối kết luận khi không đủ căn cứ;
- có giao diện demo.

MVP chưa cần:

- Agents;
- Multi-agent;
- Knowledge Graph;
- DPO;
- GRPO;
- Reinforcement Learning;
- Distributed Training.

## Cấu trúc repository đề xuất

```text
vietnamese-legal-ai/
│
├── README.md
├── ROADMAP.md
├── ARCHITECTURE.md
├── TRAINING.md
│
├── requirements.txt
├── pyproject.toml
│
├── notebooks/
│   ├── 01_baseline.ipynb
│   ├── 02_data_exploration.ipynb
│   ├── 03_embedding.ipynb
│   ├── 04_retrieval.ipynb
│   ├── 05_rag.ipynb
│   ├── 06_evaluation.ipynb
│   └── 07_finetune.ipynb
│
├── data/
│   ├── raw/
│   ├── processed/
│   └── evaluation/
│
├── src/
│   ├── ingestion/
│   │   ├── crawler.py
│   │   ├── parser.py
│   │   └── chunker.py
│   ├── retrieval/
│   │   ├── bm25.py
│   │   ├── dense.py
│   │   ├── hybrid.py
│   │   └── reranker.py
│   ├── rag/
│   │   ├── prompt.py
│   │   ├── context.py
│   │   └── pipeline.py
│   ├── model/
│   │   └── generator.py
│   └── evaluation/
│       ├── retrieval.py
│       ├── generation.py
│       └── citations.py
│
├── training/
│   ├── prepare_sft.py
│   ├── train_lora.py
│   ├── evaluate.py
│   └── config.yaml
│
├── api/
│   └── main.py
│
├── frontend/
├── docker/
├── tests/
└── scripts/
```

## Thứ tự ưu tiên

1. Baseline Model
2. Legal Corpus
3. Retrieval
4. RAG
5. Evaluation
6. Fine-tuning
7. Backend / UI
8. Production

Chi tiết xem:

- `ROADMAP.md`
- `ARCHITECTURE.md`
- `TRAINING.md`
