import { NextResponse } from 'next/server';

import type { GuestChatRequest } from '@/lib/chat-types';
import { websiteServiceAccessToken } from '@/lib/service-token';
import {
  envFlagEnabled,
  isTurnstileVerificationEnabled,
  resolveClientIpFromRequest,
  verifyTurnstileToken,
} from '@/lib/turnstile-verify';

export async function POST(request: Request): Promise<NextResponse> {
  if (!envFlagEnabled('NEXT_PUBLIC_PUBLIC_CHAT_ENABLED')) {
    return NextResponse.json({ detail: 'Not found' }, { status: 404 });
  }

  let body: GuestChatRequest;
  try {
    body = (await request.json()) as GuestChatRequest;
  } catch {
    return NextResponse.json({ detail: 'Invalid JSON body' }, { status: 422 });
  }

  const question = typeof body.question === 'string' ? body.question.trim() : '';
  if (!question || question.length > 300) {
    return NextResponse.json({ detail: 'Invalid question' }, { status: 422 });
  }

  if (isTurnstileVerificationEnabled()) {
    const turnstileToken =
      typeof body.turnstileToken === 'string' ? body.turnstileToken.trim() : '';
    const remoteIp = resolveClientIpFromRequest(request);
    if (!turnstileToken || !(await verifyTurnstileToken(turnstileToken, remoteIp))) {
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
