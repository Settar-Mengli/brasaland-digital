"""Dockerfile and compose image hygiene checks."""

from __future__ import annotations

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]


def _dockerfile_declares_non_root_user(path: Path) -> bool:
    text = path.read_text(encoding="utf-8")
    user_lines = [line.strip() for line in text.splitlines() if line.strip().startswith("USER ")]
    if not user_lines:
        return False
    if user_lines[-1] != "USER app":
        return False
    return "useradd" in text and "groupadd" in text


def test_knowledge_dockerfile_declares_non_root_user() -> None:
    path = REPO_ROOT / "services" / "knowledge" / "Dockerfile"
    assert _dockerfile_declares_non_root_user(path)


def test_reporting_dockerfile_declares_non_root_user() -> None:
    path = REPO_ROOT / "services" / "reporting" / "Dockerfile"
    assert _dockerfile_declares_non_root_user(path)


def test_compose_pins_qdrant_image_tag() -> None:
    compose = (REPO_ROOT / "docker-compose.yml").read_text(encoding="utf-8")
    match = re.search(r"image:\s*qdrant/qdrant:([\w.-]+)", compose)
    assert match is not None
    assert match.group(1) != ""
