/** @vitest-environment jsdom */
import { cleanup, render, screen } from '@testing-library/react';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { SectionCard } from '@/app/rfp/_components/RfpTicketView';
import type { RfpSection } from '@/lib/rfp-types';

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
