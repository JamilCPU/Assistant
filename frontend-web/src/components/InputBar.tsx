import { useState, useRef, useCallback, useEffect, type KeyboardEvent, type DragEvent } from 'react';
import * as api from '../api/client';
import { useChat } from '../context/ChatContext';

interface PendingAttachment {
  upload_id: string;
  filename: string;
  size: number;
  status: 'uploading' | 'done' | 'error';
  error?: string;
}

interface InputBarProps {
  onSend: (text: string, uploadIds?: string[], attachments?: Array<{ filename: string; size: number }>) => void;
  disabled?: boolean;
  placeholder?: string;
}

export default function InputBar({ onSend, disabled = false, placeholder = 'Ask anything…' }: InputBarProps) {
  const { state } = useChat();
  const [text, setText] = useState('');
  const [attachments, setAttachments] = useState<PendingAttachment[]>([]);
  const [dragOver, setDragOver] = useState(false);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const apiKey: string | undefined = undefined; // API key is not stored in frontend state

  const uploadFile = useCallback(
    async (file: File) => {
      const tempId = `tmp-${Date.now()}-${Math.random()}`;
      const pending: PendingAttachment = {
        upload_id: tempId,
        filename: file.name,
        size: file.size,
        status: 'uploading',
      };
      setAttachments((prev) => [...prev, pending]);

      try {
        const res = await api.uploadFile(file, state.sessionId ?? undefined, apiKey);
        setAttachments((prev) =>
          prev.map((a) =>
            a.upload_id === tempId
              ? { upload_id: res.upload_id, filename: res.filename, size: res.size, status: 'done' }
              : a,
          ),
        );
      } catch (err) {
        const msg = err instanceof Error ? err.message : String(err);
        setAttachments((prev) =>
          prev.map((a) =>
            a.upload_id === tempId ? { ...a, status: 'error', error: msg } : a,
          ),
        );
      }
    },
    [state.sessionId, apiKey],
  );

  const handleFiles = useCallback(
    (files: FileList | null) => {
      if (!files) return;
      Array.from(files).forEach((f) => uploadFile(f));
    },
    [uploadFile],
  );

  const handleSend = useCallback(() => {
    const trimmed = text.trim();
    if ((!trimmed && attachments.length === 0) || disabled) return;
    // Only pass done uploads
    const doneAttachments = attachments.filter((a) => a.status === 'done');
    const uploadIds = doneAttachments.map((a) => a.upload_id);
    const attachMeta = doneAttachments.map((a) => ({ filename: a.filename, size: a.size }));
    onSend(trimmed || '(file)', uploadIds.length > 0 ? uploadIds : undefined, attachMeta.length > 0 ? attachMeta : undefined);
    setText('');
    setAttachments([]);
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
    }
  }, [text, attachments, disabled, onSend]);

  const handleKeyDown = useCallback(
    (e: KeyboardEvent<HTMLTextAreaElement>) => {
      if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        handleSend();
      }
    },
    [handleSend],
  );

  const handleDragOver = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setDragOver(true);
  };

  const handleDragLeave = () => setDragOver(false);

  const handleDrop = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setDragOver(false);
    handleFiles(e.dataTransfer.files);
  };

  const removeAttachment = (id: string) => {
    setAttachments((prev) => prev.filter((a) => a.upload_id !== id));
  };

  const hasUploading = attachments.some((a) => a.status === 'uploading');

  return (
    <div
      className={`w-full flex justify-center px-4 pb-4 pt-2 ${dragOver ? 'bg-accent/5' : ''}`}
      onDragOver={handleDragOver}
      onDragLeave={handleDragLeave}
      onDrop={handleDrop}
    >
      <div className={`w-full max-w-3xl flex flex-col rounded-2xl border bg-input-bg transition-colors focus-within:border-border-light ${dragOver ? 'border-accent' : 'border-input-border'}`}>

        {/* Attachment chips */}
        {attachments.length > 0 && (
          <div className="flex flex-wrap gap-1.5 px-4 pt-2.5">
            {attachments.map((a) => (
              <span
                key={a.upload_id}
                className={`inline-flex items-center gap-1 text-xs rounded-lg px-2 py-0.5 border ${
                  a.status === 'error'
                    ? 'bg-danger/10 text-danger border-danger/30'
                    : a.status === 'uploading'
                    ? 'bg-border/20 text-text-muted border-border animate-pulse'
                    : 'bg-accent/10 text-accent border-accent/30'
                }`}
              >
                <span>{a.status === 'uploading' ? '⏳' : a.status === 'error' ? '⚠' : '📄'}</span>
                <span className="max-w-[120px] truncate">{a.filename}</span>
                {a.status === 'error' && <span className="text-[10px]">(failed)</span>}
                <button
                  onClick={() => removeAttachment(a.upload_id)}
                  className="ml-0.5 hover:opacity-70 transition-opacity cursor-pointer"
                  title="Remove"
                >
                  ✕
                </button>
              </span>
            ))}
          </div>
        )}

        <div className="flex items-end gap-2 px-4 py-2">
          {/* Paperclip button */}
          <button
            type="button"
            onClick={() => fileInputRef.current?.click()}
            disabled={disabled}
            title="Attach file"
            className="flex-shrink-0 w-[30px] h-[30px] flex items-center justify-center text-text-muted hover:text-text-primary transition-colors disabled:opacity-40 cursor-pointer"
          >
            📎
          </button>
          <input
            ref={fileInputRef}
            type="file"
            multiple
            className="hidden"
            onChange={(e) => handleFiles(e.target.files)}
          />

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
            disabled={disabled || hasUploading || (!text.trim() && attachments.filter((a) => a.status === 'done').length === 0)}
            className="flex-shrink-0 w-[34px] h-[34px] rounded-[10px] bg-text-primary text-main-bg font-bold text-sm flex items-center justify-center hover:bg-white disabled:bg-send-btn-disabled disabled:text-text-muted transition-colors cursor-pointer"
            title="Send message"
          >
            {hasUploading ? (
              <span className="w-3.5 h-3.5 border-2 border-main-bg/30 border-t-main-bg rounded-full animate-spin" />
            ) : (
              '↑'
            )}
          </button>
        </div>
      </div>
    </div>
  );
}
