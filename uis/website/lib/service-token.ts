/**
 * Cached service-token acquisition for the website BFF (server-only).
 */

type CachedServiceToken = {
  accessToken: string;
  renewAtMs: number;
  credentialsKey: string;
};

let cachedToken: CachedServiceToken | null = null;

function credentialsKey(clientId: string, authOrigin: string): string {
  return `${clientId}:${authOrigin}`;
}

function readCredentials(): {
  clientId: string;
  clientSecret: string;
  authOrigin: string;
} {
  const clientId = process.env.WEBSITE_KNOWLEDGE_CLIENT_ID?.trim() ?? '';
  const clientSecret = process.env.WEBSITE_KNOWLEDGE_CLIENT_SECRET?.trim() ?? '';
  const authOrigin = (process.env.AUTH_API_ORIGIN ?? 'http://localhost:8002').replace(/\/$/, '');
  if (!clientId || !clientSecret) {
    throw new Error('WEBSITE_KNOWLEDGE_CLIENT_ID/SECRET are not configured');
  }
  return { clientId, clientSecret, authOrigin };
}

async function acquireServiceToken(
  clientId: string,
  clientSecret: string,
  authOrigin: string,
): Promise<CachedServiceToken> {
  const basic = Buffer.from(`${clientId}:${clientSecret}`).toString('base64');
  const response = await fetch(`${authOrigin}/auth/service-token`, {
    method: 'POST',
    headers: { Authorization: `Basic ${basic}` },
  });
  if (!response.ok) {
    throw new Error(`service-token acquisition failed with HTTP ${response.status}`);
  }
  const payload = (await response.json()) as {
    access_token?: string;
    token_type?: string;
    expires_in?: number;
  };
  const accessToken = payload.access_token;
  const tokenType = payload.token_type;
  const expiresIn = payload.expires_in;
  if (
    !accessToken ||
    tokenType?.toLowerCase() !== 'bearer' ||
    typeof expiresIn !== 'number' ||
    expiresIn <= 0
  ) {
    throw new Error('service-token acquisition returned an invalid response');
  }
  const renewLeadMs = Math.min(30_000, expiresIn * 1000 * 0.1);
  return {
    accessToken,
    renewAtMs: Date.now() + expiresIn * 1000 - renewLeadMs,
    credentialsKey: credentialsKey(clientId, authOrigin),
  };
}

export async function websiteServiceAccessToken(): Promise<string> {
  const { clientId, clientSecret, authOrigin } = readCredentials();
  const key = credentialsKey(clientId, authOrigin);
  if (
    cachedToken !== null &&
    cachedToken.credentialsKey === key &&
    Date.now() < cachedToken.renewAtMs
  ) {
    return cachedToken.accessToken;
  }
  cachedToken = await acquireServiceToken(clientId, clientSecret, authOrigin);
  return cachedToken.accessToken;
}

export function clearWebsiteServiceTokenCache(): void {
  cachedToken = null;
}
