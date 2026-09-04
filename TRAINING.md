# Vietnamese Legal AI — Training & Evaluation

## 1. Training Philosophy

Fine-tuning không có nhiệm vụ ghi nhớ toàn bộ pháp luật.

Fine-tuning nên giúp model:

- hiểu thuật ngữ pháp lý;
- hiểu cấu trúc luật;
- hiểu tình huống;
- legal reasoning;
- legal classification;
- explanation;
- summarization;
- contradiction / entailment;
- citation-aware answering;
- abstention khi thiếu dữ liệu.

RAG chịu trách nhiệm cung cấp:

- Điều;
- Khoản;
- Điểm;
- văn bản;
- hiệu lực;
- phiên bản;
- nguồn;
- căn cứ.

---

# 2. Base Model

```text
Qwen/Qwen3-4B
```

Không full fine-tune ở giai đoạn đầu.

Phương pháp:

```text
QLoRA / LoRA
+
Supervised Fine-Tuning
```

---

# 3. Training Stack

```text
PyTorch
Transformers
Datasets
TRL
PEFT
Accelerate
bitsandbytes
```

Cài:

```bash
pip install -U \
transformers \
datasets \
trl \
peft \
accelerate \
bitsandbytes
```

---

# 4. Baseline Inference

```python
import torch

from transformers import (
    AutoTokenizer,
    AutoModelForCausalLM,
)

MODEL_NAME = "Qwen/Qwen3-4B"

tokenizer = AutoTokenizer.from_pretrained(
    MODEL_NAME
)

model = AutoModelForCausalLM.from_pretrained(
    MODEL_NAME,
    torch_dtype=torch.float16,
    device_map="auto",
)
```

---

# 5. Evaluation Dataset

Trước khi train cần tạo bộ evaluation cố định.

Ví dụ:

```json
{
  "id": "labor_001",
  "question": "Người lao động nghỉ việc trong trường hợp nào được hưởng trợ cấp thôi việc?",
  "category": "labor",
  "type": "legal_reasoning",
  "expected_articles": [
    "Điều 46 Bộ luật Lao động 2019"
  ]
}
```

Khoảng:

```text
100–300 câu cho benchmark riêng
```

Các loại task:

- Legal QA
- Legal Reasoning
- Legal Basis
- Legal Classification
- Legal Entailment
- Legal Contradiction
- Summarization
- Scope Identification
- Practical QA
- Unanswerable Questions

---

# 6. SFT Dataset Format

Recommended format:

```json
{
  "prompt": [
    {
      "role": "system",
      "content": "Bạn là trợ lý nghiên cứu pháp luật Việt Nam."
    },
    {
      "role": "user",
      "content": "..."
    }
  ],
  "completion": [
    {
      "role": "assistant",
      "content": "..."
    }
  ]
}
```

Nếu dataset có `messages`:

```python
def convert(example):
    messages = example["messages"]

    return {
        "prompt": messages[:-1],
        "completion": [messages[-1]]
    }
```

---

# 7. Dataset Strategy

Không đổ toàn bộ dataset lớn vào train ngay.

Bắt đầu bằng tập nhỏ, sạch và đa dạng.

Ưu tiên:

```text
legal_qa
legal_reasoning
legal_basis
practical_qa
explain_simple
scope
summarize
classification
entailment
contradiction
```

Nên tránh quá nhiều sample kiểu:

```text
Question:
Điều 15 nói gì?

Answer:
Nguyên văn Điều 15...
```

vì đây thiên về memorization.

---

# 8. Quantization

```python
import torch

from transformers import BitsAndBytesConfig

quant_config = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_quant_type="nf4",
    bnb_4bit_use_double_quant=True,
    bnb_4bit_compute_dtype=torch.float16,
)
```

---

# 9. Tokenizer

```python
from transformers import AutoTokenizer

MODEL_NAME = "Qwen/Qwen3-4B"

tokenizer = AutoTokenizer.from_pretrained(
    MODEL_NAME
)

if tokenizer.pad_token is None:
    tokenizer.pad_token = tokenizer.eos_token
```

---

# 10. LoRA Config

```python
from peft import LoraConfig

lora_config = LoraConfig(
    r=16,
    lora_alpha=32,
    lora_dropout=0.05,

    target_modules=[
        "q_proj",
        "k_proj",
        "v_proj",
        "o_proj",
        "gate_proj",
        "up_proj",
        "down_proj",
    ],

    bias="none",
    task_type="CAUSAL_LM",
)
```

---

# 11. Training Configuration

```python
from trl import SFTConfig

training_args = SFTConfig(
    output_dir="./legal-qwen3",

    max_length=2048,

    per_device_train_batch_size=1,
    per_device_eval_batch_size=1,

    gradient_accumulation_steps=8,

    learning_rate=1e-4,
    num_train_epochs=2,

    fp16=True,
    gradient_checkpointing=True,

    logging_steps=10,

    eval_strategy="steps",
    eval_steps=200,

    save_strategy="steps",
    save_steps=200,
    save_total_limit=2,

    completion_only_loss=True,

    report_to="none",
)
```

