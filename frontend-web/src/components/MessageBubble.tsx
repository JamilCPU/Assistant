import type { Message } from '../context/ChatContext';

interface MessageBubbleProps {
  message: Message;
}

export default function MessageBubble({ message }: MessageBubbleProps) {
  const { role, content, streaming } = message;

  if (role === 'user') {
    return (
      <div className="flex justify-end mb-2">
        <div className="max-w-[85%] md:max-w-[70%] rounded-2xl bg-user-bubble px-4 py-2.5">
          <p className="text-sm leading-relaxed text-text-primary whitespace-pre-wrap break-words">
            {content}
          </p>
        </div>
      </div>
    );
  }

  if (role === 'system') {
    return (
      <div className="flex justify-center mb-2">
        <div className="max-w-[85%] md:max-w-[70%] rounded-md border border-border px-4 py-2">
          <p className="text-xs italic text-text-muted whitespace-pre-wrap break-words">
            {content}
          </p>
        </div>
      </div>
    );
  }

  // assistant
  return (
    <div className="flex justify-start mb-2">
      <div className="max-w-[85%] md:max-w-[70%]">
        <span className="text-xs font-semibold text-text-secondary block mb-1">Assistant</span>
        <p className="text-sm leading-relaxed text-text-primary whitespace-pre-wrap break-words">
          {content}
          {streaming && (
            <span className="inline-block w-[2px] h-[1em] bg-text-primary ml-0.5 animate-pulse align-middle" />
          )}
        </p>
      </div>
    </div>
  );
}
