"""Create reporting schema and enable RLS on reporting tables (idempotent).

What: Ensures ``CREATE SCHEMA IF NOT EXISTS reporting``. For each of
``reporting.weekly_location_performance`` and ``reporting.pipeline_runs``,
runs ``ALTER TABLE ... ENABLE ROW LEVEL SECURITY`` when the table exists;
when absent, prints ``table not present, RLS skipped`` and continues.
Does not create policies and does not set FORCE ROW LEVEL SECURITY.

Why: SQLModel ``create_all`` with ``schema="reporting"`` fails if the schema
does not exist yet. Operators run this script first (schema only / RLS skipped),
then Lane-1 ``ensure_schema``, then this script again (RLS enablement).

How to run::

    uv run --python 3.13 python scripts/setup_reporting_schema.py --dry-run
    uv run --python 3.13 python scripts/setup_reporting_schema.py

Operator only. Safe before tables exist (exit 0). Do not agent-run against
brasaland-m5.
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

import psycopg2
from dotenv import load_dotenv

SCHEMA = "reporting"
TABLES: tuple[str, ...] = (
    "weekly_location_performance",
    "pipeline_runs",
)
CREATE_SCHEMA_SQL = f"CREATE SCHEMA IF NOT EXISTS {SCHEMA}"


def repo_root() -> Path:
    return Path(__file__).resolve().parent.parent


def resolve_database_url() -> str:
    url = os.environ.get("DATABASE_URL")
    if url:
        return url

    load_dotenv(repo_root() / "data" / ".env")
    url = os.environ.get("DATABASE_URL")
    if url:
        return url

    load_dotenv(repo_root() / "services" / "inventory" / ".env")
    url = os.environ.get("DATABASE_URL")
    if url:
        return url

    raise SystemExit(
        "DATABASE_URL is not set. Export it in the environment or add it to "
        "data/.env or services/inventory/.env"
    )


def connect(url: str) -> psycopg2.extensions.connection:
    try:
        connection = psycopg2.connect(url)
    except psycopg2.Error as exc:
        raise SystemExit(f"Connection failed: {type(exc).__name__}") from exc

    connection.autocommit = True
    return connection


def table_exists(conn: psycopg2.extensions.connection, table: str) -> bool:
    with conn.cursor() as cursor:
        cursor.execute(
            """
            SELECT EXISTS (
              SELECT 1
              FROM information_schema.tables
              WHERE table_schema = %s AND table_name = %s
            )
            """,
            (SCHEMA, table),
        )
        row = cursor.fetchone()
    return bool(row and row[0])


def enable_rls_sql(table: str) -> str:
    return f"ALTER TABLE {SCHEMA}.{table} ENABLE ROW LEVEL SECURITY"


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Create reporting schema and enable RLS on reporting tables "
            "(idempotent; safe before tables exist)."
        )
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print planned statements only; do not connect or mutate.",
    )
    args = parser.parse_args()

    if args.dry_run:
        print("Dry run — planned statements:")
        print(f"  {CREATE_SCHEMA_SQL}")
        for table in TABLES:
            print(
                f"  IF {SCHEMA}.{table} exists → {enable_rls_sql(table)}; "
                f"ELSE → table not present, RLS skipped"
            )
        print("Dry run — no changes made.")
        return 0

    url = resolve_database_url()
    conn = connect(url)

    try:
        with conn.cursor() as cursor:
            cursor.execute(CREATE_SCHEMA_SQL)
        print(f"Executed: {CREATE_SCHEMA_SQL}")

        for table in TABLES:
            qualified = f"{SCHEMA}.{table}"
            if not table_exists(conn, table):
                print(f"{qualified}: table not present, RLS skipped")
                continue
            sql = enable_rls_sql(table)
            with conn.cursor() as cursor:
                cursor.execute(sql)
            print(f"Executed: {sql}")

        return 0
    finally:
        conn.close()


if __name__ == "__main__":
    sys.exit(main())
