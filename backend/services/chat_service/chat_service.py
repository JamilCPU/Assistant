"""Chat service implementation."""

from typing import Any, AsyncGenerator, Dict, List, Optional

from backend.services.base import ChatService
from backend.services.chat_service.adapters.ollama_adapter import OllamaAdapter
from backend.storage.config import get_config


class ChatServiceManager:
    """Manages chat service and adapter lifecycle."""
    
    def __init__(self):
        """Initialize chat service manager."""
        self.config = get_config()
        self.adapter: Optional[OllamaAdapter] = None
        self._initialize_adapter()
    
    def _initialize_adapter(self) -> None:
        """Initialize the chat service adapter."""
        ollama_url = self.config.get("models.chat.ollama_url", "http://localhost:11434")
        self.adapter = OllamaAdapter(ollama_url)

    def _require_adapter(self) -> OllamaAdapter:
        if not self.adapter:
            raise RuntimeError("Chat service adapter not initialized")
        return self.adapter

    # ── Health ────────────────────────────────────────────────────────────

    async def health(self) -> bool:
        """Check if Ollama is reachable."""
        return await self._require_adapter().health()

    # ── Non-streaming generate ────────────────────────────────────────────

    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        messages: Optional[List[Dict[str, str]]] = None,
        tools: Optional[List[Dict[str, Any]]] = None,
        model: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Generate a chat response.
        
        Pass `messages` (full conversation history) to maintain context across turns.
        If omitted, only the current `prompt` is sent to the model.
        """
        adapter = self._require_adapter()
        if model is None:
            model = self.config.get("models.chat.default", "llama3")
        return await adapter.generate(
            prompt=prompt,
            system_prompt=system_prompt,
            messages=messages,
            tools=tools,
            model=model,
            **kwargs
        )

    # ── Streaming generate ────────────────────────────────────────────────

    async def generate_stream(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        messages: Optional[List[Dict[str, str]]] = None,
        tools: Optional[List[Dict[str, Any]]] = None,
        model: Optional[str] = None,
        **kwargs
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """Stream a chat response token-by-token.
        
        Pass `messages` (full conversation history) to maintain context across turns.
        If omitted, only the current `prompt` is sent to the model.
        """
        adapter = self._require_adapter()
        if model is None:
            model = self.config.get("models.chat.default", "llama3")
        async for chunk in adapter.generate_stream(
            prompt=prompt,
            system_prompt=system_prompt,
            messages=messages,
            tools=tools,
            model=model,
            **kwargs
        ):
            yield chunk

    # ── Model listing ─────────────────────────────────────────────────────

    async def list_models(self) -> List[str]:
        """List available models (names only)."""
        return await self._require_adapter().list_models()

    async def list_models_detailed(self) -> List[Dict[str, Any]]:
        """List available models with metadata."""
        return await self._require_adapter().list_models_detailed()

    # ── Model management ──────────────────────────────────────────────────

    async def pull_model(self, name: str) -> AsyncGenerator[Dict[str, Any], None]:
        """Pull a model, yielding progress."""
        async for chunk in self._require_adapter().pull_model(name):
            yield chunk

    async def delete_model(self, name: str) -> bool:
        """Delete a model."""
        return await self._require_adapter().delete_model(name)

    async def show_model(self, name: str) -> Dict[str, Any]:
        """Show detailed model info."""
        return await self._require_adapter().show_model(name)
