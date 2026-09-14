"""Baseline orchestration independent of a concrete model runtime."""

from __future__ import annotations

import hashlib
import subprocess
import sys
from pathlib import Path

import yaml
from pydantic import Field

from vietlegal.contracts.api import ChatStatus
from vietlegal.contracts.data import StrictModel
from vietlegal.evaluation.baseline import (
    BaselinePrediction,
    BenchmarkRecord,
    TextGenerator,
    parse_baseline_output,
    summarize_predictions,
    write_json_atomic,
    write_jsonl_atomic,
)


class BaselineConfig(StrictModel):
    name: str
    model_id: str
    revision: str = Field(pattern=r"^[a-f0-9]{40}$")
    license: str
    dtype: str
    seed: int
    max_input_tokens: int = Field(ge=1)
    max_new_tokens: int = Field(ge=1)
    batch_size: int = Field(ge=1)
    enable_thinking: bool
    do_sample: bool
    device: str

    def config_hash(self) -> str:
        return hashlib.sha256(self.model_dump_json().encode("utf-8")).hexdigest()


def load_baseline_config(path: Path | str) -> BaselineConfig:
    parsed = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    return BaselineConfig.model_validate(parsed)


def render_prompt(template: str, record: BenchmarkRecord) -> str:
    return template.format(question=record.question, reference_date=record.reference_date)


def run_records(
    generator: TextGenerator,
    records: list[BenchmarkRecord],
    prompt_template: str,
    existing: dict[str, BaselinePrediction] | None = None,
) -> list[BaselinePrediction]:
    predictions = dict(existing or {})
    for record in records:
        if record.id in predictions:
            continue
        try:
            raw_output, input_tokens, output_tokens, latency_ms = generator.generate(
                render_prompt(prompt_template, record)
            )
        except Exception as error:
            predictions[record.id] = BaselinePrediction(
                benchmark_id=record.id,
                raw_output="",
                input_tokens=0,
                output_tokens=0,
                latency_ms=0.0,
                error=f"GENERATION_FAILED:{type(error).__name__}",
            )
            continue
        parsed = parse_baseline_output(raw_output)
        predictions[record.id] = BaselinePrediction(
            benchmark_id=record.id,
            status=ChatStatus(parsed["status"]) if parsed else None,
            conclusion=parsed["conclusion"] if parsed else None,
            analysis=parsed["analysis"] if parsed else None,
            legal_basis=parsed["legal_basis"] if parsed else [],
            notes=parsed["notes"] if parsed else None,
            raw_output=raw_output,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            latency_ms=latency_ms,
            error=None if parsed else "INVALID_MODEL_OUTPUT",
        )
    return [predictions[record.id] for record in records]


def write_run_artifacts(
    output_dir: Path,
    config: BaselineConfig,
    records: list[BenchmarkRecord],
    predictions: list[BaselinePrediction],
    prompt_template: str = "",
    chat_template_sha256: str | None = None,
) -> None:
    summary = summarize_predictions(records, predictions)
    output_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = output_dir / "run-manifest.json"
    if manifest_path.exists():
        existing_manifest = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))
        if existing_manifest.get("config_hash") != config.config_hash():
            raise ValueError("refusing to mix artifacts with a different config hash")
    write_jsonl_atomic(output_dir / "predictions.jsonl", predictions)
    write_json_atomic(output_dir / "summary.json", summary.model_dump(mode="json"))
    write_json_atomic(
        manifest_path,
        {
            "config": config.model_dump(mode="json"),
            "config_hash": config.config_hash(),
            "benchmark_checksum": summary.benchmark_checksum,
            "prompt_sha256": hashlib.sha256(prompt_template.encode("utf-8")).hexdigest(),
            "chat_template_sha256": chat_template_sha256,
            "git_commit": git_commit(),
            "model": {
                "id": config.model_id,
                "revision": config.revision,
                "license": config.license,
            },
            "seed": config.seed,
            "runtime": {"python": sys.version},
        },
    )
    report = (
        "# Baseline report\n\n"
        + "\n".join(f"- {key}: {value}" for key, value in summary.model_dump(mode="json").items())
        + "\n"
    )
    (output_dir / "report.md").write_text(report, encoding="utf-8")


def git_commit() -> str:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"], text=True, stderr=subprocess.DEVNULL
        ).strip()
    except (OSError, subprocess.CalledProcessError):
        return "unknown"
