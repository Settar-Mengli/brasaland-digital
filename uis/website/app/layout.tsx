import type { Metadata, Viewport } from 'next';
import { Inter, Playfair_Display } from 'next/font/google';
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

const DESCRIPTION =
  'Brasaland is a grilled-food restaurant chain with 14 locations across Colombia and the United States. Experience the warmth of Latin American cuisine, crafted on the grill since 2008.';

export const metadata: Metadata = {
  title: 'Brasaland — The Taste of the Grill, in Every Bite',
  description: DESCRIPTION,
  icons: { icon: '/favicon.svg' },
  openGraph: {
    type: 'website',
    siteName: 'Brasaland',
    title: 'Brasaland — The Taste of the Grill, in Every Bite',
    description: DESCRIPTION,
    url: 'https://brasaland.com',
  },
  twitter: {
    card: 'summary_large_image',
    title: 'Brasaland — The Taste of the Grill, in Every Bite',
    description: DESCRIPTION,
  },
};

export const viewport: Viewport = {
  themeColor: '#C24A2B',
};

const jsonLd = {
  '@context': 'https://schema.org',
  '@type': 'Restaurant',
  name: 'Brasaland',
  description: 'A 14-location grilled-food restaurant chain across Colombia and the United States.',
  url: 'https://brasaland.com',
  foundingDate: '2008',
  servesCuisine: ['Brazilian', 'Colombian', 'Grilled'],
  priceRange: '$$',
  address: [
    {
      '@type': 'PostalAddress',
      streetAddress: 'El Poblado',
      addressLocality: 'Medellín',
      addressCountry: 'CO',
    },
    {
      '@type': 'PostalAddress',
      streetAddress: 'Brickell',
      addressLocality: 'Miami',
      addressRegion: 'FL',
      addressCountry: 'US',
    },
  ],
  contactPoint: {
    '@type': 'ContactPoint',
    contactType: 'customer service',
    availableLanguage: ['English', 'Spanish'],
  },
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en" className={`${inter.variable} ${playfair.variable}`}>
      <head>
        <script
          type="application/ld+json"
          dangerouslySetInnerHTML={{ __html: JSON.stringify(jsonLd) }}
        />
      </head>
      <body className="font-sans bg-brasaland-ivory text-brasaland-charcoal antialiased">
        <a
          href="#main-content"
          className="sr-only focus:not-sr-only focus:absolute focus:top-4 focus:left-4 focus:z-50 focus:px-4 focus:py-2 focus:bg-brasaland-ember focus:text-brasaland-ivory focus:rounded"
        >
          Skip to main content
        </a>
        {children}
      </body>
    </html>
  );
}
