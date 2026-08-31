export const STAFF_BASE_PATH = '/staff';

export function getStaffBasePath(): string {
  const configured = process.env.NEXT_PUBLIC_STAFF_BASE_PATH?.trim();
  return (configured || STAFF_BASE_PATH).replace(/\/$/, '');
}

/** Path under staff mount, e.g. `/staff/login`. */
export function staffPath(path: string): string {
  const base = getStaffBasePath();
  const suffix = path.startsWith('/') ? path : `/${path}`;
  return `${base}${suffix}`;
}

export function staffLoginPath(): string {
  return staffPath('/login');
}

/**
 * Same-origin staff API base for one BFF segment.
 * Uses explicit NEXT_PUBLIC_* when set; otherwise defaults under the staff mount.
 * Legacy env values like `/api/inventory` or `http://host:3003/api/inventory` are
 * normalized to include the staff mount so Next basePath rewrites match.
 */
export function resolveStaffApiBase(segment: string, envVar: string): string {
  const explicit = process.env[envVar]?.trim();
  if (!explicit) {
    return staffPath(`/api/${segment}`);
  }

  const trimmed = explicit.replace(/\/$/, '');
  const staffApiPrefix = `${getStaffBasePath()}/api/`;

  function withStaffMount(pathname: string): string {
    if (pathname.startsWith(staffApiPrefix)) {
      return pathname;
    }
    if (pathname.startsWith('/api/')) {
      return `${getStaffBasePath()}${pathname}`;
    }
    return pathname;
  }

  if (trimmed.startsWith('http://') || trimmed.startsWith('https://')) {
    const url = new URL(trimmed);
    url.pathname = withStaffMount(url.pathname);
    return `${url.origin}${url.pathname}`.replace(/\/$/, '');
  }

  if (trimmed.startsWith('/')) {
    return withStaffMount(trimmed);
  }

  return trimmed;
}
