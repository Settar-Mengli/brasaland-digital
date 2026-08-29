'use client';

import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { type FormEvent, useState } from 'react';

import { fetchAuthorizedLocations, login } from '@/lib/auth';
import { locationLabel, setSessionLocationSlug } from '@/lib/locations';
import { mapLoginFailureReason } from '@/lib/login-failure-aggregation';
import { track } from '@/lib/telemetry';

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [locationSlug, setLocationSlug] = useState('');
  const [authorizedLocations, setAuthorizedLocations] = useState<string[]>([]);
  const [locationsReady, setLocationsReady] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [preflightLoading, setPreflightLoading] = useState(false);

  function resetLocationState() {
    setLocationsReady(false);
    setAuthorizedLocations([]);
    setLocationSlug('');
  }

  function handleLocationChange(value: string) {
    setLocationSlug(value);
    setSessionLocationSlug(value);
  }

  async function runPreflight() {
    setError(null);
    setPreflightLoading(true);
    try {
      const result = await fetchAuthorizedLocations(email, password);
      setAuthorizedLocations(result.authorized_locations);
      setLocationsReady(true);
      if (result.authorized_locations.length === 1) {
        const slug = result.authorized_locations[0] ?? '';
        setLocationSlug(slug);
        if (slug) {
          setSessionLocationSlug(slug);
        }
      } else {
        setLocationSlug('');
      }
    } catch (continueError) {
      const message =
        continueError instanceof Error ? continueError.message : 'Could not verify credentials.';
      track('user_login_failed', {
        failure_reason: mapLoginFailureReason(message),
        source: 'backoffice',
      });
      setError(message);
      resetLocationState();
    } finally {
      setPreflightLoading(false);
    }
  }

  async function handleContinue(event: FormEvent) {
    event.preventDefault();
    await runPreflight();
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);

    if (!locationsReady) {
      await runPreflight();
      return;
    }

    if (!locationSlug) {
      setError('Select a location.');
      return;
    }

    setSubmitting(true);
    try {
      await login(email, password, locationSlug);
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

  const showLocationPicker = locationsReady && authorizedLocations.length > 1;

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

        {showLocationPicker ? (
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
              {authorizedLocations.map((slug) => (
                <option key={slug} value={slug}>
                  {locationLabel(slug)}
                </option>
              ))}
            </select>
          </div>
        ) : null}

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
            onChange={(event) => {
              setEmail(event.target.value);
              resetLocationState();
            }}
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
            onChange={(event) => {
              setPassword(event.target.value);
              resetLocationState();
            }}
            className="w-full rounded-md border border-brasaland-charcoal/20 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brasaland-ember"
          />
        </div>

        {!locationsReady ? (
          <button
            type="button"
            disabled={preflightLoading}
            onClick={(event) => {
              void handleContinue(event);
            }}
            className="w-full px-4 py-2 rounded-md bg-brasaland-charcoal text-white font-medium hover:bg-brasaland-charcoal/90 focus:outline-none focus:ring-2 focus:ring-brasaland-charcoal focus:ring-offset-2 transition-colors disabled:opacity-60"
          >
            {preflightLoading ? 'Checking credentials…' : 'Continue'}
          </button>
        ) : (
          <button
            type="submit"
            disabled={submitting}
            className="w-full px-4 py-2 rounded-md bg-brasaland-ember text-white font-medium hover:bg-brasaland-ember/90 focus:outline-none focus:ring-2 focus:ring-brasaland-ember focus:ring-offset-2 transition-colors disabled:opacity-60"
          >
            {submitting ? 'Signing in…' : 'Sign in'}
          </button>
        )}
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
