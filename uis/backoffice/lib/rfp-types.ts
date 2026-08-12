/**
 * Wire types for the RFP ticket API (`POST/GET /rfp/tickets`).
 */
export interface RfpTicket {
  ticket_id: string;
  rfp_id: string;
  status: string;
  created_at?: string;
  updated_at?: string;
}

export type RfpUploadResponse = Pick<RfpTicket, 'ticket_id' | 'rfp_id' | 'status'>;

export const TERMINAL_STATUSES = ['intake_complete', 'discarded'] as const;

export type TerminalStatus = (typeof TERMINAL_STATUSES)[number];
