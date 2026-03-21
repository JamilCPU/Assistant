import { useChat } from '../context/ChatContext';

export default function Auto1111Status() {
  const { state, dispatch } = useChat();

  const online = state.auto1111Online;
  const modelCount = state.auto1111ModelCount;

  return (
    <div className="fixed bottom-4 left-[140px] z-50">
      <button
        onClick={() => dispatch({ type: 'SET_MODE', mode: 'image' })}
        className="group flex items-center gap-2 rounded-full bg-sidebar-bg border border-border px-3 py-1.5 shadow-lg hover:bg-button-hover transition-colors cursor-pointer"
        title={online ? `Auto1111 · ${modelCount} model${modelCount !== 1 ? 's' : ''}` : 'Auto1111 · Offline'}
      >
        <span
          className={`w-2.5 h-2.5 rounded-full shrink-0 ${
            online ? 'bg-green-500 shadow-[0_0_6px_rgba(34,197,94,0.6)]' : 'bg-red-500 shadow-[0_0_6px_rgba(239,68,68,0.6)]'
          }`}
        />
        <span className="text-xs text-text-secondary group-hover:text-text-primary transition-colors">
          Auto1111
        </span>
      </button>
    </div>
  );
}
