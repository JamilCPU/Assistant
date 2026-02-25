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

// ── Ollama types ─────────────────────────────────────────────────────────

export interface OllamaStatusResponse {
  online: boolean;
  model_count: number;
}

export interface OllamaModelInfo {
  name: string;
  size: number;
  modified_at: string;
  family: string;
  parameter_size: string;
  quantization_level: string;
}

export interface OllamaModelsListResponse {
  models: OllamaModelInfo[];
}

export interface OllamaModelDetail {
  name: string;
  family: string;
  parameter_size: string;
  quantization_level: string;
  format: string;
  template: string;
  system: string;
  license: string;
  modelfile: string;
}

export interface OllamaPullProgress {
  status: string;
  completed: number;
  total: number;
}

// ── Streaming chat types ─────────────────────────────────────────────────

export interface StreamTokenEvent {
  content: string;
}

export interface StreamToolCallEvent {
  name: string;
  arguments: Record<string, unknown>;
}

export interface StreamDoneEvent {
  session_id: string;
  audio_url: string | null;
}

// ── Helpers ──────────────────────────────────────────────────────────────

const BASE = ''; // Vite proxy handles /api/* in dev

function buildHeaders(apiKey?: string): HeadersInit {
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
    headers: buildHeaders(apiKey),
    body: body ? JSON.stringify(body) : undefined,
  });
  if (!res.ok) {
    const text = await res.text().catch(() => res.statusText);
    throw new Error(`${res.status}: ${text}`);
  }
  return res.json();
}

// ── Public API – existing endpoints ──────────────────────────────────────

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

// ── Public API – Ollama endpoints ────────────────────────────────────────

export function ollamaStatus(apiKey?: string) {
  return request<OllamaStatusResponse>('GET', '/api/ollama/status', undefined, apiKey);
}

export function ollamaModels(apiKey?: string) {
  return request<OllamaModelsListResponse>('GET', '/api/ollama/models', undefined, apiKey);
}

export function ollamaModelInfo(name: string, apiKey?: string) {
  return request<OllamaModelDetail>('GET', `/api/ollama/models/${encodeURIComponent(name)}`, undefined, apiKey);
}

export async function ollamaDelete(name: string, apiKey?: string) {
  const res = await fetch(`${BASE}/api/ollama/models/${encodeURIComponent(name)}`, {
    method: 'DELETE',
    headers: buildHeaders(apiKey),
  });
  if (!res.ok) {
    const text = await res.text().catch(() => res.statusText);
    throw new Error(`${res.status}: ${text}`);
  }
}

/**
 * Pull a model from the Ollama library.
 * Returns a ReadableStream of SSE events with progress info.
 */
export function ollamaPull(
  name: string,
  onProgress: (p: OllamaPullProgress) => void,
  onDone: () => void,
  onError: (err: string) => void,
  apiKey?: string,
): AbortController {
  const controller = new AbortController();

  fetch(`${BASE}/api/ollama/pull`, {
    method: 'POST',
    headers: buildHeaders(apiKey),
    body: JSON.stringify({ name }),
    signal: controller.signal,
  })
    .then(async (res) => {
      if (!res.ok || !res.body) {
        const text = await res.text().catch(() => res.statusText);
        onError(text);
        return;
      }
      const reader = res.body.getReader();
      const decoder = new TextDecoder();
      let buffer = '';

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop() ?? '';

        for (const line of lines) {
          if (line.startsWith('data:')) {
            const jsonStr = line.slice(5).trim();
            if (!jsonStr) continue;
            try {
              const data = JSON.parse(jsonStr);
              if (data.error) {
                onError(data.error);
              } else if (data.status === 'success') {
                onDone();
              } else {
                onProgress(data as OllamaPullProgress);
              }
            } catch {
              // ignore malformed lines
            }
          }
        }
      }
      onDone();
    })
    .catch((err) => {
      if (err.name !== 'AbortError') {
        onError(String(err));
      }
    });

  return controller;
}

// ── Public API – streaming chat ──────────────────────────────────────────

export interface ChatStreamCallbacks {
  onToken: (content: string) => void;
  onToolCall?: (tc: StreamToolCallEvent) => void;
  onDone: (info: StreamDoneEvent) => void;
  onError: (error: string) => void;
}

/**
 * Stream a chat response via SSE.
 * Returns an AbortController to cancel the stream.
 */
export function chatStream(
  req: ChatRequest,
  callbacks: ChatStreamCallbacks,
  apiKey?: string,
): AbortController {
  const controller = new AbortController();

  fetch(`${BASE}/api/chat/stream`, {
    method: 'POST',
    headers: buildHeaders(apiKey),
    body: JSON.stringify(req),
    signal: controller.signal,
  })
    .then(async (res) => {
      if (!res.ok || !res.body) {
        const text = await res.text().catch(() => res.statusText);
        callbacks.onError(text);
        return;
      }

      const reader = res.body.getReader();
      const decoder = new TextDecoder();
      let buffer = '';
      let currentEvent = '';

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop() ?? '';

        for (const line of lines) {
          if (line.startsWith('event:')) {
            currentEvent = line.slice(6).trim();
          } else if (line.startsWith('data:')) {
            const jsonStr = line.slice(5).trim();
            if (!jsonStr) continue;
            try {
              const data = JSON.parse(jsonStr);

              switch (currentEvent) {
                case 'token':
                  callbacks.onToken(data.content);
                  break;
                case 'tool_call':
                  callbacks.onToolCall?.(data as StreamToolCallEvent);
                  break;
                case 'done':
                  callbacks.onDone(data as StreamDoneEvent);
                  break;
                case 'error':
                  callbacks.onError(data.error ?? 'Unknown streaming error');
                  break;
              }
            } catch {
              // ignore malformed JSON
            }
            currentEvent = '';
          }
        }
      }
    })
    .catch((err) => {
      if (err.name !== 'AbortError') {
        callbacks.onError(String(err));
      }
    });

  return controller;
}
