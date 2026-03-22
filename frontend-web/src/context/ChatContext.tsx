import {
  createContext,
  useContext,
  useReducer,
  useCallback,
  useEffect,
  useRef,
  type ReactNode,
  type Dispatch,
} from 'react';
import * as api from '../api/client';

// ── Types ────────────────────────────────────────────────────────────────

export type AppMode = 'chat' | 'image' | 'models' | 'gallery';

export interface Message {
  id: number;
  role: 'user' | 'assistant' | 'system' | 'tool';
  content: string;
  timestamp?: string;
  streaming?: boolean; // true while tokens are still arriving
  audioUrl?: string | null;
  attachments?: Array<{ filename: string; size: number }>;
}

export interface ChatState {
  mode: AppMode;
  sessionId: string | null;
  messages: Message[];
  chatModels: string[];
  imageModels: string[];
  selectedModel: string | null;
  ttsEnabled: boolean;
  ttsVoice: string | null;
  ttsVoices: string[];
  sidebarOpen: boolean;
  sessions: api.SessionInfo[];
  loading: boolean;
  // Ollama
  ollamaOnline: boolean;
  ollamaModelCount: number;
  // Auto1111
  auto1111Online: boolean;
  auto1111ModelCount: number;
  // Settings
  systemPromptDefault: string;
  // Gallery → Image template
  imageTemplate: Record<string, unknown> | null;
  // Personas
  personas: api.Persona[];
  selectedPersona: api.Persona | null;
  systemPrompt: string;
}

// ── Actions ──────────────────────────────────────────────────────────────

type Action =
  | { type: 'SET_MODE'; mode: AppMode }
  | { type: 'SET_SESSION'; sessionId: string | null }
  | { type: 'SET_MESSAGES'; messages: Message[] }
  | { type: 'ADD_MESSAGE'; message: Message }
  | { type: 'APPEND_TOKEN'; msgId: number; content: string }
  | { type: 'FINISH_STREAMING'; msgId: number }
  | { type: 'SET_AUDIO_URL'; msgId: number; audioUrl: string | null }
  | { type: 'SET_MODELS'; chat: string[]; image: string[] }
  | { type: 'SELECT_MODEL'; model: string }
  | { type: 'TOGGLE_TTS' }
  | { type: 'SET_TTS_VOICE'; voice: string | null }
  | { type: 'SET_TTS_VOICES'; voices: string[] }
  | { type: 'TOGGLE_SIDEBAR' }
  | { type: 'SET_SIDEBAR'; open: boolean }
  | { type: 'SET_SESSIONS'; sessions: api.SessionInfo[] }
  | { type: 'SET_LOADING'; loading: boolean }
  | { type: 'SET_OLLAMA_STATUS'; online: boolean; modelCount: number }
  | { type: 'SET_AUTO1111_STATUS'; online: boolean; modelCount: number }
  | { type: 'SET_SYSTEM_PROMPT_DEFAULT'; prompt: string }
  | { type: 'SET_IMAGE_TEMPLATE'; template: Record<string, unknown> | null }
  | { type: 'SET_PERSONAS'; personas: api.Persona[] }
  | { type: 'SELECT_PERSONA'; persona: api.Persona | null }
  | { type: 'SET_SYSTEM_PROMPT'; prompt: string }
  | { type: 'NEW_CHAT' };

// ── Reducer ──────────────────────────────────────────────────────────────

const initialState: ChatState = {
  mode: 'chat',
  sessionId: null,
  messages: [],
  chatModels: [],
  imageModels: [],
  selectedModel: null,
  ttsEnabled: false,
  ttsVoice: null,
  ttsVoices: [],
  sidebarOpen: true,
  sessions: [],
  loading: false,
  ollamaOnline: false,
  ollamaModelCount: 0,
  auto1111Online: false,
  auto1111ModelCount: 0,
  systemPromptDefault: '',
  imageTemplate: null,
  personas: [],
  selectedPersona: null,
  systemPrompt: '',
};

