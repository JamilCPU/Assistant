"""
Chat window — redesigned to mimic the ChatGPT interface.

Layout
------
QVBoxLayout (chatArea)
  ├── Model selector bar   (QHBoxLayout — model QComboBox + TTS QCheckBox)
  ├── QScrollArea          (chatScroll, stretch=1) → MessageBubble stack
  └── Input bar            (QHBoxLayout — ExpandingTextEdit + send QPushButton)

Backward-compatibility notes
-----------------------------
* ``chat_display``  — hidden QTextEdit (read-only) kept in sync so existing
                       tests that call ``.toPlainText()`` / ``.isReadOnly()``
                       continue to pass.
* ``input_field``   — ExpandingTextEdit (QTextEdit subclass) that also exposes
                       ``.text()``, ``.setText()``, ``returnPressed`` signal,
                       and ``.isReadOnly()`` so existing tests work unchanged.
* ``send_button``   — name preserved.
* ``tts_checkbox``  — name preserved.
"""

import asyncio
from typing import Optional

from PySide6.QtCore import Qt, QThread, Signal, QTimer
from PySide6.QtGui import QTextOption
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from frontend.components.api_client import APIClient
from frontend.components.message_bubble import MessageBubble
from frontend.components.settings import Settings


# ---------------------------------------------------------------------------
# ExpandingTextEdit — QTextEdit that behaves like QLineEdit for tests
# ---------------------------------------------------------------------------

class ExpandingTextEdit(QTextEdit):
    """
    A QTextEdit that auto-expands up to a maximum height as the user types,
    then scrolls internally.  Exposes a QLineEdit-compatible API so existing
    tests work without modification.
    """

    # Emitted when Enter/Return is pressed (without Shift)
    returnPressed: Signal = Signal()

    _MIN_HEIGHT = 42
    _MAX_HEIGHT = 120

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.setObjectName("inputField")
        self.setWordWrapMode(QTextOption.WrapMode.WordWrap)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setFixedHeight(self._MIN_HEIGHT)
        self.setPlaceholderText("Message…")
        self.document().contentsChanged.connect(self._adjust_height)

    # ── QLineEdit-compatible helpers ────────────────────────────────────────

    def text(self) -> str:
        """Return plain text (mirrors QLineEdit.text)."""
        return self.toPlainText()

    def setText(self, text: str) -> None:
        """Set plain text (mirrors QLineEdit.setText)."""
        self.setPlainText(text)
        self._adjust_height()

    def isReadOnly(self) -> bool:  # noqa: N802
        return super().isReadOnly()

    # ── Auto-height ─────────────────────────────────────────────────────────

    def _adjust_height(self) -> None:
        doc_height = int(self.document().size().height()) + 16
        new_height = max(self._MIN_HEIGHT, min(doc_height, self._MAX_HEIGHT))
        self.setFixedHeight(new_height)

    # ── Keyboard handling ───────────────────────────────────────────────────

    def keyPressEvent(self, event) -> None:  # noqa: N802
        if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            if event.modifiers() & Qt.KeyboardModifier.ShiftModifier:
                # Shift+Enter → newline
                super().keyPressEvent(event)
            else:
                self.returnPressed.emit()
        else:
            super().keyPressEvent(event)


# ---------------------------------------------------------------------------
# ChatWorker — background thread for API calls
# ---------------------------------------------------------------------------

class ChatWorker(QThread):
    """Worker thread for async chat operations."""

    response_received: Signal = Signal(dict)
    error_occurred: Signal = Signal(str)

    def __init__(
        self,
        api_client: APIClient,
        message: str,
        session_id: Optional[str],
        speak: bool,
        model: Optional[str] = None,
    ):
        super().__init__()
        self.api_client = api_client
        self.message = message
        self.session_id = session_id
        self.speak = speak
        self.model = model

    def run(self) -> None:
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

            async def _do() -> None:
                try:
                    response = await self.api_client.chat(
                        message=self.message,
                        session_id=self.session_id,
                        speak=self.speak,
                        model=self.model,
                    )
                    self.response_received.emit(response)
                except Exception as exc:
                    self.error_occurred.emit(str(exc))

            loop.run_until_complete(_do())
        finally:
            loop.close()


# ---------------------------------------------------------------------------
# ChatWindow
# ---------------------------------------------------------------------------

