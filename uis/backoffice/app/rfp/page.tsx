'use client';

import { useEffect, useRef, useState } from 'react';
import InventoryAuthGuard from '@/app/_components/InventoryAuthGuard';
import { getRfpTicket, uploadRfp } from '@/lib/rfp';
import { TERMINAL_STATUSES, type RfpTicket } from '@/lib/rfp-types';

const POLL_INTERVAL_MS = 2500;
const MAX_POLL_ATTEMPTS = 40;

type ViewState =
  | { status: 'idle' }
  | { status: 'uploading' }
  | { status: 'polling'; ticket: Pick<RfpTicket, 'ticket_id' | 'rfp_id' | 'status'> }
  | { status: 'done'; ticket: RfpTicket }
  | { status: 'error'; message: string; ticket?: RfpTicket };

function isTerminal(status: string): boolean {
  return (TERMINAL_STATUSES as readonly string[]).includes(status);
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

  function startPolling(ticketId: string, initial: Pick<RfpTicket, 'ticket_id' | 'rfp_id' | 'status'>) {
    clearPoll();
    attemptsRef.current = 0;
    setView({ status: 'polling', ticket: initial });

    pollRef.current = setInterval(async () => {
      attemptsRef.current += 1;
      try {
        const ticket = await getRfpTicket(ticketId);
        if (isTerminal(ticket.status)) {
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
      startPolling(uploaded.ticket_id, uploaded);
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

  return (
    <>
      <div className="mb-8">
        <h1 className="font-display text-3xl font-bold text-brasaland-charcoal">RFP intake</h1>
        <p className="text-sm text-brasaland-charcoal/60 mt-1">
          Upload a PDF RFP. The worker analyzes it and advances the ticket to intake_complete or
          discarded.
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
          Analyzing ticket {view.ticket.ticket_id}… status: {view.ticket.status}
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
                    : 'text-brasaland-charcoal/90'
              }
            >
              {liveTicket.status}
            </span>
          </p>
          {liveTicket.status === 'discarded' ? (
            <p className="text-sm text-brasaland-error mt-2">This RFP was discarded.</p>
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
