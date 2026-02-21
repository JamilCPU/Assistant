"""
Image generation window — restyled with ChatGPT-style dark QSS.

All widget names / logic are preserved from the original implementation
so existing E2E tests continue to pass without modification.
"""

import asyncio
from pathlib import Path
from typing import Optional

from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QDoubleSpinBox,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QSpinBox,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from frontend.components.api_client import APIClient
from frontend.components.settings import Settings


# ---------------------------------------------------------------------------
# ImageWorker — background thread for image generation
# ---------------------------------------------------------------------------

class ImageWorker(QThread):
    """Worker thread for async image generation."""

    image_generated: Signal = Signal(dict)
    error_occurred: Signal = Signal(str)

    def __init__(self, api_client: APIClient, prompt: str, **kwargs):
        super().__init__()
        self.api_client = api_client
        self.prompt = prompt
        self.kwargs = kwargs

    def run(self) -> None:
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

            async def _do() -> None:
                try:
                    response = await self.api_client.generate_image(
                        prompt=self.prompt, **self.kwargs
                    )
                    self.image_generated.emit(response)
                except Exception as exc:
                    self.error_occurred.emit(str(exc))

            loop.run_until_complete(_do())
        finally:
            loop.close()


# ---------------------------------------------------------------------------
# ImageWindow
# ---------------------------------------------------------------------------

