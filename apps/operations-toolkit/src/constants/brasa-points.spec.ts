import { readFileSync, readdirSync, statSync } from 'node:fs';
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

function readWebsiteAppSources(): string {
  const appRoot = resolve(REPO_ROOT, 'uis/website/app');
  const files: string[] = [];

  function walk(dir: string): void {
    for (const entry of readdirSync(dir)) {
      const full = resolve(dir, entry);
      if (statSync(full).isDirectory()) {
        walk(full);
      } else if (entry.endsWith('.tsx') || entry.endsWith('.ts')) {
        files.push(readFileSync(full, 'utf-8'));
      }
    }
  }

  walk(appRoot);
  return files.join('\n');
}

describe('public content drift', () => {
  it('M4 website sources omit retired stale claims', () => {
    const combined = readWebsiteAppSources();
    const forbidden = [
      'Orlando',
      'free dishes',
      'no more paper cards',
      'confirmation email',
      'registration was successful',
    ];
    for (const phrase of forbidden) {
      expect(combined).not.toContain(phrase);
    }
  });

  it('public locations.json slugs match canonical set', () => {
    const locations = JSON.parse(
      readFileSync(resolve(REPO_ROOT, 'docs/public-knowledge-base/locations.json'), 'utf-8'),
    ) as { locations: Array<{ slug: string }> };
    const slugs = new Set(locations.locations.map((loc) => loc.slug));
    const canonical = new Set([
      'medellin_centro',
      'medellin_poblado',
      'medellin_laureles',
      'bogota_zona_rosa',
      'bogota_chapinero',
      'bogota_usaquen',
      'bogota_norte',
      'cali_san_fernando',
      'cali_granada',
      'cali_ciudad_jardin',
      'miami_brickell',
      'miami_wynwood',
      'miami_coral_gables',
      'miami_kendall',
    ]);
    expect(slugs).toEqual(canonical);
  });

  it('public loyalty.md includes tier thresholds', () => {
    const loyalty = readFileSync(
      resolve(REPO_ROOT, 'docs/public-knowledge-base/loyalty.md'),
      'utf-8',
    );
    expect(loyalty).toContain('Bronze (0');
    expect(loyalty).toContain('Silver (20');
    expect(loyalty).toContain('Gold (50');
  });

  it('brasa points page does not collect PII via form fields', () => {
    const info = readFileSync(
      resolve(REPO_ROOT, 'uis/website/app/brasa-points/_components/BrasaPointsInfo.tsx'),
      'utf-8',
    );
    expect(info).not.toContain('<form');
    expect(info).toContain('does not collect personal information');
  });
});