function reducer(state: ChatState, action: Action): ChatState {
  switch (action.type) {
    case 'SET_MODE':
      return { ...state, mode: action.mode };
    case 'SET_SESSION':
      return { ...state, sessionId: action.sessionId };
    case 'SET_MESSAGES':
      return { ...state, messages: action.messages };
    case 'ADD_MESSAGE':
      return { ...state, messages: [...state.messages, action.message] };
    case 'APPEND_TOKEN':
      return {
        ...state,
        messages: state.messages.map((m) =>
          m.id === action.msgId ? { ...m, content: m.content + action.content } : m,
        ),
      };
    case 'FINISH_STREAMING':
      return {
        ...state,
        messages: state.messages.map((m) =>
          m.id === action.msgId ? { ...m, streaming: false } : m,
        ),
      };
    case 'SET_AUDIO_URL':
      return {
        ...state,
        messages: state.messages.map((m) =>
          m.id === action.msgId ? { ...m, audioUrl: action.audioUrl } : m,
        ),
      };
    case 'SET_MODELS':
      return {
        ...state,
        chatModels: action.chat,
        imageModels: action.image,
        selectedModel: state.selectedModel ?? action.chat[0] ?? null,
      };
    case 'SELECT_MODEL':
      return { ...state, selectedModel: action.model };
    case 'TOGGLE_TTS':
      return { ...state, ttsEnabled: !state.ttsEnabled };
    case 'SET_TTS_VOICE':
      return { ...state, ttsVoice: action.voice };
    case 'SET_TTS_VOICES':
      return { ...state, ttsVoices: action.voices };
    case 'TOGGLE_SIDEBAR':
      return { ...state, sidebarOpen: !state.sidebarOpen };
    case 'SET_SIDEBAR':
      return { ...state, sidebarOpen: action.open };
    case 'SET_SESSIONS':
      return { ...state, sessions: action.sessions };
    case 'SET_LOADING':
      return { ...state, loading: action.loading };
    case 'SET_OLLAMA_STATUS':
      return { ...state, ollamaOnline: action.online, ollamaModelCount: action.modelCount };
    case 'SET_AUTO1111_STATUS':
      return { ...state, auto1111Online: action.online, auto1111ModelCount: action.modelCount };
    case 'SET_SYSTEM_PROMPT_DEFAULT':
      return { ...state, systemPromptDefault: action.prompt };
    case 'SET_IMAGE_TEMPLATE':
      return { ...state, imageTemplate: action.template };
    case 'SET_PERSONAS':
      return { ...state, personas: action.personas };
    case 'SELECT_PERSONA': {
      const persona = action.persona;
      return {
        ...state,
        selectedPersona: persona,
        systemPrompt: persona ? persona.system_prompt : '',
      };
    }
    case 'SET_SYSTEM_PROMPT':
      return { ...state, systemPrompt: action.prompt };
    case 'NEW_CHAT':
      return {
        ...state,
        sessionId: null,
        messages: [],
        mode: 'chat',
        selectedPersona: null,
        systemPrompt: state.systemPromptDefault,
      };
    default:
      return state;
  }
}

// ── Context ──────────────────────────────────────────────────────────────

interface ChatContextValue {
  state: ChatState;
  dispatch: Dispatch<Action>;
  sendMessage: (text: string, uploadIds?: string[], attachments?: Array<{ filename: string; size: number }>) => Promise<void>;
  loadConversation: (sessionId: string) => Promise<void>;
  refreshSessions: () => Promise<void>;
  refreshModels: () => Promise<void>;
  refreshOllamaStatus: () => Promise<void>;
  refreshAuto1111Status: () => Promise<void>;
  loadSettings: () => Promise<void>;
  refreshPersonas: () => Promise<void>;
}

const ChatContext = createContext<ChatContextValue | null>(null);

// ── Provider ─────────────────────────────────────────────────────────────

let nextMsgId = 1;

