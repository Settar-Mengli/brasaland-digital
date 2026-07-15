/** Wire types for the reporting API (CONTEXT §6). */

export type LocationPerformanceItem = {
  location_id: string;
  country: string;
  total_purchase_cost: number;
  total_waste_cost: number;
  waste_ratio: number;
  stockout_events_count: number;
  price_alert_events_count: number;
  currency: string;
};

export type WeeklyLocationPerformanceResponse = {
  week_start: string | null;
  locations: LocationPerformanceItem[];
};

export type PipelineRunResponse = {
  run_id: string | null;
  started_at: string | null;
  finished_at: string | null;
  status: string | null;
  week_start: string | null;
  records_extracted: number | null;
  records_loaded: number | null;
  missing_cost_events_count: number | null;
  error_detail: string | null;
};
