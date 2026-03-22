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
  tts_voice?: string | null;
  upload_ids?: string[] | null;
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
  seed?: number;
  batch_size?: number;
  batch_count?: number;
  restore_faces?: boolean;
  tiling?: boolean;
  clip_skip?: number;
  enable_hr?: boolean;
  hr_scale?: number;
  hr_upscaler?: string | null;
  hr_second_pass_steps?: number;
  denoising_strength?: number;
  hr_resize_x?: number;
  hr_resize_y?: number;
  styles?: string[] | null;
}

export interface ImageGenerateResponse {
  image_path: string;
  image_url?: string | null;
  images: string[];
  metadata: Record<string, unknown>;
  filename: string;
}

export interface ImageRecord {
  id: number;
  filename: string;
  filepath: string;
  prompt: string;
  negative_prompt?: string | null;
  model_name?: string | null;
  lora_used?: string[] | null;
  parameters: Record<string, unknown>;
  created_at: string;
  file_size: number;
  width: number;
  height: number;
}

export interface ImagesPaginatedResponse {
  images: ImageRecord[];
  total: number;
  page: number;
  per_page: number;
}

// ── Settings types ────────────────────────────────────────────────────────

export interface ChatSettings {
  default_model: string;
  system_prompt: string;
}

export interface ImageSettings {
  default_model: string;
  default_sampler: string;
  default_steps: number;
  default_cfg: number;
  default_width: number;
  default_height: number;
}

export interface TTSSettings {
  enabled: boolean;
  default_voice: string;
}

export interface ToolsSettings {
  filesystem_allowlist: string[];
  max_file_size_mb: number;
}

export interface ServerSettings {
  api_key: string;
}

export interface UserSettings {
  chat: ChatSettings;
  image: ImageSettings;
  tts: TTSSettings;
  tools: ToolsSettings;
  server: ServerSettings;
}

export type PartialUserSettings = {
  chat?: Partial<ChatSettings>;
  image?: Partial<ImageSettings>;
  tts?: Partial<TTSSettings>;
  tools?: Partial<ToolsSettings>;
  server?: Partial<ServerSettings>;
};

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

export async function deleteConversation(sessionId: string, apiKey?: string): Promise<void> {
  const res = await fetch(`${BASE}/api/conversations/${sessionId}`, {
    method: 'DELETE',
    headers: buildHeaders(apiKey),
  });
  if (!res.ok) {
    const text = await res.text().catch(() => res.statusText);
    throw new Error(`${res.status}: ${text}`);
  }
}

export function renameConversation(sessionId: string, title: string, apiKey?: string) {
  return request<{ session_id: string; title: string }>(
    'PATCH',
    `/api/conversations/${sessionId}`,
    { title },
    apiKey,
  );
}

/**
 * Build a URL for downloading a conversation export.
 * The download is triggered via window.open() rather than fetch.
 */
export function exportConversationUrl(
  sessionId: string,
  format: 'json' | 'markdown' | 'txt',
): string {
  return `${BASE}/api/conversations/${sessionId}/export?format=${format}`;
}

// ── Public API – Ollama endpoints ────────────────────────────────────────

export function ollamaStatus(apiKey?: string) {
  return request<OllamaStatusResponse>('GET', '/api/ollama/status', undefined, apiKey);
}

export function auto1111Status(apiKey?: string) {
  return request<OllamaStatusResponse>('GET', '/api/auto1111/status', undefined, apiKey);
}

export function auto1111Samplers(apiKey?: string) {
  return request<{ samplers: string[] }>('GET', '/api/auto1111/samplers', undefined, apiKey);
}

export function auto1111Upscalers(apiKey?: string) {
  return request<{ upscalers: string[] }>('GET', '/api/auto1111/upscalers', undefined, apiKey);
}

