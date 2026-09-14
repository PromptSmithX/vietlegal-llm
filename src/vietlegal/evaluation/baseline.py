"""Immutable benchmark contracts and deterministic baseline-run utilities."""

from __future__ import annotations

import hashlib
import json
import re
from collections import Counter
from collections.abc import Iterable
from datetime import UTC, datetime
from enum import StrEnum
from pathlib import Path
from typing import Any, Protocol

from pydantic import Field, model_validator

from vietlegal.contracts.api import ChatStatus
from vietlegal.contracts.data import StrictModel


class BenchmarkSplit(StrEnum):
    DEVELOPMENT = "development"
    TEST = "test"


class Answerability(StrEnum):
    ANSWERABLE = "answerable"
    UNANSWERABLE = "unanswerable"


class BenchmarkRecord(StrictModel):
    id: str = Field(pattern=r"^[a-z][a-z0-9_]{2,100}$")
    question: str = Field(min_length=1, max_length=2_000)
    reference_date: str = Field(pattern=r"^\d{4}-\d{2}-\d{2}$")
    category: str = Field(min_length=1)
    task_type: str = Field(min_length=1)
    answerability: Answerability
    expected_provision_ids: list[str] = Field(default_factory=list)
    required_facts: list[str] = Field(default_factory=list)
    notes: str = Field(min_length=1)
    scenario_family: str = Field(min_length=1)
    split: BenchmarkSplit
    validation_status: str = "technical_unreviewed"

    @model_validator(mode="after")
    def validate_answerability(self) -> BenchmarkRecord:
        if self.answerability is Answerability.ANSWERABLE and not self.expected_provision_ids:
            raise ValueError("answerable records require expected_provision_ids")
        if self.answerability is Answerability.UNANSWERABLE and self.expected_provision_ids:
            raise ValueError("unanswerable records cannot have expected_provision_ids")
        return self


class BaselinePrediction(StrictModel):
    benchmark_id: str
    status: ChatStatus | None = None
    conclusion: str | None = None
    analysis: str | None = None
    legal_basis: list[str] = Field(default_factory=list)
    notes: str | None = None
    raw_output: str
    input_tokens: int
    output_tokens: int
    latency_ms: float
    error: str | None = None


class BaselineSummary(StrictModel):
    benchmark_checksum: str
    total: int
    completion_rate: float
    json_schema_rate: float
    abstention_accuracy: float
    fake_citation_rate: float
    url_hallucination_rate: float
    legal_basis_presence_rate: float
    error_count: int
    answer_correctness: None = None


class TextGenerator(Protocol):
    def generate(self, prompt: str) -> tuple[str, int, int, float]: ...


def benchmark_checksum(records: Iterable[BenchmarkRecord]) -> str:
    payload = "\n".join(record.model_dump_json() for record in records)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def load_benchmark(path: Path | str) -> list[BenchmarkRecord]:
    records = [
        BenchmarkRecord.model_validate_json(line)
        for line in Path(path).read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    validate_benchmark(records)
    return records


def validate_benchmark(records: list[BenchmarkRecord]) -> None:
    if len(records) != 100:
        raise ValueError("legal-eval-v1 must contain exactly 100 records")
    if len({record.id for record in records}) != len(records):
        raise ValueError("benchmark IDs must be unique")
    splits = Counter(record.split for record in records)
    if splits != Counter({BenchmarkSplit.DEVELOPMENT: 50, BenchmarkSplit.TEST: 50}):
        raise ValueError("benchmark must use a 50/50 development/test split")
    expected_categories = Counter(
        {
            "exact_reference": 15,
            "semantic_practical": 15,
            "definition_scope": 10,
            "legal_reasoning": 15,
            "deadline_condition_exception": 15,
            "historical": 10,
            "partial_expired": 5,
            "missing_facts": 5,
            "out_of_scope": 5,
            "adversarial": 5,
        }
    )
    if Counter(record.category for record in records) != expected_categories:
        raise ValueError("benchmark category quotas do not match legal-eval-v1")
    families: dict[str, BenchmarkSplit] = {}
    normalized_questions: set[str] = set()
    for record in records:
        if (
            record.scenario_family in families
            and families[record.scenario_family] is not record.split
        ):
            raise ValueError("scenario families cannot cross benchmark splits")
        families[record.scenario_family] = record.split
        normalized = re.sub(r"\W+", "", record.question.lower())
        if normalized in normalized_questions:
            raise ValueError("benchmark questions must not be duplicated")
        normalized_questions.add(normalized)


def parse_baseline_output(raw_output: str) -> dict[str, Any] | None:
    candidate = raw_output.strip()
    if candidate.startswith("```") and candidate.endswith("```"):
        candidate = candidate.split("\n", maxsplit=1)[-1].rsplit("```", maxsplit=1)[0].strip()
    try:
        parsed = json.loads(candidate)
    except json.JSONDecodeError:
        return None
    required = {"status", "conclusion", "analysis", "legal_basis", "notes"}
    if not isinstance(parsed, dict) or set(parsed) != required:
        return None
    if parsed["status"] not in {status.value for status in ChatStatus}:
        return None
    if not isinstance(parsed["legal_basis"], list) or not all(
        isinstance(item, str) for item in parsed["legal_basis"]
    ):
        return None
    return parsed


def summarize_predictions(
    records: list[BenchmarkRecord], predictions: list[BaselinePrediction]
) -> BaselineSummary:
    by_id = {prediction.benchmark_id: prediction for prediction in predictions}
    ordered = [by_id.get(record.id) for record in records]
    completed = [prediction for prediction in ordered if prediction and prediction.error is None]
    parsed = [
        prediction for prediction in completed if prediction and prediction.status is not None
    ]
    expected_abstentions = [
        record.answerability is Answerability.UNANSWERABLE for record in records
    ]
    observed_abstentions = [
        prediction is not None and prediction.status is ChatStatus.INSUFFICIENT_CONTEXT
        for prediction in ordered
    ]
    return BaselineSummary(
        benchmark_checksum=benchmark_checksum(records),
        total=len(records),
        completion_rate=len(completed) / len(records),
        json_schema_rate=len(parsed) / len(records),
        abstention_accuracy=sum(
            a == b for a, b in zip(expected_abstentions, observed_abstentions, strict=True)
        )
        / len(records),
        fake_citation_rate=sum("[C" in prediction.raw_output for prediction in completed)
        / max(1, len(completed)),
        url_hallucination_rate=sum(
            "http://" in prediction.raw_output or "https://" in prediction.raw_output
            for prediction in completed
        )
        / max(1, len(completed)),
        legal_basis_presence_rate=sum(bool(prediction.legal_basis) for prediction in parsed)
        / max(1, len(parsed)),
        error_count=len(records) - len(completed),
    )


def write_json_atomic(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    temporary.replace(path)


def write_jsonl_atomic(path: Path, values: Iterable[StrictModel]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        "\n".join(value.model_dump_json() for value in values) + "\n", encoding="utf-8"
    )
    temporary.replace(path)


def runtime_stamp() -> str:
    return datetime.now(UTC).isoformat()
