"""Verify the Alembic history against a fresh disposable PostgreSQL database.

The check deliberately creates the test database through PostgreSQL, then lets
Alembic own every application table and constraint. It never imports models or
calls SQLModel ``create_all``.

Usage (from the repository root)::

    DATABASE_URL=postgresql://postgres:postgres@localhost:5432/postgres \
      uv run --directory data --python 3.13 \
      python ../scripts/verify_alembic_migrations.py

``DATABASE_URL`` must point to an administrative database on a disposable
PostgreSQL instance. The script creates a unique database beside it and leaves
that database available for inspection after a run.
"""

from __future__ import annotations

import os
import re
import subprocess
import sys
import time
import uuid
from pathlib import Path

import psycopg2
from psycopg2 import sql
from sqlalchemy.engine import make_url

EXPECTED_HEAD = "e4f8a1b2c3d4"
POSTGRES_ADMIN_DATABASE = "postgres"
READINESS_ATTEMPTS = 30
READINESS_DELAY_SECONDS = 1

EXPECTED_TABLES: tuple[tuple[str, str], ...] = (
    ("public", "incident"),
    ("public", "ingredient"),
    ("public", "ingrediententry"),
    ("public", "ingredientexit"),
    ("public", "ticket"),
    ("public", "rfp_metadata"),
    ("public", "department_section"),
    ("public", "final_document"),
    ("public", "telemetry_events"),
    ("reporting", "job_runs"),
    ("reporting", "pipeline_runs"),
    ("reporting", "task_dead_letters"),
    ("reporting", "weekly_location_performance"),
)
EXPECTED_CONSTRAINTS = (
    ("public", "department_section", "uq_department_section_ticket_department"),
    ("public", "final_document", "uq_final_document_ticket"),
)

URL_CREDENTIALS_RE = re.compile(
    r"(postgres(?:ql)?(?:\+[^:/@]+)?://)[^@\s]+@", re.IGNORECASE
)
PASSWORD_PARAMETER_RE = re.compile(r"(password=)[^\s,;]+", re.IGNORECASE)


def _safe_message(message: str) -> str:
    """Remove credentials from a connection or subprocess error message."""

    sanitized = URL_CREDENTIALS_RE.sub(r"\1[redacted]@", message)
    return PASSWORD_PARAMETER_RE.sub(r"\1[redacted]", sanitized)


def _render_psycopg_url(url_text: str) -> str:
    """Render a SQLAlchemy URL in the driver-neutral form psycopg2 accepts."""

    parsed = make_url(url_text)
    if parsed.drivername.startswith("postgresql+"):
        parsed = parsed.set(drivername="postgresql")
    return parsed.render_as_string(hide_password=False)


def _url_for_database(url_text: str, database: str) -> str:
    """Return ``url_text`` with its database component replaced."""

    return make_url(url_text).set(database=database).render_as_string(hide_password=False)


def _assert_disposable_host(url_text: str) -> None:
    """Refuse known Supabase hosts so the check cannot target the live project."""

    host = (make_url(url_text).host or "").lower()
    if "supabase" in host:
        raise RuntimeError("Refusing to run against a Supabase host; use disposable Postgres")


def _connect(url_text: str, timeout: int = 5) -> psycopg2.extensions.connection:
    """Open a PostgreSQL connection without exposing the URL on failure."""

    try:
        return psycopg2.connect(_render_psycopg_url(url_text), connect_timeout=timeout)
    except psycopg2.Error as exc:
        raise RuntimeError(f"PostgreSQL connection failed: {_safe_message(str(exc))}") from exc


def _wait_for_postgres(admin_url: str) -> None:
    """Wait until PostgreSQL accepts a real authenticated connection."""

    last_error = "unknown error"
    for attempt in range(1, READINESS_ATTEMPTS + 1):
        try:
            connection = _connect(admin_url)
        except RuntimeError as exc:
            last_error = str(exc)
            if attempt < READINESS_ATTEMPTS:
                time.sleep(READINESS_DELAY_SECONDS)
            continue
        connection.close()
        print(f"PostgreSQL readiness connection succeeded on attempt {attempt}.")
        return
    raise RuntimeError(
        f"PostgreSQL did not accept a real connection after {READINESS_ATTEMPTS} attempts: "
        f"{last_error}"
    )


def _assert_invalid_credentials_fail(admin_url: str) -> None:
    """Prove that the disposable service rejects an invalid password."""

    invalid_url = make_url(admin_url).set(password=f"invalid-{uuid.uuid4().hex}")
    try:
        connection = _connect(str(invalid_url), timeout=3)
    except RuntimeError as exc:
        print(f"Invalid database credentials rejected as expected ({_safe_message(str(exc))}).")
        return
    connection.close()
    raise RuntimeError("Invalid database credentials were unexpectedly accepted")


def _create_clean_database(admin_url: str) -> tuple[str, str]:
    """Create a unique empty database and return its name and connection URL."""

    database_name = f"alembic_ci_{uuid.uuid4().hex[:12]}"
    connection = _connect(admin_url)
    connection.autocommit = True
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                sql.SQL("CREATE DATABASE {} WITH TEMPLATE template0").format(
                    sql.Identifier(database_name)
                )
            )
    finally:
        connection.close()
    database_url = _url_for_database(admin_url, database_name)
    print(f"Created clean test database {database_name} from template0.")
    return database_name, database_url


