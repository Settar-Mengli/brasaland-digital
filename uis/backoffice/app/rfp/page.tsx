'use client';

import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { useEffect, useRef, useState } from 'react';
import InventoryAuthGuard from '@/app/_components/InventoryAuthGuard';
import { RfpTicketView } from '@/app/rfp/_components/RfpTicketView';
import { getRfpTicket, startRfpApproval, triggerRfpResponse, uploadRfp } from '@/lib/rfp';
import {
  APPROVAL_START_TERMINAL_STATUSES,
  RESPONSE_TERMINAL_STATUSES,
  TERMINAL_STATUSES,
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

function RfpPageContent() {
  const router = useRouter();
  const [file, setFile] = useState<File | null>(null);
  const [loadId, setLoadId] = useState('');
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

  function onLoadTicket() {
    const id = loadId.trim();
    if (!id) {
      setView({ status: 'error', message: 'Enter a ticket_id to load.' });
      return;
    }
    router.push(`/rfp/${encodeURIComponent(id)}`);
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

  async function onStartApproval() {
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
      const triggered = await startRfpApproval(current.ticket_id);
      startPolling(triggered.ticket_id, triggered, APPROVAL_START_TERMINAL_STATUSES);
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Failed to start approval.';
      const errorView: ViewState =
        'sections' in current
          ? { status: 'error', message, ticket: current as RfpTicket }
          : { status: 'error', message };
      setView(errorView);
    }
  }

  const fullTicket = liveTicket && 'sections' in liveTicket ? (liveTicket as RfpTicket) : undefined;

  return (
    <>
      <div className="mb-8">
        <h1 className="font-display text-3xl font-bold text-brasaland-charcoal">RFP intake</h1>
        <p className="text-sm text-brasaland-charcoal/60 mt-1">
          Upload a PDF RFP. The worker analyzes it and advances the ticket to intake_complete or
          discarded. After intake, generate department response drafts. After evaluation, run
          approval and CEO sign-off when required. Resume any ticket via its link or Load ticket.
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

      <div className="mt-8 space-y-3 max-w-2xl" aria-labelledby="rfp-load">
        <h2 id="rfp-load" className="font-semibold text-lg text-brasaland-charcoal">
          Load ticket by ID
        </h2>
        <p className="text-sm text-brasaland-charcoal/60">
          Resume an existing ticket (approval, CEO, or final document) without re-uploading.
        </p>
        <label htmlFor="rfp-load-id" className="block text-sm font-medium">
          ticket_id
        </label>
        <div className="flex flex-wrap gap-2">
          <input
            id="rfp-load-id"
            value={loadId}
            onChange={(event) => setLoadId(event.target.value)}
            placeholder="uuid ticket_id"
            className="min-w-[16rem] flex-1 rounded-md border border-brasaland-charcoal/20 bg-white px-3 py-2 text-sm"
          />
          <button
            type="button"
            onClick={onLoadTicket}
            disabled={busy}
            className="rounded-md border border-brasaland-charcoal/30 px-4 py-2 text-sm font-medium text-brasaland-charcoal disabled:opacity-60"
          >
            Load ticket
          </button>
        </div>
      </div>

      {view.status === 'uploading' ? (
        <p role="status" className="text-sm text-brasaland-charcoal/60 mt-6">
          Uploading PDF…
        </p>
      ) : null}

      {view.status === 'polling' ? (
        <p role="status" className="text-sm text-brasaland-charcoal/60 mt-6">
          Processing ticket{' '}
          <Link
            href={`/rfp/${view.ticket.ticket_id}`}
            className="text-brasaland-ember underline underline-offset-2"
          >
            {view.ticket.ticket_id}
          </Link>
          … status: {view.ticket.status}
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

      {fullTicket ? (
        <RfpTicketView
          ticket={fullTicket}
          showResumeLink
          pipelineBusy={busy}
          onTicketChange={(ticket) => setView({ status: 'done', ticket })}
          onError={(message, ticket) => setView({ status: 'error', message, ticket })}
          onGenerateResponse={() => {
            void onGenerateResponse();
          }}
          onStartApproval={() => {
            void onStartApproval();
          }}
        />
      ) : liveTicket ? (
        <section aria-labelledby="rfp-ticket-lite" className="mt-8 max-w-2xl">
          <h2 id="rfp-ticket-lite" className="font-semibold text-xl mb-2">
            Ticket
          </h2>
          <p className="text-sm text-brasaland-charcoal/90">
            <span className="font-medium">ticket_id:</span>{' '}
            <Link
              href={`/rfp/${liveTicket.ticket_id}`}
              className="text-brasaland-ember underline underline-offset-2"
            >
              {liveTicket.ticket_id}
            </Link>
          </p>
          {'rfp_id' in liveTicket && liveTicket.rfp_id ? (
            <p className="text-sm text-brasaland-charcoal/90">
              <span className="font-medium">rfp_id:</span> {liveTicket.rfp_id}
            </p>
          ) : null}
          <p className="text-sm mt-2">
            <span className="font-medium">status:</span> {liveTicket.status}
          </p>
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
