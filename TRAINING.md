# Vietnamese Legal AI — Training and Model Evaluation

## 1. Mục tiêu fine-tuning

Fine-tuning có thể cải thiện:

- hiểu thuật ngữ và cấu trúc pháp lý;
- reasoning trên context đã cung cấp;
- cấu trúc câu trả lời;
- citation-aware answering;
- abstention khi thiếu dữ liệu.

Fine-tuning không dùng để ghi nhớ luật, thay retrieval hoặc sửa corpus thiếu/sai.

## 2. Điều kiện bắt đầu

Chỉ bắt đầu Phase 6 khi:

- corpus đạt data quality gate;
- Recall@5 và nDCG@10 đạt gate;
- RAG với base model đã được đánh giá;
- error analysis cho thấy expected context nằm trong Top 5 nhưng generator vẫn lỗi;
- Phase 5 ghi quyết định `SFT justified`.

Nếu lỗi thuộc parser, validity, missing corpus, retrieval hoặc citation validator, phải sửa component tương ứng trước.

## 3. Base model và stack

Base model: `Qwen/Qwen3-4B`. Revision, license và chat template phải được khóa trước experiment đầu tiên.

Stack dự kiến:

```text
PyTorch
Transformers
Datasets
TRL
PEFT
Accelerate
bitsandbytes
```

MVP dùng LoRA/QLoRA + supervised fine-tuning; không full fine-tune, DPO, GRPO hoặc reinforcement learning.

## 4. SFT dataset contract

Format chuẩn:

```json
{
  "id": "sft_labor_reasoning_001",
  "task_type": "legal_reasoning",
  "source_provenance": ["vn_bll_45_2019_qh14:article-46:clause-1"],
  "prompt": [
    {"role": "system", "content": "Bạn là trợ lý nghiên cứu pháp luật Việt Nam."},
    {"role": "user", "content": "..."}
  ],
  "completion": [
    {"role": "assistant", "content": "..."}
  ]
}
```

Mỗi sample phải có ID, task type, provenance, license/rights note và validation status. Sample không rõ nguồn hoặc chứa dữ liệu cá nhân không được train.

Ưu tiên:

- legal reasoning và practical QA dựa trên context;
- terminology, scope, entailment và contradiction;
- explain-simple và summarization;
- citation format và abstention.

Không ưu tiên sample chỉ yêu cầu model chép nguyên văn một Điều vì làm tăng memorization mà không cải thiện grounded reasoning.

## 5. Split và leakage control

- Split theo scenario family, legal topic và source provision.
- Không để paraphrase/cùng tình huống ở cả train và held-out test.
- So khớp exact hash và semantic similarity giữa SFT data với `legal-eval-v1`.
- Test set không dùng để chọn epoch, threshold, prompt hoặc LoRA config.
- Mọi thay đổi dataset tạo version mới; không overwrite.

## 6. QLoRA defaults cho experiment đầu

Defaults là điểm xuất phát, không phải cấu hình đã tối ưu:

```yaml
quantization:
  load_in_4bit: true
  quant_type: nf4
  double_quant: true
  compute_dtype: float16
lora:
  r: 16
  alpha: 32
  dropout: 0.05
  target_modules:
    - q_proj
    - k_proj
    - v_proj
    - o_proj
    - gate_proj
    - up_proj
    - down_proj
training:
  max_length: 2048
  batch_size: 1
  gradient_accumulation_steps: 8
  learning_rate: 0.0001
  epochs: 2
  gradient_checkpointing: true
  completion_only_loss: true
```

Colab/Kaggle GPU khoảng 16 GB bắt đầu với sequence length 1.024 nếu 2.048 gây OOM. Không cộng VRAM của nhiều GPU như bộ nhớ thống nhất.

## 7. Experiment discipline

Mỗi experiment chỉ đổi một nhóm biến có lý do rõ ràng. Lưu:

- base model/revision và tokenizer/chat template;
- dataset version và split manifest;
- resolved training/LoRA/quantization config;
- seed, environment, package versions và commit hash;
- checkpoints, logs, raw predictions và evaluation report.

Không chọn model chỉ vì training loss thấp.

## 8. Evaluation matrix

| System | Retrieval | Fine-tune | Reranker | Mục đích |
|---|---|---|---|---|
| Qwen3-4B Base | No | No | No | Baseline model |
| Base + Dense RAG | Dense | No | No | Dense contribution |
| Base + Hybrid RAG | Hybrid | No | No | Sparse contribution |
| Base + Hybrid + Reranker | Hybrid | No | Yes | Reranker contribution |
| Fine-tuned Qwen3 | No | Yes | No | Adapter behavior |
| Final System | Hybrid | Yes | Yes | End-to-end candidate |

Metrics và rubric nằm trong [Evaluation specification](docs/EVALUATION.md).

## 9. Model selection gate

Adapter chỉ được nhận nếu:

- metric mục tiêu đã nêu trong quyết định `SFT justified` cải thiện;
- faithfulness, citation và abstention không giảm quá 0,02 tuyệt đối;
- unsupported legal-reference rate vẫn bằng 0% trên release test set;
- không phát sinh lỗi Critical;
- kết quả tái lập được từ config/artifact đã lưu.

Nếu không đạt, final system tiếp tục dùng base model + RAG.

## 10. Versioning

Ví dụ:

```text
legal-sft-v1
legal-qwen3-lora-v0.1
legal-qwen3-lora-v0.2
legal-qwen3-lora-v1.0
```

Mỗi model version tham chiếu base revision, dataset version, training config, LoRA config, commit hash và evaluation result. Adapter lưu độc lập với base model.

## 11. Definition of Done

- Training tái lập được và có validation split.
- Leakage checks đạt.
- So sánh trực tiếp với base model và base + RAG.
- Hallucination, citation, faithfulness và abstention được đo.
- Adapter/model/dataset có version và provenance.
- Fine-tuned model đã test trong RAG, không chỉ standalone.
- Model card ghi rõ chưa có chuyên gia pháp lý thẩm định.
