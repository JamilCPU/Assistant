import type { APIRequestContext } from '@playwright/test';

export const API_URL = 'http://localhost:8000';
export const API_KEY = process.env.API_KEY ?? '';

function headers(): Record<string, string> {
  const h: Record<string, string> = { 'Content-Type': 'application/json' };
  if (API_KEY) h['X-API-Key'] = API_KEY;
  return h;
}

// ── Conversation helpers ─────────────────────────────────────────────────

export async function getConversations(request: APIRequestContext) {
  return request.get(`${API_URL}/api/conversations`, { headers: headers() });
}

export async function getConversation(request: APIRequestContext, id: string) {
  return request.get(`${API_URL}/api/conversations/${id}`, { headers: headers() });
}

/**
 * Returns the most recently created SessionInfo from the backend,
 * or null if there are no sessions.
 */
export async function getLatestSession(request: APIRequestContext) {
  const res = await getConversations(request);
  const data = await res.json();
  const sessions: Array<{ session_id: string; created_at: string; last_activity: string; title?: string }> =
    data.sessions ?? [];
  if (sessions.length === 0) return null;
  return sessions.sort((a, b) => b.last_activity.localeCompare(a.last_activity))[0];
}

// ── Model helpers ────────────────────────────────────────────────────────

export async function getModels(request: APIRequestContext) {
  return request.get(`${API_URL}/api/models`, { headers: headers() });
}

// ── Image helpers ────────────────────────────────────────────────────────

export async function getImages(request: APIRequestContext) {
  return request.get(`${API_URL}/api/images`, { headers: headers() });
}

// ── Health check ─────────────────────────────────────────────────────────

export async function checkHealth(request: APIRequestContext) {
  return request.get(`${API_URL}/health`);
}
