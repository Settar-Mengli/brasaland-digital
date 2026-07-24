'use client';

import { type FormEvent, useState } from 'react';

import FormField, { formInputClassName } from '@/app/_components/FormField';
import {
  CATEGORY_LABELS,
  INCIDENT_CATEGORIES,
  INCIDENT_ORIGINS,
  type IncidentBranch,
  type IncidentCategory,
  type IncidentOrigin,
} from '@/lib/incident-types';
import { CreateIncidentError, createIncident } from '@/lib/incidents';
import {
  hasRegisterFormErrors,
  mapApiFieldErrors,
  shouldHighlightBranch,
  validateRegisterForm,
  type RegisterFormErrors,
  type RegisterFormValues,
} from '@/lib/validate-register-form';

const BRANCH_SELECT_ORDER: readonly IncidentBranch[] = [
  'Central',
  'COL-01',
  'COL-02',
  'COL-03',
  'COL-04',
  'COL-05',
  'COL-06',
  'COL-07',
  'COL-08',
  'COL-09',
  'COL-10',
  'FLA-01',
  'FLA-02',
  'FLA-03',
  'FLA-04',
];

const INITIAL_VALUES: RegisterFormValues = {
  title: '',
  description: '',
  category: '',
  origin: 'customer',
  branch: '',
};

export default function RegisterPage() {
  const [values, setValues] = useState<RegisterFormValues>(INITIAL_VALUES);
  const [fieldErrors, setFieldErrors] = useState<RegisterFormErrors>({});
  const [formError, setFormError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  const branchHighlighted = shouldHighlightBranch(values.origin);
  const inputClassName = formInputClassName();

  function updateField<K extends keyof RegisterFormValues>(field: K, value: RegisterFormValues[K]) {
    setValues((current) => ({ ...current, [field]: value }));
    setFieldErrors((current) => {
      if (!current[field]) {
        return current;
      }
      const next = { ...current };
      delete next[field];
      return next;
    });
    setFormError(null);
    setSuccessMessage(null);
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setFormError(null);
    setSuccessMessage(null);

    const clientErrors = validateRegisterForm(values);
    if (hasRegisterFormErrors(clientErrors)) {
      setFieldErrors(clientErrors);
      return;
    }

    setFieldErrors({});
    setSubmitting(true);

    try {
      await createIncident({
        title: values.title.trim(),
        description: values.description.trim(),
        category: values.category as IncidentCategory,
        origin: values.origin as IncidentOrigin,
        branch: values.branch as IncidentBranch,
      });

      setValues(INITIAL_VALUES);
      setSuccessMessage('Incident registered successfully.');
    } catch (submitError) {
      if (submitError instanceof CreateIncidentError) {
        const apiFieldErrors = mapApiFieldErrors(submitError.fieldErrors);
        if (hasRegisterFormErrors(apiFieldErrors)) {
          setFieldErrors(apiFieldErrors);
        }
        setFormError(submitError.message);
        return;
      }

      const message =
        submitError instanceof Error
          ? submitError.message
          : 'Something went wrong. Please try again.';
      setFormError(message);
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="max-w-3xl">
      <div className="mb-6">
        <h1 className="font-display text-3xl font-bold text-brasaland-charcoal">
          Register Incident
        </h1>
        <p className="text-sm text-brasaland-charcoal/60 mt-1">
          Log a new operational incident for tracking across Brasaland locations.
        </p>
      </div>

      <form
        onSubmit={handleSubmit}
        noValidate
        className="border border-brasaland-charcoal/10 rounded-xl p-6 bg-white shadow-sm space-y-5"
      >
        {formError ? (
          <p
            role="alert"
            className="text-sm text-brasaland-error bg-brasaland-error/10 rounded-md px-3 py-2"
          >
            {formError}
          </p>
        ) : null}

        {successMessage ? (
          <p
            role="status"
            className="text-sm text-brasaland-success bg-brasaland-success/10 rounded-md px-3 py-2"
          >
            {successMessage}
          </p>
        ) : null}

        <div className="grid gap-4 sm:grid-cols-2">
          <FormField id="title" label="Title" error={fieldErrors.title}>
            <input
              id="title"
              name="title"
              type="text"
              value={values.title}
              onChange={(event) => updateField('title', event.target.value)}
              className={inputClassName}
            />
          </FormField>

          <FormField id="category" label="Category" error={fieldErrors.category}>
            <select
              id="category"
              name="category"
              value={values.category}
              onChange={(event) => updateField('category', event.target.value)}
              className={inputClassName}
            >
              <option value="">Select category</option>
              {INCIDENT_CATEGORIES.map((category) => (
                <option key={category} value={category}>
                  {CATEGORY_LABELS[category]}
                </option>
              ))}
            </select>
          </FormField>

          <FormField id="origin" label="Origin" error={fieldErrors.origin}>
            <select
              id="origin"
              name="origin"
              value={values.origin}
              onChange={(event) => updateField('origin', event.target.value)}
              className={inputClassName}
            >
              {INCIDENT_ORIGINS.map((origin) => (
                <option key={origin} value={origin}>
                  {origin}
                </option>
              ))}
            </select>
          </FormField>

          <FormField
            id="branch"
            label="Branch"
            error={fieldErrors.branch}
            highlighted={branchHighlighted}
            helperText={
              branchHighlighted
                ? 'Reporting from a specific location — choose the branch where this incident occurred.'
                : undefined
            }
          >
            <select
              id="branch"
              name="branch"
              value={values.branch}
              onChange={(event) => updateField('branch', event.target.value)}
              className={inputClassName}
            >
              <option value="">Select branch</option>
              {BRANCH_SELECT_ORDER.map((branch) => (
                <option key={branch} value={branch}>
                  {branch}
                </option>
              ))}
            </select>
          </FormField>
        </div>

        <FormField id="description" label="Description" error={fieldErrors.description}>
          <textarea
            id="description"
            name="description"
            rows={4}
            value={values.description}
            onChange={(event) => updateField('description', event.target.value)}
            className={inputClassName}
          />
        </FormField>

        <button
          type="submit"
          disabled={submitting}
          className="px-4 py-2 rounded-md bg-brasaland-ember text-white font-medium hover:bg-brasaland-ember/90 focus:outline-none focus:ring-2 focus:ring-brasaland-ember focus:ring-offset-2 transition-colors disabled:opacity-60"
        >
          {submitting ? 'Registering…' : 'Register incident'}
        </button>
      </form>
    </div>
  );
}
