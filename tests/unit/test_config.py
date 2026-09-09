from __future__ import annotations

import json
from pathlib import Path

import pytest

from vietlegal.config import ConfigurationError, load_settings, materialize_resolved_config


def write(path: Path, content: str) -> None:
    path.write_text(content, encoding="utf-8")


def test_configuration_precedence_and_hash_are_deterministic(tmp_path: Path) -> None:
    config_dir = tmp_path / "configs"
    config_dir.mkdir()
    write(
        config_dir / "default.yaml",
        """config_version: v1
app_env: development
log_level: INFO
timezone: Asia/Ho_Chi_Minh
generator_model: Qwen/Qwen3-4B
embedding_model: Qwen/Qwen3-Embedding-0.6B
reranker_model: Qwen/Qwen3-Reranker-0.6B
artifact_root: artifacts
""",
    )
    write(config_dir / "test.yaml", "log_level: WARNING\nartifact_root: profile-artifacts\n")
    dotenv_path = tmp_path / ".env"
    write(dotenv_path, "APP_ENV=test\nLOG_LEVEL=ERROR\n")

    settings = load_settings(
        config_dir=config_dir,
        env_file=dotenv_path,
        environment={"LOG_LEVEL": "DEBUG", "CORPUS_VERSION": "legal-corpus-v1"},
    )

    assert settings.app_env == "test"
    assert settings.log_level == "DEBUG"
    assert settings.corpus_version == "legal-corpus-v1"
    assert settings.artifact_root == Path("profile-artifacts")
    assert settings.config_hash() == settings.config_hash()


def test_configuration_rejects_unknown_yaml_and_dotenv_keys(tmp_path: Path) -> None:
    config_dir = tmp_path / "configs"
    config_dir.mkdir()
    write(config_dir / "default.yaml", "config_version: v1\nunknown: value\n")

    with pytest.raises(ConfigurationError, match="unknown configuration key"):
        load_settings(config_dir=config_dir, env_file=None, environment={})

    write(
        config_dir / "default.yaml",
        "\n".join(
            [
                "config_version: v1",
                "app_env: development",
                "log_level: INFO",
                "timezone: UTC",
                "generator_model: x",
                "embedding_model: y",
                "reranker_model: z",
                "artifact_root: artifacts",
                "",
            ]
        ),
    )
    dotenv_path = tmp_path / ".env"
    write(dotenv_path, "UNKNOWN=value\n")

    with pytest.raises(ConfigurationError, match="unknown .env key"):
        load_settings(config_dir=config_dir, env_file=dotenv_path, environment={})


def test_materialized_config_is_redacted_and_contains_hash(tmp_path: Path) -> None:
    config_dir = Path("configs")
    settings = load_settings(config_dir=config_dir, env_file=None, environment={})

    output_path = materialize_resolved_config(settings, tmp_path / "artifact")
    payload = json.loads(output_path.read_text(encoding="utf-8"))

    assert payload["config_hash"] == settings.config_hash()
    assert payload["config"]["timezone"] == "Asia/Ho_Chi_Minh"