class ImageWindow(QWidget):
    """Image generation window with dark ChatGPT-style UI."""

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.setObjectName("imageArea")
        self.settings = Settings()
        self.api_client = APIClient(
            base_url=self.settings.get("api_url", "http://localhost:8000"),
            api_key=self.settings.get("api_key"),
        )
        self._worker: Optional[ImageWorker] = None
        self.current_image_path: Optional[str] = None
        self._setup_ui()
        self._load_models()

    # ------------------------------------------------------------------
    # UI construction
    # ------------------------------------------------------------------

    def _setup_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ── Scroll area wraps all controls + image ─────────────────────
        scroll = QScrollArea()
        scroll.setObjectName("chatScroll")
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        inner = QWidget()
        inner.setObjectName("imageArea")
        inner_layout = QVBoxLayout(inner)
        inner_layout.setContentsMargins(32, 24, 32, 24)
        inner_layout.setSpacing(16)

        # ── Title ──────────────────────────────────────────────────────
        title = QLabel("Image Generation")
        title.setStyleSheet(
            "font-size: 18px; font-weight: 600; color: #ececec; background: transparent;"
        )
        inner_layout.addWidget(title)

        # ── Prompt ────────────────────────────────────────────────────
        prompt_label = QLabel("Prompt")
        prompt_label.setObjectName("sectionLabel")
        inner_layout.addWidget(prompt_label)

        self.prompt_input = QTextEdit()
        self.prompt_input.setObjectName("promptInput")
        self.prompt_input.setPlaceholderText("Describe the image you want to generate…")
        self.prompt_input.setMaximumHeight(100)
        inner_layout.addWidget(self.prompt_input)

        # ── Negative prompt ────────────────────────────────────────────
        neg_label = QLabel("Negative Prompt")
        neg_label.setObjectName("sectionLabel")
        inner_layout.addWidget(neg_label)

        self.neg_prompt_input = QTextEdit()
        self.neg_prompt_input.setObjectName("negPromptInput")
        self.neg_prompt_input.setPlaceholderText("Things to avoid in the image (optional)…")
        self.neg_prompt_input.setMaximumHeight(70)
        inner_layout.addWidget(self.neg_prompt_input)

        # ── Parameters row ────────────────────────────────────────────
        params_label = QLabel("Parameters")
        params_label.setObjectName("sectionLabel")
        inner_layout.addWidget(params_label)

        params_frame = QFrame()
        params_frame.setObjectName("imageArea")
        params_layout = QHBoxLayout(params_frame)
        params_layout.setContentsMargins(0, 0, 0, 0)
        params_layout.setSpacing(24)

        def _param_col(label_text: str, widget: QWidget) -> QVBoxLayout:
            col = QVBoxLayout()
            col.setSpacing(4)
            lbl = QLabel(label_text)
            lbl.setStyleSheet("color: #8e8ea0; font-size: 12px; background: transparent;")
            col.addWidget(lbl)
            col.addWidget(widget)
            return col

        self.width_spin = QSpinBox()
        self.width_spin.setRange(64, 2048)
        self.width_spin.setValue(512)
        self.width_spin.setSingleStep(64)
        params_layout.addLayout(_param_col("Width", self.width_spin))

        self.height_spin = QSpinBox()
        self.height_spin.setRange(64, 2048)
        self.height_spin.setValue(512)
        self.height_spin.setSingleStep(64)
        params_layout.addLayout(_param_col("Height", self.height_spin))

        self.steps_spin = QSpinBox()
        self.steps_spin.setRange(1, 100)
        self.steps_spin.setValue(20)
        params_layout.addLayout(_param_col("Steps", self.steps_spin))

        self.cfg_spin = QDoubleSpinBox()
        self.cfg_spin.setRange(1.0, 20.0)
        self.cfg_spin.setValue(7.0)
        self.cfg_spin.setSingleStep(0.5)
        params_layout.addLayout(_param_col("CFG Scale", self.cfg_spin))

        params_layout.addStretch()
        inner_layout.addWidget(params_frame)

        # ── Generate button ────────────────────────────────────────────
        btn_row = QHBoxLayout()
        btn_row.setContentsMargins(0, 4, 0, 0)
        self.generate_button = QPushButton("Generate Image")
        self.generate_button.setObjectName("generateBtn")
        self.generate_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.generate_button.clicked.connect(self.generate_image)
        btn_row.addWidget(self.generate_button)
        btn_row.addStretch()
        inner_layout.addLayout(btn_row)

        # ── Image display ──────────────────────────────────────────────
        self.image_label = QLabel()
        self.image_label.setObjectName("imagePlaceholder")
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_label.setMinimumHeight(400)
        self.image_label.setText("Generated image will appear here…")
        self.image_label.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
        )
        inner_layout.addWidget(self.image_label, stretch=1)

        # ── Save button ────────────────────────────────────────────────
        save_row = QHBoxLayout()
        save_row.setContentsMargins(0, 0, 0, 0)
        self.save_button = QPushButton("💾  Save Image")
        self.save_button.setObjectName("saveBtn")
        self.save_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.save_button.clicked.connect(self.save_image)
        self.save_button.setEnabled(False)
        save_row.addWidget(self.save_button)
        save_row.addStretch()
        inner_layout.addLayout(save_row)

        inner_layout.addStretch()
        scroll.setWidget(inner)
        root.addWidget(scroll)

    # ------------------------------------------------------------------
    # Logic (unchanged from original)
    # ------------------------------------------------------------------

    def _load_models(self) -> None:
        """Load available models (placeholder — can be wired to backend)."""
        pass

    def generate_image(self) -> None:
        """Kick off image generation."""
        prompt = self.prompt_input.toPlainText().strip()
        if not prompt:
            return

        self.generate_button.setEnabled(False)
        self.image_label.setText("Generating image…")

        negative_prompt = self.neg_prompt_input.toPlainText().strip() or None
        width = self.width_spin.value()
        height = self.height_spin.value()
        steps = self.steps_spin.value()
        cfg_scale = self.cfg_spin.value()

        # Store as instance variable to prevent garbage collection
        self._worker = ImageWorker(
            self.api_client,
            prompt,
            negative_prompt=negative_prompt,
            width=width,
            height=height,
            steps=steps,
            cfg_scale=cfg_scale,
        )
        self._worker.image_generated.connect(self._handle_image)
        self._worker.error_occurred.connect(self._handle_error)
        self._worker.start()

    def _handle_image(self, response: dict) -> None:
        image_path = response.get("image_path")
        if not image_path:
            self._handle_error("No image path in response")
            return

        pixmap = QPixmap(image_path)
        if not pixmap.isNull():
            scaled = pixmap.scaled(
                self.image_label.size(),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
            self.image_label.setPixmap(scaled)
            self.current_image_path = image_path
            self.save_button.setEnabled(True)
        else:
            self._handle_error("Failed to load image")

        self.generate_button.setEnabled(True)

    def _handle_error(self, error: str) -> None:
        self.image_label.setText(f"Error: {error}")
        self.generate_button.setEnabled(True)

    def save_image(self) -> None:
        if not self.current_image_path:
            return

        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Image",
            "",
            "Images (*.png *.jpg *.jpeg)",
        )

        if file_path:
            import shutil
            shutil.copy(self.current_image_path, file_path)
