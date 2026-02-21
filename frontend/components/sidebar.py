"""
Sidebar widget — fixed-width left panel mimicking the ChatGPT sidebar.

Signals
-------
new_chat_requested      emitted when the "New Chat" button is clicked
conversation_selected   emitted with session_id (str) when history item clicked
mode_changed            emitted with mode name ("chat" | "image") when mode button clicked
settings_requested      emitted when the Settings button is clicked
"""

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QSizePolicy,
    QSpacerItem,
    QVBoxLayout,
    QWidget,
)


class Sidebar(QWidget):
    """
    Left sidebar containing:
      - "New Chat" button
      - Conversation history list
      - Mode switcher buttons (Chat / Image Generation)
      - Settings button at the bottom
    """

    new_chat_requested: Signal = Signal()
    conversation_selected: Signal = Signal(str)      # session_id
    mode_changed: Signal = Signal(str)               # "chat" | "image"
    settings_requested: Signal = Signal()

    _FIXED_WIDTH = 260

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.setObjectName("sidebar")
        self.setFixedWidth(self._FIXED_WIDTH)
        self._setup_ui()
        self._connect_signals()

    # ------------------------------------------------------------------
    # UI construction
    # ------------------------------------------------------------------

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # ── Top section ───────────────────────────────────────────────
        top_frame = QFrame()
        top_frame.setObjectName("sidebar")
        top_layout = QVBoxLayout(top_frame)
        top_layout.setContentsMargins(8, 12, 8, 8)
        top_layout.setSpacing(4)

        self.new_chat_btn = QPushButton("＋  New Chat")
        self.new_chat_btn.setObjectName("newChatBtn")
        self.new_chat_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        top_layout.addWidget(self.new_chat_btn)

        layout.addWidget(top_frame)

        # ── History list ──────────────────────────────────────────────
        history_header = QLabel("Recent")
        history_header.setContentsMargins(16, 10, 8, 4)
        history_header.setStyleSheet(
            "color: #6b6b7b; font-size: 11px; font-weight: 600;"
            "text-transform: uppercase; background: transparent;"
        )
        layout.addWidget(history_header)

        self.history_list = QListWidget()
        self.history_list.setObjectName("historyList")
        self.history_list.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.history_list.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.history_list.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
        )
        layout.addWidget(self.history_list, stretch=1)

        # ── Mode switcher ─────────────────────────────────────────────
        divider = QFrame()
        divider.setFrameShape(QFrame.Shape.HLine)
        divider.setStyleSheet("color: #4d4d4f; background: #4d4d4f; max-height: 1px;")
        layout.addWidget(divider)

        mode_frame = QFrame()
        mode_frame.setObjectName("sidebar")
        mode_layout = QVBoxLayout(mode_frame)
        mode_layout.setContentsMargins(8, 8, 8, 4)
        mode_layout.setSpacing(2)

        self.chat_mode_btn = QPushButton("💬  Chat")
        self.chat_mode_btn.setObjectName("modeBtn")
        self.chat_mode_btn.setCheckable(True)
        self.chat_mode_btn.setChecked(True)
        self.chat_mode_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        mode_layout.addWidget(self.chat_mode_btn)

        self.image_mode_btn = QPushButton("🎨  Image Generation")
        self.image_mode_btn.setObjectName("modeBtn")
        self.image_mode_btn.setCheckable(True)
        self.image_mode_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        mode_layout.addWidget(self.image_mode_btn)

        layout.addWidget(mode_frame)

        # ── Bottom section ────────────────────────────────────────────
        bottom_divider = QFrame()
        bottom_divider.setFrameShape(QFrame.Shape.HLine)
        bottom_divider.setStyleSheet("color: #4d4d4f; background: #4d4d4f; max-height: 1px;")
        layout.addWidget(bottom_divider)

        bottom_frame = QFrame()
        bottom_frame.setObjectName("sidebar")
        bottom_layout = QVBoxLayout(bottom_frame)
        bottom_layout.setContentsMargins(8, 8, 8, 12)
        bottom_layout.setSpacing(2)

        self.settings_btn = QPushButton("⚙  Settings")
        self.settings_btn.setObjectName("settingsBtn")
        self.settings_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        bottom_layout.addWidget(self.settings_btn)

        layout.addWidget(bottom_frame)

    def _connect_signals(self) -> None:
        self.new_chat_btn.clicked.connect(self.new_chat_requested.emit)
        self.chat_mode_btn.clicked.connect(lambda: self._switch_mode("chat"))
        self.image_mode_btn.clicked.connect(lambda: self._switch_mode("image"))
        self.settings_btn.clicked.connect(self.settings_requested.emit)
        self.history_list.itemClicked.connect(self._on_history_item_clicked)

    # ------------------------------------------------------------------
    # Internal slots
    # ------------------------------------------------------------------

    def _switch_mode(self, mode: str) -> None:
        """Toggle mode buttons and emit signal."""
        if mode == "chat":
            self.chat_mode_btn.setChecked(True)
            self.image_mode_btn.setChecked(False)
        else:
            self.chat_mode_btn.setChecked(False)
            self.image_mode_btn.setChecked(True)
        self.mode_changed.emit(mode)

    def _on_history_item_clicked(self, item: QListWidgetItem) -> None:
        session_id = item.data(Qt.ItemDataRole.UserRole)
        if session_id:
            self.conversation_selected.emit(session_id)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def set_conversations(self, conversations: list[dict]) -> None:
        """
        Populate the history list.

        Parameters
        ----------
        conversations : list of dicts with keys:
            - session_id (str)
            - title (str)   — displayed label
        """
        self.history_list.clear()
        for conv in conversations:
            label = conv.get("title") or conv.get("session_id", "Untitled")
            item = QListWidgetItem(label)
            item.setData(Qt.ItemDataRole.UserRole, conv.get("session_id"))
            self.history_list.addItem(item)

    def add_conversation(self, session_id: str, title: str = "New Chat") -> None:
        """Prepend a single conversation entry to the top of the list."""
        item = QListWidgetItem(title)
        item.setData(Qt.ItemDataRole.UserRole, session_id)
        self.history_list.insertItem(0, item)
        self.history_list.setCurrentRow(0)

    def update_conversation_title(self, session_id: str, title: str) -> None:
        """Update the display title of an existing conversation entry."""
        for i in range(self.history_list.count()):
            item = self.history_list.item(i)
            if item.data(Qt.ItemDataRole.UserRole) == session_id:
                item.setText(title)
                break
