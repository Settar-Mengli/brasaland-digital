import { describe, expect, it } from 'vitest';

import { getStockLevel } from './stock-level';

describe('getStockLevel', () => {
  it('returns empty at zero stock', () => {
    expect(getStockLevel(0)).toEqual({ level: 'empty', label: 'Empty' });
  });

  it('returns low below healthy threshold', () => {
    expect(getStockLevel(19)).toEqual({ level: 'low', label: 'Low' });
    expect(getStockLevel(1)).toEqual({ level: 'low', label: 'Low' });
  });

  it('returns healthy at threshold and above', () => {
    expect(getStockLevel(20)).toEqual({ level: 'healthy', label: 'OK' });
    expect(getStockLevel(80)).toEqual({ level: 'healthy', label: 'OK' });
  });
});
