'use client';

import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { type FormEvent, useState } from 'react';

import { LOCATION_OPTIONS, setSessionLocationSlug } from '@/lib/locations';
import { login } from '@/lib/auth';
import { mapLoginFailureReason } from '@/lib/login-failure-aggregation';
import { track } from '@/lib/telemetry';

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [locationSlug, setLocationSlug] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  function handleLocationChange(value: string) {
    setLocationSlug(value);
    setSessionLocationSlug(value);
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);

    if (!locationSlug) {
      setError('Select a location.');
      return;
    }

    setSubmitting(true);
    try {
      await login(email, password);
      track('user_login_succeeded', { location_id: locationSlug });
      router.replace('/inventory/products');
    } catch (submitError) {
      const message =
        submitError instanceof Error ? submitError.message : 'Login failed. Please try again.';
      track('user_login_failed', {
        failure_reason: mapLoginFailureReason(message),
        source: 'backoffice',
      });
      setError(message);
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="max-w-md mx-auto">
      <div className="mb-8">
        <h1 className="font-display text-3xl font-bold text-brasaland-charcoal">Sign in</h1>
        <p className="text-sm text-brasaland-charcoal/60 mt-1">
          Brasaland Backoffice — inventory management
        </p>
      </div>

      <form
        onSubmit={handleSubmit}
        className="border border-brasaland-charcoal/10 rounded-lg p-6 bg-white space-y-4"
      >
        {error ? (
          <p
            role="alert"
            className="text-sm text-brasaland-error bg-brasaland-error/10 rounded-md px-3 py-2"
          >
            {error}
          </p>
        ) : null}

        <div>
          <label htmlFor="location" className="block text-sm font-medium mb-1">
            Location
          </label>
          <select
            id="location"
            name="location"
            required
            value={locationSlug}
            onChange={(event) => handleLocationChange(event.target.value)}
            className="w-full rounded-md border border-brasaland-charcoal/20 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brasaland-ember"
          >
            <option value="" disabled>
              Select a location…
            </option>
            {LOCATION_OPTIONS.map((option) => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>
        </div>

        <div>
          <label htmlFor="email" className="block text-sm font-medium mb-1">
            Email
          </label>
          <input
            id="email"
            name="email"
            type="email"
            autoComplete="username"
            required
            value={email}
            onChange={(event) => setEmail(event.target.value)}
            className="w-full rounded-md border border-brasaland-charcoal/20 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brasaland-ember"
          />
        </div>

        <div>
          <label htmlFor="password" className="block text-sm font-medium mb-1">
            Password
          </label>
          <input
            id="password"
            name="password"
            type="password"
            autoComplete="current-password"
            required
            minLength={8}
            value={password}
            onChange={(event) => setPassword(event.target.value)}
            className="w-full rounded-md border border-brasaland-charcoal/20 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brasaland-ember"
          />
        </div>

        <button
          type="submit"
          disabled={submitting}
          className="w-full px-4 py-2 rounded-md bg-brasaland-ember text-white font-medium hover:bg-brasaland-ember/90 focus:outline-none focus:ring-2 focus:ring-brasaland-ember focus:ring-offset-2 transition-colors disabled:opacity-60"
        >
          {submitting ? 'Signing in…' : 'Sign in'}
        </button>
        <p className="text-sm text-brasaland-charcoal/60 text-center">
          Need an account?{' '}
          <Link href="/register" className="text-brasaland-ember hover:underline">
            Create account
          </Link>
        </p>
      </form>
    </div>
  );
}
