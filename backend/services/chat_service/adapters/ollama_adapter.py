"""Ollama adapter for chat service."""

import httpx
from typing import Any, Dict, List, Optional

from backend.services.base import ChatService


class OllamaAdapter(ChatService):
    """Adapter for Ollama LLM service."""
    
    def __init__(self, base_url: str = "http://localhost:11434"):
        """
        Initialize Ollama adapter.
        
        Args:
            base_url: Ollama API base URL
        """
        self.base_url = base_url.rstrip('/')
        self.client = httpx.AsyncClient(timeout=300.0)  # 5 minute timeout for long generations
    
    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        tools: Optional[List[Dict[str, Any]]] = None,
        model: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Generate a chat response using Ollama.
        
        Args:
            prompt: User message/prompt
            system_prompt: Optional system prompt
            tools: Optional list of tool schemas for function calling
            model: Model name (defaults to llama3)
            **kwargs: Additional parameters
            
        Returns:
            Dictionary with text, tool_calls, and finish_reason
        """
        model = model or "llama3"
        
        # Build messages
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        # Prepare request body
        body = {
            "model": model,
            "messages": messages,
            "stream": False
        }
        
        # Add tools if provided (Ollama supports function calling)
        if tools:
            # Convert tool schemas to Ollama format
            functions = []
            for tool_schema in tools:
                if "function" in tool_schema:
                    functions.append(tool_schema["function"])
            
            if functions:
                body["tools"] = functions
        
        # Add any additional parameters
        body.update(kwargs)
        
        try:
            response = await self.client.post(
                f"{self.base_url}/api/chat",
                json=body
            )
            response.raise_for_status()
            data = response.json()
            
            # Extract response
            message = data.get("message", {})
            content = message.get("content", "")
            tool_calls = message.get("tool_calls", [])
            
            # Convert Ollama tool calls to standard format
            formatted_tool_calls = []
            for tool_call in tool_calls:
                formatted_tool_calls.append({
                    "name": tool_call.get("function", {}).get("name", ""),
                    "arguments": tool_call.get("function", {}).get("arguments", {})
                })
            
            return {
                "text": content,
                "tool_calls": formatted_tool_calls if formatted_tool_calls else None,
                "finish_reason": data.get("done", True) and "stop" or "length",
                "model": model
            }
        
        except httpx.HTTPStatusError as e:
            raise RuntimeError(f"Ollama API error: {e.response.status_code} - {e.response.text}")
        except httpx.RequestError as e:
            raise RuntimeError(f"Ollama connection error: {str(e)}")
    
    async def list_models(self) -> List[str]:
        """
        List available Ollama models.
        
        Returns:
            List of model names
        """
        try:
            response = await self.client.get(f"{self.base_url}/api/tags")
            response.raise_for_status()
            data = response.json()
            
            models = []
            for model_info in data.get("models", []):
                models.append(model_info.get("name", ""))
            
            return models
        
        except Exception as e:
            # If we can't list models, return empty list
            return []
