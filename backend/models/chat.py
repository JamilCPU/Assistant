"""Chat request/response models."""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel


# ── Chat ──────────────────────────────────────────────────────────────────

class ChatRequest(BaseModel):
    """Chat request model."""
    message: str
    session_id: Optional[str] = None
    model: Optional[str] = None
    speak: bool = False  # TTS option
    system_prompt: Optional[str] = None


class ToolCall(BaseModel):
    """Tool call model."""
    name: str
    arguments: Dict[str, Any]


class ChatResponse(BaseModel):
    """Chat response model."""
    response: str
    session_id: str
    tool_calls: Optional[List[ToolCall]] = None
    audio_url: Optional[str] = None  # TTS audio URL if speak=True


# ── Conversations ─────────────────────────────────────────────────────────

class ConversationMessage(BaseModel):
    """Conversation message model."""
    id: int
    role: str
    content: str
    timestamp: str
    metadata: Optional[Dict[str, Any]] = None


class ConversationResponse(BaseModel):
    """Conversation response model."""
    session_id: str
    messages: List[ConversationMessage]


class SessionInfo(BaseModel):
    """Session information model."""
    session_id: str
    created_at: str
    last_activity: str
    title: Optional[str] = None


class SessionsListResponse(BaseModel):
    """Sessions list response model."""
    sessions: List[SessionInfo]


# ── Ollama status / models ────────────────────────────────────────────────

class OllamaStatusResponse(BaseModel):
    """Ollama health-check response."""
    online: bool
    model_count: int = 0


class OllamaModelInfo(BaseModel):
    """Summary info for one Ollama model."""
    name: str
    size: int = 0
    modified_at: str = ""
    family: str = ""
    parameter_size: str = ""
    quantization_level: str = ""


class OllamaModelDetail(BaseModel):
    """Detailed info returned by /api/show."""
    name: str
    family: str = ""
    parameter_size: str = ""
    quantization_level: str = ""
    format: str = ""
    template: str = ""
    system: str = ""
    license: str = ""
    modelfile: str = ""


class OllamaModelsListResponse(BaseModel):
    """List of Ollama models with metadata."""
    models: List[OllamaModelInfo]


class OllamaPullRequest(BaseModel):
    """Request to pull/download a model."""
    name: str
