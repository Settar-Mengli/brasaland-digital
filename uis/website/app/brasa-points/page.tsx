import type { Metadata } from 'next';
import Footer from '@/app/_components/Footer';
import Header from '@/app/_components/Header';
import BrasaPointsInfo from './_components/BrasaPointsInfo';

export const metadata: Metadata = {
  title: 'Brasa Points — Brasaland',
  description:
    'Learn how Brasa Points works: earn rates, tiers, redemption, and stamp-card transfer policy.',
};

export default function BrasaPointsPage() {
  return (
    <>
      <Header />
      <main id="main-content" className="min-h-screen bg-brasaland-ivory py-12">
        <div className="max-w-2xl mx-auto px-4 sm:px-6 lg:px-8">
          <BrasaPointsInfo />
        </div>
      </main>
      <Footer />
    </>
  );
}
