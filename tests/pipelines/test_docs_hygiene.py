"""Documentation hygiene: README test counts and CONTEXT link targets."""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

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


def _count_backoffice_vitest_tests() -> int:
    """Count ``it(`` / ``test(`` blocks under backoffice vitest files."""
    root = REPO_ROOT / "uis" / "backoffice"
    pattern = re.compile(r"^\s*(?:it|test)\(", re.MULTILINE)
    total = 0
    for suffix in ("*.test.ts", "*.test.tsx", "*.spec.ts", "*.spec.tsx"):
        for path in root.rglob(suffix):
            total += len(pattern.findall(path.read_text(encoding="utf-8")))
    return total


def test_backoffice_readme_expect_count_matches_discovered_tests() -> None:
    readme_count = _expect_count(REPO_ROOT / "uis" / "backoffice" / "README.md")
    discovered = _count_backoffice_vitest_tests()
    assert readme_count == discovered
