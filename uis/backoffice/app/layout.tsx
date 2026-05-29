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
  title: 'Brasaland Backoffice — Operations Dashboard',
  description: 'Internal operations dashboard powered by the Brasaland operations toolkit.',
};

export default function BackofficeLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en" className={`${inter.variable} ${playfair.variable}`}>
      <body className="font-sans bg-brasaland-ivory text-brasaland-charcoal antialiased">
        <header className="bg-brasaland-charcoal text-brasaland-ivory border-b-4 border-brasaland-ember">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-14 flex items-center gap-6">
            <Link
              href="/"
              className="font-display font-bold text-lg tracking-tight text-brasaland-ivory"
            >
              Brasaland Backoffice
            </Link>
            <nav aria-label="Backoffice navigation" className="flex items-center gap-6">
              <Link
                href="/"
                className="text-sm text-brasaland-ivory/70 hover:text-brasaland-ivory transition-colors"
              >
                Dashboard
              </Link>
              <Link
                href="/locations"
                className="text-sm text-brasaland-ivory/70 hover:text-brasaland-ivory transition-colors"
              >
                Locations
              </Link>
            </nav>
          </div>
        </header>
        <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">{children}</main>
      </body>
    </html>
  );
}
