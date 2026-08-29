"""Apply runtime DB roles, grants, and RLS policies on disposable PostgreSQL.

Requires migration owner URL (MIGRATION_DATABASE_URL or DATABASE_URL) and an
Alembic-upgraded schema. Never run against live brasaland-m5 from automation.

Usage (repo root)::

    BRASALAND_RUNTIME_ROLE_PASSWORD=... \\
    MIGRATION_DATABASE_URL=postgresql://postgres:pass@localhost:5432/postgres \\
      uv run --directory data --python 3.13 python ../scripts/apply_db_roles_rls.py

    uv run --directory data --python 3.13 python ../scripts/apply_db_roles_rls.py --dry-run
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import psycopg2
from psycopg2 import sql

from db_roles_constants import DEFAULT_CI_ROLE_PASSWORD, RUNTIME_ROLES

REPO_ROOT = Path(__file__).resolve().parent.parent
SQL_DIR = Path(__file__).resolve().parent / "sql"


def resolve_admin_url() -> str:
    url = os.environ.get("MIGRATION_DATABASE_URL") or os.environ.get("DATABASE_URL")
    if not url:
        raise RuntimeError(
            "MIGRATION_DATABASE_URL or DATABASE_URL is required (migration owner)."
        )
    host = url.lower()
    if "supabase" in host:
        raise RuntimeError("Refusing to run against a Supabase host; use disposable Postgres")
    return url


def resolve_role_password() -> str:
    password = os.environ.get("BRASALAND_RUNTIME_ROLE_PASSWORD")
    if password:
        return password
    return DEFAULT_CI_ROLE_PASSWORD


def load_sql(path: Path, password: str) -> str:
    text = path.read_text(encoding="utf-8")
    return text.replace("{{ROLE_PASSWORD}}", password.replace("'", "''"))


def grant_connect(conn: psycopg2.extensions.connection) -> None:
    with conn.cursor() as cursor:
        cursor.execute("SELECT current_database()")
        database_name = cursor.fetchone()[0]
        for role in RUNTIME_ROLES:
            cursor.execute(
                sql.SQL("GRANT CONNECT ON DATABASE {} TO {}").format(
                    sql.Identifier(database_name),
                    sql.Identifier(role),
                )
            )


def apply_sql(conn: psycopg2.extensions.connection, script: str) -> None:
    with conn.cursor() as cursor:
        cursor.execute(script)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print planned steps without connecting.",
    )
    args = parser.parse_args()

    grants_path = SQL_DIR / "db_roles_grants.sql"
    policies_path = SQL_DIR / "db_rls_policies.sql"
    password = resolve_role_password()

    if args.dry_run:
        print("Dry run — planned apply order:")
        print(f"  1. {grants_path.name} (roles + grants, password redacted)")
        print(f"  2. GRANT CONNECT ON DATABASE <current> TO each runtime role")
        print(f"  3. {policies_path.name}")
        print("Dry run — no changes made.")
        return 0

    admin_url = resolve_admin_url()
    grants_sql = load_sql(grants_path, password)
    policies_sql = policies_path.read_text(encoding="utf-8")

    conn = psycopg2.connect(admin_url)
    conn.autocommit = True
    try:
        print("Applying roles and grants...")
        apply_sql(conn, grants_sql)
        print("Granting CONNECT on current database to runtime roles...")
        grant_connect(conn)
        print("Applying RLS policies...")
        apply_sql(conn, policies_sql)
        print("DB roles and RLS policies applied successfully.")
        return 0
    except psycopg2.Error as exc:
        print(f"apply_db_roles_rls failed: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 1
    finally:
        conn.close()


if __name__ == "__main__":
    raise SystemExit(main())
