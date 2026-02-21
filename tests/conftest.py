"""
Shared test infrastructure.

Provides:
- --live pytest flag for running against real services
- Test database (temporary SQLite, not production)
- FastAPI test server on port 8111
- Mock adapters for Ollama, Auto1111, Piper (default; skipped with --live)
"""

import asyncio
import json
import os
import shutil
import tempfile
import threading
import time
from pathlib import Path
from typing import Any, Dict, List, Optional
from unittest.mock import AsyncMock, patch

import pytest
import uvicorn
from PIL import Image

# ---------------------------------------------------------------------------
# pytest CLI option: --live
# ---------------------------------------------------------------------------

def pytest_addoption(parser):
    parser.addoption(
        "--live",
        action="store_true",
        default=False,
        help="Run tests against live Ollama/Auto1111/Piper services instead of mocks.",
    )


@pytest.fixture(scope="session")
def live_mode(request):
    """True when --live flag is passed."""
    return request.config.getoption("--live")


# ---------------------------------------------------------------------------
# Temporary directories & test database
# ---------------------------------------------------------------------------

@pytest.fixture(scope="session")
def tmp_test_dir():
    """Create a temporary directory tree for the entire test session."""
    d = tempfile.mkdtemp(prefix="assistant_test_")
    (Path(d) / "images").mkdir()
    (Path(d) / "audio").mkdir()
    (Path(d) / "db").mkdir()
    yield d
    shutil.rmtree(d, ignore_errors=True)


@pytest.fixture(scope="session")
def test_db_path(tmp_test_dir):
    """Path to the temporary test database."""
    return str(Path(tmp_test_dir) / "db" / "test.db")


@pytest.fixture(scope="session")
def test_images_dir(tmp_test_dir):
    """Path to temporary image output directory."""
    return str(Path(tmp_test_dir) / "images")


@pytest.fixture(scope="session")
def test_audio_dir(tmp_test_dir):
    """Path to temporary audio output directory."""
    return str(Path(tmp_test_dir) / "audio")


# ---------------------------------------------------------------------------
# Test config file
# ---------------------------------------------------------------------------

@pytest.fixture(scope="session")
def test_config_path(tmp_test_dir, test_db_path, test_images_dir):
    """Write a test config JSON and return its path."""
    config = {
        "server": {
            "host": "127.0.0.1",
            "port": 8111,
            "api_key": "test-key"
        },
        "models": {
            "chat": {
                "default": "llama3",
                "ollama_url": "http://localhost:11434"
            },
            "image": {
                "default": "stable-diffusion-xl",
                "auto1111_url": "http://localhost:7860",
                "save_path": test_images_dir
            },
            "tts": {
                "default_voice": "en_US-lessac-medium",
                "piper_path": "./piper"
            }
        },
        "tools": {
            "filesystem_allowlist": [tmp_test_dir],
            "max_file_size_mb": 10
        },
        "permissions": {
            "local_mode": "full",
            "remote_mode": "restricted"
        },
        "storage": {
            "data_dir": tmp_test_dir,
            "images_dir": test_images_dir,
            "conversations_db": test_db_path
        }
    }
    path = str(Path(tmp_test_dir) / "test_config.json")
    with open(path, "w") as f:
        json.dump(config, f)
    return path


# ---------------------------------------------------------------------------
# Mock adapters (canned responses for Ollama, Auto1111, Piper)
# ---------------------------------------------------------------------------

def _create_test_image(directory: str, width: int = 64, height: int = 64) -> str:
    """Create a tiny PNG in *directory* and return its path."""
    from datetime import datetime
    ts = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    filename = f"image_{ts}.png"
    filepath = Path(directory) / filename
    img = Image.new("RGB", (width, height), color=(128, 128, 255))
    img.save(str(filepath))
    return str(filepath), filename


class MockOllamaAdapter:
    """Returns canned chat responses."""

    async def generate(self, prompt, system_prompt=None, tools=None, model=None, **kw):
        return {
            "text": f"Mock assistant response to: {prompt}",
            "tool_calls": None,
            "finish_reason": "stop",
            "model": model or "llama3",
        }

    async def list_models(self):
        return ["llama3", "mistral"]


class MockAuto1111Adapter:
    """Returns a tiny generated PNG."""

    def __init__(self, save_path: str):
        self.save_path = save_path

    async def generate(self, prompt, negative_prompt=None, model=None,
                       width=512, height=512, steps=20, cfg_scale=7.0,
                       sampler=None, lora=None, **kw):
        filepath, filename = _create_test_image(self.save_path, width=64, height=64)
        return {
            "image_path": filepath,
            "image_url": None,
            "metadata": {
                "prompt": prompt,
                "negative_prompt": negative_prompt,
                "width": width,
                "height": height,
                "steps": steps,
                "cfg_scale": cfg_scale,
                "sampler": sampler or "Euler a",
                "lora": lora,
            },
            "filename": filename,
        }

    async def list_models(self):
        return ["sd-xl-base-1.0", "deliberate-v2"]

    async def list_loras(self):
        return ["detail-tweaker", "add-detail"]


