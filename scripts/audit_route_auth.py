"""OpenAPI auth sweep for contain-public-access FastAPI services.

What: For each listed service, load ``app.openapi()`` in that service's uv
environment and assert mutation/export routes declare a security scheme.
Expected-open routes are an explicit allowlist — anything else open is FAIL.

Why: Final verification gate before PR; catches regressions where a mutation
or cross-user GET ships without JWT wiring visible in OpenAPI.

How to run (from repo root)::

    uv run --directory services/auth python ../../scripts/audit_route_auth.py

Or (preferred — script fans out per service itself)::

    python scripts/audit_route_auth.py

The orchestrator invokes ``uv run --directory services/<name>`` for each
service so FastAPI/auth-verify deps resolve (same lesson as the Lane-2 DDL
scripts: do not expect bare repo-root Python to import service apps).
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent

# (service_name, directory relative to repo root)
SERVICES: list[tuple[str, str]] = [
    ("auth", "services/auth"),
    ("supplier-directory", "services/supplier-directory"),
    ("incident-manager", "services/incident-manager"),
    ("incident-analysis", "services/incident-analysis"),
    ("inventory", "services/inventory"),
    ("telemetry", "services/telemetry"),
    ("reporting", "services/reporting"),
    ("rfp", "services/rfp"),
    ("knowledge", "services/knowledge"),
]

# Explicit expected-open exceptions: (service, METHOD, path_template)
# Paths use OpenAPI templates ({param}), not concrete IDs.
ALLOWLIST_OPEN: frozenset[tuple[str, str, str]] = frozenset(
    {
        # --- probes / static ---
        ("auth", "GET", "/"),
        ("auth", "GET", "/livez"),
        ("auth", "GET", "/readyz"),
        ("auth", "GET", "/forgot-password"),
        ("auth", "GET", "/reset-password"),
        ("supplier-directory", "GET", "/"),
        ("incident-manager", "GET", "/"),
        ("incident-analysis", "GET", "/"),
        ("telemetry", "GET", "/"),
        ("reporting", "GET", "/"),
        ("rfp", "GET", "/"),
        ("rfp", "GET", "/livez"),
        ("rfp", "GET", "/readyz"),
        ("knowledge", "GET", "/"),
        # --- auth public token endpoints ---
        ("auth", "POST", "/auth/register"),
        ("auth", "POST", "/auth/login"),
        ("auth", "POST", "/auth/login/authorized-locations"),
        ("auth", "POST", "/auth/refresh"),
        ("auth", "POST", "/auth/logout"),
        ("auth", "POST", "/auth/forgot-password"),
        ("auth", "POST", "/auth/reset-password"),
        # --- telemetry ingest (token-optional by design; Phase 2) ---
        ("telemetry", "POST", "/telemetry/events"),
    }
)

MUTATION_METHODS = frozenset({"post", "put", "patch", "delete"})

# GET path fragments that indicate export / list / cross-user data surfaces.
GET_SENSITIVE_MARKERS = (
    "/export",
    "/report",
    "/summary",
    "/users",
    "/suppliers",
    "/incidents",
    "/inventory/",
    "/tickets",
    "/memory",
    "/trace",
    "/tasks",
    "/pipeline",
    "/weekly",
    "/orders",
    "/agent/",
    "/knowledge/",
    "/rfp/",
    "/telemetry/",
    "/reporting/",
    "/auth/me",
    "/auth/profiles",
    "/api/",
)


def _is_sensitive_get(path: str) -> bool:
    lower = path.lower()
    return any(marker in lower for marker in GET_SENSITIVE_MARKERS)


def _in_scope(method: str, path: str) -> bool:
    m = method.lower()
    if m in MUTATION_METHODS:
        return True
    if m == "get" and _is_sensitive_get(path):
        return True
    return False


def _has_security(operation: dict[str, Any], schema: dict[str, Any]) -> bool:
    """True when the operation declares a non-empty OpenAPI security requirement."""
    sec = operation.get("security")
    if sec is None:
        # Fall back to top-level security if present.
        sec = schema.get("security")
    if not sec:
        return False
    # Empty list means "optional / no auth" in OpenAPI terms for some generators;
    # treat only non-empty requirement objects as guarded.
    for requirement in sec:
        if isinstance(requirement, dict) and requirement:
            return True
    return False


def _prepare_env() -> dict[str, str]:
    """Minimal JWT/env so apps import without contacting live secrets."""
    env = os.environ.copy()
    # Synthetic RS256 keypair for import-time ensure_jwt_configured checks.
    try:
        from brasaland_auth_verify.testing import generate_rsa_keypair

        _priv, pub = generate_rsa_keypair()
        env.setdefault("JWT_PUBLIC_KEY", pub)
        env.setdefault("JWT_PRIVATE_KEY", _priv)
    except Exception:
        pass
    env.setdefault("JWT_ALGORITHM", "RS256")
    env.setdefault("DATABASE_URL", "sqlite://")
    env.setdefault("REDIS_URL", "redis://127.0.0.1:6379/0")
    env.setdefault("AUTH_DB_PATH", str(REPO_ROOT / ".tmp-audit-auth.json"))
    # Docs may be gated off in live compose; schema is still available via app.openapi().
    env.pop("EXPOSE_DOCS", None)
    return env


def emit_schema_for_current_service(service: str) -> dict[str, Any]:
    """Import ``app`` from CWD (a services/<name> directory) and return openapi()."""
    env_prep = _prepare_env()
    for key, value in env_prep.items():
        os.environ[key] = value

    if service == "auth":
        # Auth signs tokens; needs a real private key in-process.
        from brasaland_auth_verify.testing import generate_rsa_keypair
        from cryptography.hazmat.primitives import serialization
        from cryptography.hazmat.primitives.asymmetric import rsa

        # Prefer auth-verify helper when available; else cryptography.
        try:
            priv, pub = generate_rsa_keypair()
            os.environ["JWT_PRIVATE_KEY"] = priv
            os.environ["JWT_PUBLIC_KEY"] = pub
        except Exception:
            key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
            os.environ["JWT_PRIVATE_KEY"] = key.private_bytes(
                serialization.Encoding.PEM,
                serialization.PrivateFormat.PKCS8,
                serialization.NoEncryption(),
            ).decode()
            os.environ["JWT_PUBLIC_KEY"] = (
                key.public_key()
                .public_bytes(
                    serialization.Encoding.PEM,
                    serialization.PublicFormat.SubjectPublicKeyInfo,
                )
                .decode()
            )

    # Ensure service root is importable.
    cwd = Path.cwd()
    if str(cwd) not in sys.path:
        sys.path.insert(0, str(cwd))

    from app import app  # type: ignore[import-not-found]

    return app.openapi()


def audit_schema(service: str, schema: dict[str, Any]) -> tuple[list[dict[str, str]], int, int]:
    """Return (rows, fail_count, in_scope_count)."""
    rows: list[dict[str, str]] = []
    fails = 0
    in_scope = 0
    paths = schema.get("paths") or {}
    for path, methods in sorted(paths.items()):
        for method, operation in sorted(methods.items()):
            if method.startswith("x-") or not isinstance(operation, dict):
                continue
            upper = method.upper()
            if not _in_scope(upper, path):
                continue
            in_scope += 1
            guarded = _has_security(operation, schema)
            key = (service, upper, path)
            allowlisted = key in ALLOWLIST_OPEN
            if guarded:
                verdict = "PASS"
                state = "guarded"
            elif allowlisted:
                verdict = "PASS"
                state = "open(allowlisted)"
            else:
                verdict = "FAIL"
                state = "open"
                fails += 1
            rows.append(
                {
                    "service": service,
                    "method": upper,
                    "path": path,
                    "state": state,
                    "verdict": verdict,
                }
            )
    return rows, fails, in_scope


def run_worker(service: str) -> int:
    schema = emit_schema_for_current_service(service)
    rows, fails, in_scope = audit_schema(service, schema)
    payload = {"service": service, "rows": rows, "fails": fails, "in_scope": in_scope}
    print(json.dumps(payload))
    return 1 if fails else 0


def _format_table(rows: list[dict[str, str]]) -> str:
    if not rows:
        return "(no in-scope routes)"
    col_m = max(len(r["method"]) for r in rows)
    col_p = max(len(r["path"]) for r in rows)
    col_s = max(len(r["state"]) for r in rows)
    lines = [f"{'METHOD'.ljust(col_m)}  {'PATH'.ljust(col_p)}  {'STATE'.ljust(col_s)}  VERDICT"]
    lines.append(f"{'-' * col_m}  {'-' * col_p}  {'-' * col_s}  -------")
    for r in rows:
        lines.append(
            f"{r['method'].ljust(col_m)}  {r['path'].ljust(col_p)}  "
            f"{r['state'].ljust(col_s)}  {r['verdict']}"
        )
    return "\n".join(lines)


def run_orchestrator() -> int:
    total_fails = 0
    total_scope = 0
    print("OpenAPI auth sweep — contain-public-access")
    print(f"Allowlist entries: {len(ALLOWLIST_OPEN)}")
    print()

    for service, rel in SERVICES:
        service_dir = REPO_ROOT / rel
        if not service_dir.is_dir():
            print(f"=== {service} ===")
            print("FAIL: service directory missing")
            total_fails += 1
            continue

        proc = subprocess.run(
            [
                "uv",
                "run",
                "--directory",
                str(service_dir),
                "python",
                str(Path(__file__).resolve()),
                "--worker",
                service,
            ],
            cwd=str(REPO_ROOT),
            capture_output=True,
            text=True,
            check=False,
        )
        print(f"=== {service} ===")
        if proc.returncode not in (0, 1) or not proc.stdout.strip():
            print("FAIL: worker could not load OpenAPI")
            if proc.stderr:
                print(proc.stderr[-2000:])
            if proc.stdout:
                print(proc.stdout[-1000:])
            total_fails += 1
            print()
            continue

        # Worker prints one JSON object on stdout; tolerate trailing log noise.
        line = proc.stdout.strip().splitlines()[-1]
        try:
            payload = json.loads(line)
        except json.JSONDecodeError:
            print("FAIL: worker returned non-JSON")
            print(proc.stdout[-1000:])
            total_fails += 1
            print()
            continue

        rows = payload["rows"]
        fails = int(payload["fails"])
        in_scope = int(payload["in_scope"])
        total_fails += fails
        total_scope += in_scope
        print(_format_table(rows))
        print(f"in-scope={in_scope} fails={fails}")
        print()

    print("=== SUMMARY ===")
    if total_fails:
        print(f"FAIL — {total_fails} unallowlisted open route(s) across {total_scope} in-scope")
        return 1
    print(f"PASS — {total_scope} in-scope routes guarded or explicitly allowlisted")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--worker",
        metavar="SERVICE",
        help="Internal: emit JSON audit for SERVICE (cwd must be that service).",
    )
    args = parser.parse_args()
    if args.worker:
        return run_worker(args.worker)
    return run_orchestrator()


if __name__ == "__main__":
    sys.exit(main())
