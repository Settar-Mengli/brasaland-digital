"""Documentation hygiene: README test counts and CONTEXT link targets."""

from __future__ import annotations

import platform
import re
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]


def _expect_count(readme_path: Path) -> int:
    text = readme_path.read_text(encoding="utf-8")
    match = re.search(r"Expect \*\*(\d+)\*\* passed", text)
    assert match is not None, f"Expect count missing in {readme_path}"
    return int(match.group(1))


def test_context_files_do_not_link_missing_es_translations() -> None:
    pattern = re.compile(r"\]\(\./[^)]+\.es\.md\)")
    for path in REPO_ROOT.rglob("CONTEXT*.md"):
        text = path.read_text(encoding="utf-8")
        for match in pattern.finditer(text):
            target = REPO_ROOT / path.parent / match.group(0)[2:-1]
            assert target.is_file(), f"{path} links to missing {target.name}"


def test_pipelines_readme_expect_count_matches_pytest_collect() -> None:
    readme_count = _expect_count(REPO_ROOT / "tests" / "pipelines" / "README.md")
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "pytest",
            "../tests/pipelines",
            "--collect-only",
            "-q",
        ],
        cwd=REPO_ROOT / "data",
        check=True,
        capture_output=True,
        text=True,
    )
    match = re.search(r"(\d+) tests collected", result.stdout)
    assert match is not None, result.stdout
    collected = int(match.group(1))
    assert readme_count == collected


def test_backoffice_readme_expect_count_matches_vitest() -> None:
    if shutil.which("npm") is None:
        pytest.skip("npm not available")
    readme_count = _expect_count(REPO_ROOT / "uis" / "backoffice" / "README.md")
    command = "npm run test --workspace @brasaland/backoffice"
    result = subprocess.run(
        command,
        cwd=REPO_ROOT,
        check=True,
        capture_output=True,
        text=True,
        shell=platform.system() == "Windows",
    )
    match = re.search(r"Tests\s+(\d+) passed", result.stdout)
    assert match is not None, result.stdout
    passed = int(match.group(1))
    assert readme_count == passed
