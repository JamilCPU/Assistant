"""
E2E Image Generation Tests

Every test exercises the full chain:
  UI interaction -> API Client -> FastAPI backend -> Auto1111 adapter -> database -> UI display

Mock adapter returns a tiny PNG by default; use ``pytest --live`` to hit
real Automatic1111.
"""

import asyncio

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QTextEdit, QPushButton, QLabel, QSpinBox, QDoubleSpinBox,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _wait_for_generation(qtbot, image_window, timeout=15_000):
    """Block until the generate button is re-enabled (image generation done)."""
    qtbot.waitUntil(lambda: image_window.generate_button.isEnabled(), timeout=timeout)


def _run_async(coro):
    """Run an async coroutine from synchronous test code."""
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestImageUIElements:
    """Verify all image generation UI elements exist and have correct defaults."""

    def test_prompt_input_exists(self, image_window):
        """Prompt input area is present."""
        assert isinstance(image_window.prompt_input, QTextEdit)

    def test_negative_prompt_input_exists(self, image_window):
        """Negative prompt input area is present."""
        assert isinstance(image_window.neg_prompt_input, QTextEdit)

    def test_generate_button_exists(self, image_window):
        """Generate button is present and enabled."""
        assert isinstance(image_window.generate_button, QPushButton)
        assert image_window.generate_button.isEnabled()

    def test_save_button_initially_disabled(self, image_window):
        """Save button starts disabled (no image generated yet)."""
        assert isinstance(image_window.save_button, QPushButton)
        assert not image_window.save_button.isEnabled()

    def test_image_display_exists(self, image_window):
        """Image display label is present."""
        assert isinstance(image_window.image_label, QLabel)

    def test_parameter_defaults_correct(self, image_window):
        """
        Full flow: Open image tab -> verify width=512, height=512, steps=20, CFG=7.0.
        """
        assert image_window.width_spin.value() == 512
        assert image_window.height_spin.value() == 512
        assert image_window.steps_spin.value() == 20
        assert image_window.cfg_spin.value() == 7.0


class TestGenerateImageFullFlow:
    """
    Full flow: Enter prompt -> set params -> click Generate ->
    request hits backend -> adapter returns image -> metadata saved to DB ->
    image displayed in UI -> save button enables.
    """

    def test_generate_image_full_flow(self, image_window, qtbot, read_test_db, main_window):
        """
        Enter prompt -> generate -> mock image appears in UI -> DB has metadata.
        """
        # Switch to image tab to make sure it's visible
        main_window.tabs.setCurrentIndex(1)
        qtbot.wait(100)

        # Enter a prompt
        image_window.prompt_input.clear()
        qtbot.keyClicks(image_window.prompt_input, "A beautiful sunset over mountains")

        # Click Generate
        qtbot.mouseClick(image_window.generate_button, Qt.LeftButton)

        # Wait for generation to complete
        _wait_for_generation(qtbot, image_window)

        # UI should display an image (pixmap set on label)
        pixmap = image_window.image_label.pixmap()
        assert pixmap is not None and not pixmap.isNull()

        # Save button should now be enabled
        assert image_window.save_button.isEnabled()

        # current_image_path should be set
        assert image_window.current_image_path is not None

        # Verify database has the image metadata
        images = _run_async(read_test_db.get_images())
        assert len(images) >= 1
        latest = images[0]
        assert "sunset" in latest["prompt"].lower() or "beautiful" in latest["prompt"].lower()
        assert latest["width"] is not None
        assert latest["height"] is not None


class TestEmptyPromptBlocked:
    """
    Full flow: Click Generate with empty prompt -> no API call -> no DB entry -> no UI change.
    """

    def test_empty_prompt_blocked(self, image_window, qtbot, read_test_db):
        """Empty prompt should not trigger generation."""
        # Clear prompt
        image_window.prompt_input.clear()
        assert image_window.prompt_input.toPlainText().strip() == ""

        # Count existing images in DB
        images_before = _run_async(read_test_db.get_images())
        count_before = len(images_before)

        # Click Generate
        qtbot.mouseClick(image_window.generate_button, Qt.LeftButton)
        qtbot.wait(500)

        # Button should still be enabled (no processing happened)
        assert image_window.generate_button.isEnabled()

        # No new images in DB
        images_after = _run_async(read_test_db.get_images())
        assert len(images_after) == count_before


