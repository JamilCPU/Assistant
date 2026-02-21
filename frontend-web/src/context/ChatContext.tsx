import {
  createContext,
  useContext,
  useReducer,
  useCallback,
  useEffect,
  type ReactNode,
  type Dispatch,
} from 'react';
import * as api from '../api/client';

// ── Types ────────────────────────────────────────────────────────────────

export type AppMode = 'chat' | 'image';

export interface Message {
  id: number;
  role: 'user' | 'assistant' | 'system';
  content: string;
  timestamp?: string;
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
}

// ── Actions ──────────────────────────────────────────────────────────────

type Action =
  | { type: 'SET_MODE'; mode: AppMode }
  | { type: 'SET_SESSION'; sessionId: string | null }
  | { type: 'SET_MESSAGES'; messages: Message[] }
  | { type: 'ADD_MESSAGE'; message: Message }
  | { type: 'SET_MODELS'; chat: string[]; image: string[] }
  | { type: 'SELECT_MODEL'; model: string }
  | { type: 'TOGGLE_TTS' }
  | { type: 'TOGGLE_SIDEBAR' }
  | { type: 'SET_SIDEBAR'; open: boolean }
  | { type: 'SET_SESSIONS'; sessions: api.SessionInfo[] }
  | { type: 'SET_LOADING'; loading: boolean }
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
}

const ChatContext = createContext<ChatContextValue | null>(null);

// ── Provider ─────────────────────────────────────────────────────────────

let nextMsgId = 1;

export function ChatProvider({ children }: { children: ReactNode }) {
  const [state, dispatch] = useReducer(reducer, initialState);

  // Fetch models on mount
  const refreshModels = useCallback(async () => {
    try {
      const data = await api.listModels();
      dispatch({ type: 'SET_MODELS', chat: data.chat ?? [], image: data.image ?? [] });
    } catch {
      // Silently ignore — models will be empty
    }
  }, []);

  // Fetch sessions list
  const refreshSessions = useCallback(async () => {
    try {
      const data = await api.listConversations();
      dispatch({ type: 'SET_SESSIONS', sessions: data.sessions ?? [] });
    } catch {
      // Silently ignore
    }
  }, []);

  // Load conversation history
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

  // Send a chat message
  const sendMessage = useCallback(
    async (text: string) => {
      const userMsg: Message = { id: nextMsgId++, role: 'user', content: text };
      dispatch({ type: 'ADD_MESSAGE', message: userMsg });
      dispatch({ type: 'SET_LOADING', loading: true });

      try {
        const res = await api.chat({
          message: text,
          session_id: state.sessionId,
          model: state.selectedModel,
          speak: state.ttsEnabled,
        });

        if (!state.sessionId && res.session_id) {
          dispatch({ type: 'SET_SESSION', sessionId: res.session_id });
        }

        const assistantMsg: Message = {
          id: nextMsgId++,
          role: 'assistant',
          content: res.response,
        };
        dispatch({ type: 'ADD_MESSAGE', message: assistantMsg });

        // Refresh sidebar sessions after a new message
        refreshSessions();
      } catch (err) {
        const errorText = err instanceof Error ? err.message : 'Unknown error';
        dispatch({
          type: 'ADD_MESSAGE',
          message: { id: nextMsgId++, role: 'system', content: `Error: ${errorText}` },
        });
      } finally {
        dispatch({ type: 'SET_LOADING', loading: false });
      }
    },
    [state.sessionId, state.selectedModel, state.ttsEnabled, refreshSessions],
  );

  // Initial data fetch
  useEffect(() => {
    refreshModels();
    refreshSessions();
  }, [refreshModels, refreshSessions]);

  return (
    <ChatContext.Provider
      value={{ state, dispatch, sendMessage, loadConversation, refreshSessions, refreshModels }}
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
