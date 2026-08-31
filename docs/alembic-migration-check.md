# Disposable Alembic migration check

The `Alembic migration check` workflow runs against the pinned `postgres:16.4`
service. The verifier makes a real authenticated PostgreSQL connection, creates
a uniquely named database from `template0`, and confirms that no application
tables exist before Alembic runs. It then executes `upgrade head`, asserts head
revision `f9a2b3c4d5e6`, and checks the public tables, the `reporting` schema and
tables, and the two RFP unique constraints:

- `uq_department_section_ticket_department`
- `uq_final_document_ticket`

The verifier runs `upgrade head` a second time and asserts the same head again.
This proves the migration history is idempotent. It never imports application
models and never calls `SQLModel.metadata.create_all`, so the checked schema is
created by the Alembic revisions. Connection and subprocess errors are
sanitized before being printed, and an intentionally invalid password must be
rejected.

## Local reproduction

Use only a disposable PostgreSQL instance. Do not point this check at a
developer database, Supabase, or any shared environment.

```powershell
docker run --rm --name brasaland-alembic-postgres `
  -e POSTGRES_USER=postgres `
  -e POSTGRES_PASSWORD=local_postgres_password `
  -e POSTGRES_DB=postgres `
  -p 5432:5432 postgres:16.4

$env:DATABASE_URL = "postgresql://postgres:local_postgres_password@localhost:5432/postgres"
uv run --directory data --locked --python 3.13 python ../scripts/verify_alembic_migrations.py

docker rm -f brasaland-alembic-postgres
```

The script leaves its uniquely named `alembic_ci_*` database for inspection.
Drop that disposable database after a successful run if it is no longer needed.

## DB roles and RLS check

After migrations pass, the `DB roles and RLS check` workflow applies runtime
roles, grants, FORCE RLS, and policies then verifies the privilege matrix.
Local reproduction (same disposable Postgres container):

```powershell
$env:MIGRATION_DATABASE_URL = $env:DATABASE_URL
$env:BRASALAND_RUNTIME_ROLE_PASSWORD = "ci_brasaland_runtime_role_password"
uv run --directory data --locked --python 3.13 python ../scripts/apply_db_roles_rls.py
uv run --directory data --locked --python 3.13 python ../scripts/verify_db_roles_rls.py
```

Operator apply on live m5 uses `scripts/m5_apply_db_roles_rls.sql` on a direct
session — not the disposable CI apply script.
