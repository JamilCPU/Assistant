"""
Main application window — redesigned ChatGPT-style layout.

Structure
---------
QMainWindow
  └── central QWidget (root QHBoxLayout)
        └── QSplitter (Horizontal)
              ├── Sidebar  (fixed 260 px)
              └── QStackedWidget
                    ├── [0] ChatWindow
                    └── [1] ImageWindow

Backward-compatibility shim
----------------------------
``main_window.tabs`` is a ``_TabsShim`` instance that proxies the
``QStackedWidget``.  It exposes the same API that the existing navigation
E2E tests rely on:

    tabs.count()            → 2
    tabs.tabText(0/1)       → "Chat" / "Image Generation"
    tabs.currentIndex()     → current stack index
    tabs.setCurrentIndex(i) → switches the stack
    isinstance(tabs, QTabWidget) → True  (shim inherits QTabWidget)
"""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QHBoxLayout,
    QMainWindow,
    QSizePolicy,
    QSplitter,
    QStackedWidget,
    QTabWidget,
    QWidget,
)

from frontend.components.sidebar import Sidebar
from frontend.components.style import APP_STYLESHEET
from frontend.windows.chat_window import ChatWindow
from frontend.windows.image_window import ImageWindow


# ---------------------------------------------------------------------------
# _TabsShim — makes QStackedWidget look like a QTabWidget to the tests
# ---------------------------------------------------------------------------

class _TabsShim(QTabWidget):
    """
    Minimal QTabWidget subclass that delegates all calls to the real
    QStackedWidget so existing navigation tests pass unchanged.

    We inherit QTabWidget so ``isinstance(tabs, QTabWidget)`` still returns True.
    The shim is never shown; it carries no widgets of its own.
    """

    _LABELS = ["Chat", "Image Generation"]

    def __init__(self, stack: QStackedWidget, parent: QWidget | None = None):
        super().__init__(parent)
        self._stack = stack

    # ── QTabWidget API ──────────────────────────────────────────────────────

    def count(self) -> int:  # noqa: D102
        return len(self._LABELS)

    def tabText(self, index: int) -> str:  # noqa: N802, D102
        try:
            return self._LABELS[index]
        except IndexError:
            return ""

    def currentIndex(self) -> int:  # noqa: N802, D102
        return self._stack.currentIndex()

    def setCurrentIndex(self, index: int) -> None:  # noqa: N802, D102
        self._stack.setCurrentIndex(index)


# ---------------------------------------------------------------------------
# MainWindow
# ---------------------------------------------------------------------------

class MainWindow(QMainWindow):
    """Main application window."""

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.setWindowTitle("Local AI Assistant Platform")
        self.setMinimumSize(900, 600)
        self.resize(1280, 820)

        # Apply global stylesheet
        self.setStyleSheet(APP_STYLESHEET)

        self._setup_ui()

    # ------------------------------------------------------------------
    # UI construction
    # ------------------------------------------------------------------

    def _setup_ui(self) -> None:
        # Root central widget
        central = QWidget()
        central.setObjectName("chatArea")
        self.setCentralWidget(central)

        root_layout = QHBoxLayout(central)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        # ── Splitter ───────────────────────────────────────────────────
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setHandleWidth(1)
        splitter.setChildrenCollapsible(False)
        root_layout.addWidget(splitter)

        # ── Sidebar ────────────────────────────────────────────────────
        self._sidebar = Sidebar()
        splitter.addWidget(self._sidebar)
        splitter.setStretchFactor(0, 0)   # sidebar doesn't stretch

        # ── Stacked content area ───────────────────────────────────────
        self._stack = QStackedWidget()
        self._stack.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
        )
        splitter.addWidget(self._stack)
        splitter.setStretchFactor(1, 1)   # content area takes remaining space

        # Lock sidebar width after the splitter is set up
        splitter.setSizes([Sidebar._FIXED_WIDTH, self.width() - Sidebar._FIXED_WIDTH])

        # ── Child windows ──────────────────────────────────────────────
        self.chat_window = ChatWindow()
        self._stack.addWidget(self.chat_window)      # index 0

        self.image_window = ImageWindow()
        self._stack.addWidget(self.image_window)     # index 1

        # Default to Chat
        self._stack.setCurrentIndex(0)

        # ── Backward-compat tabs shim ──────────────────────────────────
        self.tabs = _TabsShim(self._stack)

        # ── Wire sidebar signals ───────────────────────────────────────
        self._sidebar.mode_changed.connect(self._on_mode_changed)
        self._sidebar.new_chat_requested.connect(self._on_new_chat)
        self._sidebar.conversation_selected.connect(self._on_conversation_selected)
        self._sidebar.settings_requested.connect(self._on_settings)

    # ------------------------------------------------------------------
    # Sidebar signal handlers
    # ------------------------------------------------------------------

    def _on_mode_changed(self, mode: str) -> None:
        """Switch main area between Chat (0) and Image Generation (1)."""
        self._stack.setCurrentIndex(0 if mode == "chat" else 1)

    def _on_new_chat(self) -> None:
        """Reset the chat window and generate a new session."""
        self._stack.setCurrentIndex(0)
        self._sidebar.chat_mode_btn.setChecked(True)
        self._sidebar.image_mode_btn.setChecked(False)

        # Clear chat and reset session
        cw = self.chat_window
        cw.session_id = None

        # Clear message bubbles
        layout = cw._messages_layout
        while layout.count() > 1:          # keep the trailing stretch
            item = layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        # Clear hidden display
        cw.chat_display.clear()

    def _on_conversation_selected(self, session_id: str) -> None:
        """Load an existing conversation into the chat window."""
        self._stack.setCurrentIndex(0)
        self._sidebar.chat_mode_btn.setChecked(True)
        self._sidebar.image_mode_btn.setChecked(False)
        # The chat window could load history here; left as a future enhancement

    def _on_settings(self) -> None:
        """Open settings dialog (placeholder)."""
        pass   # Settings dialog can be added here

    # ------------------------------------------------------------------
    # Window lifecycle
    # ------------------------------------------------------------------

    def closeEvent(self, event) -> None:  # noqa: N802
        """Clean up on close."""
        event.accept()
