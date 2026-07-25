'use client';

import { type FormEvent, useEffect, useState } from 'react';

import InventoryAuthGuard from '@/app/_components/InventoryAuthGuard';
import { getProfile, updateProfile } from '@/lib/profile';

function ProfileContent() {
  const [email, setEmail] = useState('');
  const [name, setName] = useState('');
  const [phone, setPhone] = useState('');
  const [address, setAddress] = useState('');
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;

    async function load() {
      setLoading(true);
      setError(null);
      try {
        const profile = await getProfile();
        if (cancelled) {
          return;
        }
        setEmail(profile.email);
        setName(profile.name);
        setPhone(profile.phone);
        setAddress(profile.address);
      } catch (loadError) {
        if (cancelled) {
          return;
        }
        setError(loadError instanceof Error ? loadError.message : 'Failed to load profile.');
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    }

    void load();
    return () => {
      cancelled = true;
    };
  }, []);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);
    setSuccess(null);
    setSaving(true);

    try {
      const updated = await updateProfile({
        name,
        phone,
        address,
      });
      setEmail(updated.email);
      setName(updated.name);
      setPhone(updated.phone);
      setAddress(updated.address);
      setSuccess('Profile saved.');
    } catch (saveError) {
      setError(saveError instanceof Error ? saveError.message : 'Failed to save profile.');
    } finally {
      setSaving(false);
    }
  }

  const inputClass =
    'w-full rounded-md border border-brasaland-charcoal/20 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brasaland-ember';

  if (loading) {
    return <p className="text-sm text-brasaland-charcoal/60">Loading profile…</p>;
  }

  return (
    <form
      onSubmit={handleSubmit}
      className="max-w-md border border-brasaland-charcoal/10 rounded-lg p-6 bg-white space-y-4"
    >
      {error ? (
        <p
          role="alert"
          className="text-sm text-brasaland-error bg-brasaland-error/10 rounded-md px-3 py-2"
        >
          {error}
        </p>
      ) : null}

      {success ? (
        <p
          role="status"
          className="text-sm text-brasaland-success bg-brasaland-success/10 rounded-md px-3 py-2"
        >
          {success}
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
          value={email}
          readOnly
          className={`${inputClass} bg-brasaland-charcoal/5 text-brasaland-charcoal/70`}
        />
      </div>

      <div>
        <label htmlFor="name" className="block text-sm font-medium mb-1">
          Name
        </label>
        <input
          id="name"
          name="name"
          type="text"
          autoComplete="name"
          value={name}
          onChange={(event) => setName(event.target.value)}
          className={inputClass}
        />
      </div>

      <div>
        <label htmlFor="phone" className="block text-sm font-medium mb-1">
          Phone
        </label>
        <input
          id="phone"
          name="phone"
          type="tel"
          autoComplete="tel"
          value={phone}
          onChange={(event) => setPhone(event.target.value)}
          className={inputClass}
        />
      </div>

      <div>
        <label htmlFor="address" className="block text-sm font-medium mb-1">
          Address
        </label>
        <input
          id="address"
          name="address"
          type="text"
          autoComplete="street-address"
          value={address}
          onChange={(event) => setAddress(event.target.value)}
          className={inputClass}
        />
      </div>

      <button
        type="submit"
        disabled={saving}
        className="w-full px-4 py-2 rounded-md bg-brasaland-ember text-white font-medium hover:bg-brasaland-ember/90 focus:outline-none focus:ring-2 focus:ring-brasaland-ember focus:ring-offset-2 transition-colors disabled:opacity-60"
      >
        {saving ? 'Saving…' : 'Save profile'}
      </button>
    </form>
  );
}

export default function ProfilePage() {
  return (
    <InventoryAuthGuard>
      <div className="mb-8">
        <h1 className="font-display text-3xl font-bold text-brasaland-charcoal">Profile</h1>
        <p className="text-sm text-brasaland-charcoal/60 mt-1">
          Update your name, phone, and address
        </p>
      </div>
      <ProfileContent />
    </InventoryAuthGuard>
  );
}
