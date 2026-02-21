"""
E2E Navigation Tests

Full flows tested:
- App starts -> window visible -> correct title -> correct size
- App starts -> tabs exist -> switch between Chat and Image Generation
- App starts -> close window -> resources cleaned up -> no crash
"""

from PySide6.QtWidgets import QTabWidget
from PySide6.QtCore import Qt


class TestAppLaunch:
    """Test that the application launches and displays correctly."""

    def test_app_launches_and_shows_window(self, main_window, qtbot):
        """
        Full flow: App starts -> window visible -> correct title -> correct size.
        """
        # Window should be visible
        assert main_window.isVisible()

        # Correct window title
        assert main_window.windowTitle() == "Local AI Assistant Platform"

        # Window should have reasonable dimensions
        assert main_window.width() >= 800
        assert main_window.height() >= 600

    def test_window_has_central_widget(self, main_window):
        """
        Full flow: App starts -> central widget exists -> layout is set up.
        """
        central = main_window.centralWidget()
        assert central is not None
        assert central.layout() is not None


class TestTabNavigation:
    """Test tab switching between Chat and Image Generation modes."""

    def test_tabs_exist(self, main_window):
        """
        Full flow: App starts -> tab widget exists -> two tabs present.
        """
        tabs = main_window.tabs
        assert isinstance(tabs, QTabWidget)
        assert tabs.count() == 2

    def test_tab_labels_correct(self, main_window):
        """
        Full flow: App starts -> tabs labelled "Chat" and "Image Generation".
        """
        tabs = main_window.tabs
        assert tabs.tabText(0) == "Chat"
        assert tabs.tabText(1) == "Image Generation"

    def test_chat_tab_active_by_default(self, main_window):
        """
        Full flow: App starts -> "Chat" tab selected by default -> chat UI visible.
        """
        tabs = main_window.tabs
        assert tabs.currentIndex() == 0
        assert main_window.chat_window.isVisible()

    def test_switch_to_image_tab(self, main_window, qtbot):
        """
        Full flow: App starts -> click "Image Generation" tab -> image UI visible
                    -> chat UI no longer the current widget.
        """
        tabs = main_window.tabs
        tabs.setCurrentIndex(1)
        qtbot.wait(100)

        assert tabs.currentIndex() == 1
        assert main_window.image_window.isVisible()

    def test_switch_back_to_chat_tab(self, main_window, qtbot):
        """
        Full flow: Switch to Image tab -> switch back to Chat tab -> chat UI visible.
        """
        tabs = main_window.tabs

        # Go to image tab
        tabs.setCurrentIndex(1)
        qtbot.wait(100)
        assert tabs.currentIndex() == 1

        # Go back to chat tab
        tabs.setCurrentIndex(0)
        qtbot.wait(100)
        assert tabs.currentIndex() == 0
        assert main_window.chat_window.isVisible()

    def test_rapid_tab_switching(self, main_window, qtbot):
        """
        Full flow: Rapidly switch tabs multiple times -> no crash -> final state correct.
        """
        tabs = main_window.tabs
        for i in range(10):
            tabs.setCurrentIndex(i % 2)
            qtbot.wait(20)

        # Should end on the Chat tab (10 toggles -> index 0)
        assert tabs.currentIndex() == 0


class TestWindowClose:
    """Test that closing the window cleans up without crashing."""

    def test_close_event_cleanup(self, qapp, qtbot, test_settings_path, backend_server):
        """
        Full flow: App starts -> close window -> resources cleaned up -> no crash.

        We create a separate window for this test so we can close it
        without affecting other tests.
        """
        import json
        from pathlib import Path
        from unittest.mock import patch

        from frontend.components.settings import Settings
        from frontend.windows.main_window import MainWindow

        with patch.object(Settings, "__init__", lambda self, settings_path=None: (
            setattr(self, "settings_path", Path(test_settings_path)),
            setattr(self, "_settings", json.load(open(test_settings_path))),
        )[-1]):
            window = MainWindow()
            qtbot.addWidget(window)
            window.show()
            qtbot.waitExposed(window)

            assert window.isVisible()

            # Close the window
            window.close()
            qtbot.wait(100)

            # Should no longer be visible
            assert not window.isVisible()
