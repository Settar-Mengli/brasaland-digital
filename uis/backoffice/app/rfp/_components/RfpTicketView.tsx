'use client';

import Link from 'next/link';
import { useState } from 'react';
import { decideRfpCeo, decideRfpSection, getRfpTicket } from '@/lib/rfp';
import {
  isCeoPending,
  type RfpFinalDocument,
  type RfpSection,
  type RfpTicket,
} from '@/lib/rfp-types';

export type SectionCardProps = {
  section: RfpSection;
  decisionBusy?: boolean;
  onApprove?: () => void;
  onReject?: (feedback: string) => void;
};

export function SectionCard({ section, decisionBusy, onApprove, onReject }: SectionCardProps) {
  const evaluation = section.evaluation_results ?? null;
  const review = evaluation?.needs_human_review === true;
  const passed = evaluation?.overall_pass === true;
  const pending = evaluation == null;
  const awaiting = section.awaiting_decision === true;
  const [feedback, setFeedback] = useState('');

  return (
    <article className="mt-6 border-t border-brasaland-charcoal/10 pt-4">
      <div className="flex flex-wrap items-baseline gap-2 mb-2">
        <h3 className="font-semibold text-lg text-brasaland-charcoal">{section.department_id}</h3>
        <span className="text-xs text-brasaland-charcoal/60">
          approval: {section.approval_status ?? 'pending'}
        </span>
        {section.approver ? (
          <span className="text-xs text-brasaland-charcoal/60">approver: {section.approver}</span>
        ) : null}
        {section.approved_at ? (
          <span className="text-xs text-brasaland-charcoal/60">at {section.approved_at}</span>
        ) : null}
      </div>

      <div className="flex flex-wrap gap-2 mb-3 text-xs font-medium">
        {pending ? (
          <span className="rounded-md bg-brasaland-charcoal/10 px-2 py-1 text-brasaland-charcoal/80">
            Pending
          </span>
        ) : null}
        {awaiting ? (
          <span
            role="status"
            className="rounded-md bg-brasaland-ember/15 px-2 py-1 text-brasaland-ember"
          >
            Awaiting decision
          </span>
        ) : null}
        {review ? (
          <span
            role="status"
            className="rounded-md bg-brasaland-error/15 px-2 py-1 text-brasaland-error"
          >
            Needs human review
          </span>
        ) : null}
        {!pending && passed ? (
          <span className="rounded-md bg-brasaland-charcoal/10 px-2 py-1 text-brasaland-charcoal">
            Passed evaluation
          </span>
        ) : null}
        {evaluation?.ceo_approval_required === true ? (
          <span className="rounded-md bg-brasaland-ember/15 px-2 py-1 text-brasaland-ember">
            CEO approval required
          </span>
        ) : null}
      </div>

      {section.draft_content ? (
        <div className="mb-3">
          <p className="text-sm font-medium mb-1">Draft</p>
          <pre className="whitespace-pre-wrap text-sm text-brasaland-charcoal/90 font-sans bg-brasaland-cream/40 rounded-md px-3 py-2">
            {section.draft_content}
          </pre>
        </div>
      ) : (
        <p className="text-sm text-brasaland-charcoal/60 mb-3">No draft yet.</p>
      )}

      {evaluation ? (
        <div className="text-sm space-y-2 text-brasaland-charcoal/90">
          <p className="font-medium">Evaluation</p>
          <ul className="list-disc pl-5 space-y-1">
            <li>
              Readability:{' '}
              {evaluation.readability?.pass === true
                ? 'pass'
                : evaluation.readability?.pass === false
                  ? 'fail'
                  : 'n/a'}
              {typeof evaluation.readability?.score === 'number'
                ? ` (score ${evaluation.readability.score.toFixed(1)})`
                : ''}
            </li>
            <li>
              Relevance:{' '}
              {evaluation.relevance?.pass === true
                ? 'pass'
                : evaluation.relevance?.pass === false
                  ? 'fail'
                  : 'n/a'}
              {evaluation.relevance?.missing_aspects &&
              evaluation.relevance.missing_aspects.length > 0
                ? ` — missing: ${evaluation.relevance.missing_aspects.join('; ')}`
                : ''}
            </li>
            <li>
              Compliance:{' '}
              {evaluation.compliance?.pass === true
                ? 'pass'
                : evaluation.compliance?.pass === false
                  ? 'fail'
                  : 'n/a'}
              {evaluation.compliance?.rule_ids && evaluation.compliance.rule_ids.length > 0
                ? ` — rules: ${evaluation.compliance.rule_ids.join(', ')}`
                : ''}
            </li>
          </ul>
          {evaluation.compliance?.violations && evaluation.compliance.violations.length > 0 ? (
            <ul className="list-disc pl-5 text-brasaland-error/90">
              {evaluation.compliance.violations.map((violation) => (
                <li key={violation}>{violation}</li>
              ))}
            </ul>
          ) : null}
          {evaluation.feedback_for_generator ? (
            <p className="text-brasaland-charcoal/70">
              <span className="font-medium">Feedback:</span> {evaluation.feedback_for_generator}
            </p>
          ) : null}
        </div>
      ) : null}

      {awaiting && onApprove && onReject ? (
        <div className="mt-4 space-y-3">
          <label className="block text-sm font-medium" htmlFor={`reject-${section.department_id}`}>
            Reject feedback (optional)
          </label>
          <textarea
            id={`reject-${section.department_id}`}
            value={feedback}
            onChange={(event) => setFeedback(event.target.value)}
            disabled={decisionBusy === true}
            rows={3}
            placeholder="Notes for the regen pass — improves the redraft when provided."
            className="w-full rounded-md border border-brasaland-charcoal/20 bg-white px-3 py-2 text-sm"
          />
          <div className="flex flex-wrap gap-2">
            <button
              type="button"
              onClick={onApprove}
              disabled={decisionBusy === true}
              className="rounded-md bg-brasaland-ember px-4 py-2 text-sm font-medium text-brasaland-ivory disabled:opacity-60"
            >
              {decisionBusy === true ? 'Working…' : 'Approve'}
            </button>
            <button
              type="button"
              onClick={() => onReject(feedback)}
              disabled={decisionBusy === true}
              className="rounded-md border border-brasaland-charcoal/30 px-4 py-2 text-sm font-medium text-brasaland-charcoal disabled:opacity-60"
            >
              Reject
            </button>
          </div>
        </div>
      ) : null}
    </article>
  );
}

