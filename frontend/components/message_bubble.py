"""
MessageBubble — a single chat message displayed in the chat scroll area.

ChatGPT-style layout:
    - All messages are contained in a centered column (max-width ~768 px).
    - "user"      → right-aligned pill with subtle background.
    - "assistant" → left-aligned plain text, no background.
    - "system"    → centered, muted italic text.
"""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

# Maximum width of the message column — mirrors the input pill max-width
_MAX_COL_WIDTH = 768


class MessageBubble(QWidget):
    """
    A single message in the chat history.

    Parameters
    ----------
    role : str
        One of "user", "assistant", or "system".
    content : str
        The text to display.
    parent : QWidget, optional
    """

    def __init__(self, role: str, content: str, parent: QWidget | None = None):
        super().__init__(parent)
        self._role = role
        self._content = content
        self._setup_ui()

    # ------------------------------------------------------------------
    # UI construction
    # ------------------------------------------------------------------

    def _setup_ui(self) -> None:
        """
        Outer row: horizontal spacers keep the inner column centered and
        constrained to _MAX_COL_WIDTH.
        """
        outer = QHBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        # Side margins center the column
        outer.addStretch()

        column = self._build_column()
        column.setMaximumWidth(_MAX_COL_WIDTH)
        column.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        outer.addWidget(column, stretch=1)

        outer.addStretch()

    def _build_column(self) -> QWidget:
        """Build the inner column widget that holds the bubble."""
        column = QWidget()
        column.setObjectName("messageRow")
        col_layout = QHBoxLayout(column)
        col_layout.setContentsMargins(16, 4, 16, 4)
        col_layout.setSpacing(0)

        if self._role == "user":
            # Right-aligned pill
            col_layout.addStretch()
            col_layout.addWidget(self._build_user_bubble())

        elif self._role == "system":
            # Centered system notice
            col_layout.addStretch()
            col_layout.addWidget(self._build_system_bubble())
            col_layout.addStretch()

        else:
            # "assistant" — left-aligned plain text
            col_layout.addWidget(self._build_assistant_bubble())
            col_layout.addStretch()

        return column

    # ------------------------------------------------------------------
    # Bubble constructors
    # ------------------------------------------------------------------

    def _build_user_bubble(self) -> QFrame:
        frame = QFrame()
        frame.setObjectName("userBubble")
        frame.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Minimum)
        frame.setMaximumWidth(560)

        layout = QVBoxLayout(frame)
        layout.setContentsMargins(16, 10, 16, 10)
        layout.setSpacing(0)

        label = self._make_label(self._content)
        label.setObjectName("bubbleText")
        layout.addWidget(label)
        return frame

    def _build_assistant_bubble(self) -> QFrame:
        frame = QFrame()
        frame.setObjectName("assistantBubble")
        frame.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        layout = QVBoxLayout(frame)
        layout.setContentsMargins(0, 10, 0, 10)
        layout.setSpacing(4)

        label = self._make_label(self._content)
        label.setObjectName("bubbleText")
        layout.addWidget(label)
        return frame

    def _build_system_bubble(self) -> QFrame:
        frame = QFrame()
        frame.setObjectName("systemBubble")
        frame.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Minimum)

        layout = QVBoxLayout(frame)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(0)

        label = self._make_label(self._content)
        label.setObjectName("systemText")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(label)
        return frame

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _make_label(text: str) -> QLabel:
        label = QLabel(text)
        label.setWordWrap(True)
        label.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse
            | Qt.TextInteractionFlag.TextSelectableByKeyboard
        )
        label.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum
        )
        return label

    # ------------------------------------------------------------------
    # Public helpers
    # ------------------------------------------------------------------

    def set_content(self, content: str) -> None:
        """Update the bubble's text (used for streaming)."""
        self._content = content
        # Locate the label: it's inside the frame inside the column
        column = self.layout().itemAt(1).widget()      # stretch, column, stretch
        col_layout = column.layout()
        # Find the frame (first non-stretch item)
        for i in range(col_layout.count()):
            item = col_layout.itemAt(i)
            if item.widget() is not None:
                frame = item.widget()
                label: QLabel = frame.layout().itemAt(
                    frame.layout().count() - 1
                ).widget()
                label.setText(content)
                return
