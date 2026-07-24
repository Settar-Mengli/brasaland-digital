export type IncidentStatus = 'open' | 'in_progress' | 'resolved' | 'discarded';

export type IncidentOrigin = 'customer' | 'branch' | 'internal';

export type IncidentCategory =
  | 'QUEJA_CLIENTE'
  | 'EQUIPAMIENTO'
  | 'ABASTECIMIENTO'
  | 'CALIDAD_ALIMENTO'
  | 'PERSONAL';

export type IncidentBranch =
  | 'COL-01'
  | 'COL-02'
  | 'COL-03'
  | 'COL-04'
  | 'COL-05'
  | 'COL-06'
  | 'COL-07'
  | 'COL-08'
  | 'COL-09'
  | 'COL-10'
  | 'FLA-01'
  | 'FLA-02'
  | 'FLA-03'
  | 'FLA-04'
  | 'Central';

export const INCIDENT_STATUSES = [
  'open',
  'in_progress',
  'resolved',
  'discarded',
] as const satisfies readonly IncidentStatus[];

export const INCIDENT_ORIGINS = [
  'customer',
  'branch',
  'internal',
] as const satisfies readonly IncidentOrigin[];

export const INCIDENT_CATEGORIES = [
  'QUEJA_CLIENTE',
  'EQUIPAMIENTO',
  'ABASTECIMIENTO',
  'CALIDAD_ALIMENTO',
  'PERSONAL',
] as const satisfies readonly IncidentCategory[];

export const INCIDENT_BRANCHES = [
  'COL-01',
  'COL-02',
  'COL-03',
  'COL-04',
  'COL-05',
  'COL-06',
  'COL-07',
  'COL-08',
  'COL-09',
  'COL-10',
  'FLA-01',
  'FLA-02',
  'FLA-03',
  'FLA-04',
  'Central',
] as const satisfies readonly IncidentBranch[];

export const CATEGORY_LABELS: Record<IncidentCategory, string> = {
  QUEJA_CLIENTE: 'Customer Complaint',
  EQUIPAMIENTO: 'Equipment',
  ABASTECIMIENTO: 'Supply',
  CALIDAD_ALIMENTO: 'Food Quality',
  PERSONAL: 'Staff',
};

export type Incident = {
  id: number;
  source_incident_id: string;
  title: string;
  description: string;
  category: IncidentCategory;
  status: IncidentStatus;
  origin: IncidentOrigin;
  branch: IncidentBranch;
  created_at: string;
  updated_at: string;
};

export type IncidentCreateInput = {
  title: string;
  description: string;
  category: IncidentCategory;
  origin: IncidentOrigin;
  branch: IncidentBranch;
  status?: IncidentStatus;
};

export type IncidentStatusUpdate = {
  status: IncidentStatus;
};

export type IncidentSummary = {
  total: number;
  by_status: Partial<Record<IncidentStatus, number>>;
  by_category: Partial<Record<IncidentCategory, number>>;
  by_origin: Partial<Record<IncidentOrigin, number>>;
  by_branch: Partial<Record<IncidentBranch, number>>;
};

export type IncidentListFilters = {
  status?: IncidentStatus;
  origin?: IncidentOrigin;
  branch?: IncidentBranch;
  category?: IncidentCategory;
};

export const STATUS_TRANSITIONS: Record<IncidentStatus, readonly IncidentStatus[]> = {
  open: ['in_progress', 'discarded'],
  in_progress: ['resolved', 'discarded'],
  resolved: [],
  discarded: [],
};

export function getAllowedNextStatuses(current: IncidentStatus): IncidentStatus[] {
  return [...STATUS_TRANSITIONS[current]];
}
