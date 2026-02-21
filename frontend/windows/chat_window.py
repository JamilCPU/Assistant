"""Chat window UI."""

import asyncio
from typing import Optional

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTextEdit, QLineEdit,
    QPushButton, QCheckBox, QLabel
)
from PySide6.QtCore import Qt, QThread, Signal

from frontend.components.api_client import APIClient
from frontend.components.settings import Settings


class ChatWorker(QThread):
    """Worker thread for async chat operations."""
    
    response_received = Signal(dict)
    error_occurred = Signal(str)
    
    def __init__(self, api_client: APIClient, message: str, session_id: Optional[str],
                 speak: bool, model: Optional[str] = None):
        """Initialize worker."""
        super().__init__()
        self.api_client = api_client
        self.message = message
        self.session_id = session_id
        self.speak = speak
        self.model = model
    
    def run(self):
        """Run async chat operation."""
        try:
            # Create new event loop for this thread
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            async def do_chat():
                try:
                    response = await self.api_client.chat(
                        message=self.message,
                        session_id=self.session_id,
                        speak=self.speak,
                        model=self.model
                    )
                    self.response_received.emit(response)
                except Exception as e:
                    self.error_occurred.emit(str(e))
            
            loop.run_until_complete(do_chat())
        finally:
            loop.close()


class ChatWindow(QWidget):
    """Chat mode window."""
    
    def __init__(self):
        """Initialize chat window."""
        super().__init__()
        self.settings = Settings()
        self.api_client = APIClient(
            base_url=self.settings.get("api_url", "http://localhost:8000"),
            api_key=self.settings.get("api_key")
        )
        self.session_id: Optional[str] = None
        self._setup_ui()
    
    def _setup_ui(self):
        """Setup UI components."""
        layout = QVBoxLayout(self)
        
        # Chat display area
        self.chat_display = QTextEdit()
        self.chat_display.setReadOnly(True)
        self.chat_display.setPlaceholderText("Chat messages will appear here...")
        layout.addWidget(self.chat_display)
        
        # Input area
        input_layout = QHBoxLayout()
        
        self.input_field = QLineEdit()
        self.input_field.setPlaceholderText("Type your message...")
        self.input_field.returnPressed.connect(self.send_message)
        input_layout.addWidget(self.input_field)
        
        self.send_button = QPushButton("Send")
        self.send_button.clicked.connect(self.send_message)
        input_layout.addWidget(self.send_button)
        
        layout.addLayout(input_layout)
        
        # Options
        options_layout = QHBoxLayout()
        
        self.tts_checkbox = QCheckBox("Enable TTS")
        options_layout.addWidget(self.tts_checkbox)
        
        options_layout.addStretch()
        
        self.model_label = QLabel("Model:")
        options_layout.addWidget(self.model_label)
        
        # Model selector could be added here
        
        layout.addLayout(options_layout)
    
    def send_message(self):
        """Send chat message."""
        message = self.input_field.text().strip()
        if not message:
            return
        
        # Disable input while processing
        self.input_field.setEnabled(False)
        self.send_button.setEnabled(False)
        
        # Display user message
        self._add_message("user", message)
        self.input_field.clear()
        
        # Get TTS setting
        speak = self.tts_checkbox.isChecked()
        
        # Create worker thread for async operation
        # Store as instance variable to prevent garbage collection before completion
        self._worker = ChatWorker(
            self.api_client,
            message,
            self.session_id,
            speak
        )
        self._worker.response_received.connect(self._handle_response)
        self._worker.error_occurred.connect(self._handle_error)
        self._worker.start()
    
    def _handle_response(self, response: dict):
        """Handle chat response."""
        # Update session ID
        self.session_id = response.get("session_id")
        
        # Display assistant response
        response_text = response.get("response", "")
        self._add_message("assistant", response_text)
        
        # Handle audio if TTS was enabled
        audio_url = response.get("audio_url")
        if audio_url:
            # Could play audio here
            pass
        
        # Re-enable input
        self.input_field.setEnabled(True)
        self.send_button.setEnabled(True)
        self.input_field.setFocus()
    
    def _handle_error(self, error: str):
        """Handle error."""
        self._add_message("system", f"Error: {error}")
        self.input_field.setEnabled(True)
        self.send_button.setEnabled(True)
    
    def _add_message(self, role: str, content: str):
        """Add message to chat display."""
        if role == "user":
            prefix = "<b>You:</b> "
            color = "#0066cc"
        elif role == "assistant":
            prefix = "<b>Assistant:</b> "
            color = "#009900"
        else:
            prefix = "<b>System:</b> "
            color = "#cc0000"
        
        formatted = f'<p style="color: {color};">{prefix}{content}</p>'
        self.chat_display.append(formatted)
        
        # Scroll to bottom
        self.chat_display.verticalScrollBar().setValue(
            self.chat_display.verticalScrollBar().maximum()
        )
