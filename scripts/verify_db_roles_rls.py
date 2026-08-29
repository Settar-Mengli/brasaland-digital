"""Verify runtime DB roles, grants, RLS, and cross-service isolation on disposable Postgres.

Run after verify_alembic_migrations.py and apply_db_roles_rls.py::

    BRASALAND_RUNTIME_ROLE_PASSWORD=... \\
    MIGRATION_DATABASE_URL=postgresql://postgres:pass@localhost:5432/testdb \\
      uv run --directory data --python 3.13 python ../scripts/verify_db_roles_rls.py
"""

from __future__ import annotations

import os
import sys
from pathlib import Path
from urllib.parse import quote

sys.path.insert(0, str(Path(__file__).resolve().parent))

import psycopg2

from db_roles_constants import (
    CROSS_DENY_READS,
    DEFAULT_CI_ROLE_PASSWORD,
    POLICY_SUFFIX,
    REPORTING_TELEMETRY_READ_POLICY,
    RLS_PUBLIC_TABLES,
    RLS_REPORTING_TABLES,
    RUNTIME_ROLES,
    TABLE_GRANTS,
)

REPO_ROOT = Path(__file__).resolve().parent.parent


def resolve_admin_url() -> str:
    url = os.environ.get("MIGRATION_DATABASE_URL") or os.environ.get("DATABASE_URL")
    if not url:
        raise RuntimeError("MIGRATION_DATABASE_URL or DATABASE_URL is required")
    if "supabase" in url.lower():
        raise RuntimeError("Refusing to run against a Supabase host")
    return url


def resolve_role_password() -> str:
    return os.environ.get("BRASALAND_RUNTIME_ROLE_PASSWORD") or DEFAULT_CI_ROLE_PASSWORD


def role_database_url(admin_url: str, role: str, password: str) -> str:
    """Build a role URL preserving host/db from admin_url."""
    from sqlalchemy.engine import make_url

    parsed = make_url(admin_url)
    encoded_password = quote(password, safe="")
    user = quote(role, safe="")
    host = parsed.host or "localhost"
    port = parsed.port or 5432
    database = parsed.database or "postgres"
    driver = parsed.drivername.split("+")[0]
    return f"{driver}://{user}:{encoded_password}@{host}:{port}/{database}"


def assert_roles_exist(conn: psycopg2.extensions.connection) -> None:
    with conn.cursor() as cursor:
        cursor.execute(
            "SELECT rolname FROM pg_roles WHERE rolname = ANY(%s)",
            (list(RUNTIME_ROLES),),
        )
        found = {row[0] for row in cursor.fetchall()}
    missing = set(RUNTIME_ROLES) - found
    if missing:
        raise RuntimeError(f"Missing runtime roles: {', '.join(sorted(missing))}")
    print(f"Roles asserted: {len(RUNTIME_ROLES)} runtime roles exist.")


def assert_grants(conn: psycopg2.extensions.connection) -> None:
    for role, table_map in TABLE_GRANTS.items():
        for (schema, table), privileges in table_map.items():
            for privilege in privileges:
                with conn.cursor() as cursor:
                    cursor.execute(
                        "SELECT has_table_privilege(%s, %s, %s)",
                        (role, f"{schema}.{table}", privilege),
                    )
                    allowed = cursor.fetchone()[0]
                if not allowed:
                    raise RuntimeError(
                        f"Missing grant: {role} needs {privilege} on {schema}.{table}"
                    )
    print("Grants asserted: table privilege matrix matches expectations.")


def assert_rls_force(conn: psycopg2.extensions.connection) -> None:
    with conn.cursor() as cursor:
        for table in RLS_PUBLIC_TABLES:
            cursor.execute(
                """
                SELECT c.relrowsecurity, c.relforcerowsecurity
                FROM pg_class AS c
                JOIN pg_namespace AS n ON n.oid = c.relnamespace
                WHERE n.nspname = 'public' AND c.relname = %s
                """,
                (table,),
            )
            row = cursor.fetchone()
            if row is None:
                raise RuntimeError(f"Missing public table: {table}")
            if not row[0] or not row[1]:
                raise RuntimeError(
                    f"RLS not enabled+forced on public.{table}: "
                    f"rowsecurity={row[0]} forcerowsecurity={row[1]}"
                )
        for table in RLS_REPORTING_TABLES:
            cursor.execute(
                """
                SELECT c.relrowsecurity, c.relforcerowsecurity
                FROM pg_class AS c
                JOIN pg_namespace AS n ON n.oid = c.relnamespace
                WHERE n.nspname = 'reporting' AND c.relname = %s
                """,
                (table,),
            )
            row = cursor.fetchone()
            if row is None:
                raise RuntimeError(f"Missing reporting table: {table}")
            if not row[0] or not row[1]:
                raise RuntimeError(
                    f"RLS not enabled+forced on reporting.{table}: "
                    f"rowsecurity={row[0]} forcerowsecurity={row[1]}"
                )
    print(
        f"RLS asserted: FORCE ROW LEVEL SECURITY on "
        f"{len(RLS_PUBLIC_TABLES) + len(RLS_REPORTING_TABLES)} tables."
    )


def assert_policies(conn: psycopg2.extensions.connection) -> None:
    expected_names: set[str] = set(POLICY_SUFFIX.values())
    expected_names.add(REPORTING_TELEMETRY_READ_POLICY)

    with conn.cursor() as cursor:
        cursor.execute(
            """
            SELECT policyname FROM pg_policies
            WHERE schemaname IN ('public', 'reporting')
            """
        )
        found = {row[0] for row in cursor.fetchall()}

    missing = expected_names - found
    if missing:
        raise RuntimeError(
            f"Missing RLS policies: {', '.join(sorted(missing))}"
        )
    print(f"Policies asserted: {len(expected_names)} expected policy names present.")


def smoke_cross_denies(admin_url: str, password: str) -> None:
    admin_conn = psycopg2.connect(admin_url)
    try:
        for role, deny_list in CROSS_DENY_READS.items():
            for schema, table in deny_list:
                qualified = f"{schema}.{table}"
                with admin_conn.cursor() as cursor:
                    cursor.execute(
                        "SELECT has_table_privilege(%s, %s, %s)",
                        (role, qualified, "SELECT"),
                    )
                    allowed = cursor.fetchone()[0]
                if allowed:
                    raise RuntimeError(
                        f"Cross-service smoke failed: {role} has SELECT on {qualified}"
                    )
    finally:
        admin_conn.close()

    # Own-table read smoke: inventory can read ingredient
    inventory_url = role_database_url(admin_url, "brasaland_inventory", password)
    inv_conn = psycopg2.connect(inventory_url)
    try:
        with inv_conn.cursor() as cursor:
            cursor.execute("SELECT 1 FROM public.ingredient LIMIT 1")
            cursor.fetchone()
    finally:
        inv_conn.close()

    print("Smoke asserted: cross-service SELECT denied; inventory own-table SELECT ok.")


def main() -> int:
    admin_url = resolve_admin_url()
    password = resolve_role_password()

    conn = psycopg2.connect(admin_url)
    try:
        assert_roles_exist(conn)
        assert_grants(conn)
        assert_rls_force(conn)
        assert_policies(conn)
    finally:
        conn.close()

    smoke_cross_denies(admin_url, password)
    print("DB roles and RLS verification passed.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except RuntimeError as exc:
        print(f"DB roles and RLS verification failed: {exc}", file=sys.stderr)
        raise SystemExit(1)
