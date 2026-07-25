'use client';

import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { type FormEvent, useState } from 'react';

import { register } from '@/lib/auth';

type FieldErrors = {
  email?: string;
  password?: string;
  name?: string;
  phone?: string;
  address?: string;
};

function parseFieldErrors(message: string): { fields: FieldErrors; general: string | null } {
  const fields: FieldErrors = {};
  const generalParts: string[] = [];

  for (const part of message.split(';')) {
    const trimmed = part.trim();
    if (!trimmed) {
      continue;
    }
    const colonIndex = trimmed.indexOf(':');
    if (colonIndex === -1) {
      generalParts.push(trimmed);
      continue;
    }
    const field = trimmed.slice(0, colonIndex).trim();
    const detail = trimmed.slice(colonIndex + 1).trim();
    if (
      field === 'email' ||
      field === 'password' ||
      field === 'name' ||
      field === 'phone' ||
      field === 'address'
    ) {
      fields[field] = detail;
    } else {
      generalParts.push(trimmed);
    }
  }

  return {
    fields,
    general: generalParts.length > 0 ? generalParts.join('; ') : null,
  };
}

export default function RegisterPage() {
  const router = useRouter();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [name, setName] = useState('');
  const [phone, setPhone] = useState('');
  const [address, setAddress] = useState('');
  const [fieldErrors, setFieldErrors] = useState<FieldErrors>({});
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);
    setFieldErrors({});
    setSubmitting(true);

    try {
      await register(email, password, {
        name: name.trim(),
        phone: phone.trim(),
        address: address.trim(),
      });
      router.replace('/inventory/products');
    } catch (submitError) {
      const message =
        submitError instanceof Error
          ? submitError.message
          : 'Registration failed. Please try again.';
      const parsed = parseFieldErrors(message);
      setFieldErrors(parsed.fields);
      setError(parsed.general ?? (Object.keys(parsed.fields).length === 0 ? message : null));
    } finally {
      setSubmitting(false);
    }
  }

  const inputClass =
    'w-full rounded-md border border-brasaland-charcoal/20 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brasaland-ember';
  const errorClass = 'text-xs text-brasaland-error mt-1';

  return (
    <div className="max-w-md mx-auto">
      <div className="mb-8">
        <h1 className="font-display text-3xl font-bold text-brasaland-charcoal">Create account</h1>
        <p className="text-sm text-brasaland-charcoal/60 mt-1">
          Brasaland Backoffice — register for inventory access
        </p>
      </div>

      <form
        onSubmit={handleSubmit}
        className="border border-brasaland-charcoal/10 rounded-lg p-6 bg-white space-y-4"
        noValidate
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
            aria-invalid={fieldErrors.email ? true : undefined}
            aria-describedby={fieldErrors.email ? 'email-error' : undefined}
            className={inputClass}
          />
          {fieldErrors.email ? (
            <p id="email-error" role="alert" className={errorClass}>
              {fieldErrors.email}
            </p>
          ) : null}
        </div>

        <div>
          <label htmlFor="password" className="block text-sm font-medium mb-1">
            Password
          </label>
          <input
            id="password"
            name="password"
            type="password"
            autoComplete="new-password"
            required
            minLength={8}
            value={password}
            onChange={(event) => setPassword(event.target.value)}
            aria-invalid={fieldErrors.password ? true : undefined}
            aria-describedby={fieldErrors.password ? 'password-error' : undefined}
            className={inputClass}
          />
          {fieldErrors.password ? (
            <p id="password-error" role="alert" className={errorClass}>
              {fieldErrors.password}
            </p>
          ) : null}
        </div>

        <div>
          <label htmlFor="name" className="block text-sm font-medium mb-1">
            Name <span className="text-brasaland-charcoal/50 font-normal">(optional)</span>
          </label>
          <input
            id="name"
            name="name"
            type="text"
            autoComplete="name"
            value={name}
            onChange={(event) => setName(event.target.value)}
            aria-invalid={fieldErrors.name ? true : undefined}
            aria-describedby={fieldErrors.name ? 'name-error' : undefined}
            className={inputClass}
          />
          {fieldErrors.name ? (
            <p id="name-error" role="alert" className={errorClass}>
              {fieldErrors.name}
            </p>
          ) : null}
        </div>

        <div>
          <label htmlFor="phone" className="block text-sm font-medium mb-1">
            Phone <span className="text-brasaland-charcoal/50 font-normal">(optional)</span>
          </label>
          <input
            id="phone"
            name="phone"
            type="tel"
            autoComplete="tel"
            value={phone}
            onChange={(event) => setPhone(event.target.value)}
            aria-invalid={fieldErrors.phone ? true : undefined}
            aria-describedby={fieldErrors.phone ? 'phone-error' : undefined}
            className={inputClass}
          />
          {fieldErrors.phone ? (
            <p id="phone-error" role="alert" className={errorClass}>
              {fieldErrors.phone}
            </p>
          ) : null}
        </div>

        <div>
          <label htmlFor="address" className="block text-sm font-medium mb-1">
            Address <span className="text-brasaland-charcoal/50 font-normal">(optional)</span>
          </label>
          <input
            id="address"
            name="address"
            type="text"
            autoComplete="street-address"
            value={address}
            onChange={(event) => setAddress(event.target.value)}
            aria-invalid={fieldErrors.address ? true : undefined}
            aria-describedby={fieldErrors.address ? 'address-error' : undefined}
            className={inputClass}
          />
          {fieldErrors.address ? (
            <p id="address-error" role="alert" className={errorClass}>
              {fieldErrors.address}
            </p>
          ) : null}
        </div>

        <button
          type="submit"
          disabled={submitting}
          className="w-full px-4 py-2 rounded-md bg-brasaland-ember text-white font-medium hover:bg-brasaland-ember/90 focus:outline-none focus:ring-2 focus:ring-brasaland-ember focus:ring-offset-2 transition-colors disabled:opacity-60"
        >
          {submitting ? 'Creating account…' : 'Create account'}
        </button>

        <p className="text-sm text-brasaland-charcoal/60 text-center">
          Already have an account?{' '}
          <Link href="/login" className="text-brasaland-ember hover:underline">
            Sign in
          </Link>
        </p>
      </form>
    </div>
  );
}
