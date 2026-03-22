import { useState, useRef, useEffect } from 'react';
import type { Message } from '../context/ChatContext';

function formatBytes(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(0)} KB`;
  return `${(bytes / 1024 / 1024).toFixed(1)} MB`;
}

interface MessageBubbleProps {
  message: Message;
}

interface ToolPayload {
  name: string;
  arguments: Record<string, unknown>;
}

function AudioPlayer({ src }: { src: string }) {
  const audioRef = useRef<HTMLAudioElement>(null);
  const [playing, setPlaying] = useState(false);
  const [current, setCurrent] = useState(0);
  const [duration, setDuration] = useState(0);

  useEffect(() => {
    const el = audioRef.current;
    if (!el) return;
    const onTime = () => setCurrent(el.currentTime);
    const onLoaded = () => setDuration(el.duration);
    const onEnded = () => setPlaying(false);
    el.addEventListener('timeupdate', onTime);
    el.addEventListener('loadedmetadata', onLoaded);
    el.addEventListener('ended', onEnded);
    return () => {
      el.removeEventListener('timeupdate', onTime);
      el.removeEventListener('loadedmetadata', onLoaded);
      el.removeEventListener('ended', onEnded);
    };
  }, []);

  const toggle = () => {
    const el = audioRef.current;
    if (!el) return;
    if (playing) { el.pause(); setPlaying(false); }
    else { el.play(); setPlaying(true); }
  };

  const seek = (e: React.ChangeEvent<HTMLInputElement>) => {
    const el = audioRef.current;
    if (!el) return;
    el.currentTime = Number(e.target.value);
    setCurrent(el.currentTime);
  };

  const fmt = (s: number) => `${Math.floor(s / 60)}:${String(Math.floor(s % 60)).padStart(2, '0')}`;

  return (
    <div className="mt-2 flex items-center gap-2 bg-black/20 rounded-lg px-3 py-1.5 w-full max-w-xs sm:max-w-xs">
      <audio ref={audioRef} src={src} preload="metadata" />
      <button onClick={toggle} className="text-text-secondary hover:text-text-primary transition-colors text-xs w-5 shrink-0">
        {playing ? '⏸' : '▶'}
      </button>
      <input
        type="range"
        min={0}
        max={duration || 1}
        step={0.1}
        value={current}
        onChange={seek}
        className="flex-1 h-1 accent-text-secondary cursor-pointer"
      />
      <span className="text-xs text-text-muted shrink-0 tabular-nums">
        {fmt(current)} / {fmt(duration)}
      </span>
    </div>
  );
}

export default function MessageBubble({ message }: MessageBubbleProps) {
  const { role, content, streaming, audioUrl, attachments } = message;
  const [toolExpanded, setToolExpanded] = useState(false);

  if (role === 'user') {
    return (
      <div className="flex justify-end mb-2">
        <div className="max-w-[85%] md:max-w-[70%] rounded-2xl bg-user-bubble px-4 py-2.5">
          <p className="text-sm leading-relaxed text-text-primary whitespace-pre-wrap break-words">
            {content}
          </p>
          {attachments && attachments.length > 0 && (
            <div className="mt-2 flex flex-wrap gap-1.5">
              {attachments.map((a, i) => (
                <span
                  key={i}
                  className="inline-flex items-center gap-1 text-xs bg-border/40 text-text-secondary rounded-lg px-2 py-0.5"
                >
                  <span>📄</span>
                  <span className="max-w-[140px] truncate">{a.filename}</span>
                  <span className="text-text-muted">({formatBytes(a.size)})</span>
                </span>
              ))}
            </div>
          )}
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

  if (role === 'tool') {
    let payload: ToolPayload | null = null;
    try {
      payload = JSON.parse(content) as ToolPayload;
    } catch {
      // malformed — show raw
    }

    const toolName = payload?.name ?? 'tool';
    const toolArgs = payload?.arguments ?? {};

    return (
      <div className="flex justify-start mb-1.5">
        <div className="max-w-[85%] md:max-w-[70%] rounded-md border border-border-light px-3 py-1.5">
          <button
            onClick={() => setToolExpanded((v) => !v)}
            className="flex items-center gap-1.5 text-xs text-text-muted hover:text-text-secondary transition-colors w-full text-left cursor-pointer"
          >
            <span>🔧 {toolName}</span>
            <span className="ml-auto">{toolExpanded ? '▲' : '▼'}</span>
          </button>
          {toolExpanded && (
            <pre className="mt-2 bg-black/30 rounded text-xs font-mono text-text-secondary p-2 overflow-x-auto whitespace-pre-wrap break-all">
              {JSON.stringify(toolArgs, null, 2)}
            </pre>
          )}
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
        {audioUrl && !streaming && <AudioPlayer src={audioUrl} />}
      </div>
    </div>
  );
}
