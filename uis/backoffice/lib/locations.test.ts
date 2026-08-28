import { describe, expect, it } from 'vitest';

import { LOCATION_MAP, locationSlug } from './locations';

describe('locations', () => {
  it('maps all 14 form values to slugs', () => {
    expect(Object.keys(LOCATION_MAP)).toHaveLength(14);
    expect(locationSlug(1)).toBe('medellin_centro');
    expect(locationSlug('14')).toBe('miami_kendall');
  });

  it('throws for unknown form values', () => {
    expect(() => locationSlug(0)).toThrow();
    expect(() => locationSlug(99)).toThrow();
  });
});
