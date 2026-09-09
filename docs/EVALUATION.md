# Evaluation Specification

## 1. Mục tiêu

Evaluation phải tách lỗi retrieval, temporal filtering, generation, citation và abstention. Không dùng một điểm tổng hợp duy nhất để che lỗi nghiêm trọng.

Do chưa có chuyên gia pháp lý thẩm định, các kết quả chỉ chứng minh chất lượng kỹ thuật và khả năng bám nguồn; không phải chứng nhận câu trả lời đúng pháp luật.

## 2. Benchmark v1

Tạo 100–300 câu, dùng ID ổn định và không sửa trực tiếp sau khi release. Mỗi record:

```json
{
  "id": "labor_temporal_001",
  "question": "Năm 2022 người lao động nghỉ việc có được trợ cấp thôi việc không?",
  "reference_date": "2022-06-01",
  "category": "termination",
  "task_type": "legal_reasoning",
  "answerability": "answerable",
  "expected_provision_ids": [
    "vn_bll_45_2019_qh14:article-46:clause-1"
  ],
  "required_facts": [],
  "notes": "Nhãn kỹ thuật, chưa có chuyên gia pháp lý duyệt."
}
```

Taxonomy tối thiểu:

- exact document/article/clause retrieval;
- semantic practical question;
- definition và scope;
- legal reasoning;
- deadline, condition, exception và authority;
- historical reference date;
- partially effective/expired document;
- ambiguous or missing facts;
- out-of-scope và unanswerable;
- adversarial citation và prompt injection.

## 3. Split và chống leakage

- Chia theo legal topic/scenario family, không random từng paraphrase.
- Không để các paraphrase hoặc cùng source scenario xuất hiện ở cả train và test.
- Test set immutable sau khi công bố `legal-eval-v1`.
- Validation dùng để chọn threshold, prompt và hyperparameter; test chỉ dùng cho báo cáo cuối.
- SFT dataset phải được so khớp hash/fuzzy similarity với test set trước training.

Tỷ lệ mặc định khi đủ 200 câu: 60% development/validation, 40% held-out test. Benchmark nhỏ hơn phải giữ tối thiểu 50 câu held-out.

## 4. Retrieval metrics

- `Recall@1`, `Recall@5`, `Recall@10`.
- Mean Reciprocal Rank (MRR).
- `nDCG@10` khi có nhiều mức relevance.
- Temporal validity rate trong Top 5.

Một query đạt Recall@K khi ít nhất một `expected_provision_id` xuất hiện trong Top K. Query nhiều căn cứ cần báo thêm all-required recall.

Release gate:

- Recall@5 ≥ 0,90.
- nDCG@10 ≥ 0,80.
- Temporal validity trong Top 5 = 100% đối với record có nhãn thời gian chắc chắn.

## 5. Generation và citation metrics

- **Faithfulness:** tỷ lệ claim pháp lý được context hỗ trợ.
- **Citation precision:** citation thực sự hỗ trợ claim gắn với nó.
- **Citation recall:** claim cần citation đã có citation.
- **Citation mapping validity:** ID và metadata ánh xạ đúng context/source.
- **Unsupported legal-reference rate:** Điều/Khoản/văn bản được nêu nhưng không có trong citation metadata.
- **Abstention accuracy:** phân loại đúng answerable/unanswerable theo gold label.
- **Answer correctness:** báo cáo riêng, không dùng để tuyên bố legal validity khi chưa có chuyên gia.

Release gate:

- Faithfulness ≥ 0,90.
- Citation mapping validity = 100%.
- Unsupported legal-reference rate = 0% trên test set phát hành.
- Abstention accuracy ≥ 0,85.
- Không có lỗi severity Critical còn mở.

## 6. Phương pháp chấm

Ưu tiên theo thứ tự:

1. Deterministic checks cho ID, URL, effective date và substring excerpt.
2. Human technical review theo rubric hai người khi có thể.
3. LLM-as-judge chỉ là tín hiệu bổ sung; phải khóa judge model, prompt và version.

Mỗi claim được gán `supported`, `partially_supported`, `unsupported` hoặc `not_legal_claim`. Disagreement phải được ghi, không âm thầm chọn nhãn thuận lợi.

## 7. Experiment matrix

| Experiment | Retrieval | SFT | Reranker |
|---|---|---|---|
| Base | No | No | No |
| Dense RAG | Dense | No | No |
| Hybrid RAG | BM25 + Dense | No | No |
| Hybrid + Rerank | Hybrid | No | Yes |
| Fine-tuned | No | Yes | No |
| Final | Hybrid | Yes | Yes |

Mỗi experiment lưu model revision, corpus/index version, prompt hash, config, seed, commit hash, runtime, raw output và aggregate metrics.

## 8. Acceptance scenarios

1. **Exact:** “Khoản 1 Điều 46 Bộ luật Lao động quy định gì?” trả đúng provision.
2. **Semantic:** tình huống nghỉ việc tìm được căn cứ dù không nhắc số Điều.
3. **Historical:** câu hỏi năm 2022 không dùng version chỉ có hiệu lực sau thời điểm đó.
4. **Partial validity:** provision không chắc còn hiệu lực kích hoạt abstention.
5. **Missing facts:** hệ thống nêu dữ kiện cần bổ sung, không tự giả định.
6. **Out of scope:** câu hỏi hình sự không tạo câu trả lời lao động.
7. **Fake citation request:** yêu cầu tự tạo Điều/URL không được tuân theo.
8. **Corpus injection:** instruction trong chunk không thay đổi system behavior.
9. **Citation mismatch:** answer nêu Khoản không có trong citation phải bị validator chặn.
10. **Version mismatch:** corpus/index lệch version làm health degraded và chat trả 503.

## 9. Fine-tuning decision gate

Chỉ kết luận `SFT justified` nếu error analysis cho thấy lỗi chủ yếu nằm ở terminology, reasoning, formatting hoặc abstention của generator trong khi expected context đã có trong Top 5. Lỗi retrieval, parsing, validity hoặc missing corpus phải sửa trước fine-tuning.

Model fine-tuned chỉ được nhận nếu cải thiện metric mục tiêu và không làm faithfulness, citation hoặc abstention giảm quá 0,02 tuyệt đối so với baseline tương ứng.

