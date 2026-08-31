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
 */
export function resolveStaffApiBase(segment: string, envVar: string): string {
  const explicit = process.env[envVar]?.trim();
  if (explicit) {
    return explicit.replace(/\/$/, '');
  }
  return staffPath(`/api/${segment}`);
}
