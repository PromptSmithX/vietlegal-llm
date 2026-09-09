from __future__ import annotations

import json
import re
from pathlib import Path
from urllib.parse import urlparse

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[2]
MARKDOWN_LINK = re.compile(r"(?<!!)\[[^\]]+\]\(([^)]+)\)")
FENCED_BLOCK = re.compile(r"^```(json|yaml|yml)\s*\n(.*?)^```", re.MULTILINE | re.DOTALL)


def markdown_files() -> list[Path]:
    root_documents = ROOT.glob("*.md")
    specification_documents = (ROOT / "docs").rglob("*.md")
    return sorted([*root_documents, *specification_documents])


@pytest.mark.parametrize(
    "markdown_path", markdown_files(), ids=lambda path: str(path.relative_to(ROOT))
)
def test_markdown_local_links_exist(markdown_path: Path) -> None:
    content = markdown_path.read_text(encoding="utf-8")
    for target in MARKDOWN_LINK.findall(content):
        destination = target.strip().split(maxsplit=1)[0]
        parsed = urlparse(destination)
        if parsed.scheme or destination.startswith("#"):
            continue
        relative_path = destination.split("#", maxsplit=1)[0]
        assert relative_path, f"empty local link target in {markdown_path}"
        assert (markdown_path.parent / relative_path).resolve().exists(), (
            f"broken link {destination!r} in {markdown_path.relative_to(ROOT)}"
        )


@pytest.mark.parametrize(
    "markdown_path", markdown_files(), ids=lambda path: str(path.relative_to(ROOT))
)
def test_json_and_yaml_fences_parse(markdown_path: Path) -> None:
    content = markdown_path.read_text(encoding="utf-8")
    for language, block in FENCED_BLOCK.findall(content):
        try:
            if language == "json":
                json.loads(block)
            else:
                yaml.safe_load(block)
        except (json.JSONDecodeError, yaml.YAMLError) as exc:
            pytest.fail(f"invalid {language} fence in {markdown_path.relative_to(ROOT)}: {exc}")
