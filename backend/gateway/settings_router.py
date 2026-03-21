"""Settings API endpoints."""

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from backend.gateway.auth import verify_api_key
from backend.storage.config import get_config

settings_router = APIRouter()


# ── Pydantic models ───────────────────────────────────────────────────────


class ChatSettings(BaseModel):
    default_model: str = ""
    system_prompt: str = ""


class ImageSettings(BaseModel):
    default_model: str = ""
    default_sampler: str = "Euler a"
    default_steps: int = 20
    default_cfg: float = 7.0
    default_width: int = 512
    default_height: int = 512


class TTSSettings(BaseModel):
    enabled: bool = True
    default_voice: str = "en_US-lessac-medium"


class ToolsSettings(BaseModel):
    filesystem_allowlist: List[str] = []
    max_file_size_mb: int = 10


class ServerSettings(BaseModel):
    api_key: str = ""


class UserSettings(BaseModel):
    chat: ChatSettings = ChatSettings()
    image: ImageSettings = ImageSettings()
    tts: TTSSettings = TTSSettings()
    tools: ToolsSettings = ToolsSettings()
    server: ServerSettings = ServerSettings()


class PartialChatSettings(BaseModel):
    default_model: Optional[str] = None
    system_prompt: Optional[str] = None


class PartialImageSettings(BaseModel):
    default_model: Optional[str] = None
    default_sampler: Optional[str] = None
    default_steps: Optional[int] = None
    default_cfg: Optional[float] = None
    default_width: Optional[int] = None
    default_height: Optional[int] = None


class PartialTTSSettings(BaseModel):
    enabled: Optional[bool] = None
    default_voice: Optional[str] = None


class PartialToolsSettings(BaseModel):
    filesystem_allowlist: Optional[List[str]] = None
    max_file_size_mb: Optional[int] = None


class PartialServerSettings(BaseModel):
    api_key: Optional[str] = None


class UpdateSettingsRequest(BaseModel):
    chat: Optional[PartialChatSettings] = None
    image: Optional[PartialImageSettings] = None
    tts: Optional[PartialTTSSettings] = None
    tools: Optional[PartialToolsSettings] = None
    server: Optional[PartialServerSettings] = None


# ── Helpers ───────────────────────────────────────────────────────────────


def get_user_settings() -> Dict[str, Any]:
    """Read user-facing config values from ConfigManager."""
    cfg = get_config()
    return {
        "chat": {
            "default_model": cfg.get("models.chat.default", ""),
            "system_prompt": cfg.get("chat.system_prompt", ""),
        },
        "image": {
            "default_model": cfg.get("models.image.default", ""),
            "default_sampler": cfg.get("image.default_sampler", "Euler a"),
            "default_steps": cfg.get("image.default_steps", 20),
            "default_cfg": cfg.get("image.default_cfg", 7.0),
            "default_width": cfg.get("image.default_width", 512),
            "default_height": cfg.get("image.default_height", 512),
        },
        "tts": {
            "enabled": cfg.get("tts.enabled", True),
            "default_voice": cfg.get("models.tts.default_voice", "en_US-lessac-medium"),
        },
        "tools": {
            "filesystem_allowlist": cfg.get("tools.filesystem_allowlist", []),
            "max_file_size_mb": cfg.get("tools.max_file_size_mb", 10),
        },
        "server": {
            "api_key": cfg.get("server.api_key", ""),
        },
    }


def update_user_settings(updates: UpdateSettingsRequest) -> None:
    """Write partial settings update to ConfigManager."""
    cfg = get_config()

    if updates.chat is not None:
        if updates.chat.default_model is not None:
            cfg.set("models.chat.default", updates.chat.default_model)
        if updates.chat.system_prompt is not None:
            cfg.set("chat.system_prompt", updates.chat.system_prompt)

    if updates.image is not None:
        if updates.image.default_model is not None:
            cfg.set("models.image.default", updates.image.default_model)
        if updates.image.default_sampler is not None:
            cfg.set("image.default_sampler", updates.image.default_sampler)
        if updates.image.default_steps is not None:
            cfg.set("image.default_steps", updates.image.default_steps)
        if updates.image.default_cfg is not None:
            cfg.set("image.default_cfg", updates.image.default_cfg)
        if updates.image.default_width is not None:
            cfg.set("image.default_width", updates.image.default_width)
        if updates.image.default_height is not None:
            cfg.set("image.default_height", updates.image.default_height)

    if updates.tts is not None:
        if updates.tts.enabled is not None:
            cfg.set("tts.enabled", updates.tts.enabled)
        if updates.tts.default_voice is not None:
            cfg.set("models.tts.default_voice", updates.tts.default_voice)

    if updates.tools is not None:
        if updates.tools.filesystem_allowlist is not None:
            cfg.set("tools.filesystem_allowlist", updates.tools.filesystem_allowlist)
        if updates.tools.max_file_size_mb is not None:
            cfg.set("tools.max_file_size_mb", updates.tools.max_file_size_mb)

    if updates.server is not None:
        if updates.server.api_key is not None:
            cfg.set("server.api_key", updates.server.api_key)


# ── Endpoints ─────────────────────────────────────────────────────────────


@settings_router.get("/api/settings", response_model=UserSettings)
async def get_settings(api_key: str = Depends(verify_api_key)) -> UserSettings:
    """Get user-facing settings."""
    data = get_user_settings()
    return UserSettings(**data)


@settings_router.put("/api/settings", response_model=UserSettings)
async def update_settings(
    request: UpdateSettingsRequest,
    api_key: str = Depends(verify_api_key),
) -> UserSettings:
    """Update user-facing settings (partial update supported)."""
    update_user_settings(request)
    data = get_user_settings()
    return UserSettings(**data)
