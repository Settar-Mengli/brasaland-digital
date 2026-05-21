'use client';

import { useRef } from 'react';
import { useRouter } from 'next/navigation';
import { STATUS_LABELS, STAGE_LABELS } from '@/lib/api';

interface FilterBarProps {
  /** Current filter values parsed from URL search params. */
  defaults: {
    status?: string;
    stage?: string;
    search?: string;
  };
}

/**
 * Form-based filter bar. The URL is the single source of truth for filter
 * state; this component only writes to it. Status and stage selects
 * auto-submit on change for instant-filter UX; the search input requires
 * pressing Enter or clicking Apply.
 */
export default function FilterBar({ defaults }: FilterBarProps) {
  const router = useRouter();
  const formRef = useRef<HTMLFormElement>(null);

  function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const formData = new FormData(event.currentTarget);
    const params = new URLSearchParams();
    for (const [key, value] of formData.entries()) {
      if (typeof value === 'string' && value !== '') {
        params.set(key, value);
      }
    }
    // Reset to page 1 on any filter change — omitted entirely from URL
    params.delete('page');
    const query = params.toString();
    router.push(query ? `/?${query}` : '/');
  }

  function submitNow() {
    formRef.current?.requestSubmit();
  }

  const inputClass =
    'border border-brasaland-charcoal/20 bg-brasaland-ivory px-3 py-2 rounded-md text-brasaland-charcoal focus:outline-none focus:ring-2 focus:ring-brasaland-ember focus:border-brasaland-ember';

  return (
    <form
      ref={formRef}
      onSubmit={handleSubmit}
      aria-labelledby="filters-heading"
      className="rounded-lg border border-brasaland-charcoal/10 bg-brasaland-cream/40 p-4 mb-6"
    >
      <h2 id="filters-heading" className="sr-only">
        Filter candidates
      </h2>
      <div className="flex flex-col gap-3 md:flex-row md:items-end">
        <label className="flex flex-col gap-1 text-sm font-medium text-brasaland-charcoal">
          Status
          <select
            name="status"
            defaultValue={defaults.status ?? ''}
            onChange={submitNow}
            className={inputClass}
          >
            <option value="">All statuses</option>
            {Object.entries(STATUS_LABELS).map(([value, label]) => (
              <option key={value} value={value}>
                {label}
              </option>
            ))}
          </select>
        </label>

        <label className="flex flex-col gap-1 text-sm font-medium text-brasaland-charcoal">
          Stage
          <select
            name="stage"
            defaultValue={defaults.stage ?? ''}
            onChange={submitNow}
            className={inputClass}
          >
            <option value="">All stages</option>
            {Object.entries(STAGE_LABELS).map(([value, label]) => (
              <option key={value} value={value}>
                {label}
              </option>
            ))}
          </select>
        </label>

        <label className="flex flex-col gap-1 text-sm font-medium text-brasaland-charcoal md:flex-1">
          Search
          <input
            type="search"
            name="search"
            defaultValue={defaults.search ?? ''}
            placeholder="Name, email, or position"
            className={inputClass}
          />
        </label>

        <button
          type="submit"
          className="px-4 py-2 rounded-md bg-brasaland-ember text-white font-medium hover:bg-brasaland-ember/90 focus:outline-none focus:ring-2 focus:ring-brasaland-ember focus:ring-offset-2 focus:ring-offset-brasaland-cream transition-colors"
        >
          Apply
        </button>
      </div>
    </form>
  );
}