function CeoGatePanel({
  busy,
  onApprove,
  onReject,
}: {
  busy: boolean;
  onApprove: () => void;
  onReject: () => void;
}) {
  return (
    <section
      aria-labelledby="rfp-ceo-gate"
      className="mt-8 border border-brasaland-ember/30 rounded-md px-4 py-4 bg-brasaland-ember/5"
    >
      <h2 id="rfp-ceo-gate" className="font-semibold text-xl mb-2 text-brasaland-charcoal">
        CEO approval (Mariana Restrepo)
      </h2>
      <p className="text-sm text-brasaland-charcoal/70 mb-4">
        Contract is above the $50k threshold. Approve to synthesize the final document, or reject to
        leave the ticket waiting.
      </p>
      <div className="flex flex-wrap gap-2">
        <button
          type="button"
          onClick={onApprove}
          disabled={busy}
          className="rounded-md bg-brasaland-ember px-4 py-2 text-sm font-medium text-brasaland-ivory disabled:opacity-60"
        >
          {busy ? 'Working…' : 'Approve as CEO'}
        </button>
        <button
          type="button"
          onClick={onReject}
          disabled={busy}
          className="rounded-md border border-brasaland-charcoal/30 px-4 py-2 text-sm font-medium text-brasaland-charcoal disabled:opacity-60"
        >
          Reject as CEO
        </button>
      </div>
    </section>
  );
}

