'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';

const LINKS = [
  { href: '/', label: 'Dashboard' },
  { href: '/locations', label: 'Locations' },
  { href: '/inventory/products', label: 'Inventory' },
  { href: '/inventory/orders', label: 'Orders' },
  { href: '/reporting', label: 'Reporting' },
] as const;

function isActive(pathname: string, href: string): boolean {
  if (href === '/') {
    return pathname === '/';
  }
  return pathname === href || pathname.startsWith(`${href}/`);
}

export default function NavLinks() {
  const pathname = usePathname();
  return (
    <nav aria-label="Backoffice navigation" className="flex items-center gap-6">
      {LINKS.map((link) => {
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
    </nav>
  );
}
