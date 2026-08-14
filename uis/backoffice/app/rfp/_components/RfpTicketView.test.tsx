/** @vitest-environment jsdom */
import { cleanup, fireEvent, render, screen } from '@testing-library/react';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { RfpTicketView, SectionCard } from '@/app/rfp/_components/RfpTicketView';
import type { RfpSection, RfpTicket } from '@/lib/rfp-types';

afterEach(() => {
  cleanup();
});

function baseSection(overrides: Partial<RfpSection> = {}): RfpSection {
  return {
    department_id: 'marketing',
    draft_content: 'Draft body',
    approval_status: 'pending',
    evaluation_results: { overall_pass: true },
    ...overrides,
  };
}

function underEvaluationTicket(overrides: Partial<RfpTicket> = {}): RfpTicket {
  return {
    ticket_id: 't-1',
    rfp_id: 'r-1',
    status: 'under_evaluation',
    sections: [baseSection()],
    ...overrides,
  };
}

describe('SectionCard approval controls', () => {
  it('renders Approve and Reject when awaiting_decision and handlers are provided', () => {
    const onApprove = vi.fn();
    const onReject = vi.fn();
    render(
      <SectionCard
        section={baseSection({ awaiting_decision: true })}
        onApprove={onApprove}
        onReject={onReject}
      />,
    );

    expect(screen.getByRole('button', { name: 'Approve' })).toBeTruthy();
    expect(screen.getByRole('button', { name: 'Reject' })).toBeTruthy();
    expect(screen.getByLabelText(/Reject feedback/i)).toBeTruthy();
  });

  it('does not render Approve/Reject when awaiting_decision is false', () => {
    render(
      <SectionCard
        section={baseSection({ awaiting_decision: false })}
        onApprove={vi.fn()}
        onReject={vi.fn()}
      />,
    );

    expect(screen.queryByRole('button', { name: 'Approve' })).toBeNull();
    expect(screen.queryByRole('button', { name: 'Reject' })).toBeNull();
  });

  it('does not render Approve/Reject when handlers are omitted', () => {
    render(<SectionCard section={baseSection({ awaiting_decision: true })} />);

    expect(screen.queryByRole('button', { name: 'Approve' })).toBeNull();
    expect(screen.queryByRole('button', { name: 'Reject' })).toBeNull();
  });
});

describe('RfpTicketView actionsDisabled', () => {
  it('disables Start approval when actionsDisabled is true', () => {
    render(
      <RfpTicketView
        ticket={underEvaluationTicket()}
        onTicketChange={vi.fn()}
        onStartApproval={vi.fn()}
        actionsDisabled
      />,
    );

    const button = screen.getByRole('button', { name: /Start approval/i });
    expect(button).toHaveProperty('disabled', true);
    expect(button.getAttribute('title')).toBe('Reload the ticket to continue');
  });

  it('keeps Start approval enabled by default and fires onClick', () => {
    const onStartApproval = vi.fn();
    render(
      <RfpTicketView
        ticket={underEvaluationTicket()}
        onTicketChange={vi.fn()}
        onStartApproval={onStartApproval}
      />,
    );

    const button = screen.getByRole('button', { name: 'Start approval' });
    expect(button).toHaveProperty('disabled', false);
    fireEvent.click(button);
    expect(onStartApproval).toHaveBeenCalledTimes(1);
  });
});
