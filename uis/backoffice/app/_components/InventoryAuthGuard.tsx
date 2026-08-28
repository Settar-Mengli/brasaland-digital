'use client';

import { useRouter } from 'next/navigation';
import { useEffect, useState } from 'react';

import { clearAccessToken, getAccessToken } from '@/lib/auth';
import {
  clearTelemetrySessionKeys,
  computeIdleDurationMs,
  hasTelemetrySessionEvidence,
  isAccessTokenExpired,
  shouldEmitSessionExpired,
  track,
} from '@/lib/telemetry';

export default function InventoryAuthGuard({ children }: Readonly<{ children: React.ReactNode }>) {
  const router = useRouter();
  const [ready, setReady] = useState(false);

  useEffect(() => {
    const token = getAccessToken();
    const tokenExpired = token !== null && isAccessTokenExpired(token);
    const hasSessionEvidence = hasTelemetrySessionEvidence();

    if (token === null || tokenExpired) {
      if (shouldEmitSessionExpired({ token, tokenExpired, hasSessionEvidence })) {
        track('session_expired', {
          idle_duration_ms: computeIdleDurationMs(),
          source: 'backoffice',
        });
        clearTelemetrySessionKeys();
      }
      if (token) {
        clearAccessToken();
      }
      router.replace('/login');
      return;
    }

    let cancelled = false;
    queueMicrotask(() => {
      if (!cancelled) {
        setReady(true);
      }
    });
    return () => {
      cancelled = true;
    };
  }, [router]);

  if (!ready) {
    return <p className="text-sm text-brasaland-charcoal/60">Loading…</p>;
  }

  return <>{children}</>;
}
