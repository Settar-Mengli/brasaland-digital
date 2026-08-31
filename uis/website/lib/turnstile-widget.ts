/** Client-side helpers for guest chat Turnstile widget gating. */

export function envFlagEnabledFromPublic(value: string | undefined): boolean {
  const raw = value?.trim().toLowerCase();
  return raw === '1' || raw === 'true' || raw === 'yes' || raw === 'on';
}

export function publicChatEnabled(): boolean {
  return envFlagEnabledFromPublic(process.env.NEXT_PUBLIC_PUBLIC_CHAT_ENABLED);
}

export function turnstileWidgetEnabled(): boolean {
  return (
    publicChatEnabled() &&
    envFlagEnabledFromPublic(process.env.NEXT_PUBLIC_TURNSTILE_ENABLED) &&
    Boolean(process.env.NEXT_PUBLIC_TURNSTILE_SITE_KEY?.trim())
  );
}

export function turnstileSiteKey(): string | null {
  const siteKey = process.env.NEXT_PUBLIC_TURNSTILE_SITE_KEY?.trim();
  return siteKey || null;
}
