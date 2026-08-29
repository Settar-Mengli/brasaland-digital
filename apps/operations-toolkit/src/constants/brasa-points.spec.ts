import { readFileSync } from 'node:fs';
import { dirname, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import { describe, expect, it } from 'vitest';

import {
  BRASA_POINTS_EARN_COP,
  BRASA_POINTS_EARN_USD,
  formatBrasaPointsEarnLine,
} from './brasa-points';

const REPO_ROOT = resolve(dirname(fileURLToPath(import.meta.url)), '../../../..');

describe('brasa-points earn rate', () => {
  it('formats the canonical earn line', () => {
    expect(formatBrasaPointsEarnLine()).toBe(
      'Accumulate 1 point for every $10,000 COP or $10 USD.',
    );
  });

  it('matches loyalty-program.md earn facts', () => {
    const manual = readFileSync(
      resolve(REPO_ROOT, 'docs/company-knowledge-base/loyalty-program.md'),
      'utf-8',
    );
    expect(manual).toContain('10,000 COP');
    expect(manual).toContain('10 USD');
    expect(BRASA_POINTS_EARN_USD).toBe(10);
    expect(BRASA_POINTS_EARN_COP).toBe(10000);
  });

  it('matches M1 public website copy', () => {
    const html = readFileSync(resolve(REPO_ROOT, 'apps/public-website/index.html'), 'utf-8');
    expect(html).toContain(formatBrasaPointsEarnLine());
  });

  it('matches M4 BrasaPointsSection source', () => {
    const source = readFileSync(
      resolve(REPO_ROOT, 'uis/website/app/_components/BrasaPointsSection.tsx'),
      'utf-8',
    );
    expect(source).toContain('formatBrasaPointsEarnLine');
    expect(source).toContain('@brasaland/operations-toolkit');
  });
});
