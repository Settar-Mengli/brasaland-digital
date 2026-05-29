'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';

const LINKS = [
  { href: '/', label: 'Dashboard' },
  { href: '/locations', label: 'Locations' },
] as const;

export default function NavLinks() {
  const pathname = usePathname();
  return (
    <nav aria-label="Backoffice navigation" className="flex items-center gap-6">
      {LINKS.map((link) => (
        <Link
          key={link.href}
          href={link.href}
          className={
            pathname === link.href
              ? 'text-sm text-brasaland-ivory font-medium transition-colors'
              : 'text-sm text-brasaland-ivory/70 hover:text-brasaland-ivory transition-colors'
          }
          aria-current={pathname === link.href ? 'page' : undefined}
        >
          {link.label}
        </Link>
      ))}
    </nav>
  );
}
