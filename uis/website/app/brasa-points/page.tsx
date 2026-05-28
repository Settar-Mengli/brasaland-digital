import type { Metadata } from 'next';
import BrasaPointsForm from './_components/BrasaPointsForm';

export const metadata: Metadata = {
  title: 'Brasa Points Registration — Brasaland',
  description:
    'Join the Brasa Points loyalty program and earn rewards at every Brasaland location.',
};

export default function BrasaPointsPage() {
  return (
    <main className="min-h-screen bg-brasaland-ivory py-12">
      <div className="max-w-2xl mx-auto px-4 sm:px-6 lg:px-8">
        <BrasaPointsForm />
      </div>
    </main>
  );
}
