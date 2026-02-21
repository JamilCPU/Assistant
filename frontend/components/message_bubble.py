"""
MessageBubble — a single chat message displayed in the chat scroll area.

Two main variants:
    - "user"      → right-aligned, background #40414f
    - "assistant" → left-aligned, background #2d2d30
    - "system"    → centered, muted color, italic
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
        outer = QHBoxLayout(self)
        outer.setContentsMargins(16, 6, 16, 6)
        outer.setSpacing(0)

        bubble = self._build_bubble()

        if self._role == "user":
            # Right-aligned: spacer → bubble
            outer.addStretch()
            outer.addWidget(bubble)
        elif self._role == "system":
            # Centered
            outer.addStretch()
            outer.addWidget(bubble)
            outer.addStretch()
        else:
            # "assistant" — left-aligned: bubble → spacer
            outer.addWidget(bubble)
            outer.addStretch()

    def _build_bubble(self) -> QFrame:
        frame = QFrame()
        frame.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Minimum)

        if self._role == "user":
            frame.setObjectName("userBubble")
            max_width_fraction = 0.75
        elif self._role == "system":
            frame.setObjectName("systemBubble")
            max_width_fraction = 0.85
        else:
            frame.setObjectName("assistantBubble")
            max_width_fraction = 0.85

        frame.setMaximumWidth(700)

        layout = QVBoxLayout(frame)
        layout.setContentsMargins(14, 10, 14, 10)
        layout.setSpacing(0)

        label = QLabel(self._content)
        label.setWordWrap(True)
        label.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse
            | Qt.TextInteractionFlag.TextSelectableByKeyboard
        )
        label.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum
        )

        if self._role == "system":
            label.setObjectName("systemText")
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        else:
            label.setObjectName("bubbleText")

        layout.addWidget(label)
        return frame

    # ------------------------------------------------------------------
    # Public helpers
    # ------------------------------------------------------------------

    def set_content(self, content: str) -> None:
        """Update the bubble's text (used for streaming)."""
        self._content = content
        # The label is the first widget inside the frame's layout
        frame: QFrame = self.layout().itemAt(
            0 if self._role == "assistant" else 1
        ).widget()
        label: QLabel = frame.layout().itemAt(0).widget()
        label.setText(content)
