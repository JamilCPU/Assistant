"""Chat service implementation."""

from typing import Any, Dict, List, Optional

from backend.services.base import ChatService
from backend.services.chat_service.adapters.ollama_adapter import OllamaAdapter
from backend.storage.config import get_config


class ChatServiceManager:
    """Manages chat service and adapter lifecycle."""
    
    def __init__(self):
        """Initialize chat service manager."""
        self.config = get_config()
        self.adapter: Optional[ChatService] = None
        self._initialize_adapter()
    
    def _initialize_adapter(self) -> None:
        """Initialize the chat service adapter."""
        ollama_url = self.config.get("models.chat.ollama_url", "http://localhost:11434")
        self.adapter = OllamaAdapter(ollama_url)
    
    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        tools: Optional[List[Dict[str, Any]]] = None,
        model: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Generate a chat response.
        
        Args:
            prompt: User message/prompt
            system_prompt: Optional system prompt
            tools: Optional list of tool schemas for function calling
            model: Optional model name override
            **kwargs: Additional model-specific parameters
            
        Returns:
            Dictionary with response and tool calls
        """
        if not self.adapter:
            raise RuntimeError("Chat service adapter not initialized")
        
        # Use default model if not specified
        if model is None:
            model = self.config.get("models.chat.default", "llama3")
        
        return await self.adapter.generate(
            prompt=prompt,
            system_prompt=system_prompt,
            tools=tools,
            model=model,
            **kwargs
        )
    
    async def list_models(self) -> List[str]:
        """List available models."""
        if not self.adapter:
            raise RuntimeError("Chat service adapter not initialized")
        
        return await self.adapter.list_models()
