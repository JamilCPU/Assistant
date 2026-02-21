import { useState, useRef, useCallback, type KeyboardEvent } from 'react';

interface InputBarProps {
  onSend: (text: string) => void;
  disabled?: boolean;
  placeholder?: string;
}

export default function InputBar({ onSend, disabled = false, placeholder = 'Ask anything…' }: InputBarProps) {
  const [text, setText] = useState('');
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const handleSend = useCallback(() => {
    const trimmed = text.trim();
    if (!trimmed || disabled) return;
    onSend(trimmed);
    setText('');
    // Reset textarea height
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
    }
  }, [text, disabled, onSend]);

  const handleKeyDown = useCallback(
    (e: KeyboardEvent<HTMLTextAreaElement>) => {
      if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        handleSend();
      }
    },
    [handleSend],
  );

  return (
    <div className="w-full flex justify-center px-4 pb-4 pt-2">
      <div className="w-full max-w-3xl flex items-end gap-2 rounded-2xl border border-input-border bg-input-bg px-4 py-2 focus-within:border-border-light transition-colors">
        <textarea
          ref={textareaRef}
          value={text}
          onChange={(e) => setText(e.target.value)}
          onKeyDown={handleKeyDown}
          disabled={disabled}
          placeholder={placeholder}
          rows={1}
          className="flex-1 resize-none bg-transparent text-text-primary text-[15px] leading-relaxed outline-none placeholder:text-text-muted min-h-[28px] max-h-[160px] py-1"
        />
        <button
          onClick={handleSend}
          disabled={disabled || !text.trim()}
          className="flex-shrink-0 w-[34px] h-[34px] rounded-[10px] bg-text-primary text-main-bg font-bold text-sm flex items-center justify-center hover:bg-white disabled:bg-send-btn-disabled disabled:text-text-muted transition-colors cursor-pointer"
          title="Send message"
        >
          ↑
        </button>
      </div>
    </div>
  );
}
