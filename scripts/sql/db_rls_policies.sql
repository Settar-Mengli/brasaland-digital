-- Table-scoped RLS policies (model A: service isolation). Run after grants.
-- Idempotent: DROP POLICY IF EXISTS before CREATE.

-- Inventory
ALTER TABLE public.ingredient ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.ingredient FORCE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS inventory_ingredient_all ON public.ingredient;
CREATE POLICY inventory_ingredient_all ON public.ingredient
  FOR ALL TO brasaland_inventory USING (true) WITH CHECK (true);

ALTER TABLE public.ingrediententry ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.ingrediententry FORCE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS inventory_ingrediententry_all ON public.ingrediententry;
CREATE POLICY inventory_ingrediententry_all ON public.ingrediententry
  FOR ALL TO brasaland_inventory USING (true) WITH CHECK (true);

ALTER TABLE public.ingredientexit ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.ingredientexit FORCE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS inventory_ingredientexit_all ON public.ingredientexit;
CREATE POLICY inventory_ingredientexit_all ON public.ingredientexit
  FOR ALL TO brasaland_inventory USING (true) WITH CHECK (true);

-- Telemetry
ALTER TABLE public.telemetry_events ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.telemetry_events FORCE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS telemetry_events_all ON public.telemetry_events;
CREATE POLICY telemetry_events_all ON public.telemetry_events
  FOR ALL TO brasaland_telemetry USING (true) WITH CHECK (true);

DROP POLICY IF EXISTS reporting_telemetry_events_read ON public.telemetry_events;
CREATE POLICY reporting_telemetry_events_read ON public.telemetry_events
  FOR SELECT TO brasaland_reporting USING (true);

-- Incident
ALTER TABLE public.incident ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.incident FORCE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS incident_all ON public.incident;
CREATE POLICY incident_all ON public.incident
  FOR ALL TO brasaland_incident USING (true) WITH CHECK (true);

-- RFP
ALTER TABLE public.ticket ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.ticket FORCE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS rfp_ticket_all ON public.ticket;
CREATE POLICY rfp_ticket_all ON public.ticket
  FOR ALL TO brasaland_rfp USING (true) WITH CHECK (true);

ALTER TABLE public.rfp_metadata ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.rfp_metadata FORCE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS rfp_metadata_all ON public.rfp_metadata;
CREATE POLICY rfp_metadata_all ON public.rfp_metadata
  FOR ALL TO brasaland_rfp USING (true) WITH CHECK (true);

ALTER TABLE public.department_section ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.department_section FORCE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS rfp_department_section_all ON public.department_section;
CREATE POLICY rfp_department_section_all ON public.department_section
  FOR ALL TO brasaland_rfp USING (true) WITH CHECK (true);

ALTER TABLE public.final_document ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.final_document FORCE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS rfp_final_document_all ON public.final_document;
CREATE POLICY rfp_final_document_all ON public.final_document
  FOR ALL TO brasaland_rfp USING (true) WITH CHECK (true);

-- Reporting schema
ALTER TABLE reporting.weekly_location_performance ENABLE ROW LEVEL SECURITY;
ALTER TABLE reporting.weekly_location_performance FORCE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS reporting_weekly_location_performance_all ON reporting.weekly_location_performance;
CREATE POLICY reporting_weekly_location_performance_all ON reporting.weekly_location_performance
  FOR ALL TO brasaland_reporting USING (true) WITH CHECK (true);

ALTER TABLE reporting.pipeline_runs ENABLE ROW LEVEL SECURITY;
ALTER TABLE reporting.pipeline_runs FORCE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS reporting_pipeline_runs_all ON reporting.pipeline_runs;
CREATE POLICY reporting_pipeline_runs_all ON reporting.pipeline_runs
  FOR ALL TO brasaland_reporting USING (true) WITH CHECK (true);

ALTER TABLE reporting.job_runs ENABLE ROW LEVEL SECURITY;
ALTER TABLE reporting.job_runs FORCE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS reporting_job_runs_all ON reporting.job_runs;
CREATE POLICY reporting_job_runs_all ON reporting.job_runs
  FOR ALL TO brasaland_reporting USING (true) WITH CHECK (true);

ALTER TABLE reporting.task_dead_letters ENABLE ROW LEVEL SECURITY;
ALTER TABLE reporting.task_dead_letters FORCE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS reporting_task_dead_letters_all ON reporting.task_dead_letters;
CREATE POLICY reporting_task_dead_letters_all ON reporting.task_dead_letters
  FOR ALL TO brasaland_reporting USING (true) WITH CHECK (true);
