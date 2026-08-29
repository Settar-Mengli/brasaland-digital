-- Runtime role grants for brasaland-m5 (disposable Postgres + operator review).
-- Run as migration owner (postgres / brasaland_migrator). Passwords set separately.
-- Substitute {{ROLE_PASSWORD}} when applied by scripts/apply_db_roles_rls.py.

DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'brasaland_inventory') THEN
    CREATE ROLE brasaland_inventory WITH LOGIN PASSWORD '{{ROLE_PASSWORD}}';
  ELSE
    ALTER ROLE brasaland_inventory WITH LOGIN PASSWORD '{{ROLE_PASSWORD}}';
  END IF;
  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'brasaland_telemetry') THEN
    CREATE ROLE brasaland_telemetry WITH LOGIN PASSWORD '{{ROLE_PASSWORD}}';
  ELSE
    ALTER ROLE brasaland_telemetry WITH LOGIN PASSWORD '{{ROLE_PASSWORD}}';
  END IF;
  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'brasaland_incident') THEN
    CREATE ROLE brasaland_incident WITH LOGIN PASSWORD '{{ROLE_PASSWORD}}';
  ELSE
    ALTER ROLE brasaland_incident WITH LOGIN PASSWORD '{{ROLE_PASSWORD}}';
  END IF;
  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'brasaland_rfp') THEN
    CREATE ROLE brasaland_rfp WITH LOGIN PASSWORD '{{ROLE_PASSWORD}}';
  ELSE
    ALTER ROLE brasaland_rfp WITH LOGIN PASSWORD '{{ROLE_PASSWORD}}';
  END IF;
  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'brasaland_reporting') THEN
    CREATE ROLE brasaland_reporting WITH LOGIN PASSWORD '{{ROLE_PASSWORD}}';
  ELSE
    ALTER ROLE brasaland_reporting WITH LOGIN PASSWORD '{{ROLE_PASSWORD}}';
  END IF;
END
$$;

GRANT USAGE ON SCHEMA public TO brasaland_inventory;
GRANT USAGE ON SCHEMA public TO brasaland_telemetry;
GRANT USAGE ON SCHEMA public TO brasaland_incident;
GRANT USAGE ON SCHEMA public TO brasaland_rfp;
GRANT USAGE ON SCHEMA public TO brasaland_reporting;

GRANT USAGE ON SCHEMA reporting TO brasaland_reporting;

-- Inventory
GRANT SELECT, INSERT, UPDATE ON public.ingredient TO brasaland_inventory;
GRANT SELECT, INSERT, UPDATE ON public.ingrediententry TO brasaland_inventory;
GRANT SELECT, INSERT, UPDATE ON public.ingredientexit TO brasaland_inventory;

-- Telemetry
GRANT SELECT, INSERT ON public.telemetry_events TO brasaland_telemetry;

-- Incident
GRANT SELECT, INSERT, UPDATE ON public.incident TO brasaland_incident;

-- RFP
GRANT SELECT, INSERT, UPDATE ON public.ticket TO brasaland_rfp;
GRANT SELECT, INSERT, UPDATE ON public.rfp_metadata TO brasaland_rfp;
GRANT SELECT, INSERT, UPDATE ON public.department_section TO brasaland_rfp;
GRANT SELECT, INSERT, UPDATE ON public.final_document TO brasaland_rfp;

-- Reporting (schema + telemetry read)
GRANT SELECT, INSERT, UPDATE, DELETE ON reporting.weekly_location_performance TO brasaland_reporting;
GRANT SELECT, INSERT, UPDATE, DELETE ON reporting.pipeline_runs TO brasaland_reporting;
GRANT SELECT, INSERT, UPDATE, DELETE ON reporting.job_runs TO brasaland_reporting;
GRANT SELECT, INSERT, UPDATE, DELETE ON reporting.task_dead_letters TO brasaland_reporting;
GRANT SELECT ON public.telemetry_events TO brasaland_reporting;

-- Revoke broad PUBLIC access on application tables (idempotent).
REVOKE ALL ON public.ingredient FROM PUBLIC;
REVOKE ALL ON public.ingrediententry FROM PUBLIC;
REVOKE ALL ON public.ingredientexit FROM PUBLIC;
REVOKE ALL ON public.incident FROM PUBLIC;
REVOKE ALL ON public.telemetry_events FROM PUBLIC;
REVOKE ALL ON public.ticket FROM PUBLIC;
REVOKE ALL ON public.rfp_metadata FROM PUBLIC;
REVOKE ALL ON public.department_section FROM PUBLIC;
REVOKE ALL ON public.final_document FROM PUBLIC;

REVOKE ALL ON reporting.weekly_location_performance FROM PUBLIC;
REVOKE ALL ON reporting.pipeline_runs FROM PUBLIC;
REVOKE ALL ON reporting.job_runs FROM PUBLIC;
REVOKE ALL ON reporting.task_dead_letters FROM PUBLIC;
