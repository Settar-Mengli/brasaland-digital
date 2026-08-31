'use client';

import { FormEvent, useState } from 'react';

import TurnstileChallenge from '@/app/_components/TurnstileChallenge';
import { askGuestChat } from '@/lib/chat-client';
import { publicChatEnabled, turnstileWidgetEnabled } from '@/lib/turnstile-widget';

export default function GuestChatWidget() {
  const [open, setOpen] = useState(false);
  const [question, setQuestion] = useState('');
  const [answer, setAnswer] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [turnstileToken, setTurnstileToken] = useState<string | null>(null);
  const [turnstileResetSignal, setTurnstileResetSignal] = useState(0);

  const turnstileEnabled = turnstileWidgetEnabled();

  if (!publicChatEnabled()) {
    return null;
  }

  async function onSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const trimmed = question.trim();
    if (!trimmed || loading) {
      return;
    }
    if (turnstileEnabled && !turnstileToken) {
      setError('Complete the security check before asking.');
      return;
    }
    setLoading(true);
    setError('');
    setAnswer('');
    try {
      const response = await askGuestChat(
        trimmed,
        turnstileEnabled ? (turnstileToken ?? undefined) : undefined,
      );
      setAnswer(response);
      setQuestion('');
    } catch (submitError) {
      const message =
        submitError instanceof Error ? submitError.message : 'Unable to get an answer right now.';
      setError(message);
    } finally {
      setLoading(false);
      if (turnstileEnabled) {
        setTurnstileResetSignal((value) => value + 1);
      }
    }
  }

  const submitDisabled =
    loading || !question.trim() || (turnstileEnabled && turnstileToken === null);

  return (
    <div className="fixed bottom-4 right-4 z-50 flex flex-col items-end gap-2">
      {open ? (
        <section
          id="guest-chat-panel"
          aria-label="Guest information chat"
          className="w-[min(100vw-2rem,22rem)] rounded-lg border border-brasaland-charcoal/10 bg-brasaland-cream shadow-lg"
        >
          <header className="flex items-center justify-between border-b border-brasaland-charcoal/10 px-4 py-3">
            <h2 className="font-display text-lg font-bold text-brasaland-charcoal">Guest FAQ</h2>
            <button
              type="button"
              onClick={() => setOpen(false)}
              className="rounded px-2 py-1 text-sm text-brasaland-charcoal hover:bg-brasaland-ivory focus:outline-none focus-visible:ring-2 focus-visible:ring-brasaland-ember"
              aria-label="Close guest chat"
            >
              Close
            </button>
          </header>
          <div className="px-4 py-3 space-y-3 text-sm text-brasaland-charcoal">
            <p>
              Ask about hours, locations, menu highlights, or Brasa Points. Do not enter personal
              information.
            </p>
            <p>For severe allergies, confirm details with staff — cross-contact risk may apply.</p>
            <form onSubmit={onSubmit} className="space-y-2">
              <label htmlFor="guest-chat-question" className="block font-medium">
                Your question
              </label>
              <textarea
                id="guest-chat-question"
                name="question"
                rows={3}
                maxLength={300}
                value={question}
                onChange={(event) => setQuestion(event.target.value)}
                className="w-full rounded border border-brasaland-charcoal/20 bg-white px-3 py-2 text-sm focus:outline-none focus-visible:ring-2 focus-visible:ring-brasaland-ember"
                disabled={loading}
                aria-describedby="guest-chat-status"
              />
              {turnstileEnabled ? (
                <TurnstileChallenge
                  onTokenChange={setTurnstileToken}
                  resetSignal={turnstileResetSignal}
                />
              ) : null}
              <button
                type="submit"
                disabled={submitDisabled}
                className="rounded bg-brasaland-ember px-4 py-2 text-sm font-semibold text-white disabled:opacity-50 focus:outline-none focus-visible:ring-2 focus-visible:ring-brasaland-ember"
              >
                {loading ? 'Sending…' : 'Ask'}
              </button>
            </form>
            <div id="guest-chat-status" aria-live="polite" className="min-h-[1.25rem]">
              {loading ? <p>Loading answer…</p> : null}
              {error ? <p>{error}</p> : null}
              {answer ? <p className="whitespace-pre-wrap">{answer}</p> : null}
            </div>
          </div>
        </section>
      ) : null}
      <button
        type="button"
        onClick={() => setOpen((value) => !value)}
        className="rounded-full bg-brasaland-ember px-4 py-3 text-sm font-semibold text-white shadow-lg focus:outline-none focus-visible:ring-2 focus-visible:ring-brasaland-ember"
        aria-expanded={open}
        aria-controls="guest-chat-panel"
      >
        {open ? 'Hide FAQ chat' : 'Ask a question'}
      </button>
    </div>
  );
}