class MockPiperAdapter:
    """Returns a dummy audio path."""

    def __init__(self, audio_dir: str):
        self.audio_dir = audio_dir

    async def speak(self, text, voice=None, speed=1.0, **kw):
        from datetime import datetime
        ts = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        audio_path = str(Path(self.audio_dir) / f"tts_{ts}.wav")
        # Write a minimal WAV header (44 bytes) so the file exists
        with open(audio_path, "wb") as f:
            f.write(b"\x00" * 44)
        return {
            "audio_path": audio_path,
            "audio_url": None,
            "duration": len(text) * 0.1,
            "voice": voice or "en_US-lessac-medium",
            "text_length": len(text),
        }

    async def list_voices(self):
        return ["en_US-lessac-medium", "en_US-lessac-low"]


# ---------------------------------------------------------------------------
# FastAPI test server (runs in a background thread)
# ---------------------------------------------------------------------------

def _reset_singletons():
    """Reset global singletons so they pick up the test config / DB."""
    import backend.storage.config as cfg_mod
    import backend.storage.database as db_mod
    cfg_mod._config_manager = None
    db_mod._db = None


@pytest.fixture(scope="session")
def backend_server(test_config_path, test_db_path, test_images_dir, test_audio_dir, live_mode):
    """
    Start the real FastAPI app on port 8111 with a temp DB.

    External service adapters are mocked unless --live is passed.
    """

    # Point the config singleton at our test config BEFORE importing the app
    _reset_singletons()

    import backend.storage.config as cfg_mod
    cfg_mod._config_manager = cfg_mod.ConfigManager(test_config_path)

    import backend.storage.database as db_mod
    db_mod._db = db_mod.Database(test_db_path)

    # Patch adapters unless running live
    patches = []
    if not live_mode:
        mock_ollama = MockOllamaAdapter()
        mock_auto1111 = MockAuto1111Adapter(test_images_dir)
        mock_piper = MockPiperAdapter(test_audio_dir)

        patches.append(patch(
            "backend.services.chat_service.chat_service.ChatServiceManager._initialize_adapter",
            lambda self: setattr(self, "adapter", mock_ollama),
        ))
        patches.append(patch(
            "backend.services.image_service.image_service.ImageServiceManager._initialize_adapter",
            lambda self: setattr(self, "adapter", mock_auto1111),
        ))
        patches.append(patch(
            "backend.services.tts_service.tts_service.TTSServiceManager._initialize_adapter",
            lambda self: setattr(self, "adapter", mock_piper),
        ))

    for p in patches:
        p.start()

    # Now import the app (after singletons and patches are in place)
    import importlib
    import backend.gateway.router as router_mod
    importlib.reload(router_mod)
    import backend.gateway.main as main_mod
    importlib.reload(main_mod)

    app = main_mod.app

    config = uvicorn.Config(app, host="127.0.0.1", port=8111, log_level="warning")
    server = uvicorn.Server(config)

    thread = threading.Thread(target=server.run, daemon=True)
    thread.start()

    # Wait for server to be ready
    import httpx
    for _ in range(50):
        try:
            r = httpx.get("http://127.0.0.1:8111/docs", timeout=1.0)
            if r.status_code == 200:
                break
        except Exception:
            pass
        time.sleep(0.2)
    else:
        raise RuntimeError("Test backend did not start within 10 seconds")

    yield "http://127.0.0.1:8111"

    # Teardown
    server.should_exit = True
    thread.join(timeout=5)
    for p in patches:
        p.stop()
    _reset_singletons()


# ---------------------------------------------------------------------------
# Helpers for verifying database state
# ---------------------------------------------------------------------------

@pytest.fixture()
def read_test_db(test_db_path):
    """Return an async helper that queries the test database."""
    import aiosqlite

    class DBReader:
        async def get_messages(self, session_id: str) -> list:
            async with aiosqlite.connect(test_db_path) as db:
                db.row_factory = aiosqlite.Row
                async with db.execute(
                    "SELECT * FROM conversations WHERE session_id = ? ORDER BY timestamp ASC",
                    (session_id,),
                ) as cursor:
                    return [dict(row) for row in await cursor.fetchall()]

        async def get_all_messages(self) -> list:
            async with aiosqlite.connect(test_db_path) as db:
                db.row_factory = aiosqlite.Row
                async with db.execute(
                    "SELECT * FROM conversations ORDER BY timestamp ASC"
                ) as cursor:
                    return [dict(row) for row in await cursor.fetchall()]

        async def get_images(self) -> list:
            async with aiosqlite.connect(test_db_path) as db:
                db.row_factory = aiosqlite.Row
                async with db.execute(
                    "SELECT * FROM generated_images ORDER BY created_at DESC"
                ) as cursor:
                    return [dict(row) for row in await cursor.fetchall()]

        async def get_tool_executions(self, session_id: str) -> list:
            async with aiosqlite.connect(test_db_path) as db:
                db.row_factory = aiosqlite.Row
                async with db.execute(
                    "SELECT * FROM tool_executions WHERE session_id = ?",
                    (session_id,),
                ) as cursor:
                    return [dict(row) for row in await cursor.fetchall()]

    return DBReader()
