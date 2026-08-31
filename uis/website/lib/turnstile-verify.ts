/**
 * Server-only Turnstile verification helpers for the guest chat BFF.
 */

const SITEVERIFY_URL = 'https://challenges.cloudflare.com/turnstile/v0/siteverify';

export function envFlagEnabled(name: string): boolean {
  const raw = process.env[name]?.trim().toLowerCase();
  return raw === '1' || raw === 'true' || raw === 'yes' || raw === 'on';
}

export function isTurnstileVerificationEnabled(): boolean {
  return envFlagEnabled('TURNSTILE_ENABLED');
}

export function resolveClientIpFromRequest(request: Request): string | undefined {
  const forwarded = request.headers.get('x-forwarded-for');
  if (forwarded) {
    const first = forwarded.split(',')[0]?.trim();
    if (first) {
      return first;
    }
  }
  const realIp = request.headers.get('x-real-ip')?.trim();
  return realIp || undefined;
}

export async function verifyTurnstileToken(
  token: string,
  remoteIp?: string,
): Promise<boolean> {
  const secret = process.env.TURNSTILE_SECRET_KEY?.trim();
  if (!secret) {
    return false;
  }

  const params = new URLSearchParams({ secret, response: token });
  if (remoteIp) {
    params.set('remoteip', remoteIp);
  }

  try {
    const response = await fetch(SITEVERIFY_URL, {
      method: 'POST',
      body: params,
    });
    if (!response.ok) {
      return false;
    }
    const payload = (await response.json()) as { success?: boolean };
    return payload.success === true;
  } catch {
    return false;
  }
}
