import { useRef, useEffect, useState } from 'react';
import { useChat } from '../context/ChatContext';
import InputBar from './InputBar';
import WelcomeScreen from './WelcomeScreen';
import MessageBubble from './MessageBubble';
import { exportConversationUrl } from '../api/client';

export default function ChatView() {
  const { state, dispatch, sendMessage } = useChat();
  const bottomRef = useRef<HTMLDivElement>(null);
  const [exportOpen, setExportOpen] = useState(false);
  const [systemPromptExpanded, setSystemPromptExpanded] = useState(false);

  // Auto-scroll to bottom when messages change
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [state.messages]);

  const hasMessages = state.messages.length > 0;

  // System prompt is locked (read-only) after the first message has been sent
  const isSystemPromptLocked = hasMessages;

  // Show loading dots only when loading AND no streaming assistant message exists yet
  const lastMsg = state.messages[state.messages.length - 1];
  const showLoadingDots =
    state.loading &&
    (!lastMsg || lastMsg.role !== 'assistant' || (!lastMsg.streaming && lastMsg.content === ''));

  const handleExport = (format: 'json' | 'markdown' | 'txt') => {
    if (!state.sessionId) return;
    window.open(exportConversationUrl(state.sessionId, format), '_blank');
    setExportOpen(false);
  };

  return (
    <div className="flex flex-col h-full">
      {hasMessages ? (
        <div className="flex-1 overflow-y-auto relative">
          {/* Export button — top-right corner, only when a session is active */}
          {state.sessionId && (
            <div className="absolute top-3 right-4 z-10">
              <div className="relative">
                <button
                  onClick={() => setExportOpen((v) => !v)}
                  className="flex items-center gap-1 px-2 py-1 rounded-md text-xs text-text-muted hover:text-text-primary hover:bg-button-hover transition-colors cursor-pointer border border-border-light"
                  title="Export conversation"
                >
                  <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
                    <path d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
                  </svg>
                  Export
                </button>
                {exportOpen && (
                  <div className="absolute right-0 mt-1 bg-sidebar-bg border border-border rounded-md shadow-lg overflow-hidden text-xs">
                    <button
                      onClick={() => handleExport('markdown')}
                      className="block w-full text-left px-4 py-2 text-text-secondary hover:bg-button-hover hover:text-text-primary cursor-pointer"
                    >
                      Markdown
                    </button>
                    <button
                      onClick={() => handleExport('json')}
                      className="block w-full text-left px-4 py-2 text-text-secondary hover:bg-button-hover hover:text-text-primary cursor-pointer"
                    >
                      JSON
                    </button>
                    <button
                      onClick={() => handleExport('txt')}
                      className="block w-full text-left px-4 py-2 text-text-secondary hover:bg-button-hover hover:text-text-primary cursor-pointer"
                    >
                      Plain text
                    </button>
                  </div>
                )}
              </div>
            </div>
          )}

          <div className="max-w-3xl mx-auto px-2 sm:px-4 py-4 sm:py-6">
            {state.messages.map((msg) => (
              <MessageBubble key={msg.id} message={msg} />
            ))}
            {showLoadingDots && (
              <div className="flex justify-start mb-2">
                <div className="max-w-[70%]">
                  <span className="text-xs font-semibold text-text-secondary block mb-1">Assistant</span>
                  <div className="flex gap-1 items-center py-2">
                    <span className="w-2 h-2 rounded-full bg-text-muted animate-bounce [animation-delay:0ms]" />
                    <span className="w-2 h-2 rounded-full bg-text-muted animate-bounce [animation-delay:150ms]" />
                    <span className="w-2 h-2 rounded-full bg-text-muted animate-bounce [animation-delay:300ms]" />
                  </div>
                </div>
              </div>
            )}
            <div ref={bottomRef} />
          </div>
        </div>
      ) : (
        <WelcomeScreen />
      )}

      {/* System prompt collapsible row */}
      <div className="border-t border-border-light max-w-3xl w-full mx-auto px-2 sm:px-4">
        <button
          onClick={() => setSystemPromptExpanded((v) => !v)}
          className="flex items-center gap-1.5 text-xs text-text-muted hover:text-text-secondary py-1.5 transition-colors cursor-pointer w-full text-left"
        >
          {isSystemPromptLocked ? (
            <span title="System prompt is locked after the first message">🔒</span>
          ) : (
            <span>⚙️</span>
          )}
          <span>System prompt</span>
          {state.systemPrompt && (
            <span className="ml-1 text-text-muted truncate max-w-[200px]">
              — {state.systemPrompt.slice(0, 40)}{state.systemPrompt.length > 40 ? '…' : ''}
            </span>
          )}
          <span className="ml-auto">{systemPromptExpanded ? '▲' : '▼'}</span>
        </button>

        {systemPromptExpanded && (
          <div className="pb-2">
            {isSystemPromptLocked ? (
              <p className="text-xs text-text-secondary bg-input-bg border border-border rounded-md px-3 py-2 whitespace-pre-wrap">
                {state.systemPrompt || <span className="text-text-muted italic">None</span>}
              </p>
            ) : (
              <textarea
                value={state.systemPrompt}
                onChange={(e) =>
                  dispatch({ type: 'SET_SYSTEM_PROMPT', prompt: e.target.value })
                }
                rows={3}
                placeholder="Set a system prompt for this conversation (applies before first message)…"
                className="w-full bg-input-bg border border-border rounded-md px-3 py-2 text-xs text-text-primary placeholder-text-muted outline-none focus:border-accent resize-none"
              />
            )}
          </div>
        )}
      </div>

      <InputBar
        onSend={(text, uploadIds, attachments) => sendMessage(text, uploadIds, attachments)}
        disabled={state.loading}
      />
    </div>
  );
}
