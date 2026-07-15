"""Add nullable unit_cost column to public.ingrediententry (idempotent).

What: Runs ALTER TABLE ... ADD COLUMN IF NOT EXISTS unit_cost DOUBLE PRECISION
on ingrediententry. Does not set NOT NULL or a DEFAULT.

Why: SQLModel metadata.create_all does not add columns to existing tables.
brasaland-m5 live rows must keep null unit_cost until new inbound orders supply a value.

How to run::

    cd services/inventory
    uv run --python 3.13 python ../../scripts/add_inventory_cost_column.py --dry-run
    uv run --python 3.13 python ../../scripts/add_inventory_cost_column.py

Operator only. Run AFTER merge and BEFORE restarting/deploying the inventory
service with the new SQLModel field.
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

import psycopg2
from dotenv import load_dotenv

TABLE = "ingrediententry"
COLUMN = "unit_cost"
DDL = (
    f"ALTER TABLE public.{TABLE} "
    f"ADD COLUMN IF NOT EXISTS {COLUMN} DOUBLE PRECISION"
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


def table_exists(conn: psycopg2.extensions.connection) -> bool:
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
            "Add nullable unit_cost to public.ingrediententry on brasaland-m5 "
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
                f"Table public.{TABLE} does not exist. Start the inventory service "
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
