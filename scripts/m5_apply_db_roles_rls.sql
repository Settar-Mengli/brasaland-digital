-- Operator apply script for brasaland-m5 DB roles + table-scoped RLS (model A).
--
-- DO NOT run from CI or agent automation against live m5.
-- Run manually on a DIRECT Postgres session (Supabase :5432 or SQL editor), not the
-- transaction pooler, unless operator confirms CREATE ROLE works on pooler.
--
-- Prerequisites:
--   1. Alembic head applied (e4f8a1b2c3d4).
--   2. Set strong passwords for each runtime role OUT OF BAND (Vault / Supabase).
--   3. Replace {{ROLE_PASSWORD}} below OR run scripts/apply_db_roles_rls.py locally
--      against disposable Postgres first, then adapt passwords for m5.
--
-- Post-apply:
--   - Point INVENTORY_DATABASE_URL, TELEMETRY_DATABASE_URL, INCIDENT_DATABASE_URL,
--     RFP_DATABASE_URL, REPORTING_DATABASE_URL at pooler URLs for each role.
--   - Keep MIGRATION_DATABASE_URL (or postgres owner URL) for Alembic only.
--   - Run scripts/verify_db_roles_rls.py against disposable Postgres to validate pattern.
--
-- Ordered apply: roles+grants (scripts/sql/db_roles_grants.sql) then policies
-- (scripts/sql/db_rls_policies.sql). Grant CONNECT ON DATABASE for each role:

-- GRANT CONNECT ON DATABASE your_db_name TO brasaland_inventory;
-- GRANT CONNECT ON DATABASE your_db_name TO brasaland_telemetry;
-- GRANT CONNECT ON DATABASE your_db_name TO brasaland_incident;
-- GRANT CONNECT ON DATABASE your_db_name TO brasaland_rfp;
-- GRANT CONNECT ON DATABASE your_db_name TO brasaland_reporting;

-- === Copy from scripts/sql/db_roles_grants.sql (substitute passwords) ===

-- === Copy from scripts/sql/db_rls_policies.sql ===
