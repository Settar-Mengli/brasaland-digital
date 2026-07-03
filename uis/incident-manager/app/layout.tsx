import type { Metadata } from 'next';
import { Inter, Playfair_Display } from 'next/font/google';
import Link from 'next/link';
import './globals.css';

const inter = Inter({
  subsets: ['latin'],
  weight: ['400', '500', '600'],
  variable: '--font-inter',
  display: 'swap',
});

const playfair = Playfair_Display({
  subsets: ['latin'],
  weight: ['400', '600', '700'],
  variable: '--font-playfair',
  display: 'swap',
});

export const metadata: Metadata = {
  title: 'Brasaland — Incident Manager',
  description: 'Centralized incident registration, tracking, and summary metrics for Brasaland Operations.',
};

export default function IncidentManagerLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en" className={`${inter.variable} ${playfair.variable}`}>
      <body className="font-sans bg-brasaland-ivory text-brasaland-charcoal antialiased">
        <header className="bg-brasaland-charcoal text-brasaland-ivory border-b-4 border-brasaland-ember">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-14 flex items-center gap-6">
            <Link
              href="/"
              className="font-display font-bold text-lg tracking-tight text-brasaland-ivory"
            >
              Brasaland Incident Manager
            </Link>
            <nav aria-label="Main navigation" className="text-sm text-brasaland-ivory/60">
              {/* Register, Incidents, and Summary links — Chunk D */}
            </nav>
          </div>
        </header>
        <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">{children}</main>
      </body>
    </html>
  );
}
