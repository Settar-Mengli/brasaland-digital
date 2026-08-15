"""Add nullable owner_user_uuid column to public.ticket (idempotent).

What: Runs ALTER TABLE ... ADD COLUMN IF NOT EXISTS owner_user_uuid TEXT
on ticket. Does not set NOT NULL or a DEFAULT.

Why: SQLModel metadata.create_all does not add columns to existing tables.
Existing brasaland-m5 ticket rows stay NULL (legacy) until new uploads stamp an
owner; ACL treats NULL as deny for non-admins.

How to run::

    cd services/rfp
    uv run --python 3.13 python ../../scripts/add_rfp_ticket_owner_column.py --dry-run
    uv run --python 3.13 python ../../scripts/add_rfp_ticket_owner_column.py

Operator only. Run AFTER merge and BEFORE relying on owner ACL against the
shared database (restart/redeploy rfp after the column exists).
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

TABLE = "ticket"
COLUMN = "owner_user_uuid"
DDL = (
    f"ALTER TABLE public.{TABLE} "
    f"ADD COLUMN IF NOT EXISTS {COLUMN} TEXT"
)


def repo_root() -> Path:
    return Path(__file__).resolve().parent.parent


def resolve_database_url() -> str:
    url = os.environ.get("DATABASE_URL")
    if url:
        return url

    load_dotenv(repo_root() / ".env")
    url = os.environ.get("DATABASE_URL")
    if url:
        return url

    raise SystemExit(
        "DATABASE_URL is not set. Export it in the environment or add it to "
        "the repo-root .env"
    )


def connect(url: str):
    import psycopg2

    try:
        connection = psycopg2.connect(url)
    except psycopg2.Error as exc:
        raise SystemExit(f"Connection failed: {type(exc).__name__}") from exc

    connection.autocommit = True
    return connection


def table_exists(conn) -> bool:
    with conn.cursor() as cursor:
        cursor.execute(
            """
            SELECT EXISTS (
              SELECT 1
              FROM information_schema.tables
              WHERE table_schema = 'public' AND table_name = %s
            )
            """,
            (TABLE,),
        )
        row = cursor.fetchone()
    return bool(row and row[0])


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Add nullable owner_user_uuid to public.ticket on brasaland-m5 "
            "(idempotent)."
        )
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print planned DDL only; do not execute.",
    )
    args = parser.parse_args()

    if args.dry_run:
        print(f"-- {TABLE}.{COLUMN}")
        print(DDL)
        print("Dry run — no changes made.")
        return 0

    url = resolve_database_url()
    conn = connect(url)

    try:
        if not table_exists(conn):
            raise SystemExit(
                f"Table public.{TABLE} does not exist. Start the rfp service "
                "once so create_all creates it, then re-run this script."
            )

        with conn.cursor() as cursor:
            cursor.execute(DDL)
            print(f"Ensured column: public.{TABLE}.{COLUMN}")

        print(f"{COLUMN} ready on public.{TABLE}.")
        return 0
    finally:
        conn.close()


if __name__ == "__main__":
    sys.exit(main())
