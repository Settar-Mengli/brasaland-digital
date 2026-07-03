import { describe, expect, it } from 'vitest';

import {
  hasRegisterFormErrors,
  shouldHighlightBranch,
  validateRegisterForm,
} from './validate-register-form';

describe('shouldHighlightBranch', () => {
  it('highlights when origin is branch', () => {
    expect(shouldHighlightBranch('branch')).toBe(true);
  });

  it('does not highlight for customer or internal', () => {
    expect(shouldHighlightBranch('customer')).toBe(false);
    expect(shouldHighlightBranch('internal')).toBe(false);
    expect(shouldHighlightBranch('')).toBe(false);
  });
});

describe('validateRegisterForm', () => {
  const validValues = {
    title: 'Grill temperature issue',
    description: 'Customer reported undercooked steak',
    category: 'QUEJA_CLIENTE',
    origin: 'customer',
    branch: 'COL-01',
  };

  it('returns no errors for valid values', () => {
    expect(validateRegisterForm(validValues)).toEqual({});
    expect(hasRegisterFormErrors(validateRegisterForm(validValues))).toBe(false);
  });

  it('blocks submit when required fields are missing', () => {
    const errors = validateRegisterForm({
      title: '',
      description: '   ',
      category: '',
      origin: '',
      branch: '',
    });

    expect(errors.title).toBe('Title is required');
    expect(errors.description).toBe('Description is required');
    expect(errors.category).toBe('Category is required');
    expect(errors.origin).toBe('Origin is required');
    expect(errors.branch).toBe('Branch is required');
    expect(hasRegisterFormErrors(errors)).toBe(true);
  });

  it('rejects values outside CONTEXT vocabulary', () => {
    const errors = validateRegisterForm({
      ...validValues,
      category: 'INVALID',
      origin: 'hq',
      branch: 'NYC-01',
    });

    expect(errors.category).toBe('Category must be one of the allowed values');
    expect(errors.origin).toBe('Origin must be one of the allowed values');
    expect(errors.branch).toBe('Branch must be one of the allowed values');
  });
});
