from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

import psycopg2
from dotenv import load_dotenv

TABLE = "telemetry_events"
INDEXES: tuple[tuple[str, str], ...] = (
    ("ix_telemetry_events_timestamp", "CREATE INDEX IF NOT EXISTS ix_telemetry_events_timestamp ON telemetry_events (timestamp)"),
    ("ix_telemetry_events_event_type", "CREATE INDEX IF NOT EXISTS ix_telemetry_events_event_type ON telemetry_events (event_type)"),
    (
        "ix_telemetry_events_tags_gin",
        "CREATE INDEX IF NOT EXISTS ix_telemetry_events_tags_gin ON telemetry_events USING GIN (tags)",
    ),
)


def repo_root() -> Path:
    return Path(__file__).resolve().parent.parent


def resolve_database_url() -> str:
    url = os.environ.get("DATABASE_URL")
    if url:
        return url

    load_dotenv(repo_root() / "services" / "telemetry" / ".env")
    url = os.environ.get("DATABASE_URL")
    if url:
        return url

    load_dotenv(repo_root() / "services" / "inventory" / ".env")
    url = os.environ.get("DATABASE_URL")
    if url:
        return url

    raise SystemExit(
        "DATABASE_URL is not set. Export it in the environment or add it to "
        "services/telemetry/.env or services/inventory/.env"
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
        description="Create telemetry_events indexes on brasaland-m5 (idempotent)."
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print planned DDL only; do not execute.",
    )
    args = parser.parse_args()

    if args.dry_run:
        for name, ddl in INDEXES:
            print(f"-- {name}")
            print(ddl)
        print("Dry run — no changes made.")
        return 0

    url = resolve_database_url()
    conn = connect(url)

    try:
        if not table_exists(conn):
            raise SystemExit(
                f"Table public.{TABLE} does not exist. Start the telemetry service once "
                "so ensure_schema() creates it, then re-run this script."
            )

        with conn.cursor() as cursor:
            for name, ddl in INDEXES:
                cursor.execute(ddl)
                print(f"Ensured index: {name}")

        print(f"telemetry_events indexes ready on public.{TABLE}.")
        return 0
    finally:
        conn.close()


if __name__ == "__main__":
    sys.exit(main())
