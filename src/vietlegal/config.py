"""Deterministic configuration loading and artifact materialization for Phase 0."""

from __future__ import annotations

import hashlib
import json
import os
from collections.abc import Mapping
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, ConfigDict, Field, field_validator

SETTINGS_ENV_MAP = {
    "APP_ENV": "app_env",
    "LOG_LEVEL": "log_level",
    "TIMEZONE": "timezone",
    "CORPUS_VERSION": "corpus_version",
    "INDEX_VERSION": "index_version",
    "GENERATOR_MODEL": "generator_model",
    "GENERATOR_REVISION": "generator_revision",
    "EMBEDDING_MODEL": "embedding_model",
    "EMBEDDING_REVISION": "embedding_revision",
    "RERANKER_MODEL": "reranker_model",
    "RERANKER_REVISION": "reranker_revision",
    "ARTIFACT_ROOT": "artifact_root",
}
SENSITIVE_NAME_PARTS = ("secret", "token", "password", "api_key", "credential")


class ConfigurationError(ValueError):
    """Raised when a configuration source is malformed or contains unknown keys."""


class AppSettings(BaseModel):
    """Resolved, non-secret settings shared by future project phases."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True, validate_assignment=True)

    config_version: str = Field(min_length=1)
    app_env: str = Field(min_length=1, pattern=r"^[a-z][a-z0-9_-]*$")
    log_level: str = Field(pattern=r"^(DEBUG|INFO|WARNING|ERROR|CRITICAL)$")
    timezone: str = Field(min_length=1)
    corpus_version: str | None = None
    index_version: str | None = None
    generator_model: str = Field(min_length=1)
    generator_revision: str | None = None
    embedding_model: str = Field(min_length=1)
    embedding_revision: str | None = None
    reranker_model: str = Field(min_length=1)
    reranker_revision: str | None = None
    artifact_root: Path

    @field_validator("log_level", mode="before")
    @classmethod
    def normalize_log_level(cls, value: str) -> str:
        return value.upper()

    def config_hash(self) -> str:
        """Return a stable SHA-256 hash of the resolved, serializable configuration."""
        serialized = json.dumps(self.model_dump(mode="json"), sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


def _read_yaml(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        parsed = yaml.safe_load(path.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        raise ConfigurationError(f"invalid YAML in {path}") from exc
    if parsed is None:
        return {}
    if not isinstance(parsed, dict) or not all(isinstance(key, str) for key in parsed):
        raise ConfigurationError(f"{path} must contain a mapping with string keys")
    return parsed


def _read_dotenv(path: Path) -> dict[str, str]:
    if not path.exists():
        return {}
    values: dict[str, str] = {}
    for line_number, raw_line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line.removeprefix("export ").strip()
        if "=" not in line:
            raise ConfigurationError(f"invalid .env assignment at {path}:{line_number}")
        key, value = line.split("=", maxsplit=1)
        key = key.strip()
        value = value.strip()
        if not key:
            raise ConfigurationError(f"empty .env key at {path}:{line_number}")
        if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
            value = value[1:-1]
        if key not in SETTINGS_ENV_MAP:
            raise ConfigurationError(f"unknown .env key: {key}")
        values[key] = value
    return values


def _validate_yaml_keys(values: Mapping[str, Any], source: Path) -> None:
    allowed_keys = set(AppSettings.model_fields)
    unknown_keys = sorted(set(values) - allowed_keys)
    if unknown_keys:
        raise ConfigurationError(
            f"unknown configuration key(s) in {source}: {', '.join(unknown_keys)}"
        )


def _environment_overrides(environment: Mapping[str, str]) -> dict[str, str]:
    return {
        settings_key: environment[environment_key]
        for environment_key, settings_key in SETTINGS_ENV_MAP.items()
        if environment_key in environment
    }


def _redacted_config(settings: AppSettings) -> dict[str, Any]:
    values = settings.model_dump(mode="json")
    return {
        key: "***REDACTED***"
        if any(part in key.lower() for part in SENSITIVE_NAME_PARTS)
        else value
        for key, value in values.items()
    }


def load_settings(
    *,
    config_dir: Path | str = Path("configs"),
    env_file: Path | str | None = Path(".env"),
    environment: Mapping[str, str] | None = None,
) -> AppSettings:
    """Load settings as defaults -> environment YAML -> .env -> process environment.

    ``APP_ENV`` from a .env file is read early only to select the matching YAML profile;
    it still overrides the resulting settings in its documented precedence position.
    """
    config_path = Path(config_dir)
    dotenv_path = Path(env_file) if env_file is not None else None
    process_environment = os.environ if environment is None else environment
    dotenv_values = _read_dotenv(dotenv_path) if dotenv_path is not None else {}

    defaults = _read_yaml(config_path / "default.yaml")
    _validate_yaml_keys(defaults, config_path / "default.yaml")
    selected_env = (
        process_environment.get("APP_ENV")
        or dotenv_values.get("APP_ENV")
        or defaults.get("app_env", "development")
    )
    if not isinstance(selected_env, str):
        raise ConfigurationError("APP_ENV must be a string")

    profile_path = config_path / f"{selected_env}.yaml"
    profile = _read_yaml(profile_path)
    _validate_yaml_keys(profile, profile_path)
    dotenv_overrides = {
        settings_key: value
        for environment_key, settings_key in SETTINGS_ENV_MAP.items()
        if (value := dotenv_values.get(environment_key)) is not None
    }

    merged: dict[str, Any] = {}
    merged.update(defaults)
    merged.update(profile)
    merged.update(dotenv_overrides)
    merged.update(_environment_overrides(process_environment))
    try:
        return AppSettings.model_validate(merged)
    except Exception as exc:
        raise ConfigurationError("resolved configuration does not match AppSettings") from exc


def materialize_resolved_config(settings: AppSettings, artifact_dir: Path | str) -> Path:
    """Persist a redacted resolved config and hash in a caller-selected artifact directory."""
    destination = Path(artifact_dir)
    destination.mkdir(parents=True, exist_ok=True)
    output_path = destination / "resolved-config.json"
    payload = {
        "config": _redacted_config(settings),
        "config_hash": settings.config_hash(),
    }
    output_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return output_path
