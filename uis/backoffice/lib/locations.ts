const ACCESS_TOKEN_KEY = 'brasaland_access_token';

export const LOCATION_SLUG_KEY = 'brasaland_location_slug';

export const LOCATION_MAP: Record<number, string> = {
  1: 'medellin_centro',
  2: 'medellin_poblado',
  3: 'medellin_laureles',
  4: 'bogota_zona_rosa',
  5: 'bogota_chapinero',
  6: 'bogota_usaquen',
  7: 'bogota_norte',
  8: 'cali_san_fernando',
  9: 'cali_granada',
  10: 'cali_ciudad_jardin',
  11: 'miami_brickell',
  12: 'miami_wynwood',
  13: 'miami_coral_gables',
  14: 'miami_kendall',
};

const LOCATION_LABELS: Record<string, string> = {
  medellin_centro: 'Medellín Centro',
  medellin_poblado: 'Medellín Poblado',
  medellin_laureles: 'Medellín Laureles',
  bogota_zona_rosa: 'Bogotá Zona Rosa',
  bogota_chapinero: 'Bogotá Chapinero',
  bogota_usaquen: 'Bogotá Usaquén',
  bogota_norte: 'Bogotá Norte',
  cali_san_fernando: 'Cali San Fernando',
  cali_granada: 'Cali Granada',
  cali_ciudad_jardin: 'Cali Ciudad Jardín',
  miami_brickell: 'Miami Brickell',
  miami_wynwood: 'Miami Wynwood',
  miami_coral_gables: 'Miami Coral Gables',
  miami_kendall: 'Miami Kendall',
};

export const LOCATION_OPTIONS = Object.values(LOCATION_MAP).map((slug) => ({
  value: slug,
  label: LOCATION_LABELS[slug] ?? slug,
}));

export function locationLabel(slug: string): string {
  return LOCATION_LABELS[slug] ?? slug;
}

export function locationSlug(formValue: number | string): string {
  const numeric = typeof formValue === 'string' ? Number(formValue) : formValue;
  const slug = LOCATION_MAP[numeric];
  if (!slug) {
    throw new Error(`Unknown location form value: ${String(formValue)}`);
  }
  return slug;
}

export function locationIdFromSlug(slug: string): number {
  const match = Object.entries(LOCATION_MAP).find(([, value]) => value === slug);
  if (!match) {
    throw new Error(`Unknown location slug: ${slug}`);
  }
  return Number(match[0]);
}

function decodeJwtPayload(token: string): Record<string, unknown> | null {
  const payloadSegment = token.split('.')[1];
  if (!payloadSegment) {
    return null;
  }
  try {
    const normalized = payloadSegment.replace(/-/g, '+').replace(/_/g, '/');
    const padded = normalized.padEnd(normalized.length + ((4 - (normalized.length % 4)) % 4), '=');
    const parsed: unknown = JSON.parse(atob(padded));
    if (typeof parsed === 'object' && parsed !== null && !Array.isArray(parsed)) {
      return parsed as Record<string, unknown>;
    }
    return null;
  } catch {
    return null;
  }
}

/** Read location_slug from the stored access JWT when session slug is missing. */
export function readLocationSlugFromAccessToken(): string | null {
  if (typeof window === 'undefined') {
    return null;
  }
  const token = localStorage.getItem(ACCESS_TOKEN_KEY);
  if (!token) {
    return null;
  }
  const payload = decodeJwtPayload(token);
  const slug = payload?.location_slug;
  if (typeof slug !== 'string' || !slug.trim()) {
    return null;
  }
  return slug.trim();
}

export function getSessionLocationId(): number {
  const sessionSlug = getSessionLocationSlug();
  if (sessionSlug) {
    return locationIdFromSlug(sessionSlug);
  }

  const tokenSlug = readLocationSlugFromAccessToken();
  if (tokenSlug) {
    setSessionLocationSlug(tokenSlug);
    return locationIdFromSlug(tokenSlug);
  }

  throw new Error('Session location is not set. Sign in again and choose a location.');
}

export function getSessionLocationSlug(): string {
  if (typeof window === 'undefined') {
    return '';
  }
  return sessionStorage.getItem(LOCATION_SLUG_KEY) ?? '';
}

export function setSessionLocationSlug(slug: string): void {
  if (typeof window === 'undefined') {
    return;
  }
  sessionStorage.setItem(LOCATION_SLUG_KEY, slug);
}

export function clearSessionLocationSlug(): void {
  if (typeof window === 'undefined') {
    return;
  }
  sessionStorage.removeItem(LOCATION_SLUG_KEY);
}
