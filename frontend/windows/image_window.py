"""Image generation window."""

import asyncio
from pathlib import Path
from typing import Optional

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTextEdit, QPushButton,
    QLabel, QSpinBox, QDoubleSpinBox, QComboBox, QFileDialog
)
from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtGui import QPixmap

from frontend.components.api_client import APIClient
from frontend.components.settings import Settings


class ImageWorker(QThread):
    """Worker thread for async image generation."""
    
    image_generated = Signal(dict)
    error_occurred = Signal(str)
    
    def __init__(self, api_client: APIClient, prompt: str, **kwargs):
        """Initialize worker."""
        super().__init__()
        self.api_client = api_client
        self.prompt = prompt
        self.kwargs = kwargs
    
    def run(self):
        """Run async image generation."""
        try:
            # Create new event loop for this thread
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            async def do_generate():
                try:
                    response = await self.api_client.generate_image(
                        prompt=self.prompt,
                        **self.kwargs
                    )
                    self.image_generated.emit(response)
                except Exception as e:
                    self.error_occurred.emit(str(e))
            
            loop.run_until_complete(do_generate())
        finally:
            loop.close()


class ImageWindow(QWidget):
    """Image generation window."""
    
    def __init__(self):
        """Initialize image window."""
        super().__init__()
        self.settings = Settings()
        self.api_client = APIClient(
            base_url=self.settings.get("api_url", "http://localhost:8000"),
            api_key=self.settings.get("api_key")
        )
        self._setup_ui()
        self._load_models()
    
    def _setup_ui(self):
        """Setup UI components."""
        layout = QVBoxLayout(self)
        
        # Prompt input
        prompt_layout = QVBoxLayout()
        prompt_label = QLabel("Prompt:")
        prompt_layout.addWidget(prompt_label)
        
        self.prompt_input = QTextEdit()
        self.prompt_input.setPlaceholderText("Enter image generation prompt...")
        self.prompt_input.setMaximumHeight(100)
        prompt_layout.addWidget(self.prompt_input)
        
        layout.addLayout(prompt_layout)
        
        # Negative prompt
        neg_prompt_layout = QVBoxLayout()
        neg_prompt_label = QLabel("Negative Prompt (optional):")
        neg_prompt_layout.addWidget(neg_prompt_label)
        
        self.neg_prompt_input = QTextEdit()
        self.neg_prompt_input.setPlaceholderText("Enter negative prompt...")
        self.neg_prompt_input.setMaximumHeight(60)
        neg_prompt_layout.addWidget(self.neg_prompt_input)
        
        layout.addLayout(neg_prompt_layout)
        
        # Parameters
        params_layout = QHBoxLayout()
        
        # Width
        width_layout = QVBoxLayout()
        width_label = QLabel("Width:")
        width_layout.addWidget(width_label)
        self.width_spin = QSpinBox()
        self.width_spin.setRange(64, 2048)
        self.width_spin.setValue(512)
        self.width_spin.setSingleStep(64)
        width_layout.addWidget(self.width_spin)
        params_layout.addLayout(width_layout)
        
        # Height
        height_layout = QVBoxLayout()
        height_label = QLabel("Height:")
        height_layout.addWidget(height_label)
        self.height_spin = QSpinBox()
        self.height_spin.setRange(64, 2048)
        self.height_spin.setValue(512)
        self.height_spin.setSingleStep(64)
        height_layout.addWidget(self.height_spin)
        params_layout.addLayout(height_layout)
        
        # Steps
        steps_layout = QVBoxLayout()
        steps_label = QLabel("Steps:")
        steps_layout.addWidget(steps_label)
        self.steps_spin = QSpinBox()
        self.steps_spin.setRange(1, 100)
        self.steps_spin.setValue(20)
        steps_layout.addWidget(self.steps_spin)
        params_layout.addLayout(steps_layout)
        
        # CFG Scale
        cfg_layout = QVBoxLayout()
        cfg_label = QLabel("CFG Scale:")
        cfg_layout.addWidget(cfg_label)
        self.cfg_spin = QDoubleSpinBox()
        self.cfg_spin.setRange(1.0, 20.0)
        self.cfg_spin.setValue(7.0)
        self.cfg_spin.setSingleStep(0.5)
        cfg_layout.addWidget(self.cfg_spin)
        params_layout.addLayout(cfg_layout)
        
        layout.addLayout(params_layout)
        
        # Generate button
        self.generate_button = QPushButton("Generate Image")
        self.generate_button.clicked.connect(self.generate_image)
        layout.addWidget(self.generate_button)
        
        # Image display
        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setMinimumHeight(400)
        self.image_label.setText("Generated image will appear here...")
        self.image_label.setStyleSheet("border: 1px solid gray;")
        layout.addWidget(self.image_label)
        
        # Save button
        button_layout = QHBoxLayout()
        self.save_button = QPushButton("Save Image")
        self.save_button.clicked.connect(self.save_image)
        self.save_button.setEnabled(False)
        button_layout.addWidget(self.save_button)
        button_layout.addStretch()
        layout.addLayout(button_layout)
        
        self.current_image_path: Optional[str] = None
    
    def _load_models(self):
        """Load available models (could be async)."""
        # Model loading could be implemented here
        pass
    
    def generate_image(self):
        """Generate image."""
        prompt = self.prompt_input.toPlainText().strip()
        if not prompt:
            return
        
        # Disable button during generation
        self.generate_button.setEnabled(False)
        self.image_label.setText("Generating image...")
        
        # Get parameters
        negative_prompt = self.neg_prompt_input.toPlainText().strip() or None
        width = self.width_spin.value()
        height = self.height_spin.value()
        steps = self.steps_spin.value()
        cfg_scale = self.cfg_spin.value()
        
        # Create worker thread
        worker = ImageWorker(
            self.api_client,
            prompt,
            negative_prompt=negative_prompt,
            width=width,
            height=height,
            steps=steps,
            cfg_scale=cfg_scale
        )
        worker.image_generated.connect(self._handle_image)
        worker.error_occurred.connect(self._handle_error)
        worker.start()
    
    def _handle_image(self, response: dict):
        """Handle generated image."""
        image_path = response.get("image_path")
        if not image_path:
            self._handle_error("No image path in response")
            return
        
        # Load and display image
        pixmap = QPixmap(image_path)
        if not pixmap.isNull():
            # Scale to fit label while maintaining aspect ratio
            scaled_pixmap = pixmap.scaled(
                self.image_label.size(),
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation
            )
            self.image_label.setPixmap(scaled_pixmap)
            self.current_image_path = image_path
            self.save_button.setEnabled(True)
        else:
            self._handle_error("Failed to load image")
        
        self.generate_button.setEnabled(True)
    
    def _handle_error(self, error: str):
        """Handle error."""
        self.image_label.setText(f"Error: {error}")
        self.generate_button.setEnabled(True)
    
    def save_image(self):
        """Save current image."""
        if not self.current_image_path:
            return
        
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Image",
            "",
            "Images (*.png *.jpg *.jpeg)"
        )
        
        if file_path:
            import shutil
            shutil.copy(self.current_image_path, file_path)
