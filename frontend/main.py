"""PySide desktop application entry point."""

import sys
from PySide6.QtWidgets import QApplication

from frontend.windows.main_window import MainWindow
from frontend.components.settings import Settings


def main():
    """Main application entry point."""
    app = QApplication(sys.argv)
    app.setApplicationName("Local AI Assistant Platform")
    
    # Load settings
    settings = Settings()
    
    # Create and show main window
    window = MainWindow()
    window.show()
    
    # Run application
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
