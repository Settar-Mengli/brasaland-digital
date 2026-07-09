import {
  type LoginFailureState,
  recordLoginFailure,
  resetLoginFailureState,
} from './login-failure-aggregation';

export const TELEMETRY_SCHEMA_VERSION = '2.0.0';
export const TELEMETRY_SERVICE = 'backoffice';

export const SESSION_ID_KEY = 'brasaland_telemetry_session_id';
export const LAST_ACTIVITY_KEY = 'brasaland_last_activity_at';

const TOKEN_KEY = 'brasaland_access_token';
const QUEUE_FLUSH_SIZE = 20;
const QUEUE_FLUSH_INTERVAL_MS = 10_000;
const MAX_FLUSH_RETRIES = 3;
const INITIAL_BACKOFF_MS = 1_000;

export type TelemetryEnvelope = {
  eventId: string;
  timestamp: string;
  sessionId: string;
  userId: string;
  event_type: string;
  schemaVersion: string;
  requestId: string;
  service: string;
  properties: Record<string, unknown>;
};

let eventQueue: TelemetryEnvelope[] = [];
let flushTimer: ReturnType<typeof setInterval> | null = null;
let visibilityListenerAttached = false;
let loginFailureState: LoginFailureState = null;
let pendingLoginFailureIndex: number | null = null;

function isBrowser(): boolean {
  return typeof window !== 'undefined';
}

function getTelemetryEndpoint(): string | null {
  const endpoint = process.env.NEXT_PUBLIC_TELEMETRY_ENDPOINT;
  if (!endpoint) {
    return null;
  }
  return endpoint.replace(/\/$/, '');
}

function decodeJwtPayload(token: string): Record<string, unknown> | null {
  const parts = token.split('.');
  if (parts.length !== 3) {
    return null;
  }
  const payloadSegment = parts[1];
  if (!payloadSegment) {
    return null;
  }
  try {
    const normalized = payloadSegment.replace(/-/g, '+').replace(/_/g, '/');
    const padded = normalized.padEnd(normalized.length + ((4 - (normalized.length % 4)) % 4), '=');
    return JSON.parse(atob(padded)) as Record<string, unknown>;
  } catch {
    return null;
  }
}

function decodeJwtSub(token: string): string {
  const payload = decodeJwtPayload(token);
  if (!payload) {
    return '';
  }
  if (typeof payload.sub === 'string' && payload.sub.length > 0) {
    return payload.sub;
  }
  if (typeof payload.sub === 'number') {
    return String(payload.sub);
  }
  return '';
}

export function isAccessTokenExpired(token: string): boolean {
  const payload = decodeJwtPayload(token);
  if (!payload || typeof payload.exp !== 'number') {
    return false;
  }
  return payload.exp * 1000 < Date.now();
}

export function computeIdleDurationMs(): number {
  const lastActivity = readLastActivityMs();
  if (lastActivity === 0) {
    return 0;
  }
  return Math.max(0, Date.now() - lastActivity);
}

function readUserId(): string {
  if (!isBrowser()) {
    return '';
  }
  const token = localStorage.getItem(TOKEN_KEY);
  if (!token) {
    return '';
  }
  return decodeJwtSub(token);
}

function readSessionId(): string {
  if (!isBrowser()) {
    return '';
  }
  const existing = sessionStorage.getItem(SESSION_ID_KEY);
  if (existing) {
    return existing;
  }
  const sessionId = crypto.randomUUID();
  sessionStorage.setItem(SESSION_ID_KEY, sessionId);
  return sessionId;
}

function regenerateSessionId(): string {
  const sessionId = crypto.randomUUID();
  if (isBrowser()) {
    sessionStorage.setItem(SESSION_ID_KEY, sessionId);
  }
  return sessionId;
}

function touchLastActivity(): void {
  if (isBrowser()) {
    sessionStorage.setItem(LAST_ACTIVITY_KEY, String(Date.now()));
  }
}

export function readLastActivityMs(): number {
  if (!isBrowser()) {
    return 0;
  }
  const raw = sessionStorage.getItem(LAST_ACTIVITY_KEY);
  if (!raw) {
    return 0;
  }
  const parsed = Number(raw);
  return Number.isFinite(parsed) ? parsed : 0;
}

export function clearTelemetrySessionKeys(): void {
  if (!isBrowser()) {
    return;
  }
  sessionStorage.removeItem(SESSION_ID_KEY);
  sessionStorage.removeItem(LAST_ACTIVITY_KEY);
}

export function hasTelemetrySessionEvidence(): boolean {
  if (!isBrowser()) {
    return false;
  }
  return (
    sessionStorage.getItem(SESSION_ID_KEY) !== null ||
    sessionStorage.getItem(LAST_ACTIVITY_KEY) !== null
  );
}

export type SessionExpiredGateInput = {
  token: string | null;
  tokenExpired: boolean;
  hasSessionEvidence: boolean;
};

/** Emit session_expired only when a prior session existed (telemetry keys or expired JWT). */
export function shouldEmitSessionExpired({
  token,
  tokenExpired,
  hasSessionEvidence,
}: SessionExpiredGateInput): boolean {
  if (token !== null && tokenExpired) {
    return true;
  }
  if (token === null && hasSessionEvidence) {
    return true;
  }
  return false;
}

