'use client';

import { useState } from 'react';
import type { FormEvent } from 'react';
import InventoryAuthGuard from '@/app/_components/InventoryAuthGuard';
import { askKnowledge } from '@/lib/rag';

type ViewState =
  | { status: 'idle' }
  | { status: 'loading' }
  | { status: 'error'; message: string }
  | { status: 'success'; answer: string };

function KnowledgePageContent() {
  const [question, setQuestion] = useState('');
  const [view, setView] = useState<ViewState>({ status: 'idle' });

  async function onSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const trimmed = question.trim();
    if (!trimmed) {
      setView({ status: 'error', message: 'Enter a question before submitting.' });
      return;
    }
    setView({ status: 'loading' });
    try {
      const answer = await askKnowledge(trimmed);
      setView({ status: 'success', answer });
    } catch (error) {
      setView({
        status: 'error',
        message: error instanceof Error ? error.message : 'Failed to get an answer.',
      });
    }
  }

  return (
    <>
      <div className="mb-8">
        <h1 className="font-display text-3xl font-bold text-brasaland-charcoal">
          Knowledge assistant
        </h1>
        <p className="text-sm text-brasaland-charcoal/60 mt-1">
          Ask about loyalty, waste, allergens, or supplier ordering — answers come from official
          manuals only.
        </p>
      </div>

      <form onSubmit={onSubmit} className="space-y-4 max-w-2xl" aria-labelledby="knowledge-form">
        <h2 id="knowledge-form" className="sr-only">
          Ask a knowledge question
        </h2>
        <label htmlFor="knowledge-question" className="block text-sm font-medium">
          Question
        </label>
        <textarea
          id="knowledge-question"
          name="question"
          rows={3}
          value={question}
          onChange={(event) => setQuestion(event.target.value)}
          className="w-full rounded-md border border-brasaland-charcoal/20 bg-white px-3 py-2 text-sm"
          placeholder="How many points for Gold tier?"
        />
        <button
          type="submit"
          disabled={view.status === 'loading'}
          className="rounded-md bg-brasaland-ember px-4 py-2 text-sm font-medium text-brasaland-ivory disabled:opacity-60"
        >
          {view.status === 'loading' ? 'Asking…' : 'Ask'}
        </button>
      </form>

      {view.status === 'loading' ? (
        <p role="status" className="text-sm text-brasaland-charcoal/60 mt-6">
          Generating answer…
        </p>
      ) : null}

      {view.status === 'error' ? (
        <p
          role="alert"
          className="text-sm text-brasaland-error bg-brasaland-error/10 rounded-md px-3 py-2 mt-6"
        >
          {view.message}
        </p>
      ) : null}

      {view.status === 'success' ? (
        <section aria-labelledby="knowledge-answer" className="mt-8 max-w-2xl">
          <h2 id="knowledge-answer" className="font-semibold text-xl mb-2">
            Answer
          </h2>
          <p className="text-sm text-brasaland-charcoal/90 whitespace-pre-wrap">{view.answer}</p>
        </section>
      ) : null}
    </>
  );
}

export default function KnowledgePage() {
  return (
    <InventoryAuthGuard>
      <KnowledgePageContent />
    </InventoryAuthGuard>
  );
}
