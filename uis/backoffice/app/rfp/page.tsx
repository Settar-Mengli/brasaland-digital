'use client';

import { useEffect, useRef, useState } from 'react';
import InventoryAuthGuard from '@/app/_components/InventoryAuthGuard';
import { getRfpTicket, triggerRfpResponse, uploadRfp } from '@/lib/rfp';
import {
  RESPONSE_TERMINAL_STATUSES,
  TERMINAL_STATUSES,
  type RfpSection,
  type RfpTicket,
} from '@/lib/rfp-types';

const POLL_INTERVAL_MS = 2500;
const MAX_POLL_ATTEMPTS = 40;

type ViewState =
  | { status: 'idle' }
  | { status: 'uploading' }
  | { status: 'polling'; ticket: Pick<RfpTicket, 'ticket_id' | 'rfp_id' | 'status'> }
  | { status: 'done'; ticket: RfpTicket }
  | { status: 'error'; message: string; ticket?: RfpTicket };

function isTerminalStatus(status: string, terminals: readonly string[]): boolean {
  return terminals.includes(status);
}

function SectionCard({ section }: { section: RfpSection }) {
  const evaluation = section.evaluation_results ?? null;
  const review = evaluation?.needs_human_review === true;
  const passed = evaluation?.overall_pass === true;
  const pending = evaluation == null;

  return (
    <article className="mt-6 border-t border-brasaland-charcoal/10 pt-4">
      <div className="flex flex-wrap items-baseline gap-2 mb-2">
        <h3 className="font-semibold text-lg text-brasaland-charcoal">{section.department_id}</h3>
        <span className="text-xs text-brasaland-charcoal/60">
          approval: {section.approval_status ?? 'pending'}
        </span>
      </div>

      <div className="flex flex-wrap gap-2 mb-3 text-xs font-medium">
        {pending ? (
          <span className="rounded-md bg-brasaland-charcoal/10 px-2 py-1 text-brasaland-charcoal/80">
            Pending
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
    </article>
  );
}

function RfpPageContent() {
  const [file, setFile] = useState<File | null>(null);
  const [view, setView] = useState<ViewState>({ status: 'idle' });
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const attemptsRef = useRef(0);

  function clearPoll() {
    if (pollRef.current !== null) {
      clearInterval(pollRef.current);
      pollRef.current = null;
    }
  }

  useEffect(() => {
    return () => {
      clearPoll();
    };
  }, []);

  function startPolling(
    ticketId: string,
    initial: Pick<RfpTicket, 'ticket_id' | 'rfp_id' | 'status'>,
    terminals: readonly string[] = TERMINAL_STATUSES,
  ) {
    clearPoll();
    attemptsRef.current = 0;
    setView({ status: 'polling', ticket: initial });

    pollRef.current = setInterval(async () => {
      attemptsRef.current += 1;
      try {
        const ticket = await getRfpTicket(ticketId);
        if (isTerminalStatus(ticket.status, terminals)) {
          clearPoll();
          setView({ status: 'done', ticket });
          return;
        }
        setView({
          status: 'polling',
          ticket: {
            ticket_id: ticket.ticket_id,
            rfp_id: ticket.rfp_id,
            status: ticket.status,
          },
        });
        if (attemptsRef.current >= MAX_POLL_ATTEMPTS) {
          clearPoll();
          setView({
            status: 'error',
            message: 'still processing — check back later',
            ticket,
          });
        }
      } catch (error) {
        clearPoll();
        setView({
          status: 'error',
          message: error instanceof Error ? error.message : 'Failed to poll ticket status.',
        });
      }
    }, POLL_INTERVAL_MS);
  }

  async function onUpload() {
    if (!file) {
      setView({ status: 'error', message: 'Choose a PDF before uploading.' });
      return;
    }
    clearPoll();
    setView({ status: 'uploading' });
    try {
      const uploaded = await uploadRfp(file);
      startPolling(uploaded.ticket_id, uploaded, TERMINAL_STATUSES);
    } catch (error) {
      setView({
        status: 'error',
        message: error instanceof Error ? error.message : 'Failed to upload RFP.',
      });
    }
  }

  const busy = view.status === 'uploading' || view.status === 'polling';
  const liveTicket =
    view.status === 'polling'
      ? view.ticket
      : view.status === 'done'
        ? view.ticket
        : view.status === 'error'
          ? view.ticket
          : undefined;

  async function onGenerateResponse() {
    if (!liveTicket) {
      return;
    }
    const current = liveTicket;
    clearPoll();
    setView({
      status: 'polling',
      ticket: {
        ticket_id: current.ticket_id,
        rfp_id: current.rfp_id,
        status: current.status,
      },
    });
    try {
      const triggered = await triggerRfpResponse(current.ticket_id);
      startPolling(triggered.ticket_id, triggered, RESPONSE_TERMINAL_STATUSES);
    } catch (error) {
      const message =
        error instanceof Error ? error.message : 'Failed to start response generation.';
      const errorView: ViewState =
        'sections' in current
          ? { status: 'error', message, ticket: current as RfpTicket }
          : { status: 'error', message };
      setView(errorView);
    }
  }

  const sections =
    liveTicket && 'sections' in liveTicket && Array.isArray(liveTicket.sections)
      ? liveTicket.sections
      : undefined;

  return (
    <>
      <div className="mb-8">
        <h1 className="font-display text-3xl font-bold text-brasaland-charcoal">RFP intake</h1>
        <p className="text-sm text-brasaland-charcoal/60 mt-1">
          Upload a PDF RFP. The worker analyzes it and advances the ticket to intake_complete or
          discarded. After intake, generate department response drafts.
        </p>
      </div>

      <div className="space-y-4 max-w-2xl" aria-labelledby="rfp-upload">
        <h2 id="rfp-upload" className="sr-only">
          Upload an RFP PDF
        </h2>
        <label htmlFor="rfp-file" className="block text-sm font-medium">
          PDF file
        </label>
        <input
          id="rfp-file"
          type="file"
          accept="application/pdf"
          onChange={(event) => {
            const next = event.target.files?.[0] ?? null;
            setFile(next);
          }}
          className="w-full rounded-md border border-brasaland-charcoal/20 bg-white px-3 py-2 text-sm"
        />
        <button
          type="button"
          onClick={onUpload}
          disabled={!file || busy}
          className="rounded-md bg-brasaland-ember px-4 py-2 text-sm font-medium text-brasaland-ivory disabled:opacity-60"
        >
          {view.status === 'uploading' ? 'Uploading…' : 'Upload'}
        </button>
      </div>

      {view.status === 'uploading' ? (
        <p role="status" className="text-sm text-brasaland-charcoal/60 mt-6">
          Uploading PDF…
        </p>
      ) : null}

      {view.status === 'polling' ? (
        <p role="status" className="text-sm text-brasaland-charcoal/60 mt-6">
          Processing ticket {view.ticket.ticket_id}… status: {view.ticket.status}
        </p>
      ) : null}

      {view.status === 'error' ? (
        <p
          role="alert"
          className="text-sm text-brasaland-error bg-brasaland-error/10 rounded-md px-3 py-2 mt-6"
        >
          {view.message}
        </p>
      ) : null}

      {liveTicket ? (
        <section aria-labelledby="rfp-ticket" className="mt-8 max-w-2xl">
          <h2 id="rfp-ticket" className="font-semibold text-xl mb-2">
            Ticket
          </h2>
          <p className="text-sm text-brasaland-charcoal/90">
            <span className="font-medium">ticket_id:</span> {liveTicket.ticket_id}
          </p>
          {'rfp_id' in liveTicket && liveTicket.rfp_id ? (
            <p className="text-sm text-brasaland-charcoal/90">
              <span className="font-medium">rfp_id:</span> {liveTicket.rfp_id}
            </p>
          ) : null}
          <p className="text-sm mt-2">
            <span className="font-medium">status:</span>{' '}
            <span
              className={
                liveTicket.status === 'intake_complete'
                  ? 'text-brasaland-charcoal font-semibold'
                  : liveTicket.status === 'discarded'
                    ? 'text-brasaland-error font-semibold'
                    : liveTicket.status === 'under_evaluation'
                      ? 'text-brasaland-charcoal font-semibold'
                      : 'text-brasaland-charcoal/90'
              }
            >
              {liveTicket.status}
            </span>
          </p>
          {liveTicket.status === 'discarded' ? (
            <p className="text-sm text-brasaland-error mt-2">This RFP was discarded.</p>
          ) : null}
          {liveTicket.status === 'intake_complete' ? (
            <button
              type="button"
              onClick={onGenerateResponse}
              disabled={busy}
              className="mt-4 rounded-md bg-brasaland-ember px-4 py-2 text-sm font-medium text-brasaland-ivory disabled:opacity-60"
            >
              {busy ? 'Generating…' : 'Generate response'}
            </button>
          ) : null}

          {sections && sections.length > 0 ? (
            <div className="mt-6" aria-labelledby="rfp-sections">
              <h2 id="rfp-sections" className="font-semibold text-xl mb-2">
                Department sections
              </h2>
              {sections.map((section) => (
                <SectionCard key={section.department_id} section={section} />
              ))}
            </div>
          ) : null}
        </section>
      ) : null}
    </>
  );
}

export default function RfpPage() {
  return (
    <InventoryAuthGuard>
      <RfpPageContent />
    </InventoryAuthGuard>
  );
}