export function ChatProvider({ children }: { children: ReactNode }) {
  const [state, dispatch] = useReducer(reducer, initialState);

  // Keep a ref to the active stream controller so we can abort if needed
  const streamControllerRef = useRef<AbortController | null>(null);

  // ── Ollama status polling ────────────────────────────────────────────

  const refreshOllamaStatus = useCallback(async () => {
    try {
      const data = await api.ollamaStatus();
      dispatch({ type: 'SET_OLLAMA_STATUS', online: data.online, modelCount: data.model_count });
    } catch {
      dispatch({ type: 'SET_OLLAMA_STATUS', online: false, modelCount: 0 });
    }
  }, []);

  // Poll every 60 seconds
  useEffect(() => {
    refreshOllamaStatus();
    const id = setInterval(refreshOllamaStatus, 60_000);
    return () => clearInterval(id);
  }, [refreshOllamaStatus]);

  // ── Auto1111 status polling ──────────────────────────────────────────

  const refreshAuto1111Status = useCallback(async () => {
    try {
      const data = await api.auto1111Status();
      dispatch({ type: 'SET_AUTO1111_STATUS', online: data.online, modelCount: data.model_count });
    } catch {
      dispatch({ type: 'SET_AUTO1111_STATUS', online: false, modelCount: 0 });
    }
  }, []);

  useEffect(() => {
    refreshAuto1111Status();
    const id = setInterval(refreshAuto1111Status, 60_000);
    return () => clearInterval(id);
  }, [refreshAuto1111Status]);

  // ── Load settings on mount ───────────────────────────────────────────

  const loadSettings = useCallback(async () => {
    try {
      const data = await api.getSettings();
      if (data.chat.system_prompt) {
        dispatch({ type: 'SET_SYSTEM_PROMPT_DEFAULT', prompt: data.chat.system_prompt });
        dispatch({ type: 'SET_SYSTEM_PROMPT', prompt: data.chat.system_prompt });
      }
    } catch {
      // Silently ignore — settings will use defaults
    }
  }, []);

  // ── Fetch models on mount ────────────────────────────────────────────

  const refreshModels = useCallback(async () => {
    try {
      const data = await api.listModels();
      dispatch({ type: 'SET_MODELS', chat: data.chat ?? [], image: data.image ?? [] });
      if (data.tts && data.tts.length > 0) {
        dispatch({ type: 'SET_TTS_VOICES', voices: data.tts });
      }
    } catch {
      // Silently ignore — models will be empty
    }
  }, []);

  // ── Fetch sessions list ──────────────────────────────────────────────

  const refreshSessions = useCallback(async () => {
    try {
      const data = await api.listConversations();
      dispatch({ type: 'SET_SESSIONS', sessions: data.sessions ?? [] });
    } catch {
      // Silently ignore
    }
  }, []);

  // ── Fetch personas ───────────────────────────────────────────────────

  const refreshPersonas = useCallback(async () => {
    try {
      const data = await api.listPersonas();
      dispatch({ type: 'SET_PERSONAS', personas: data.personas ?? [] });
    } catch {
      // Silently ignore
    }
  }, []);

  // ── Load conversation history ────────────────────────────────────────

  const loadConversation = useCallback(async (sessionId: string) => {
    dispatch({ type: 'SET_LOADING', loading: true });
    try {
      const data = await api.getConversation(sessionId);
      const msgs: Message[] = data.messages
        .filter((m) => m.content && m.content.trim().length > 0)
        .map((m) => ({
          id: nextMsgId++,
          role: m.role as Message['role'],
          content: m.content,
          timestamp: m.timestamp,
        }));
      dispatch({ type: 'SET_SESSION', sessionId });
      dispatch({ type: 'SET_MESSAGES', messages: msgs });
      dispatch({ type: 'SET_MODE', mode: 'chat' });
    } catch {
      dispatch({
        type: 'ADD_MESSAGE',
        message: { id: nextMsgId++, role: 'system', content: 'Failed to load conversation.' },
      });
    } finally {
      dispatch({ type: 'SET_LOADING', loading: false });
    }
  }, []);

  // ── Send a chat message (streaming) ──────────────────────────────────

  const sendMessage = useCallback(
    async (
      text: string,
      uploadIds?: string[],
      attachments?: Array<{ filename: string; size: number }>,
    ) => {
      // Cancel any in-flight stream
      streamControllerRef.current?.abort();

      const userMsg: Message = {
        id: nextMsgId++,
        role: 'user',
        content: text,
        attachments: attachments && attachments.length > 0 ? attachments : undefined,
      };
      dispatch({ type: 'ADD_MESSAGE', message: userMsg });
      dispatch({ type: 'SET_LOADING', loading: true });

      const assistantMsgId = nextMsgId++;
      const assistantMsg: Message = {
        id: assistantMsgId,
        role: 'assistant',
        content: '',
        streaming: true,
      };
      dispatch({ type: 'ADD_MESSAGE', message: assistantMsg });

      const controller = api.chatStream(
        {
          message: text,
          session_id: state.sessionId,
          model: state.selectedModel,
          speak: state.ttsEnabled,
          tts_voice: state.ttsVoice,
          system_prompt: state.systemPrompt || undefined,
          upload_ids: uploadIds && uploadIds.length > 0 ? uploadIds : undefined,
        },
        {
          onToken(content) {
            dispatch({ type: 'APPEND_TOKEN', msgId: assistantMsgId, content });
          },
          onToolCall(tc) {
            // Insert a display-only tool message into the conversation
            dispatch({
              type: 'ADD_MESSAGE',
              message: {
                id: nextMsgId++,
                role: 'tool',
                content: JSON.stringify({ name: tc.name, arguments: tc.arguments }),
              },
            });
          },
          onDone(info) {
            dispatch({ type: 'FINISH_STREAMING', msgId: assistantMsgId });
            dispatch({ type: 'SET_LOADING', loading: false });

            // Attach audio URL to the assistant message when TTS was used
            if (info.audio_url) {
              dispatch({ type: 'SET_AUDIO_URL', msgId: assistantMsgId, audioUrl: info.audio_url });
            }

            const isNewSession = !state.sessionId && !!info.session_id;
            if (isNewSession) {
              dispatch({ type: 'SET_SESSION', sessionId: info.session_id });
            }

            // Refresh sidebar sessions after a new message
            refreshSessions();

            // For new sessions, the auto-title is generated async on the backend (~1-2s).
            // Re-fetch sessions again after a short delay to pick up the generated title.
            if (isNewSession) {
              setTimeout(() => refreshSessions(), 2500);
            }

            streamControllerRef.current = null;
          },
          onError(error) {
            dispatch({ type: 'FINISH_STREAMING', msgId: assistantMsgId });
            dispatch({ type: 'SET_LOADING', loading: false });
            dispatch({
              type: 'ADD_MESSAGE',
              message: { id: nextMsgId++, role: 'system', content: `Error: ${error}` },
            });
            streamControllerRef.current = null;
          },
        },
      );

      streamControllerRef.current = controller;
    },
    [state.sessionId, state.selectedModel, state.ttsEnabled, state.ttsVoice, state.systemPrompt, refreshSessions],
  );

  // ── Initial data fetch ───────────────────────────────────────────────

  useEffect(() => {
    refreshModels();
    refreshSessions();
    loadSettings();
    refreshPersonas();
  }, [refreshModels, refreshSessions, loadSettings, refreshPersonas]);

  return (
    <ChatContext.Provider
      value={{
        state,
        dispatch,
        sendMessage,
        loadConversation,
        refreshSessions,
        refreshModels,
        refreshOllamaStatus,
        refreshAuto1111Status,
        loadSettings,
        refreshPersonas,
      }}
    >
      {children}
    </ChatContext.Provider>
  );
}

// ── Hook ─────────────────────────────────────────────────────────────────

export function useChat() {
  const ctx = useContext(ChatContext);
  if (!ctx) throw new Error('useChat must be used inside <ChatProvider>');
  return ctx;
}
