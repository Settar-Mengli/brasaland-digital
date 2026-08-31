'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { useEffect, useState } from 'react';

import { getAccessToken, logout } from '@/lib/auth';
import { isAccessTokenExpired } from '@/lib/telemetry';

const LINKS = [
  { href: '/', label: 'Dashboard' },
  { href: '/locations', label: 'Locations' },
  { href: '/inventory/products', label: 'Inventory' },
  { href: '/inventory/orders', label: 'Orders' },
  { href: '/reporting', label: 'Reporting' },
  { href: '/knowledge', label: 'Knowledge' },
  { href: '/rfp', label: 'RFP' },
  { href: '/account/profile', label: 'Profile' },
] as const;

const SLICE_HREFS = new Set(['/', '/locations', '/rfp', '/account/profile']);
const AUTH_ROUTES = new Set(['/login', '/register']);

function visibleLinks(): readonly (typeof LINKS)[number][] {
  if (process.env.NEXT_PUBLIC_SLICE_NAV === '1') {
    return LINKS.filter((link) => SLICE_HREFS.has(link.href));
  }
  return LINKS;
}

function isActive(pathname: string, href: string): boolean {
  if (href === '/') {
    return pathname === '/';
  }
  return pathname === href || pathname.startsWith(`${href}/`);
}

function hasValidSession(pathname: string): boolean {
  if (AUTH_ROUTES.has(pathname)) {
    return false;
  }
  const token = getAccessToken();
  if (token === null) {
    return false;
  }
  return !isAccessTokenExpired(token);
}

export default function NavLinks() {
  const pathname = usePathname();
  const [ready, setReady] = useState(false);

  useEffect(() => {
    let cancelled = false;
    queueMicrotask(() => {
      if (!cancelled) {
        setReady(true);
      }
    });
    return () => {
      cancelled = true;
    };
  }, [pathname]);

  if (!ready || !hasValidSession(pathname)) {
    return null;
  }

  return (
    <nav aria-label="Backoffice navigation" className="flex items-center gap-6">
      {visibleLinks().map((link) => {
        const active = isActive(pathname, link.href);
        return (
          <Link
            key={link.href}
            href={link.href}
            className={
              active
                ? 'text-sm text-brasaland-ivory font-medium transition-colors'
                : 'text-sm text-brasaland-ivory/70 hover:text-brasaland-ivory transition-colors'
            }
            aria-current={active ? 'page' : undefined}
          >
            {link.label}
          </Link>
        );
      })}
      <button
        type="button"
        onClick={() => {
          logout();
        }}
        className="text-sm text-brasaland-ivory/70 hover:text-brasaland-ivory transition-colors"
      >
        Logout
      </button>
    </nav>
  );
}
