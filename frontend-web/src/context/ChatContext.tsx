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

export type AppMode = 'chat' | 'image' | 'models';

export interface Message {
  id: number;
  role: 'user' | 'assistant' | 'system';
  content: string;
  timestamp?: string;
  streaming?: boolean; // true while tokens are still arriving
}

export interface ChatState {
  mode: AppMode;
  sessionId: string | null;
  messages: Message[];
  chatModels: string[];
  imageModels: string[];
  selectedModel: string | null;
  ttsEnabled: boolean;
  sidebarOpen: boolean;
  sessions: api.SessionInfo[];
  loading: boolean;
  // Ollama
  ollamaOnline: boolean;
  ollamaModelCount: number;
}

// ── Actions ──────────────────────────────────────────────────────────────

type Action =
  | { type: 'SET_MODE'; mode: AppMode }
  | { type: 'SET_SESSION'; sessionId: string | null }
  | { type: 'SET_MESSAGES'; messages: Message[] }
  | { type: 'ADD_MESSAGE'; message: Message }
  | { type: 'APPEND_TOKEN'; msgId: number; content: string }
  | { type: 'FINISH_STREAMING'; msgId: number }
  | { type: 'SET_MODELS'; chat: string[]; image: string[] }
  | { type: 'SELECT_MODEL'; model: string }
  | { type: 'TOGGLE_TTS' }
  | { type: 'TOGGLE_SIDEBAR' }
  | { type: 'SET_SIDEBAR'; open: boolean }
  | { type: 'SET_SESSIONS'; sessions: api.SessionInfo[] }
  | { type: 'SET_LOADING'; loading: boolean }
  | { type: 'SET_OLLAMA_STATUS'; online: boolean; modelCount: number }
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
  sidebarOpen: true,
  sessions: [],
  loading: false,
  ollamaOnline: false,
  ollamaModelCount: 0,
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
    case 'NEW_CHAT':
      return { ...state, sessionId: null, messages: [], mode: 'chat' };
    default:
      return state;
  }
}

// ── Context ──────────────────────────────────────────────────────────────

interface ChatContextValue {
  state: ChatState;
  dispatch: Dispatch<Action>;
  sendMessage: (text: string) => Promise<void>;
  loadConversation: (sessionId: string) => Promise<void>;
  refreshSessions: () => Promise<void>;
  refreshModels: () => Promise<void>;
  refreshOllamaStatus: () => Promise<void>;
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

  // ── Fetch models on mount ────────────────────────────────────────────

  const refreshModels = useCallback(async () => {
    try {
      const data = await api.listModels();
      dispatch({ type: 'SET_MODELS', chat: data.chat ?? [], image: data.image ?? [] });
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

  // ── Load conversation history ────────────────────────────────────────

  const loadConversation = useCallback(async (sessionId: string) => {
    dispatch({ type: 'SET_LOADING', loading: true });
    try {
      const data = await api.getConversation(sessionId);
      const msgs: Message[] = data.messages.map((m) => ({
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
    async (text: string) => {
      // Cancel any in-flight stream
      streamControllerRef.current?.abort();

      const userMsg: Message = { id: nextMsgId++, role: 'user', content: text };
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
        },
        {
          onToken(content) {
            dispatch({ type: 'APPEND_TOKEN', msgId: assistantMsgId, content });
          },
          onToolCall() {
            // Tool-call events are handled server-side; UI could display them later
          },
          onDone(info) {
            dispatch({ type: 'FINISH_STREAMING', msgId: assistantMsgId });
            dispatch({ type: 'SET_LOADING', loading: false });

            if (!state.sessionId && info.session_id) {
              dispatch({ type: 'SET_SESSION', sessionId: info.session_id });
            }

            // Refresh sidebar sessions after a new message
            refreshSessions();
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
    [state.sessionId, state.selectedModel, state.ttsEnabled, refreshSessions],
  );

  // ── Initial data fetch ───────────────────────────────────────────────

  useEffect(() => {
    refreshModels();
    refreshSessions();
  }, [refreshModels, refreshSessions]);

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
