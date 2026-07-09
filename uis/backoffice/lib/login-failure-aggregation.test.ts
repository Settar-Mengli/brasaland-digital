import { describe, expect, it } from 'vitest';

import {
  mapLoginFailureReason,
  recordLoginFailure,
  resetLoginFailureState,
} from './login-failure-aggregation';

describe('login failure aggregation', () => {
  it('starts a new window with attempt_count 1', () => {
    const result = recordLoginFailure(resetLoginFailureState(), 1_000, {
      failure_reason: 'wrong_credentials',
      source: 'backoffice',
    });
    expect(result.event.attempt_count).toBe(1);
  });

  it('increments attempt_count within the 60s window', () => {
    const first = recordLoginFailure(resetLoginFailureState(), 1_000, {
      failure_reason: 'wrong_credentials',
      source: 'backoffice',
    });
    const second = recordLoginFailure(first.nextState, 5_000, {
      failure_reason: 'wrong_credentials',
      source: 'backoffice',
    });
    expect(second.event.attempt_count).toBe(2);
  });

  it('resets the window after 60 seconds', () => {
    const first = recordLoginFailure(resetLoginFailureState(), 1_000, {
      failure_reason: 'wrong_credentials',
      source: 'backoffice',
    });
    const afterWindow = recordLoginFailure(first.nextState, 62_500, {
      failure_reason: 'wrong_credentials',
      source: 'backoffice',
    });
    expect(afterWindow.event.attempt_count).toBe(1);
  });

  it('maps locked messages to account_locked', () => {
    expect(mapLoginFailureReason('Account locked')).toBe('account_locked');
    expect(mapLoginFailureReason('Invalid credentials')).toBe('wrong_credentials');
  });
});
