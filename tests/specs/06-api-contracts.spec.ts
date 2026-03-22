import { test, expect } from '@playwright/test';

test.describe('API Contracts', () => {
  test('GET /health returns healthy', async ({ page }) => {
    const r = await page.request.get('/health');
    expect(r.status()).toBe(200);
    const d = await r.json();
    expect(d.status).toBe('healthy');
  });

  test('GET /api/ollama/status returns online field', async ({ page }) => {
    const r = await page.request.get('/api/ollama/status');
    expect(r.status()).toBe(200);
    const d = await r.json();
    expect(d).toHaveProperty('online');
    expect(d).toHaveProperty('model_count');
  });

  test('GET /api/auto1111/status returns online field', async ({ page }) => {
    const r = await page.request.get('/api/auto1111/status');
    expect(r.status()).toBe(200);
    const d = await r.json();
    expect(d).toHaveProperty('online');
    expect(d).toHaveProperty('model_count');
  });

  test('GET /api/conversations returns sessions array', async ({ page }) => {
    const r = await page.request.get('/api/conversations');
    expect(r.status()).toBe(200);
    const d = await r.json();
    expect(d).toHaveProperty('sessions');
    expect(Array.isArray(d.sessions)).toBe(true);
  });

  test('POST /api/chat — non-streaming returns response and session_id', async ({ page }) => {
    const r = await page.request.post('/api/chat', {
      data: { message: 'Reply with only the word: OK', model: null },
    });
    expect(r.status()).toBe(200);
    const d = await r.json();
    expect(d).toHaveProperty('response');
    expect(d).toHaveProperty('session_id');
    expect(typeof d.response).toBe('string');
    expect(d.response.length).toBeGreaterThan(0);
  });

  test('POST /api/chat — session_id is returned and reusable', async ({ page }) => {
    const r1 = await page.request.post('/api/chat', {
      data: { message: 'My name is TestBot' },
    });
    const d1 = await r1.json();
    const sessionId = d1.session_id;
    expect(typeof sessionId).toBe('string');

    // Second message in same session
    const r2 = await page.request.post('/api/chat', {
      data: { message: 'What is my name?', session_id: sessionId },
    });
    expect(r2.status()).toBe(200);
    const d2 = await r2.json();
    expect(d2.session_id).toBe(sessionId);
  });

  test('GET /api/conversations/{id} returns message history', async ({ page }) => {
    // Create a session
    const r = await page.request.post('/api/chat', {
      data: { message: 'History test' },
    });
    const { session_id } = await r.json();

    // Fetch conversation
    const r2 = await page.request.get(`/api/conversations/${session_id}`);
    expect(r2.status()).toBe(200);
    const d = await r2.json();
    expect(d).toHaveProperty('messages');
    expect(Array.isArray(d.messages)).toBe(true);
    expect(d.messages.length).toBeGreaterThan(0);
    expect(d.messages[0]).toHaveProperty('role');
    expect(d.messages[0]).toHaveProperty('content');
  });

  test('PATCH /api/conversations/{id} renames session', async ({ page }) => {
    const r = await page.request.post('/api/chat', { data: { message: 'Rename me' } });
    const { session_id } = await r.json();

    const r2 = await page.request.patch(`/api/conversations/${session_id}`, {
      data: { title: 'Renamed Title' },
    });
    expect(r2.status()).toBe(200);
    const d = await r2.json();
    expect(d.title).toBe('Renamed Title');
  });

  test('DELETE /api/conversations/{id} removes session', async ({ page }) => {
    const r = await page.request.post('/api/chat', { data: { message: 'Delete me' } });
    const { session_id } = await r.json();

    const r2 = await page.request.delete(`/api/conversations/${session_id}`);
    expect(r2.status()).toBe(204);

    // Session should no longer exist
    const r3 = await page.request.get(`/api/conversations/${session_id}`);
    // Should return 200 but with empty messages (session deleted)
    const d = await r3.json();
    expect(d.messages).toHaveLength(0);
  });

  test('GET /api/conversations/{id}/export?format=markdown works', async ({ page }) => {
    const r = await page.request.post('/api/chat', { data: { message: 'Export me' } });
    const { session_id } = await r.json();

    const r2 = await page.request.get(`/api/conversations/${session_id}/export?format=markdown`);
    expect(r2.status()).toBe(200);
    const text = await r2.text();
    expect(text).toContain('Export me');
  });

  test('POST /api/personas creates and DELETE removes', async ({ page }) => {
    const r = await page.request.post('/api/personas', {
      data: { name: 'TestPersona', system_prompt: 'You are a test persona', icon: '🧪' },
    });
    expect(r.status()).toBe(201);
    const { id } = await r.json();
    expect(typeof id).toBe('number');

    const r2 = await page.request.delete(`/api/personas/${id}`);
    expect(r2.status()).toBe(200);
  });

  test('POST /api/upload rejects disallowed extension', async ({ page }) => {
    const r = await page.request.post('/api/upload', {
      multipart: {
        file: { name: 'evil.exe', mimeType: 'application/octet-stream', buffer: Buffer.from('evil') },
      },
    });
    expect(r.status()).toBe(415);
  });

  test('POST /api/upload accepts .txt file', async ({ page }) => {
    const r = await page.request.post('/api/upload', {
      multipart: {
        file: { name: 'test.txt', mimeType: 'text/plain', buffer: Buffer.from('Hello world') },
      },
    });
    expect(r.status()).toBe(200);
    const d = await r.json();
    expect(d).toHaveProperty('upload_id');
    expect(d).toHaveProperty('filename');
  });
});
