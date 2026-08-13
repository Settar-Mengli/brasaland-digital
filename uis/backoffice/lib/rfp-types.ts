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
  interrupt_id?: string;
  cost?: number | null;
  setup_days?: number | null;
  price_per_cover?: number | null;
  graph_outcome?: string;
  arbitration?: RfpArbitration;
}

export interface RfpArbitration {
  ceo_approval_required?: boolean;
  ceo_interrupt_id?: string | null;
  ceo_decision?: string | null;
  ceo_approved_at?: string | null;
  triggers_fired?: unknown[];
  resolutions?: unknown[];
  conflicts?: unknown[];
}

export interface RfpSection {
  department_id: string;
  key_aspects?: string[] | null;
  draft_content?: string | null;
  evaluation_results?: EvaluationResult | null;
  approval_status?: string | null;
  approver?: string | null;
  approved_at?: string | null;
  awaiting_decision?: boolean;
}

export interface RfpFinalDocumentHeader {
  client_name?: string | null;
  location?: string | null;
  service_type?: string | null;
  generated_at?: string | null;
  ticket_id?: string;
}

export interface RfpFinalDocumentSection {
  department_id: string;
  owner?: string | null;
  draft_content?: string | null;
  approval_stamp?: string | null;
  approver?: string | null;
  approved_at?: string | null;
}

export interface RfpFinalDocument {
  header?: RfpFinalDocumentHeader;
  sections?: RfpFinalDocumentSection[];
  arbitration_outcomes?: {
    triggers_fired?: unknown[];
    resolutions?: unknown[];
  };
  ceo_line?: string | null;
  total_estimated_value?: string | null;
  open_questions?: string[];
  /** Legacy GET shape when document column is null */
  ticket_id?: string;
  generated_at?: string | null;
}

export interface RfpTicket {
  ticket_id: string;
  rfp_id: string;
  status: string;
  created_at?: string;
  updated_at?: string;
  sections?: RfpSection[];
  arbitration?: RfpArbitration | null;
  final_document?: RfpFinalDocument | null;
}

export type RfpUploadResponse = Pick<RfpTicket, 'ticket_id' | 'rfp_id' | 'status'>;

export interface RfpSectionDecisionResponse {
  ticket_id: string;
  department_id?: string;
  outcome?: string;
  status?: string;
  ceo_pending?: boolean;
  final_document?: RfpFinalDocument | null;
}

export interface RfpCeoDecisionResponse {
  ticket_id: string;
  ceo_decision?: string;
  status?: string;
  final_document?: RfpFinalDocument | null;
}

/** Upload/intake poll ends on intake_complete or discarded. */
export const TERMINAL_STATUSES = ['intake_complete', 'discarded'] as const;

/** Post-Generate response poll ends on under_evaluation or discarded. */
export const RESPONSE_TERMINAL_STATUSES = ['under_evaluation', 'discarded'] as const;

/** Post–Start approval poll ends on waiting_for_approval or discarded. */
export const APPROVAL_START_TERMINAL_STATUSES = ['waiting_for_approval', 'discarded'] as const;

export type TerminalStatus = (typeof TERMINAL_STATUSES)[number];
export type ResponseTerminalStatus = (typeof RESPONSE_TERMINAL_STATUSES)[number];
export type ApprovalStartTerminalStatus = (typeof APPROVAL_START_TERMINAL_STATUSES)[number];

/** Derived CEO gate — GET has no top-level ceo_pending. */
export function isCeoPending(ticket: RfpTicket): boolean {
  if (ticket.status !== 'waiting_for_approval') {
    return false;
  }
  const arbitration = ticket.arbitration;
  if (!arbitration || arbitration.ceo_approval_required !== true) {
    return false;
  }
  if (!arbitration.ceo_interrupt_id) {
    return false;
  }
  if (arbitration.ceo_decision === 'approved') {
    return false;
  }
  const sections = ticket.sections ?? [];
  if (sections.some((section) => section.awaiting_decision === true)) {
    return false;
  }
  return true;
}
