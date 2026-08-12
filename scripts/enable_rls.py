"""Enable Row-Level Security on brasaland-m5 public tables (no policies, no FORCE).

What: Runs ALTER TABLE ... ENABLE ROW LEVEL SECURITY on ingredient, ingrediententry,
ingredientexit, incident, telemetry_events, ticket, rfp_metadata, department_section,
final_document, and task_dead_letters. Does not create policies and does not set FORCE ROW LEVEL
SECURITY.

Why: Closes PostgREST/anon Data API exposure (deny-by-default when RLS is on with zero
policies). FastAPI services connect as table owner ``postgres`` via DATABASE_URL and
bypass RLS without FORCE.

How to run::

    cd services/inventory
    uv run --python 3.13 python ../../scripts/enable_rls.py
    uv run --python 3.13 python ../../scripts/enable_rls.py --dry-run

Future-table caveat: SQLModel.metadata.create_all creates new tables with RLS disabled.
Re-run this script after adding any table.
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

import psycopg2
from dotenv import load_dotenv

TABLES: tuple[str, ...] = (
    "ingredient",
    "ingrediententry",
    "ingredientexit",
    "incident",
    "telemetry_events",
    "ticket",
    "rfp_metadata",
    "department_section",
    "final_document",
    "task_dead_letters",
)


def repo_root() -> Path:
    return Path(__file__).resolve().parent.parent


def resolve_database_url() -> str:
    url = os.environ.get("DATABASE_URL")
    if url:
        return url

    load_dotenv(repo_root() / "services" / "inventory" / ".env")
    url = os.environ.get("DATABASE_URL")
    if url:
        return url

    raise SystemExit(
        "DATABASE_URL is not set. Export it in the environment or add it to "
        "services/inventory/.env"
    )


def connect(url: str) -> psycopg2.extensions.connection:
    try:
        connection = psycopg2.connect(url)
    except psycopg2.Error as exc:
        raise SystemExit(f"Connection failed: {type(exc).__name__}") from exc

    connection.autocommit = True
    return connection


def fetch_rowsecurity(conn: psycopg2.extensions.connection) -> dict[str, bool]:
    with conn.cursor() as cursor:
        cursor.execute(
            """
            SELECT tablename, rowsecurity
            FROM pg_tables
            WHERE schemaname = 'public' AND tablename = ANY(%s)
            """,
            (list(TABLES),),
        )
        rows = cursor.fetchall()

    state = {name: enabled for name, enabled in rows}
    missing = [table for table in TABLES if table not in state]
    if missing:
        raise SystemExit(f"Missing table(s) in public schema: {', '.join(missing)}")

    return state


def enable_rls(conn: psycopg2.extensions.connection, table: str) -> None:
    with conn.cursor() as cursor:
        cursor.execute(f"ALTER TABLE public.{table} ENABLE ROW LEVEL SECURITY")


def print_state(label: str, state: dict[str, bool]) -> None:
    print(label)
    for table in TABLES:
        status = "ENABLED" if state[table] else "DISABLED"
        print(f"  {table}: {status}")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Enable RLS on brasaland-m5 public tables (no policies)."
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Report current RLS state only; do not run ALTER TABLE.",
    )
    args = parser.parse_args()

    url = resolve_database_url()
    conn = connect(url)

    try:
        before = fetch_rowsecurity(conn)
        print_state("Before:", before)

        if args.dry_run:
            print("Dry run — no changes made.")
            return 0

        for table in TABLES:
            enable_rls(conn, table)

        after = fetch_rowsecurity(conn)
        print_state("After:", after)

        if all(after[table] for table in TABLES):
            return 0

        print("Not all tables have RLS enabled after ALTER.", file=sys.stderr)
        return 1
    finally:
        conn.close()


if __name__ == "__main__":
    sys.exit(main())
