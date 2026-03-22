import { ChatProvider, useChat } from './context/ChatContext';
import Sidebar from './components/Sidebar';
import TopBar from './components/TopBar';
import ChatView from './components/ChatView';
import ImageView from './components/ImageView';
import ModelManager from './components/ModelManager';
import GalleryView from './components/GalleryView';
import OllamaStatus from './components/OllamaStatus';
import Auto1111Status from './components/Auto1111Status';

function AppLayout() {
  const { state, dispatch } = useChat();

  return (
    <div className="flex h-screen w-screen overflow-hidden bg-main-bg text-text-primary font-sans">

      {/* Mobile overlay backdrop — visible only on small screens when sidebar is open */}
      {state.sidebarOpen && (
        <div
          className="fixed inset-0 z-40 bg-black/50 md:hidden"
          onClick={() => dispatch({ type: 'SET_SIDEBAR', open: false })}
        />
      )}

      {/* Sidebar — overlay on mobile, push on desktop */}
      {/* Mobile: absolute overlay drawer (z-50, w-[280px]) */}
      {/* Desktop (md+): shrink-0 push layout (w-[260px] or w-0) */}
      <div
        className={`
          fixed inset-y-0 left-0 z-50 w-[280px] transition-transform duration-300 ease-in-out
          md:relative md:z-auto md:w-auto md:inset-auto md:translate-x-0
          md:shrink-0 md:overflow-hidden md:transition-all
          ${state.sidebarOpen
            ? 'translate-x-0 md:w-[260px] md:visible'
            : '-translate-x-full md:w-0 md:invisible'
          }
        `}
      >
        <div className="w-[280px] md:w-[260px] h-full">
          <Sidebar />
        </div>
      </div>

      {/* Main content area */}
      <div className="flex flex-col flex-1 min-w-0">
        {/* Top bar — only show for chat mode */}
        {state.mode === 'chat' && <TopBar />}

        {/* Collapsed-sidebar toggle (visible when sidebar is hidden, on desktop only — mobile uses TopBar hamburger) */}
        {!state.sidebarOpen && (
          <button
            onClick={() => dispatch({ type: 'SET_SIDEBAR', open: true })}
            className="hidden md:flex absolute top-3 left-3 z-10 w-[30px] h-[30px] items-center justify-center rounded-md text-text-secondary hover:bg-button-hover hover:text-text-primary transition-colors cursor-pointer"
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
        {state.mode === 'gallery' && <GalleryView />}
      </div>

      {/* Always-visible status indicators */}
      <OllamaStatus />
      <Auto1111Status />
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
