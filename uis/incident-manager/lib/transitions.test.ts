import { describe, expect, it } from 'vitest';

import { getAllowedNextStatuses, STATUS_TRANSITIONS } from './incident-types';

describe('status transitions', () => {
  it('maps open to in_progress and discarded', () => {
    expect(STATUS_TRANSITIONS.open).toEqual(['in_progress', 'discarded']);
    expect(getAllowedNextStatuses('open')).toEqual(['in_progress', 'discarded']);
  });

  it('maps in_progress to resolved and discarded', () => {
    expect(STATUS_TRANSITIONS.in_progress).toEqual(['resolved', 'discarded']);
    expect(getAllowedNextStatuses('in_progress')).toEqual(['resolved', 'discarded']);
  });

  it('treats resolved and discarded as terminal', () => {
    expect(STATUS_TRANSITIONS.resolved).toEqual([]);
    expect(STATUS_TRANSITIONS.discarded).toEqual([]);
    expect(getAllowedNextStatuses('resolved')).toEqual([]);
    expect(getAllowedNextStatuses('discarded')).toEqual([]);
  });
});
