import { useRef, useEffect } from 'react';
import { useChat } from '../context/ChatContext';
import InputBar from './InputBar';
import WelcomeScreen from './WelcomeScreen';
import MessageBubble from './MessageBubble';

export default function ChatView() {
  const { state, sendMessage } = useChat();
  const bottomRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom when messages change
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [state.messages]);

  const hasMessages = state.messages.length > 0;

  return (
    <div className="flex flex-col h-full">
      {hasMessages ? (
        <div className="flex-1 overflow-y-auto">
          <div className="max-w-3xl mx-auto px-4 py-6">
            {state.messages.map((msg) => (
              <MessageBubble key={msg.id} message={msg} />
            ))}
            {state.loading && (
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

      <InputBar onSend={sendMessage} disabled={state.loading} />
    </div>
  );
}