def _assert_empty_database(database_url: str) -> None:
    """Confirm no application tables exist before Alembic runs."""

    connection = _connect(database_url)
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT table_schema, table_name
                FROM information_schema.tables
                WHERE table_schema IN ('public', 'reporting')
                ORDER BY table_schema, table_name
                """
            )
            rows = cursor.fetchall()
    finally:
        connection.close()
    if rows:
        names = ", ".join(f"{schema}.{table}" for schema, table in rows)
        raise RuntimeError(f"New test database was not empty before migration: {names}")
    print("Empty-database preflight passed: no application tables existed before Alembic.")


def _run_alembic(database_url: str, *arguments: str) -> str:
    """Run Alembic from the locked data environment and return sanitized output."""

    environment = os.environ.copy()
    environment["DATABASE_URL"] = database_url
    command = [
        "uv",
        "run",
        "--directory",
        "data",
        "--locked",
        "--python",
        "3.13",
        "alembic",
        "-c",
        "alembic.ini",
        *arguments,
    ]
    result = subprocess.run(
        command,
        check=False,
        cwd=Path(__file__).resolve().parent.parent,
        env=environment,
        capture_output=True,
        text=True,
    )
    output = _safe_message("\n".join(part for part in (result.stdout, result.stderr) if part))
    if result.returncode:
        raise RuntimeError(
            f"Alembic {' '.join(arguments)} failed with exit code {result.returncode}:\n{output}"
        )
    if output.strip():
        print(output.rstrip())
    return output


def _assert_head(database_url: str) -> None:
    """Assert both Alembic's current output and its version table are at head."""

    current_output = _run_alembic(database_url, "current")
    if not re.search(rf"\b{EXPECTED_HEAD}\b", current_output):
        raise RuntimeError(
            f"Alembic current did not report expected head {EXPECTED_HEAD}: {current_output}"
        )

    connection = _connect(database_url)
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT version_num FROM public.alembic_version")
            rows = cursor.fetchall()
    finally:
        connection.close()
    if [row[0] for row in rows] != [EXPECTED_HEAD]:
        raise RuntimeError(
            f"Alembic version table did not contain only {EXPECTED_HEAD}: {rows}"
        )
    print(f"Alembic head asserted: {EXPECTED_HEAD}.")


def _assert_schema(database_url: str) -> None:
    """Assert migration-created schemas, tables, and unique constraints."""

    connection = _connect(database_url)
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT schema_name
                FROM information_schema.schemata
                WHERE schema_name = 'reporting'
                """
            )
            if cursor.fetchone() is None:
                raise RuntimeError("Migration did not create the reporting schema")

            for schema, table in EXPECTED_TABLES:
                cursor.execute("SELECT to_regclass(%s)", (f"{schema}.{table}",))
                if cursor.fetchone()[0] is None:
                    raise RuntimeError(f"Migration did not create expected table {schema}.{table}")

            cursor.execute(
                """
                SELECT n.nspname, t.relname, c.conname
                FROM pg_constraint AS c
                JOIN pg_class AS t ON t.oid = c.conrelid
                JOIN pg_namespace AS n ON n.oid = t.relnamespace
                WHERE c.conname = ANY(%s)
                """,
                ([constraint[2] for constraint in EXPECTED_CONSTRAINTS],),
            )
            constraints = set(cursor.fetchall())
    finally:
        connection.close()

    missing_constraints = set(EXPECTED_CONSTRAINTS) - constraints
    if missing_constraints:
        names = ", ".join(".".join(item) for item in sorted(missing_constraints))
        raise RuntimeError(f"Migration did not create expected unique constraint(s): {names}")
    print(
        f"Migration-sourced schema asserted: {len(EXPECTED_TABLES)} tables, reporting schema, "
        f"and {len(EXPECTED_CONSTRAINTS)} unique constraints."
    )


def main() -> int:
    """Run the disposable migration verification."""

    admin_url = os.environ.get("DATABASE_URL")
    if not admin_url:
        print("DATABASE_URL is required and must point to disposable PostgreSQL.", file=sys.stderr)
        return 1

    database_name: str | None = None
    try:
        _assert_disposable_host(admin_url)
        _wait_for_postgres(admin_url)
        _assert_invalid_credentials_fail(admin_url)
        database_name, database_url = _create_clean_database(
            _url_for_database(admin_url, POSTGRES_ADMIN_DATABASE)
        )
        _assert_empty_database(database_url)
        _run_alembic(database_url, "upgrade", "head")
        _assert_head(database_url)
        _assert_schema(database_url)
        _run_alembic(database_url, "upgrade", "head")
        _assert_head(database_url)
        print(f"Idempotency asserted: second upgrade head succeeded for {database_name}.")
        print("Alembic migration verification passed.")
        return 0
    except (RuntimeError, psycopg2.Error) as exc:
        print(f"Alembic migration verification failed: {_safe_message(str(exc))}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
