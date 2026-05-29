'use client';

import { useEffect, useRef, useState } from 'react';
import Link from 'next/link';

const NAV_LINKS = [
  { href: '/#hero', label: 'Home' },
  { href: '/#story', label: 'Our Story' },
  { href: '/#locations', label: 'Locations' },
  { href: '/brasa-points', label: 'Brasa Points' },
  { href: '/#contact', label: 'Contact' },
] as const;

export default function Header() {
  const [isOpen, setIsOpen] = useState(false);
  const toggleRef = useRef<HTMLButtonElement>(null);
  const panelRef = useRef<HTMLElement>(null);

  useEffect(() => {
    function onKeydown(e: KeyboardEvent) {
      if (e.key !== 'Escape') return;
      if (
        panelRef.current?.contains(document.activeElement) ||
        document.activeElement === toggleRef.current
      ) {
        setIsOpen(false);
        toggleRef.current?.focus();
      }
    }
    document.addEventListener('keydown', onKeydown);
    return () => document.removeEventListener('keydown', onKeydown);
  }, []);

  return (
    <header className="sticky top-0 z-40 bg-brasaland-ivory border-b border-brasaland-charcoal/10">
      <nav
        aria-label="Primary"
        className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4 flex items-center justify-between"
      >
        <Link href="/" className="font-display text-2xl font-bold text-brasaland-ember">
          Brasaland
        </Link>

        <button
          ref={toggleRef}
          type="button"
          onClick={() => setIsOpen((o) => !o)}
          aria-expanded={isOpen}
          aria-controls="mobile-nav-panel"
          className="sm:hidden inline-flex items-center justify-center h-10 w-10 rounded-md text-brasaland-charcoal hover:bg-brasaland-charcoal/5 focus:outline-none focus:ring-2 focus:ring-brasaland-ember focus:ring-offset-2"
        >
          <span className="sr-only">Toggle navigation menu</span>
          <svg
            className="h-6 w-6"
            aria-hidden="true"
            fill="none"
            stroke="currentColor"
            strokeWidth={2}
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              d="M3.75 6.75h16.5M3.75 12h16.5m-16.5 5.25h16.5"
            />
          </svg>
        </button>

        <ul className="hidden sm:flex items-center gap-8 list-none m-0 p-0">
          {NAV_LINKS.map((link) => (
            <li key={link.href}>
              <Link
                href={link.href}
                className="text-brasaland-charcoal hover:text-brasaland-ember focus:text-brasaland-ember transition-colors focus:outline-none focus:ring-2 focus:ring-brasaland-ember focus:ring-offset-2 rounded-sm"
              >
                {link.label}
              </Link>
            </li>
          ))}
        </ul>
      </nav>

      <nav
        id="mobile-nav-panel"
        ref={panelRef}
        aria-label="Mobile navigation"
        hidden={!isOpen}
        className="sm:hidden border-t border-brasaland-charcoal/10 bg-brasaland-ivory"
      >
        <ul className="list-none m-0 px-4 py-4 flex flex-col gap-2">
          {NAV_LINKS.map((link) => (
            <li key={link.href}>
              <Link
                href={link.href}
                onClick={() => setIsOpen(false)}
                className="block px-3 py-2 rounded-md text-brasaland-charcoal hover:bg-brasaland-charcoal/5 hover:text-brasaland-ember focus:bg-brasaland-charcoal/5 focus:text-brasaland-ember focus:outline-none focus:ring-2 focus:ring-brasaland-ember"
              >
                {link.label}
              </Link>
            </li>
          ))}
        </ul>
      </nav>
    </header>
  );
}
