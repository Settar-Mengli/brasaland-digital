import { describe, expect, it } from 'vitest';

import {
  canUpdateIncidentStatus,
  getStatusSelectOptions,
  resolveStatusAfterUpdate,
} from './incident-status-control';

describe('getStatusSelectOptions', () => {
  it('returns only valid next statuses plus current for open', () => {
    expect(getStatusSelectOptions('open')).toEqual(['open', 'in_progress', 'discarded']);
  });

  it('returns only valid next statuses plus current for in_progress', () => {
    expect(getStatusSelectOptions('in_progress')).toEqual(['in_progress', 'resolved', 'discarded']);
  });

  it('returns only the current status when terminal', () => {
    expect(getStatusSelectOptions('resolved')).toEqual(['resolved']);
    expect(getStatusSelectOptions('discarded')).toEqual(['discarded']);
    expect(canUpdateIncidentStatus('resolved')).toBe(false);
    expect(canUpdateIncidentStatus('discarded')).toBe(false);
  });
});

describe('resolveStatusAfterUpdate', () => {
  it('reverts to the previous status when the update fails', () => {
    expect(resolveStatusAfterUpdate('open', 'resolved', false)).toBe('open');
  });

  it('keeps the confirmed status when the update succeeds', () => {
    expect(resolveStatusAfterUpdate('open', 'in_progress', true, 'in_progress')).toBe(
      'in_progress',
    );
  });

  it('falls back to the attempted status when success has no confirmed value', () => {
    expect(resolveStatusAfterUpdate('open', 'in_progress', true)).toBe('in_progress');
  });
});
