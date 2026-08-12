/**
 * Wire types for the RFP ticket API (`POST/GET /rfp/tickets`).
 */

export interface EvaluationReadability {
  pass?: boolean;
  score?: number;
  details?: {
    flesch_reading_ease?: number;
    flesch_kincaid_grade?: number;
  };
}

export interface EvaluationRelevance {
  pass?: boolean;
  missing_aspects?: string[];
}

export interface EvaluationCompliance {
  pass?: boolean;
  rule_ids?: string[];
  violations?: string[];
}

/** Partial-tolerant EvaluationResult from GET /rfp/tickets sections. */
export interface EvaluationResult {
  department_id?: string;
  readability?: EvaluationReadability | null;
  relevance?: EvaluationRelevance | null;
  compliance?: EvaluationCompliance | null;
  overall_pass?: boolean;
  feedback_for_generator?: string;
  iterations?: number;
  exhausted?: boolean;
  needs_human_review?: boolean;
  ceo_approval_required?: boolean;
}

export interface RfpSection {
  department_id: string;
  key_aspects?: string[] | null;
  draft_content?: string | null;
  evaluation_results?: EvaluationResult | null;
  approval_status?: string | null;
}

export interface RfpTicket {
  ticket_id: string;
  rfp_id: string;
  status: string;
  created_at?: string;
  updated_at?: string;
  sections?: RfpSection[];
}

export type RfpUploadResponse = Pick<RfpTicket, 'ticket_id' | 'rfp_id' | 'status'>;

/** Upload/intake poll ends on intake_complete or discarded. */
export const TERMINAL_STATUSES = ['intake_complete', 'discarded'] as const;

/** Post-Generate response poll ends on under_evaluation or discarded. */
export const RESPONSE_TERMINAL_STATUSES = ['under_evaluation', 'discarded'] as const;

export type TerminalStatus = (typeof TERMINAL_STATUSES)[number];
export type ResponseTerminalStatus = (typeof RESPONSE_TERMINAL_STATUSES)[number];
