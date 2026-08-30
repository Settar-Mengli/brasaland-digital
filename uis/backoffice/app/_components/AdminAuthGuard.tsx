'use client';

import { useRouter } from 'next/navigation';
import { useEffect, useState } from 'react';

import { clearAccessToken, getAccessToken, isAdminAccessToken } from '@/lib/auth';
import { isAccessTokenExpired } from '@/lib/telemetry';

export default function AdminAuthGuard({ children }: Readonly<{ children: React.ReactNode }>) {
  const router = useRouter();
  const [ready, setReady] = useState(false);

  useEffect(() => {
    const token = getAccessToken();
    if (token === null || isAccessTokenExpired(token)) {
      if (token !== null) {
        clearAccessToken();
      }
      router.replace('/login');
      return;
    }

    if (!isAdminAccessToken(token)) {
      router.replace('/');
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
    return (
      <p role="status" className="text-sm text-brasaland-charcoal/60">
        Loading…
      </p>
    );
  }

  return <>{children}</>;
}