function buildEnvelope(
  eventType: string,
  properties: Record<string, unknown>,
  sessionId: string,
): TelemetryEnvelope {
  return {
    eventId: crypto.randomUUID(),
    timestamp: new Date().toISOString(),
    sessionId,
    userId: readUserId(),
    event_type: eventType,
    schemaVersion: TELEMETRY_SCHEMA_VERSION,
    requestId: crypto.randomUUID(),
    service: TELEMETRY_SERVICE,
    properties,
  };
}

function ensureTransport(): void {
  if (!isBrowser()) {
    return;
  }
  if (!flushTimer) {
    flushTimer = setInterval(() => {
      void flushQueue('interval');
    }, QUEUE_FLUSH_INTERVAL_MS);
  }
  if (!visibilityListenerAttached) {
    document.addEventListener('visibilitychange', handleVisibilityChange);
    visibilityListenerAttached = true;
  }
}

function handleVisibilityChange(): void {
  if (document.hidden) {
    beaconQueue();
  }
}

function sleep(ms: number): Promise<void> {
  return new Promise((resolve) => {
    setTimeout(resolve, ms);
  });
}

async function postEvents(events: TelemetryEnvelope[]): Promise<boolean> {
  const endpoint = getTelemetryEndpoint();
  if (!endpoint || events.length === 0) {
    return true;
  }

  for (let attempt = 0; attempt <= MAX_FLUSH_RETRIES; attempt += 1) {
    try {
      const response = await fetch(endpoint, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ events }),
        keepalive: true,
      });
      if (response.ok) {
        return true;
      }
    } catch {
      // Telemetry must never block the app.
    }

    if (attempt < MAX_FLUSH_RETRIES) {
      await sleep(INITIAL_BACKOFF_MS * 2 ** attempt);
    }
  }

  return false;
}

async function flushQueue(_reason: 'size' | 'interval'): Promise<void> {
  if (eventQueue.length === 0) {
    return;
  }

  const batch = eventQueue.splice(0, eventQueue.length);
  const ok = await postEvents(batch);
  if (!ok) {
    // Discard batch after retries exhausted.
  }
}

function beaconQueue(): void {
  if (!isBrowser() || eventQueue.length === 0) {
    return;
  }

  const endpoint = getTelemetryEndpoint();
  if (!endpoint || typeof navigator.sendBeacon !== 'function') {
    return;
  }

  const batch = eventQueue.splice(0, eventQueue.length);
  const payload = new Blob([JSON.stringify({ events: batch })], { type: 'application/json' });
  navigator.sendBeacon(endpoint, payload);
}

function enqueue(event: TelemetryEnvelope): void {
  eventQueue.push(event);
  if (eventQueue.length >= QUEUE_FLUSH_SIZE) {
    void flushQueue('size');
  }
}

function handleLoginFailure(properties: Record<string, unknown>): void {
  const failureReason = properties.failure_reason;
  const source = properties.source;
  if (failureReason !== 'wrong_credentials' && failureReason !== 'account_locked') {
    return;
  }
  if (source !== 'backoffice') {
    return;
  }

  const result = recordLoginFailure(loginFailureState, Date.now(), {
    failure_reason: failureReason,
    source: 'backoffice',
  });
  loginFailureState = result.nextState;

  const sessionId = readSessionId();
  const event = buildEnvelope('user_login_failed', result.event, sessionId);

  if (pendingLoginFailureIndex !== null && pendingLoginFailureIndex < eventQueue.length) {
    eventQueue[pendingLoginFailureIndex] = event;
  } else {
    pendingLoginFailureIndex = eventQueue.length;
    enqueue(event);
  }
}

export function track(eventType: string, properties: Record<string, unknown>): void {
  if (!isBrowser()) {
    return;
  }

  ensureTransport();
  touchLastActivity();

  if (eventType === 'user_login_succeeded') {
    loginFailureState = resetLoginFailureState();
    pendingLoginFailureIndex = null;
    const sessionId = regenerateSessionId();
    enqueue(buildEnvelope(eventType, properties, sessionId));
    return;
  }

  if (eventType === 'user_login_failed') {
    handleLoginFailure(properties);
    return;
  }

  const sessionId = readSessionId();
  enqueue(buildEnvelope(eventType, properties, sessionId));
}

/** Test-only reset — not part of the public telemetry API surface. */
export function __resetTelemetryForTests(): void {
  eventQueue = [];
  loginFailureState = resetLoginFailureState();
  pendingLoginFailureIndex = null;
  if (flushTimer) {
    clearInterval(flushTimer);
    flushTimer = null;
  }
  if (isBrowser() && visibilityListenerAttached) {
    document.removeEventListener('visibilitychange', handleVisibilityChange);
    visibilityListenerAttached = false;
  }
}

/** Test-only queue reader. */
export function __getQueueForTests(): TelemetryEnvelope[] {
  return [...eventQueue];
}

/** Test-only flush trigger. */
export async function __flushQueueForTests(): Promise<void> {
  await flushQueue('interval');
}

/** Test-only beacon trigger. */
export function __beaconQueueForTests(): void {
  beaconQueue();
}
