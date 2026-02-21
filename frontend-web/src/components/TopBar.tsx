import { useChat } from '../context/ChatContext';

export default function TopBar() {
  const { state, dispatch } = useChat();

  return (
    <div className="flex items-center h-[52px] px-4 bg-main-bg shrink-0">
      {/* Model selector */}
      <div className="relative">
        <select
          value={state.selectedModel ?? ''}
          onChange={(e) => dispatch({ type: 'SELECT_MODEL', model: e.target.value })}
          className="appearance-none bg-transparent text-text-primary text-sm font-semibold border-none rounded-md px-2 py-1.5 pr-7 hover:bg-button-hover cursor-pointer outline-none"
        >
          {state.chatModels.length === 0 && (
            <option value="">No models</option>
          )}
          {state.chatModels.map((m) => (
            <option key={m} value={m} className="bg-sidebar-bg text-text-primary">
              {m}
            </option>
          ))}
        </select>
        {/* Dropdown arrow */}
        <div className="pointer-events-none absolute inset-y-0 right-1 flex items-center">
          <svg className="w-3 h-3 text-text-secondary" fill="currentColor" viewBox="0 0 12 12">
            <path d="M6 8L1 3h10L6 8z" />
          </svg>
        </div>
      </div>

      <div className="flex-1" />

      {/* TTS toggle */}
      <label className="flex items-center gap-1.5 text-text-secondary text-xs cursor-pointer hover:text-text-primary transition-colors mr-3">
        <input
          type="checkbox"
          checked={state.ttsEnabled}
          onChange={() => dispatch({ type: 'TOGGLE_TTS' })}
          className="w-3.5 h-3.5 rounded accent-accent"
        />
        🔊 TTS
      </label>

      {/* Profile icon */}
      <button
        className="w-8 h-8 rounded-full text-text-secondary text-[13px] font-semibold hover:bg-button-hover hover:text-text-primary transition-colors cursor-pointer"
        title="Profile"
      >
        JW
      </button>
    </div>
  );
}
