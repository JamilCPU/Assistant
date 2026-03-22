import { useState } from 'react';
import { useChat } from '../context/ChatContext';

export default function OllamaStatus() {
  const { state, dispatch } = useChat();
  const [showPopover, setShowPopover] = useState(false);

  const online = state.ollamaOnline;
  const modelCount = state.ollamaModelCount;

  return (
    <div className="fixed bottom-3 sm:bottom-4 left-2 sm:left-4 z-50">
      {/* Status dot button */}
      <button
        onClick={() => setShowPopover((p) => !p)}
        className="group relative flex items-center gap-1.5 sm:gap-2 rounded-full bg-sidebar-bg border border-border px-2 sm:px-3 py-1 sm:py-1.5 shadow-lg hover:bg-button-hover transition-colors cursor-pointer"
        title={online ? `Ollama · ${modelCount} model${modelCount !== 1 ? 's' : ''}` : 'Ollama · Offline'}
      >
        {/* Dot */}
        <span
          className={`w-2.5 h-2.5 rounded-full shrink-0 ${
            online ? 'bg-green-500 shadow-[0_0_6px_rgba(34,197,94,0.6)]' : 'bg-red-500 shadow-[0_0_6px_rgba(239,68,68,0.6)]'
          }`}
        />
        <span className="hidden sm:inline text-xs text-text-secondary group-hover:text-text-primary transition-colors">
          Ollama
        </span>
      </button>

      {/* Popover */}
      {showPopover && (
        <div className="absolute bottom-full left-0 mb-2 w-56 rounded-lg bg-sidebar-bg border border-border shadow-xl p-3">
          <div className="flex items-center gap-2 mb-2">
            <span
              className={`w-2.5 h-2.5 rounded-full ${
                online ? 'bg-green-500' : 'bg-red-500'
              }`}
            />
            <span className="text-sm font-semibold text-text-primary">
              {online ? 'Connected' : 'Disconnected'}
            </span>
          </div>

          {online && (
            <p className="text-xs text-text-secondary mb-3">
              {modelCount} model{modelCount !== 1 ? 's' : ''} available
            </p>
          )}

          {!online && (
            <p className="text-xs text-text-muted mb-3">
              Ollama is not reachable. Make sure it is running on localhost:11434.
            </p>
          )}

          <button
            onClick={() => {
              dispatch({ type: 'SET_MODE', mode: 'models' });
              setShowPopover(false);
            }}
            className="w-full text-left px-2 py-1.5 rounded-md text-xs text-accent hover:bg-button-hover transition-colors cursor-pointer"
          >
            Open Model Manager →
          </button>
        </div>
      )}
    </div>
  );
}
