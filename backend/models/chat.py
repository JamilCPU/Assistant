"""Chat request/response models."""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel


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
