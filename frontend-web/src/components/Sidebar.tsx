import { useState } from 'react';
import { useChat, type AppMode } from '../context/ChatContext';

export default function Sidebar() {
  const { state, dispatch, loadConversation } = useChat();
  const [search, setSearch] = useState('');

  const filteredSessions = state.sessions.filter((s) => {
    if (!search.trim()) return true;
    const q = search.toLowerCase();
    return (
      (s.title ?? '').toLowerCase().includes(q) ||
      s.session_id.toLowerCase().includes(q)
    );
  });

  const setMode = (mode: AppMode) => dispatch({ type: 'SET_MODE', mode });

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
              <li key={s.session_id}>
                <button
                  onClick={() => loadConversation(s.session_id)}
                  className={`w-full text-left px-2.5 py-2 rounded-md text-[13px] truncate transition-colors cursor-pointer ${
                    state.sessionId === s.session_id
                      ? 'bg-button-active text-text-primary'
                      : 'text-text-secondary hover:bg-button-hover hover:text-text-primary'
                  }`}
                  title={s.title ?? s.session_id}
                >
                  {s.title ?? s.session_id.slice(0, 24) + '…'}
                </button>
              </li>
            ))}
          </ul>
        )}
      </div>

      {/* Settings */}
      <div className="px-3 py-3 shrink-0">
        <button className="w-full text-left px-3 py-2 rounded-md text-[13px] text-text-secondary hover:bg-button-hover hover:text-text-primary transition-colors cursor-pointer">
          ⚙️ Settings
        </button>
      </div>
    </aside>
  );
}