function FinalDocumentView({ document }: { document: RfpFinalDocument }) {
  const header = document.header;
  const sections = document.sections ?? [];
  const outcomes = document.arbitration_outcomes;
  const triggers = outcomes?.triggers_fired ?? [];
  const resolutions = outcomes?.resolutions ?? [];
  const openQuestions = document.open_questions ?? [];

  return (
    <section aria-labelledby="rfp-final-doc" className="mt-8 max-w-2xl">
      <h2 id="rfp-final-doc" className="font-semibold text-xl mb-3">
        Final document
      </h2>
      {header ? (
        <div className="text-sm space-y-1 mb-4 text-brasaland-charcoal/90">
          {header.client_name ? (
            <p>
              <span className="font-medium">Client:</span> {header.client_name}
            </p>
          ) : null}
          {header.location ? (
            <p>
              <span className="font-medium">Location:</span> {header.location}
            </p>
          ) : null}
          {header.service_type ? (
            <p>
              <span className="font-medium">Service:</span> {header.service_type}
            </p>
          ) : null}
          {header.generated_at ? (
            <p>
              <span className="font-medium">Generated:</span> {header.generated_at}
            </p>
          ) : null}
          {header.ticket_id ? (
            <p>
              <span className="font-medium">Ticket:</span> {header.ticket_id}
            </p>
          ) : null}
        </div>
      ) : null}

      {sections.length > 0 ? (
        <div className="space-y-4 mb-4">
          {sections.map((section) => (
            <article
              key={section.department_id}
              className="border-t border-brasaland-charcoal/10 pt-3"
            >
              <h3 className="font-semibold text-brasaland-charcoal">
                {section.department_id}
                {section.owner ? (
                  <span className="text-sm font-normal text-brasaland-charcoal/60">
                    {' '}
                    — {section.owner}
                  </span>
                ) : null}
              </h3>
              {section.approval_stamp ? (
                <p className="text-xs text-brasaland-charcoal/60 mt-1">{section.approval_stamp}</p>
              ) : null}
              {section.draft_content ? (
                <pre className="mt-2 whitespace-pre-wrap text-sm font-sans bg-brasaland-cream/40 rounded-md px-3 py-2">
                  {section.draft_content}
                </pre>
              ) : null}
            </article>
          ))}
        </div>
      ) : null}

      {triggers.length > 0 || resolutions.length > 0 ? (
        <div className="text-sm mb-4">
          <p className="font-medium mb-1">Arbitration outcomes</p>
          {triggers.length > 0 ? (
            <pre className="whitespace-pre-wrap text-xs font-sans bg-brasaland-cream/40 rounded-md px-3 py-2 mb-2">
              {JSON.stringify(triggers, null, 2)}
            </pre>
          ) : null}
          {resolutions.length > 0 ? (
            <ul className="list-disc pl-5 space-y-1">
              {resolutions.map((resolution, index) => (
                <li key={index}>{String(resolution)}</li>
              ))}
            </ul>
          ) : null}
        </div>
      ) : null}

      {document.ceo_line ? (
        <p className="text-sm font-medium text-brasaland-charcoal mb-3">{document.ceo_line}</p>
      ) : null}

      {document.total_estimated_value ? (
        <p className="text-sm mb-3">
          <span className="font-medium">Total estimated value:</span>{' '}
          {document.total_estimated_value}
        </p>
      ) : null}

      {openQuestions.length > 0 ? (
        <div className="text-sm">
          <p className="font-medium mb-1">Open questions</p>
          <ul className="list-disc pl-5 space-y-1">
            {openQuestions.map((question) => (
              <li key={question}>{question}</li>
            ))}
          </ul>
        </div>
      ) : null}
    </section>
  );
}

export type RfpTicketViewProps = {
  ticket: RfpTicket;
  onTicketChange: (ticket: RfpTicket) => void;
  onError?: (message: string, ticket: RfpTicket) => void;
  pipelineBusy?: boolean;
  onGenerateResponse?: () => void;
  onStartApproval?: () => void;
  showResumeLink?: boolean;
};

/**
 * Shared ticket view: metadata, pipeline actions, sections, CEO gate, final document.
 * Decision handlers live here and act-and-refresh via getRfpTicket + onTicketChange.
 */