---

# 12. Trainer

```python
from trl import SFTTrainer

trainer = SFTTrainer(
    model=MODEL_NAME,
    args=training_args,

    train_dataset=train_ds,
    eval_dataset=val_ds,

    processing_class=tokenizer,

    quantization_config=quant_config,

    peft_config=lora_config,
)
```

Train:

```python
trainer.train()
```

---

# 13. Save Adapter

```python
trainer.save_model(
    "./legal-qwen3-lora"
)

tokenizer.save_pretrained(
    "./legal-qwen3-lora"
)
```

Kết quả:

```text
Qwen3-4B
+
Legal LoRA Adapter
```

---

# 14. Kaggle / Colab Config

Cho GPU khoảng 16GB:

```text
QLoRA
batch_size = 1
gradient_accumulation = 8
sequence_length = 1024 → 2048
gradient_checkpointing = True
```

Không giả định:

```text
2 × T4 16GB = 32GB unified VRAM
```

---

# 15. Fine-tuning Experiments

## Experiment 1

```text
r = 16
learning_rate = 1e-4
epoch = 1
sequence_length = 1024
```

## Experiment 2

```text
r = 16
learning_rate = 1e-4
epoch = 2
sequence_length = 2048
```

## Experiment 3

```text
r = 32
learning_rate = 1e-4
epoch = 2
sequence_length = 2048
```

Chỉ thay đổi một số ít biến mỗi experiment.

Không chọn model chỉ vì training loss thấp.

---

# 16. Retrieval Evaluation

Metrics:

```text
Recall@1
Recall@5
Recall@10
MRR
nDCG@10
```

Ví dụ:

```text
Expected:
Điều 46

Retrieved Top 5:
Điều 42
Điều 46
Điều 48
Điều 35
Điều 40

→ Recall@5 = 1
```

---

# 17. Generation Evaluation

Metrics:

```text
Answer Correctness
Faithfulness
Citation Precision
Citation Recall
Citation Accuracy
Hallucination Rate
Abstention Accuracy
```

Trong Legal AI, cần ưu tiên:

```text
Citation Accuracy
Faithfulness
Hallucination Rate
Abstention Accuracy
```

---

# 18. Experiment Matrix

| System | Retrieval | Fine-tune | Reranker | Evaluation |
|---|---|---|---|---|
| Qwen3-4B Base | No | No | No | Baseline |
| Base + Dense RAG | Dense | No | No | Compare |
| Base + Hybrid RAG | Hybrid | No | No | Compare |
| Base + Hybrid + Reranker | Hybrid | No | Yes | Compare |
| Fine-tuned Qwen3 | No | Yes | No | Compare |
| Final System | Hybrid | Yes | Yes | Final |

---

# 19. Training Workflow

```text
Prepare Dataset
↓
Validate Dataset
↓
Train LoRA
↓
Evaluate on held-out set
↓
Run legal benchmark
↓
Compare with base model
↓
Test hallucination
↓
Test citation behavior
↓
Merge with RAG
↓
Evaluate full system
```

---

# 20. Model Selection

Không chọn model dựa trên:

```text
training_loss nhỏ nhất
```

Chọn dựa trên:

```text
Legal Benchmark
+
Faithfulness
+
Citation Accuracy
+
Hallucination
+
Abstention
+
RAG Performance
```

---

# 21. Model Versioning

Ví dụ:

```text
legal-qwen3-lora-v0.1
legal-qwen3-lora-v0.2
legal-qwen3-lora-v1.0
```

Mỗi version cần lưu:

```text
Base Model
Dataset Version
Training Config
LoRA Config
Commit Hash
Evaluation Results
```

---

# 22. Dataset Versioning

```text
legal-corpus-v1
legal-corpus-v2

legal-sft-v1
legal-sft-v2

legal-eval-v1
legal-eval-v2
```

Không overwrite dataset cũ.

---

# 23. Experiment Tracking

Có thể dùng:

```text
Weights & Biases
```

hoặc:

```text
MLflow
```

Track:

- training loss;
- validation loss;
- learning rate;
- epoch;
- model version;
- dataset version;
- retrieval metrics;
- generation metrics;
- hallucination metrics;
- citation metrics.

---

# 24. Definition of Done cho Fine-tuning

Fine-tuning phase hoàn thành khi:

- Training reproducible.
- Có validation split.
- Có fixed benchmark.
- Có so sánh với base model.
- Có đo hallucination.
- Có đo citation accuracy.
- Có model versioning.
- Có dataset versioning.
- Adapter được lưu độc lập.
- Fine-tuned model đã được test cùng RAG.
