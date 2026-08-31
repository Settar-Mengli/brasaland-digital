import { afterEach, describe, expect, it, vi } from 'vitest';

vi.mock('./auth', () => ({
  getAccessToken: vi.fn(),
}));

vi.mock('./session', () => ({
  handleUnauthorized: vi.fn(),
}));

vi.mock('./api-error', () => ({
  parseApiError: vi.fn(async () => 'api error'),
}));

import { getAccessToken } from './auth';
import { askKnowledge } from './rag';

describe('askKnowledge', () => {
  afterEach(() => {
    vi.unstubAllGlobals();
    vi.clearAllMocks();
  });

  it('posts the question with a Bearer token and returns the answer', async () => {
    vi.stubEnv('NEXT_PUBLIC_KNOWLEDGE_API_URL', 'http://localhost/staff/api/knowledge');
    vi.mocked(getAccessToken).mockReturnValue('tok');
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => ({ answer: 'Gold needs 50+ points.' }),
    });
    vi.stubGlobal('fetch', fetchMock);

    const answer = await askKnowledge('How many points for Gold?');

    expect(answer).toBe('Gold needs 50+ points.');
    expect(fetchMock).toHaveBeenCalledWith(
      'http://localhost/staff/api/knowledge/query',
      expect.objectContaining({
        method: 'POST',
        headers: expect.objectContaining({
          Authorization: 'Bearer tok',
        }),
      }),
    );
  });

  it('throws when not authenticated', async () => {
    vi.stubEnv('NEXT_PUBLIC_KNOWLEDGE_API_URL', 'http://localhost/staff/api/knowledge');
    vi.mocked(getAccessToken).mockReturnValue(null);
    await expect(askKnowledge('x')).rejects.toThrow('Not authenticated');
  });
});
