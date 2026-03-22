import { useState, useRef } from 'react';
import { useChat, type AppMode } from '../context/ChatContext';
import * as api from '../api/client';
import SettingsModal from './SettingsModal';

export default function Sidebar() {
  const { state, dispatch, loadConversation, refreshSessions } = useChat();
  const [search, setSearch] = useState('');
  const [showSettings, setShowSettings] = useState(false);
  // session_id of the item currently being renamed, or null
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editValue, setEditValue] = useState('');
  const editInputRef = useRef<HTMLInputElement>(null);
  const [deletingId, setDeletingId] = useState<string | null>(null);

  const filteredSessions = state.sessions.filter((s) => {
    if (!search.trim()) return true;
    const q = search.toLowerCase();
    return (
      (s.title ?? '').toLowerCase().includes(q) ||
      s.session_id.toLowerCase().includes(q)
    );
  });

  const setMode = (mode: AppMode) => dispatch({ type: 'SET_MODE', mode });

  const startEdit = (sessionId: string, currentTitle: string | null | undefined) => {
    setEditingId(sessionId);
    setEditValue(currentTitle ?? '');
    // Focus the input on the next paint
    setTimeout(() => editInputRef.current?.focus(), 0);
  };

  const handleDelete = async (sessionId: string) => {
    setDeletingId(null);
    try {
      await api.deleteConversation(sessionId);
      if (state.sessionId === sessionId) {
        dispatch({ type: 'NEW_CHAT' });
      }
      await refreshSessions();
    } catch {
      // ignore errors
    }
  };

  const commitEdit = async (sessionId: string) => {
    const trimmed = editValue.trim();
    if (trimmed) {
      try {
        await api.renameConversation(sessionId, trimmed);
        await refreshSessions();
      } catch {
        // ignore rename errors
      }
    }
    setEditingId(null);
  };

  return (
    <aside className="flex flex-col h-full bg-sidebar-bg select-none">
      {/* Header: toggle + new chat */}
      <div className="flex items-center justify-between px-3 h-[52px] shrink-0">
        <button
          onClick={() => dispatch({ type: 'TOGGLE_SIDEBAR' })}
          className="w-[30px] h-[30px] flex items-center justify-center rounded-md text-text-secondary hover:bg-button-hover hover:text-text-primary transition-colors cursor-pointer"
          title="Toggle sidebar"
        >
          <svg className="w-[18px] h-[18px]" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
            <path d="M4 6h16M4 12h16M4 18h16" />
          </svg>
        </button>
        <button
          onClick={() => dispatch({ type: 'NEW_CHAT' })}
          className="w-[30px] h-[30px] flex items-center justify-center rounded-md text-text-secondary hover:bg-button-hover hover:text-text-primary transition-colors cursor-pointer"
          title="New chat"
        >
          <svg className="w-[18px] h-[18px]" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
            <path d="M12 5v14M5 12h14" />
          </svg>
        </button>
      </div>

      {/* Search */}
      <div className="px-3 mb-2">
        <input
          type="text"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          placeholder="Search…"
          className="w-full bg-transparent text-text-secondary text-[13px] border-none rounded-md px-3 py-2 outline-none hover:bg-button-hover focus:bg-button-hover placeholder:text-text-muted transition-colors"
        />
      </div>

      {/* Mode buttons */}
      <div className="px-3 flex flex-col gap-0.5 mb-2">
        <button
          onClick={() => setMode('chat')}
          className={`text-left px-3 py-2 rounded-md text-[13px] transition-colors cursor-pointer ${
            state.mode === 'chat'
              ? 'bg-button-active text-text-primary'
              : 'text-text-secondary hover:bg-button-hover hover:text-text-primary'
          }`}
        >
          💬 Chat
        </button>
        <button
          onClick={() => setMode('image')}
          className={`text-left px-3 py-2 rounded-md text-[13px] transition-colors cursor-pointer ${
            state.mode === 'image'
              ? 'bg-button-active text-text-primary'
              : 'text-text-secondary hover:bg-button-hover hover:text-text-primary'
          }`}
        >
          🎨 Image Generation
        </button>
        <button
          onClick={() => setMode('models')}
          className={`text-left px-3 py-2 rounded-md text-[13px] transition-colors cursor-pointer ${
            state.mode === 'models'
              ? 'bg-button-active text-text-primary'
              : 'text-text-secondary hover:bg-button-hover hover:text-text-primary'
          }`}
        >
          🧠 Models
        </button>
        <button
          onClick={() => setMode('gallery')}
          className={`text-left px-3 py-2 rounded-md text-[13px] transition-colors cursor-pointer ${
            state.mode === 'gallery'
              ? 'bg-button-active text-text-primary'
              : 'text-text-secondary hover:bg-button-hover hover:text-text-primary'
          }`}
        >
          🖼️ Gallery
        </button>
      </div>

      {/* History */}
      <div className="flex-1 overflow-y-auto px-3">
        <p className="text-[11px] font-semibold text-text-muted px-1 mb-1 uppercase tracking-wide">
          History
        </p>
        {filteredSessions.length === 0 ? (
          <p className="text-xs text-text-muted px-1 py-2">No conversations yet</p>
        ) : (
          <ul className="flex flex-col gap-0.5">
            {filteredSessions.map((s) => (
              <li key={s.session_id} className="group relative">
                {editingId === s.session_id ? (
                  <input
                    ref={editInputRef}
                    type="text"
                    value={editValue}
                    onChange={(e) => setEditValue(e.target.value)}
                    onBlur={() => commitEdit(s.session_id)}
                    onKeyDown={(e) => {
                      if (e.key === 'Enter') commitEdit(s.session_id);
                      if (e.key === 'Escape') setEditingId(null);
                    }}
                    className="w-full bg-button-hover text-text-primary text-[13px] px-2.5 py-2 rounded-md outline-none border border-border"
                  />
                ) : (
                  <div className="flex items-center">
                    <button
                      onClick={() => loadConversation(s.session_id)}
                      className={`flex-1 text-left px-2.5 py-2 rounded-md text-[13px] truncate transition-colors cursor-pointer ${
                        state.sessionId === s.session_id
                          ? 'bg-button-active text-text-primary'
                          : 'text-text-secondary hover:bg-button-hover hover:text-text-primary'
                      }`}
                      title={s.title ?? s.session_id}
                    >
                      {s.title ?? s.session_id.slice(0, 24) + '…'}
                    </button>
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        startEdit(s.session_id, s.title);
                      }}
                      className="opacity-0 group-hover:opacity-100 ml-1 shrink-0 w-[22px] h-[22px] flex items-center justify-center rounded text-text-muted hover:text-text-primary hover:bg-button-hover transition-all cursor-pointer"
                      title="Rename conversation"
                    >
                      <svg className="w-3 h-3" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
                        <path d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                      </svg>
                    </button>
                    {deletingId === s.session_id ? (
                      <span className="flex items-center gap-0.5 ml-1">
                        <button
                          onClick={(e) => { e.stopPropagation(); handleDelete(s.session_id); }}
                          className="shrink-0 w-[22px] h-[22px] flex items-center justify-center rounded text-danger hover:bg-button-hover transition-all cursor-pointer text-[11px] font-bold"
                          title="Confirm delete"
                        >✓</button>
                        <button
                          onClick={(e) => { e.stopPropagation(); setDeletingId(null); }}
                          className="shrink-0 w-[22px] h-[22px] flex items-center justify-center rounded text-text-muted hover:bg-button-hover transition-all cursor-pointer text-[11px]"
                          title="Cancel"
                        >✕</button>
                      </span>
                    ) : (
                      <button
                        onClick={(e) => { e.stopPropagation(); setDeletingId(s.session_id); }}
                        className="opacity-0 group-hover:opacity-100 ml-0.5 shrink-0 w-[22px] h-[22px] flex items-center justify-center rounded text-text-muted hover:text-danger hover:bg-button-hover transition-all cursor-pointer"
                        title="Delete conversation"
                      >
                        <svg className="w-3 h-3" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
                          <path d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                        </svg>
                      </button>
                    )}
                  </div>
                )}
              </li>
            ))}
          </ul>
        )}
      </div>

      {/* Settings */}
      <div className="px-3 py-3 shrink-0">
        <button
          onClick={() => setShowSettings(true)}
          className="w-full text-left px-3 py-2 rounded-md text-[13px] text-text-secondary hover:bg-button-hover hover:text-text-primary transition-colors cursor-pointer"
        >
          ⚙️ Settings
        </button>
      </div>

      {/* Settings Modal */}
      {showSettings && <SettingsModal onClose={() => setShowSettings(false)} />}
    </aside>
  );
}
