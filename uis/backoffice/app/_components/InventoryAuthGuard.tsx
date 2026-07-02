'use client';

import { useRouter } from 'next/navigation';
import { useEffect, useState } from 'react';

import { isAuthenticated } from '@/lib/auth';

export default function InventoryAuthGuard({ children }: Readonly<{ children: React.ReactNode }>) {
  const router = useRouter();
  const [ready, setReady] = useState(false);

  useEffect(() => {
    if (!isAuthenticated()) {
      router.replace('/login');
      return;
    }
    setReady(true);
  }, [router]);

  if (!ready) {
    return <p className="text-sm text-brasaland-charcoal/60">Loading…</p>;
  }

  return <>{children}</>;
}
