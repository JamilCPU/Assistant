"""Main application window."""

from PySide6.QtWidgets import (
    QMainWindow, QTabWidget, QWidget, QVBoxLayout
)

from frontend.windows.chat_window import ChatWindow
from frontend.windows.image_window import ImageWindow


class MainWindow(QMainWindow):
    """Main application window with tabs."""
    
    def __init__(self):
        """Initialize main window."""
        super().__init__()
        self.setWindowTitle("Local AI Assistant Platform")
        self.setGeometry(100, 100, 1200, 800)
        
        # Create central widget with tabs
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Create tab widget
        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)
        
        # Add chat tab
        self.chat_window = ChatWindow()
        self.tabs.addTab(self.chat_window, "Chat")
        
        # Add image generation tab
        self.image_window = ImageWindow()
        self.tabs.addTab(self.image_window, "Image Generation")
    
    def closeEvent(self, event):
        """Handle window close event."""
        # Clean up resources
        if hasattr(self.chat_window, 'api_client'):
            # Close API client if needed
            pass
        event.accept()
