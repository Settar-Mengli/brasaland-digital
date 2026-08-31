import { afterEach, describe, expect, it } from 'vitest';

import { turnstileWidgetEnabled } from './turnstile-widget';

describe('turnstile-widget', () => {
  const originalEnv = { ...process.env };

  afterEach(() => {
    process.env = { ...originalEnv };
  });

  it('turnstileWidgetEnabled requires chat, enabled flag, and site key', () => {
    process.env.NEXT_PUBLIC_PUBLIC_CHAT_ENABLED = 'true';
    process.env.NEXT_PUBLIC_TURNSTILE_ENABLED = 'true';
    process.env.NEXT_PUBLIC_TURNSTILE_SITE_KEY = '1x00000000000000000000AA';
    expect(turnstileWidgetEnabled()).toBe(true);

    process.env.NEXT_PUBLIC_TURNSTILE_ENABLED = 'false';
    expect(turnstileWidgetEnabled()).toBe(false);
  });
});
