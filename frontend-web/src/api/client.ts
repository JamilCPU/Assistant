/**
 * API client for the FastAPI backend.
 *
 * In dev mode Vite proxies /api/* to localhost:8000 so we can use
 * relative URLs and avoid CORS issues.
 */

// ── Types ────────────────────────────────────────────────────────────────

export interface ChatRequest {
  message: string;
  session_id?: string | null;
  model?: string | null;
  speak?: boolean;
  system_prompt?: string | null;
}

export interface ToolCall {
  name: string;
  arguments: Record<string, unknown>;
}

export interface ChatResponse {
  response: string;
  session_id: string;
  tool_calls?: ToolCall[] | null;
  audio_url?: string | null;
}

export interface SessionInfo {
  session_id: string;
  created_at: string;
  last_activity: string;
  title?: string | null;
}

export interface SessionsListResponse {
  sessions: SessionInfo[];
}

export interface ConversationMessage {
  id: number;
  role: string;
  content: string;
  timestamp: string;
  metadata?: Record<string, unknown> | null;
}

export interface ConversationResponse {
  session_id: string;
  messages: ConversationMessage[];
}

export interface ModelsResponse {
  chat: string[];
  image: string[];
  loras: string[];
  tts: string[];
}

export interface ImageGenerateRequest {
  prompt: string;
  negative_prompt?: string | null;
  model?: string | null;
  width?: number;
  height?: number;
  steps?: number;
  cfg_scale?: number;
  sampler?: string | null;
  lora?: string[] | null;
}

export interface ImageGenerateResponse {
  image_path: string;
  image_url?: string | null;
  metadata: Record<string, unknown>;
  filename: string;
}

// ── Helpers ──────────────────────────────────────────────────────────────

const BASE = ''; // Vite proxy handles /api/* in dev

function headers(apiKey?: string): HeadersInit {
  const h: Record<string, string> = { 'Content-Type': 'application/json' };
  if (apiKey) h['X-API-Key'] = apiKey;
  return h;
}

async function request<T>(
  method: string,
  path: string,
  body?: unknown,
  apiKey?: string,
): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    method,
    headers: headers(apiKey),
    body: body ? JSON.stringify(body) : undefined,
  });
  if (!res.ok) {
    const text = await res.text().catch(() => res.statusText);
    throw new Error(`${res.status}: ${text}`);
  }
  return res.json();
}

// ── Public API ───────────────────────────────────────────────────────────

export function chat(req: ChatRequest, apiKey?: string) {
  return request<ChatResponse>('POST', '/api/chat', req, apiKey);
}

export function generateImage(req: ImageGenerateRequest, apiKey?: string) {
  return request<ImageGenerateResponse>('POST', '/api/image/generate', req, apiKey);
}

export function listModels(apiKey?: string) {
  return request<ModelsResponse>('GET', '/api/models', undefined, apiKey);
}

export function listConversations(apiKey?: string) {
  return request<SessionsListResponse>('GET', '/api/conversations', undefined, apiKey);
}

export function getConversation(sessionId: string, apiKey?: string) {
  return request<ConversationResponse>('GET', `/api/conversations/${sessionId}`, undefined, apiKey);
}