export function RfpTicketView({
  ticket,
  onTicketChange,
  onError,
  pipelineBusy,
  onGenerateResponse,
  onStartApproval,
  showResumeLink,
}: RfpTicketViewProps) {
  const [busyDept, setBusyDept] = useState<string | null>(null);
  const sections = Array.isArray(ticket.sections) ? ticket.sections : [];
  const showCeoGate = isCeoPending(ticket);
  const finalDocument =
    ticket.status === 'done' && ticket.final_document ? ticket.final_document : null;
  const decisionBusy = busyDept !== null;
  const controlsBusy = pipelineBusy === true || decisionBusy;

  async function refreshTicket() {
    const next = await getRfpTicket(ticket.ticket_id);
    onTicketChange(next);
  }

  async function onSectionApprove(departmentId: string) {
    setBusyDept(departmentId);
    try {
      await decideRfpSection(ticket.ticket_id, departmentId, 'approve');
      await refreshTicket();
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Failed to submit section decision.';
      if (onError) {
        onError(message, ticket);
      }
    } finally {
      setBusyDept(null);
    }
  }

  async function onSectionReject(departmentId: string, feedback: string) {
    setBusyDept(departmentId);
    try {
      const trimmed = feedback.trim();
      if (trimmed.length > 0) {
        await decideRfpSection(ticket.ticket_id, departmentId, 'reject', trimmed);
      } else {
        await decideRfpSection(ticket.ticket_id, departmentId, 'reject');
      }
      await refreshTicket();
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Failed to submit section decision.';
      if (onError) {
        onError(message, ticket);
      }
    } finally {
      setBusyDept(null);
    }
  }

  async function onCeoDecide(action: 'approve' | 'reject') {
    setBusyDept('ceo');
    try {
      await decideRfpCeo(ticket.ticket_id, action);
      await refreshTicket();
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Failed to submit CEO decision.';
      if (onError) {
        onError(message, ticket);
      }
    } finally {
      setBusyDept(null);
    }
  }

  return (
    <section aria-labelledby="rfp-ticket" className="mt-8 max-w-2xl">
      <h2 id="rfp-ticket" className="font-semibold text-xl mb-2">
        Ticket
      </h2>
      <p className="text-sm text-brasaland-charcoal/90">
        <span className="font-medium">ticket_id:</span>{' '}
        {showResumeLink === true ? (
          <Link
            href={`/rfp/${ticket.ticket_id}`}
            className="text-brasaland-ember underline underline-offset-2"
          >
            {ticket.ticket_id}
          </Link>
        ) : (
          ticket.ticket_id
        )}
      </p>
      {ticket.rfp_id ? (
        <p className="text-sm text-brasaland-charcoal/90">
          <span className="font-medium">rfp_id:</span> {ticket.rfp_id}
        </p>
      ) : null}
      <p className="text-sm mt-2">
        <span className="font-medium">status:</span>{' '}
        <span
          className={
            ticket.status === 'intake_complete'
              ? 'text-brasaland-charcoal font-semibold'
              : ticket.status === 'discarded'
                ? 'text-brasaland-error font-semibold'
                : ticket.status === 'under_evaluation' ||
                    ticket.status === 'waiting_for_approval' ||
                    ticket.status === 'done'
                  ? 'text-brasaland-charcoal font-semibold'
                  : 'text-brasaland-charcoal/90'
          }
        >
          {ticket.status}
        </span>
      </p>
      {ticket.status === 'discarded' ? (
        <p className="text-sm text-brasaland-error mt-2">This RFP was discarded.</p>
      ) : null}
      {ticket.status === 'intake_complete' && onGenerateResponse ? (
        <button
          type="button"
          onClick={onGenerateResponse}
          disabled={controlsBusy}
          className="mt-4 rounded-md bg-brasaland-ember px-4 py-2 text-sm font-medium text-brasaland-ivory disabled:opacity-60"
        >
          {pipelineBusy === true ? 'Generating…' : 'Generate response'}
        </button>
      ) : null}
      {ticket.status === 'under_evaluation' && onStartApproval ? (
        <button
          type="button"
          onClick={onStartApproval}
          disabled={controlsBusy}
          className="mt-4 rounded-md bg-brasaland-ember px-4 py-2 text-sm font-medium text-brasaland-ivory disabled:opacity-60"
        >
          {pipelineBusy === true ? 'Starting…' : 'Start approval'}
        </button>
      ) : null}

      {sections.length > 0 ? (
        <div className="mt-6" aria-labelledby="rfp-sections">
          <h2 id="rfp-sections" className="font-semibold text-xl mb-2">
            Department sections
          </h2>
          {sections.map((section) => {
            const cardProps: SectionCardProps = {
              section,
              decisionBusy: busyDept === section.department_id,
            };
            if (section.awaiting_decision === true) {
              cardProps.onApprove = () => {
                void onSectionApprove(section.department_id);
              };
              cardProps.onReject = (feedback) => {
                void onSectionReject(section.department_id, feedback);
              };
            }
            return <SectionCard key={section.department_id} {...cardProps} />;
          })}
        </div>
      ) : null}

      {showCeoGate ? (
        <CeoGatePanel
          busy={busyDept === 'ceo'}
          onApprove={() => {
            void onCeoDecide('approve');
          }}
          onReject={() => {
            void onCeoDecide('reject');
          }}
        />
      ) : null}

      {finalDocument ? <FinalDocumentView document={finalDocument} /> : null}
    </section>
  );
}
