import { NextResponse } from 'next/server';

import { websiteServiceAccessToken } from '@/lib/service-token';
import type { GuestChatRequest } from '@/lib/chat-types';

function envFlagEnabled(name: string): boolean {
  const raw = process.env[name]?.trim().toLowerCase();
  return raw === '1' || raw === 'true' || raw === 'yes' || raw === 'on';
}

async function verifyTurnstileToken(token: string): Promise<boolean> {
  const secret = process.env.TURNSTILE_SECRET_KEY?.trim();
  if (!secret) {
    return false;
  }
  const response = await fetch('https://challenges.cloudflare.com/turnstile/v0/siteverify', {
    method: 'POST',
    body: new URLSearchParams({ secret, response: token }),
  });
  if (!response.ok) {
    return false;
  }
  const payload = (await response.json()) as { success?: boolean };
  return payload.success === true;
}

export async function POST(request: Request): Promise<NextResponse> {
  if (!envFlagEnabled('NEXT_PUBLIC_PUBLIC_CHAT_ENABLED')) {
    return NextResponse.json({ detail: 'Not found' }, { status: 404 });
  }

  let body: GuestChatRequest & { turnstileToken?: string };
  try {
    body = (await request.json()) as GuestChatRequest & { turnstileToken?: string };
  } catch {
    return NextResponse.json({ detail: 'Invalid JSON body' }, { status: 422 });
  }

  const question = typeof body.question === 'string' ? body.question.trim() : '';
  if (!question || question.length > 300) {
    return NextResponse.json({ detail: 'Invalid question' }, { status: 422 });
  }

  if (envFlagEnabled('TURNSTILE_ENABLED')) {
    const turnstileToken =
      typeof body.turnstileToken === 'string' ? body.turnstileToken.trim() : '';
    if (!turnstileToken || !(await verifyTurnstileToken(turnstileToken))) {
      return NextResponse.json(
        { detail: 'Turnstile verification failed' },
        {
          status: 403,
        },
      );
    }
  }

  const knowledgeOrigin = (
    process.env.PUBLIC_KNOWLEDGE_API_ORIGIN ?? 'http://localhost:8015'
  ).replace(/\/$/, '');

  try {
    const accessToken = await websiteServiceAccessToken();
    const upstream = await fetch(`${knowledgeOrigin}/public/knowledge/query`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${accessToken}`,
      },
      body: JSON.stringify({ question }),
    });

    if (!upstream.ok) {
      let detail = 'Unable to get an answer right now.';
      try {
        const errorBody = (await upstream.json()) as { detail?: string };
        if (errorBody.detail?.trim()) {
          detail = errorBody.detail.trim();
        }
      } catch {
        // ignore
      }
      return NextResponse.json(
        { detail },
        { status: upstream.status >= 400 ? upstream.status : 502 },
      );
    }

    const data = (await upstream.json()) as { answer?: string };
    const answer = typeof data.answer === 'string' ? data.answer : '';
    if (!answer) {
      return NextResponse.json({ detail: 'Unable to get an answer right now.' }, { status: 502 });
    }

    return NextResponse.json(
      { answer },
      {
        status: 200,
        headers: { 'Cache-Control': 'no-store' },
      },
    );
  } catch {
    return NextResponse.json({ detail: 'Unable to get an answer right now.' }, { status: 502 });
  }
}