export function auto1111Styles(apiKey?: string) {
  return request<{ styles: string[] }>('GET', '/api/auto1111/styles', undefined, apiKey);
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

export async function refreshCheckpoints(): Promise<void> {
  await fetch('/api/auto1111/refresh-checkpoints', {
    method: 'POST',
    headers: buildHeaders(),
  });
}

// ── Public API – images ───────────────────────────────────────────────────

export function listImagesPaginated(
  params: { page?: number; per_page?: number; prompt?: string; model?: string },
  apiKey?: string,
) {
  const qs = new URLSearchParams();
  if (params.page != null) qs.set('page', String(params.page));
  if (params.per_page != null) qs.set('per_page', String(params.per_page));
  if (params.prompt) qs.set('prompt', params.prompt);
  if (params.model) qs.set('model', params.model);
  const query = qs.toString();
  return request<ImagesPaginatedResponse>(
    'GET',
    `/api/images${query ? `?${query}` : ''}`,
    undefined,
    apiKey,
  );
}

export function getImage(id: number, apiKey?: string) {
  return request<ImageRecord>('GET', `/api/images/${id}`, undefined, apiKey);
}

export async function deleteImage(id: number, apiKey?: string): Promise<void> {
  const res = await fetch(`${BASE}/api/images/${id}`, {
    method: 'DELETE',
    headers: buildHeaders(apiKey),
  });
  if (!res.ok) {
    const text = await res.text().catch(() => res.statusText);
    throw new Error(`${res.status}: ${text}`);
  }
}

// ── Public API – settings ─────────────────────────────────────────────────

export function getSettings(apiKey?: string) {
  return request<UserSettings>('GET', '/api/settings', undefined, apiKey);
}

export function updateSettings(updates: PartialUserSettings, apiKey?: string) {
  return request<UserSettings>('PUT', '/api/settings', updates, apiKey);
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

// ── Persona types and API ─────────────────────────────────────────────────

export interface Persona {
  id: number;
  name: string;
  system_prompt: string;
  default_model?: string | null;
  icon: string;
  is_builtin: boolean;
  created_at: string;
}

export interface PersonasListResponse {
  personas: Persona[];
}

export function listPersonas(apiKey?: string): Promise<PersonasListResponse> {
  return request<PersonasListResponse>('GET', '/api/personas', undefined, apiKey);
}

export function createPersona(
  p: Omit<Persona, 'id' | 'is_builtin' | 'created_at'>,
  apiKey?: string,
): Promise<{ id: number }> {
  return request<{ id: number }>('POST', '/api/personas', p, apiKey);
}

export function updatePersona(
  id: number,
  p: Partial<Omit<Persona, 'id' | 'is_builtin' | 'created_at'>>,
  apiKey?: string,
): Promise<{ updated: number }> {
  return request<{ updated: number }>('PUT', `/api/personas/${id}`, p, apiKey);
}

export async function deletePersona(id: number, apiKey?: string): Promise<void> {
  const res = await fetch(`${BASE}/api/personas/${id}`, {
    method: 'DELETE',
    headers: buildHeaders(apiKey),
  });
  if (!res.ok) {
    const text = await res.text().catch(() => res.statusText);
    throw new Error(`${res.status}: ${text}`);
  }
}

// ── img2img / inpainting ──────────────────────────────────────────────────

export interface Img2ImgRequest {
  prompt: string;
  negative_prompt?: string | null;
  model?: string | null;
  width?: number;
  height?: number;
  steps?: number;
  cfg_scale?: number;
  sampler?: string | null;
  lora?: string[] | null;
  seed?: number;
  batch_size?: number;
  restore_faces?: boolean;
  tiling?: boolean;
  clip_skip?: number;
  styles?: string[] | null;
  // img2img specific
  init_image: string;            // base64 or /images/ URL
  denoising_strength?: number;
  resize_mode?: number;          // 0=just resize, 1=crop+resize, 2=resize+fill
  // Inpainting
  mask?: string | null;          // base64 PNG mask
  mask_blur?: number;
  inpainting_fill?: number;      // 0=fill, 1=original, 2=latent noise, 3=latent nothing
  inpaint_full_res?: boolean;
  inpaint_full_res_padding?: number;
}

export interface Img2ImgResponse {
  image_path: string;
  image_url?: string | null;
  images: string[];
  metadata: Record<string, unknown>;
  filename: string;
}

export function img2img(req: Img2ImgRequest, apiKey?: string): Promise<Img2ImgResponse> {
  return request<Img2ImgResponse>('POST', '/api/image/img2img', req, apiKey);
}

// ── File upload ───────────────────────────────────────────────────────────

export interface UploadResponse {
  upload_id: string;
  filename: string;
  size: number;
  stored_path: string;
  session_id?: string | null;
}

export async function uploadFile(
  file: File,
  sessionId?: string,
  apiKey?: string,
): Promise<UploadResponse> {
  const form = new FormData();
  form.append('file', file);
  if (sessionId) form.append('session_id', sessionId);

  const headers: Record<string, string> = {};
  if (apiKey) headers['X-API-Key'] = apiKey;

  const res = await fetch(`${BASE}/api/upload`, {
    method: 'POST',
    headers,
    body: form,
  });
  if (!res.ok) {
    const text = await res.text().catch(() => res.statusText);
    throw new Error(`${res.status}: ${text}`);
  }
  return res.json();
}
