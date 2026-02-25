import { ChatProvider, useChat } from './context/ChatContext';
import Sidebar from './components/Sidebar';
import TopBar from './components/TopBar';
import ChatView from './components/ChatView';
import ImageView from './components/ImageView';
import ModelManager from './components/ModelManager';
import OllamaStatus from './components/OllamaStatus';

function AppLayout() {
  const { state, dispatch } = useChat();

  return (
    <div className="flex h-screen w-screen overflow-hidden bg-main-bg text-text-primary font-sans">
      {/* Sidebar */}
      <div
        className={`shrink-0 overflow-hidden transition-all duration-300 ease-in-out ${
          state.sidebarOpen ? 'w-[260px]' : 'w-0'
        }`}
      >
        <div className="w-[260px] h-full">
          <Sidebar />
        </div>
      </div>

      {/* Main content area */}
      <div className="flex flex-col flex-1 min-w-0">
        {/* Top bar — only show for chat mode */}
        {state.mode === 'chat' && <TopBar />}

        {/* Collapsed-sidebar toggle (visible when sidebar is hidden) */}
        {!state.sidebarOpen && (
          <button
            onClick={() => dispatch({ type: 'SET_SIDEBAR', open: true })}
            className="absolute top-3 left-3 z-10 w-[30px] h-[30px] flex items-center justify-center rounded-md text-text-secondary hover:bg-button-hover hover:text-text-primary transition-colors cursor-pointer"
            title="Open sidebar"
          >
            <svg className="w-[18px] h-[18px]" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
              <path d="M4 6h16M4 12h16M4 18h16" />
            </svg>
          </button>
        )}

        {/* Mode content */}
        {state.mode === 'chat' && <ChatView />}
        {state.mode === 'image' && <ImageView />}
        {state.mode === 'models' && <ModelManager />}
      </div>

      {/* Always-visible Ollama status indicator */}
      <OllamaStatus />
    </div>
  );
}

export default function App() {
  return (
    <ChatProvider>
      <AppLayout />
    </ChatProvider>
  );
}
