import type { IncidentCategory, IncidentOrigin } from './incident-types';
import { INCIDENT_BRANCHES, INCIDENT_CATEGORIES, INCIDENT_ORIGINS } from './incident-types';

export type RegisterFormField = 'title' | 'description' | 'category' | 'origin' | 'branch';

export type RegisterFormValues = {
  title: string;
  description: string;
  category: string;
  origin: string;
  branch: string;
};

export type RegisterFormErrors = Partial<Record<RegisterFormField, string>>;

export function shouldHighlightBranch(origin: string): boolean {
  return origin === 'branch';
}

export function validateRegisterForm(values: RegisterFormValues): RegisterFormErrors {
  const errors: RegisterFormErrors = {};

  if (!values.title.trim()) {
    errors.title = 'Title is required';
  }

  if (!values.description.trim()) {
    errors.description = 'Description is required';
  }

  if (!values.category) {
    errors.category = 'Category is required';
  } else if (!INCIDENT_CATEGORIES.includes(values.category as IncidentCategory)) {
    errors.category = 'Category must be one of the allowed values';
  }

  if (!values.origin) {
    errors.origin = 'Origin is required';
  } else if (!INCIDENT_ORIGINS.includes(values.origin as IncidentOrigin)) {
    errors.origin = 'Origin must be one of the allowed values';
  }

  if (!values.branch) {
    errors.branch = 'Branch is required';
  } else if (!INCIDENT_BRANCHES.includes(values.branch as (typeof INCIDENT_BRANCHES)[number])) {
    errors.branch = 'Branch must be one of the allowed values';
  }

  return errors;
}

export function hasRegisterFormErrors(errors: RegisterFormErrors): boolean {
  return Object.keys(errors).length > 0;
}

export function mapApiFieldErrors(
  fieldErrors: ReadonlyArray<{ field: string; message: string }>,
): RegisterFormErrors {
  const allowedFields = new Set<RegisterFormField>([
    'title',
    'description',
    'category',
    'origin',
    'branch',
  ]);
  const errors: RegisterFormErrors = {};

  for (const error of fieldErrors) {
    if (allowedFields.has(error.field as RegisterFormField)) {
      errors[error.field as RegisterFormField] = error.message;
    }
  }

  return errors;
}