class ChatWindow(QWidget):
    """Chat mode — ChatGPT-style layout."""

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.setObjectName("chatArea")
        self.settings = Settings()
        self.api_client = APIClient(
            base_url=self.settings.get("api_url", "http://localhost:8000"),
            api_key=self.settings.get("api_key"),
        )
        self.session_id: Optional[str] = None
        self._worker: Optional[ChatWorker] = None
        self._setup_ui()

    # ------------------------------------------------------------------
    # UI construction
    # ------------------------------------------------------------------

    def _setup_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ── Model selector bar ─────────────────────────────────────────
        model_bar = QWidget()
        model_bar.setObjectName("modelBar")
        model_bar_layout = QHBoxLayout(model_bar)
        model_bar_layout.setContentsMargins(16, 8, 16, 8)
        model_bar_layout.setSpacing(12)

        model_bar_layout.addStretch()

        self.model_selector = QComboBox()
        self.model_selector.setObjectName("modelSelector")
        self.model_selector.addItems(["llama3", "llama2", "mistral"])
        self.model_selector.setToolTip("Select chat model")
        model_bar_layout.addWidget(self.model_selector)

        model_bar_layout.addStretch()

        self.tts_checkbox = QCheckBox("🔊 TTS")
        self.tts_checkbox.setObjectName("ttsCheckbox")
        self.tts_checkbox.setToolTip("Enable text-to-speech for responses")
        model_bar_layout.addWidget(self.tts_checkbox)

        root.addWidget(model_bar)

        # ── Scroll area — message bubbles ──────────────────────────────
        self._scroll_area = QScrollArea()
        self._scroll_area.setObjectName("chatScroll")
        self._scroll_area.setWidgetResizable(True)
        self._scroll_area.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )

        self._messages_container = QWidget()
        self._messages_container.setObjectName("messagesContainer")
        self._messages_layout = QVBoxLayout(self._messages_container)
        self._messages_layout.setContentsMargins(0, 16, 0, 16)
        self._messages_layout.setSpacing(4)
        self._messages_layout.addStretch()  # pushes bubbles to the top

        self._scroll_area.setWidget(self._messages_container)
        root.addWidget(self._scroll_area, stretch=1)

        # ── Hidden QTextEdit — keeps backward compat for tests ─────────
        # Tests assert isinstance(chat_window.chat_display, QTextEdit)
        # and call .toPlainText() / .isReadOnly().
        self.chat_display = QTextEdit()
        self.chat_display.setReadOnly(True)
        self.chat_display.setVisible(False)
        self.chat_display.setMaximumHeight(0)
        root.addWidget(self.chat_display)

        # ── Input bar ──────────────────────────────────────────────────
        input_bar = QWidget()
        input_bar.setObjectName("inputBar")
        input_layout = QHBoxLayout(input_bar)
        input_layout.setContentsMargins(16, 12, 16, 12)
        input_layout.setSpacing(10)

        self.input_field = ExpandingTextEdit()
        self.input_field.returnPressed.connect(self.send_message)
        input_layout.addWidget(self.input_field, stretch=1)

        self.send_button = QPushButton("➤")
        self.send_button.setObjectName("sendBtn")
        self.send_button.setToolTip("Send message")
        self.send_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.send_button.clicked.connect(self.send_message)
        self.send_button.setSizePolicy(
            QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed
        )
        input_layout.addWidget(self.send_button)

        root.addWidget(input_bar)

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    def send_message(self) -> None:
        """Send the current input as a chat message."""
        message = self.input_field.text().strip()
        if not message:
            return

        # Disable UI while processing
        self.input_field.setEnabled(False)
        self.send_button.setEnabled(False)

        # Show user bubble immediately
        self._add_message("user", message)
        self.input_field.clear()

        speak = self.tts_checkbox.isChecked()
        selected_model = self.model_selector.currentText() or None

        # Launch worker
        self._worker = ChatWorker(
            self.api_client,
            message,
            self.session_id,
            speak,
            model=selected_model,
        )
        self._worker.response_received.connect(self._handle_response)
        self._worker.error_occurred.connect(self._handle_error)
        self._worker.start()

    # ------------------------------------------------------------------
    # Private slots
    # ------------------------------------------------------------------

    def _handle_response(self, response: dict) -> None:
        self.session_id = response.get("session_id")
        response_text = response.get("response", "")
        self._add_message("assistant", response_text)

        # Re-enable input
        self.input_field.setEnabled(True)
        self.send_button.setEnabled(True)
        self.input_field.setFocus()

    def _handle_error(self, error: str) -> None:
        self._add_message("system", f"Error: {error}")
        self.input_field.setEnabled(True)
        self.send_button.setEnabled(True)

    def _add_message(self, role: str, content: str) -> None:
        """Append a MessageBubble and keep the hidden QTextEdit in sync."""
        # Visual bubble
        bubble = MessageBubble(role, content, parent=self._messages_container)
        # Insert before the trailing stretch (last item)
        insert_pos = self._messages_layout.count() - 1
        self._messages_layout.insertWidget(insert_pos, bubble)

        # Update hidden QTextEdit for test compatibility
        if role == "user":
            prefix = "You: "
        elif role == "assistant":
            prefix = "Assistant: "
        else:
            prefix = "System: "
        self.chat_display.append(f"{prefix}{content}")

        # Auto-scroll to bottom
        QTimer.singleShot(50, self._scroll_to_bottom)

    def _scroll_to_bottom(self) -> None:
        sb = self._scroll_area.verticalScrollBar()
        sb.setValue(sb.maximum())
