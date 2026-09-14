"""Command-line interface for validating and executing baseline experiments."""

from __future__ import annotations

import argparse
from pathlib import Path

from vietlegal.evaluation.baseline import BaselinePrediction, load_benchmark

from .baseline import load_baseline_config, run_records, write_run_artifacts
from .transformers_backend import TransformersGenerator


def main() -> None:
    parser = argparse.ArgumentParser(prog="vietlegal-baseline")
    parser.add_argument("command", choices=["validate", "smoke", "run", "report"])
    parser.add_argument("--config", default="configs/baseline-qwen3-4b-v1.yaml")
    parser.add_argument("--benchmark", default="data/evaluation/legal-eval-v1.jsonl")
    parser.add_argument("--prompt", default="prompts/baseline-v1.txt")
    parser.add_argument("--output", default="artifacts/baseline-qwen3-4b-v1")
    parser.add_argument("--split", choices=["development", "test", "all"], default="all")
    parser.add_argument("--limit", type=int, default=None)
    args = parser.parse_args()
    records = load_benchmark(args.benchmark)
    config = load_baseline_config(args.config)
    if args.command == "validate":
        print(f"valid: {len(records)} records; config={config.name}")
        return
    if args.command == "report":
        prediction_path = Path(args.output) / "predictions.jsonl"
        predictions = [
            BaselinePrediction.model_validate_json(line)
            for line in prediction_path.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
        write_run_artifacts(
            Path(args.output), config, records, predictions, Path(args.prompt).read_text()
        )
        print(f"rebuilt report for {len(predictions)} predictions")
        return
    selected = (
        records
        if args.split == "all"
        else [record for record in records if record.split.value == args.split]
    )
    if args.limit is not None:
        if args.limit < 1:
            parser.error("--limit must be at least 1")
        selected = selected[: args.limit]
    if args.command == "smoke":
        smoke_categories = [
            "exact_reference",
            "semantic_practical",
            "missing_facts",
            "out_of_scope",
            "adversarial",
        ]
        selected = [
            next(record for record in records if record.category == category)
            for category in smoke_categories
        ]
    generator = TransformersGenerator(config)
    prompt_template = Path(args.prompt).read_text(encoding="utf-8")
    prediction_path = Path(args.output) / "predictions.jsonl"
    existing = (
        {
            prediction.benchmark_id: prediction
            for prediction in (
                BaselinePrediction.model_validate_json(line)
                for line in prediction_path.read_text(encoding="utf-8").splitlines()
                if line.strip()
            )
        }
        if prediction_path.exists()
        else None
    )
    predictions = run_records(generator, selected, prompt_template, existing)
    write_run_artifacts(
        Path(args.output),
        config,
        selected,
        predictions,
        prompt_template,
        getattr(generator, "chat_template_sha256", None),
    )
    print(f"wrote {len(predictions)} predictions to {args.output}")
