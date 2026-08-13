'use client';

import Link from 'next/link';
import { useParams } from 'next/navigation';
import { useCallback, useEffect, useState } from 'react';
import InventoryAuthGuard from '@/app/_components/InventoryAuthGuard';
import { RfpTicketView } from '@/app/rfp/_components/RfpTicketView';
import { getRfpTicket, startRfpApproval, triggerRfpResponse } from '@/lib/rfp';
import type { RfpTicket } from '@/lib/rfp-types';

type LoadState =
  | { status: 'loading' }
  | { status: 'ready'; ticket: RfpTicket }
  | { status: 'error'; message: string; ticket?: RfpTicket };

function RfpTicketResumeContent() {
  const params = useParams<{ ticketId: string }>();
  const ticketId = typeof params.ticketId === 'string' ? params.ticketId : '';
  const [state, setState] = useState<LoadState>({ status: 'loading' });
  const [pipelineBusy, setPipelineBusy] = useState(false);

  const loadTicket = useCallback(async (id: string) => {
    setState({ status: 'loading' });
    try {
      const ticket = await getRfpTicket(id);
      setState({ status: 'ready', ticket });
    } catch (error) {
      setState({
        status: 'error',
        message: error instanceof Error ? error.message : 'Failed to load ticket.',
      });
    }
  }, []);

  useEffect(() => {
    if (!ticketId) {
      setState({ status: 'error', message: 'Missing ticket_id in URL.' });
      return;
    }
    void loadTicket(ticketId);
  }, [ticketId, loadTicket]);

  async function onGenerateResponse() {
    if (state.status !== 'ready') {
      return;
    }
    const current = state.ticket;
    setPipelineBusy(true);
    try {
      await triggerRfpResponse(current.ticket_id);
      const ticket = await getRfpTicket(current.ticket_id);
      setState({ status: 'ready', ticket });
      // Poll lightly until under_evaluation / discarded
      for (let i = 0; i < 40; i += 1) {
        await new Promise((resolve) => setTimeout(resolve, 2500));
        const next = await getRfpTicket(current.ticket_id);
        setState({ status: 'ready', ticket: next });
        if (next.status === 'under_evaluation' || next.status === 'discarded') {
          break;
        }
      }
    } catch (error) {
      setState({
        status: 'error',
        message: error instanceof Error ? error.message : 'Failed to start response generation.',
        ticket: current,
      });
    } finally {
      setPipelineBusy(false);
    }
  }

  async function onStartApproval() {
    if (state.status !== 'ready') {
      return;
    }
    const current = state.ticket;
    setPipelineBusy(true);
    try {
      await startRfpApproval(current.ticket_id);
      for (let i = 0; i < 40; i += 1) {
        await new Promise((resolve) => setTimeout(resolve, 2500));
        const next = await getRfpTicket(current.ticket_id);
        setState({ status: 'ready', ticket: next });
        if (next.status === 'waiting_for_approval' || next.status === 'discarded') {
          // Prefer a snapshot that already has interrupt-driven awaiting_decision
          const awaiting = (next.sections ?? []).some((s) => s.awaiting_decision === true);
          if (next.status === 'discarded' || awaiting || i >= 2) {
            break;
          }
        }
      }
    } catch (error) {
      setState({
        status: 'error',
        message: error instanceof Error ? error.message : 'Failed to start approval.',
        ticket: current,
      });
    } finally {
      setPipelineBusy(false);
    }
  }

  return (
    <>
      <div className="mb-6 max-w-2xl">
        <p className="text-sm">
          <Link href="/rfp" className="text-brasaland-ember underline underline-offset-2">
            ← Back to RFP intake
          </Link>
        </p>
        <h1 className="font-display text-3xl font-bold text-brasaland-charcoal mt-4">RFP ticket</h1>
        <p className="text-sm text-brasaland-charcoal/60 mt-1">
          Resume approval, CEO decision, or final document for this ticket.
        </p>
      </div>

      {state.status === 'loading' ? (
        <p role="status" className="text-sm text-brasaland-charcoal/60">
          Loading ticket {ticketId}…
        </p>
      ) : null}

      {state.status === 'error' ? (
        <p
          role="alert"
          className="text-sm text-brasaland-error bg-brasaland-error/10 rounded-md px-3 py-2"
        >
          {state.message}
        </p>
      ) : null}

      {(() => {
        const ticketForView =
          state.status === 'ready'
            ? state.ticket
            : state.status === 'error'
              ? state.ticket
              : undefined;
        if (!ticketForView) {
          return null;
        }
        return (
          <RfpTicketView
            ticket={ticketForView}
            pipelineBusy={pipelineBusy}
            onTicketChange={(ticket) => setState({ status: 'ready', ticket })}
            onError={(message, ticket) => setState({ status: 'error', message, ticket })}
            onGenerateResponse={() => {
              void onGenerateResponse();
            }}
            onStartApproval={() => {
              void onStartApproval();
            }}
          />
        );
      })()}
    </>
  );
}

export default function RfpTicketResumePage() {
  return (
    <InventoryAuthGuard>
      <RfpTicketResumeContent />
    </InventoryAuthGuard>
  );
}
