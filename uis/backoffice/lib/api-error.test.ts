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
      mockResponse({ detail: 'Incorrect email or password' }, 401, 'Unauthorized'),
    );
    expect(message).toBe('Incorrect email or password');
  });

  it('formats validation array detail', async () => {
    const message = await parseApiError(
      mockResponse({
        detail: [
          {
            loc: ['body', 'quantity'],
            msg: 'Input should be greater than 0',
            type: 'greater_than',
          },
          { loc: ['body', 'reason'], msg: 'Field required', type: 'missing' },
        ],
      }),
    );
    expect(message).toBe('quantity: Input should be greater than 0; reason: Field required');
  });

  it('falls back to status text when detail is missing', async () => {
    const message = await parseApiError(
      new Response(null, { status: 500, statusText: 'Internal Server Error' }),
    );
    expect(message).toBe('Internal Server Error');
  });
});
