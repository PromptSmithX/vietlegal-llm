from __future__ import annotations

from pathlib import Path

from vietlegal.model.baseline import load_baseline_config


def test_baseline_config_is_pinned() -> None:
    config = load_baseline_config(Path("configs/baseline-qwen3-4b-v1.yaml"))
    assert config.model_id == "Qwen/Qwen3-4B"
    assert config.enable_thinking is False
    assert len(config.revision) == 40
