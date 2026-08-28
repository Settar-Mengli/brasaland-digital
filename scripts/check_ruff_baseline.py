"""Fail when Ruff reports diagnostics not present in the tracked debt baseline."""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
from collections import Counter
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent
BASELINE_PATH = REPO_ROOT / ".ruff-baseline.json"
RUFF_CONFIG_PATH = REPO_ROOT / "ruff.toml"
RUFF_PATHS = (
    "data",
    "tests/pipelines",
    "services/auth",
    "packages/auth-verify",
    "packages/shared",
    "services/supplier-directory",
    "services/incident-analysis",
    "services/incident-manager",
    "services/inventory",
    "services/telemetry",
    "services/reporting",
    "services/knowledge",
    "services/rfp",
    "mcps/company-tools",
    "scripts/test_celery_queue_isolation.py",
    "scripts/check_ruff_baseline.py",
)

Fingerprint = tuple[str, str, str, str]


def _ruff_binary() -> str:
    executable = shutil.which("ruff")
    if executable is None:
        raise RuntimeError("ruff is not installed; run this checker through the data uv project")
    return executable


def _ruff_version(executable: str) -> str:
    result = subprocess.run(
        [executable, "--version"],
        cwd=REPO_ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def _run_ruff(executable: str) -> list[dict[str, Any]]:
    command = [
        executable,
        "check",
        "--config",
        str(RUFF_CONFIG_PATH),
        "--no-cache",
        "--output-format",
        "json",
        *RUFF_PATHS,
    ]
    result = subprocess.run(
        command,
        cwd=REPO_ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode not in {0, 1}:
        detail = result.stderr.strip() or result.stdout.strip()
        raise RuntimeError(f"ruff check failed to run: {detail}")

    diagnostics = json.loads(result.stdout)
    if not isinstance(diagnostics, list):
        raise RuntimeError("ruff returned an unexpected JSON payload")
    return diagnostics


def _fingerprint(diagnostic: dict[str, Any]) -> Fingerprint:
    source_path = Path(str(diagnostic["filename"])).resolve()
    try:
        relative_path = source_path.relative_to(REPO_ROOT).as_posix()
    except ValueError as exc:
        raise RuntimeError(f"ruff reported a path outside the repository: {source_path}") from exc

    location = diagnostic.get("location")
    if not isinstance(location, dict) or not isinstance(location.get("row"), int):
        raise RuntimeError(f"ruff returned an invalid location for {relative_path}")

    source_lines = source_path.read_text(encoding="utf-8").splitlines()
    row = location["row"]
    source_line = source_lines[row - 1] if 0 < row <= len(source_lines) else ""
    return (
        relative_path,
        str(diagnostic["code"]),
        str(diagnostic["message"]),
        source_line,
    )


def _current_counter(diagnostics: list[dict[str, Any]]) -> Counter[Fingerprint]:
    return Counter(_fingerprint(diagnostic) for diagnostic in diagnostics)


def _load_baseline() -> tuple[dict[str, Any], Counter[Fingerprint]]:
    if not BASELINE_PATH.exists():
        raise RuntimeError(
            f"missing {BASELINE_PATH.name}; create the reviewed initial file with "
            "--bootstrap-baseline"
        )

    payload = json.loads(BASELINE_PATH.read_text(encoding="utf-8"))
    if payload.get("schema_version") != 1:
        raise RuntimeError("unsupported Ruff baseline schema")
    if payload.get("paths") != list(RUFF_PATHS):
        raise RuntimeError("Ruff baseline paths do not match the checker's CI paths")

    baseline: Counter[Fingerprint] = Counter()
    records = payload.get("violations")
    if not isinstance(records, list):
        raise RuntimeError("Ruff baseline violations must be a list")
    for record in records:
        if not isinstance(record, dict):
            raise RuntimeError("Ruff baseline contains an invalid violation record")
        fingerprint = (
            str(record["path"]),
            str(record["code"]),
            str(record["message"]),
            str(record["source"]),
        )
        count = record.get("count")
        if not isinstance(count, int) or count < 1:
            raise RuntimeError("Ruff baseline violation counts must be positive integers")
        baseline[fingerprint] = count

    if payload.get("total") != baseline.total():
        raise RuntimeError("Ruff baseline total does not match its violation records")
    return payload, baseline


def _write_baseline(current: Counter[Fingerprint], version: str) -> None:
    violations = [
        {
            "path": path,
            "code": code,
            "message": message,
            "source": source,
            "count": count,
        }
        for (path, code, message, source), count in sorted(current.items())
    ]
    payload = {
        "schema_version": 1,
        "ruff_version": version,
        "paths": list(RUFF_PATHS),
        "total": current.total(),
        "violations": violations,
    }
    BASELINE_PATH.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def _print_new_violations(new_violations: Counter[Fingerprint]) -> None:
    for (path, code, message, source), count in sorted(new_violations.items()):
        suffix = f" (x{count})" if count > 1 else ""
        print(f"NEW {path}: {code} {message}{suffix}")
        print(f"    {source.strip()}")


def _validate_version(payload: dict[str, Any], current_version: str) -> None:
    baseline_version = payload.get("ruff_version")
    if baseline_version != current_version:
        raise RuntimeError(
            f"baseline uses {baseline_version!r}, but the active executable is "
            f"{current_version!r}"
        )


def _check(current: Counter[Fingerprint], baseline: Counter[Fingerprint]) -> int:
    new_violations = current - baseline
    cleared_count = (baseline - current).total()
    if new_violations:
        _print_new_violations(new_violations)
        print(
            "Ruff baseline gate failed: "
            f"{new_violations.total()} new, {current.total()} current, "
            f"{baseline.total()} baselined."
        )
        return 1

    print(
        "Ruff baseline gate passed: "
        f"{current.total()} current, {baseline.total()} baselined, "
        f"{cleared_count} cleared."
    )
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--update-baseline", action="store_true")
    mode.add_argument("--bootstrap-baseline", action="store_true")
    args = parser.parse_args()

    executable = _ruff_binary()
    version = _ruff_version(executable)
    current = _current_counter(_run_ruff(executable))

    if args.bootstrap_baseline:
        if BASELINE_PATH.exists():
            raise RuntimeError("bootstrap refuses to overwrite the existing Ruff baseline")
        _write_baseline(current, version)
        print(f"Created {BASELINE_PATH.name} with {current.total()} Ruff violations.")
        return 0

    payload, baseline = _load_baseline()
    _validate_version(payload, version)

    if args.update_baseline:
        new_violations = current - baseline
        if new_violations:
            _print_new_violations(new_violations)
            print("Baseline update refused: fix all new Ruff violations first.")
            return 1
        _write_baseline(current, version)
        print(
            f"Updated {BASELINE_PATH.name}: {baseline.total()} -> "
            f"{current.total()} tracked violations."
        )
        return 0

    return _check(current, baseline)


if __name__ == "__main__":
    raise SystemExit(main())
