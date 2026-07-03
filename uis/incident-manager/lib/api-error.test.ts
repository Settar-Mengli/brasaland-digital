import { describe, expect, it } from 'vitest';

import { parseApiError } from './api-error';

function mockResponse(body: unknown, status = 400, statusText = 'Bad Request'): Response {
  return new Response(JSON.stringify(body), {
    status,
    statusText,
    headers: { 'Content-Type': 'application/json' },
  });
}

describe('parseApiError', () => {
  it('returns string detail from FastAPI', async () => {
    const message = await parseApiError(
      mockResponse({ detail: 'open cannot move directly to resolved' }, 400),
    );
    expect(message).toBe('open cannot move directly to resolved');
  });

  it('formats validation array detail', async () => {
    const message = await parseApiError(
      mockResponse({
        detail: [
          { loc: ['body', 'title'], msg: 'Field required', type: 'missing' },
          { loc: ['body', 'branch'], msg: 'branch is required', type: 'value_error' },
        ],
      }),
    );
    expect(message).toBe('title: Field required; branch: branch is required');
  });

  it('falls back to status text when detail is missing', async () => {
    const message = await parseApiError(
      new Response(null, { status: 500, statusText: 'Internal Server Error' }),
    );
    expect(message).toBe('Internal Server Error');
  });
});