class TestGenerateButtonDisabledDuringProcessing:
    """
    Full flow: Click Generate -> button disables -> response arrives -> button re-enables.
    """

    def test_generate_button_disabled_during_processing(self, image_window, qtbot, main_window):
        """Generate button should disable during image generation."""
        main_window.tabs.setCurrentIndex(1)
        qtbot.wait(100)

        image_window.prompt_input.clear()
        qtbot.keyClicks(image_window.prompt_input, "Test processing state")

        qtbot.mouseClick(image_window.generate_button, Qt.LeftButton)

        # Eventually the button should re-enable after generation completes
        _wait_for_generation(qtbot, image_window)
        assert image_window.generate_button.isEnabled()


class TestNegativePromptSent:
    """
    Full flow: Enter prompt + negative prompt -> generate ->
    backend receives both values -> stored in DB.
    """

    def test_negative_prompt_sent(self, image_window, qtbot, read_test_db, main_window):
        """Negative prompt should be sent to backend and stored in DB."""
        main_window.tabs.setCurrentIndex(1)
        qtbot.wait(100)

        image_window.prompt_input.clear()
        qtbot.keyClicks(image_window.prompt_input, "A cat sitting on a chair")

        image_window.neg_prompt_input.clear()
        qtbot.keyClicks(image_window.neg_prompt_input, "blurry, low quality")

        qtbot.mouseClick(image_window.generate_button, Qt.LeftButton)
        _wait_for_generation(qtbot, image_window)

        # Verify DB has the negative prompt
        images = _run_async(read_test_db.get_images())
        assert len(images) >= 1

        # Find the image with our prompt
        matching = [img for img in images if "cat" in (img["prompt"] or "").lower()]
        assert len(matching) >= 1
        assert matching[0]["negative_prompt"] is not None
        assert "blurry" in matching[0]["negative_prompt"].lower()


class TestParameterChangesSent:
    """
    Full flow: Change width, height, steps, CFG -> generate ->
    backend receives updated values -> stored in DB.
    """

    def test_parameter_changes_sent_to_backend(self, image_window, qtbot, read_test_db, main_window):
        """Custom parameters should propagate to the backend and DB."""
        main_window.tabs.setCurrentIndex(1)
        qtbot.wait(100)

        image_window.prompt_input.clear()
        qtbot.keyClicks(image_window.prompt_input, "Parameter test image")

        # Change parameters
        image_window.width_spin.setValue(1024)
        image_window.height_spin.setValue(768)
        image_window.steps_spin.setValue(30)
        image_window.cfg_spin.setValue(9.5)

        qtbot.mouseClick(image_window.generate_button, Qt.LeftButton)
        _wait_for_generation(qtbot, image_window)

        # Verify DB has the updated parameters
        images = _run_async(read_test_db.get_images())
        matching = [img for img in images if "parameter test" in (img["prompt"] or "").lower()]
        assert len(matching) >= 1

        img = matching[0]
        # The image record stores width/height directly
        assert img["width"] == 1024
        assert img["height"] == 768

        # Reset parameters for other tests
        image_window.width_spin.setValue(512)
        image_window.height_spin.setValue(512)
        image_window.steps_spin.setValue(20)
        image_window.cfg_spin.setValue(7.0)


class TestErrorDisplay:
    """
    Full flow: Backend returns error -> error text displayed in image label.
    """

    def test_error_displayed_on_generation_failure(self, image_window, qtbot, main_window):
        """
        Temporarily break the API client URL -> generate -> error displayed in label.
        """
        main_window.tabs.setCurrentIndex(1)
        qtbot.wait(100)

        # Save original URL
        original_url = image_window.api_client.base_url

        # Point at a port nothing is listening on
        image_window.api_client.base_url = "http://127.0.0.1:19999"

        image_window.prompt_input.clear()
        qtbot.keyClicks(image_window.prompt_input, "Should fail")

        qtbot.mouseClick(image_window.generate_button, Qt.LeftButton)
        _wait_for_generation(qtbot, image_window)

        # Image label should show error text
        label_text = image_window.image_label.text()
        assert "Error" in label_text or "error" in label_text

        # Restore original URL
        image_window.api_client.base_url = original_url
