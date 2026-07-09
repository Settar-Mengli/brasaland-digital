export type LoginFailureReason = 'wrong_credentials' | 'account_locked';

export type LoginFailureInput = {
  failure_reason: LoginFailureReason;
  source: 'backoffice';
};

export type LoginFailureEvent = LoginFailureInput & {
  attempt_count: number;
};

export type LoginFailureState = {
  windowStartMs: number;
  attemptCount: number;
} | null;

const BURST_WINDOW_MS = 60_000;

export function mapLoginFailureReason(message: string): LoginFailureReason {
  if (message.toLowerCase().includes('locked')) {
    return 'account_locked';
  }
  return 'wrong_credentials';
}

export function recordLoginFailure(
  state: LoginFailureState,
  nowMs: number,
  input: LoginFailureInput,
): { nextState: LoginFailureState; event: LoginFailureEvent } {
  const withinWindow = state !== null && nowMs - state.windowStartMs <= BURST_WINDOW_MS;

  if (!withinWindow) {
    const nextState: LoginFailureState = { windowStartMs: nowMs, attemptCount: 1 };
    return {
      nextState,
      event: { ...input, attempt_count: 1 },
    };
  }

  const attemptCount = state.attemptCount + 1;
  const nextState: LoginFailureState = {
    windowStartMs: state.windowStartMs,
    attemptCount,
  };
  return {
    nextState,
    event: { ...input, attempt_count: attemptCount },
  };
}

export function resetLoginFailureState(): LoginFailureState {
  return null;
}
