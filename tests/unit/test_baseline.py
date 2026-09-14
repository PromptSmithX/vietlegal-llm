from __future__ import annotations

import json
from pathlib import Path

import pytest

from vietlegal.evaluation.baseline import (
    Answerability,
    BenchmarkRecord,
    BenchmarkSplit,
    load_benchmark,
    parse_baseline_output,
    summarize_predictions,
    validate_benchmark,
)
from vietlegal.model.baseline import (
    BaselineConfig,
    load_baseline_config,
    render_prompt,
    run_records,
    write_run_artifacts,
)


class FakeGenerator:
    def generate(self, prompt: str) -> tuple[str, int, int, float]:
        if "001" in prompt:
            return ("not-json", 4, 2, 3.0)
        return (
            json.dumps(
                {
                    "status": "answered",
                    "conclusion": "Kết luận kiểm thử.",
                    "analysis": "Phân tích kiểm thử.",
                    "legal_basis": ["Căn cứ kiểm thử."],
                    "notes": "Lưu ý kiểm thử.",
                }
            ),
            10,
            20,
            30.0,
        )


class FailingGenerator:
    def generate(self, prompt: str) -> tuple[str, int, int, float]:
        raise RuntimeError("synthetic GPU failure")


def config() -> BaselineConfig:
    return BaselineConfig(
        name="test",
        model_id="Qwen/Qwen3-4B",
        revision="1cfa9a7208912126459214e8b04321603b3df60c",
        license="apache-2.0",
        dtype="float16",
        seed=42,
        max_input_tokens=10,
        max_new_tokens=10,
        batch_size=1,
        enable_thinking=False,
        do_sample=False,
        device="cuda",
    )


def record(identifier: str = "labor_exact_reference_001") -> BenchmarkRecord:
    return BenchmarkRecord(
        id=identifier,
        question=f"Câu hỏi {identifier}",
        reference_date="2026-09-09",
        category="exact_reference",
        task_type="legal_reasoning",
        answerability=Answerability.ANSWERABLE,
        expected_provision_ids=["vn_bll_45_2019_qh14:article-46"],
        notes="Nhãn kỹ thuật, chưa có chuyên gia pháp lý duyệt.",
        scenario_family=identifier,
        split=BenchmarkSplit.DEVELOPMENT,
    )


def test_benchmark_release_is_valid_and_has_expected_quotas() -> None:
    records = load_benchmark("data/evaluation/legal-eval-v1.jsonl")
    assert len(records) == 100
    assert sum(item.split is BenchmarkSplit.TEST for item in records) == 50


def test_answerability_and_output_schema_are_enforced() -> None:
    with pytest.raises(ValueError, match="expected_provision_ids"):
        BenchmarkRecord.model_validate({**record().model_dump(), "expected_provision_ids": []})
    assert parse_baseline_output('{"status":"answered"}') is None


def test_runner_parses_predictions_writes_artifacts_and_summarizes(tmp_path: Path) -> None:
    records = [record(), record("labor_exact_reference_002")]
    predictions = run_records(
        FakeGenerator(), records, "Câu hỏi: {question}\nNgày: {reference_date}"
    )
    assert predictions[0].error == "INVALID_MODEL_OUTPUT"
    assert predictions[1].status is not None
    summary = summarize_predictions(records, predictions)
    assert summary.error_count == 1
    assert summary.json_schema_rate == 0.5

    write_run_artifacts(tmp_path, config(), records, predictions)
    assert (tmp_path / "predictions.jsonl").exists()
    assert json.loads((tmp_path / "summary.json").read_text(encoding="utf-8"))["total"] == 2
    assert "Baseline report" in (tmp_path / "report.md").read_text(encoding="utf-8")


def test_prompt_rendering_and_benchmark_validation_errors() -> None:
    assert "Câu hỏi labor_exact_reference_001" in render_prompt("{question}", record())
    with pytest.raises(ValueError, match="exactly 100"):
        validate_benchmark([record()])


def test_config_load_generation_failure_and_artifact_compatibility(tmp_path: Path) -> None:
    loaded = load_baseline_config("configs/baseline-qwen3-4b-v1.yaml")
    assert loaded.revision == config().revision
    failed = run_records(FailingGenerator(), [record()], "{question}")
    assert failed[0].error == "GENERATION_FAILED:RuntimeError"
    write_run_artifacts(tmp_path, config(), [record()], failed)
    write_run_artifacts(tmp_path, config(), [record()], failed)
    with pytest.raises(ValueError, match="different config hash"):
        write_run_artifacts(tmp_path, config().model_copy(update={"seed": 43}), [record()], failed)
