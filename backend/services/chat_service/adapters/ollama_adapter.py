"""Ollama adapter for chat service."""

import httpx
from typing import Any, AsyncGenerator, Dict, List, Optional

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
    
    # ── Health ────────────────────────────────────────────────────────────

    async def health(self) -> bool:
        """
        Check if Ollama is reachable.
        
        Returns:
            True if Ollama responds, False otherwise
        """
        try:
            response = await self.client.get(self.base_url, timeout=5.0)
            return response.status_code == 200
        except Exception:
            return False

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
        """
        Generate a chat response using Ollama.
        
        Args:
            prompt: Current user message (used only when messages is None)
            system_prompt: Optional system prompt (used only when messages is None)
            messages: Full conversation history as Ollama message objects.
                      When provided, overrides prompt/system_prompt.
            tools: Optional list of tool schemas for function calling
            model: Model name (defaults to llama3)
            **kwargs: Additional parameters
            
        Returns:
            Dictionary with text, tool_calls, and finish_reason
        """
        model = model or "llama3"
        
        if messages is None:
            messages = self._build_messages(prompt, system_prompt)
        body = self._build_body(model, messages, tools, stream=False, **kwargs)
        
        try:
            response = await self.client.post(
                f"{self.base_url}/api/chat",
                json=body
            )
            response.raise_for_status()
            data = response.json()
            
            message = data.get("message", {})
            content = message.get("content", "")
            tool_calls = message.get("tool_calls", [])
            formatted_tool_calls = self._format_tool_calls(tool_calls)
            
            return {
                "text": content,
                "tool_calls": formatted_tool_calls if formatted_tool_calls else None,
                "finish_reason": "stop" if data.get("done", True) else "length",
                "model": model
            }
        
        except httpx.HTTPStatusError as e:
            raise RuntimeError(f"Ollama API error: {e.response.status_code} - {e.response.text}")
        except httpx.RequestError as e:
            raise RuntimeError(f"Ollama connection error: {str(e)}")

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
        """
        Stream a chat response token-by-token from Ollama.

        Args:
            prompt: Current user message (used only when messages is None)
            system_prompt: Optional system prompt (used only when messages is None)
            messages: Full conversation history as Ollama message objects.
                      When provided, overrides prompt/system_prompt.

        Yields dicts with one of:
            {"type": "token",     "content": "..."}
            {"type": "tool_call", "name": "...", "arguments": {...}}
            {"type": "done",      "model": "..."}
        """
        model = model or "llama3"

        if messages is None:
            messages = self._build_messages(prompt, system_prompt)
        body = self._build_body(model, messages, tools, stream=True, **kwargs)

        try:
            async with self.client.stream(
                "POST",
                f"{self.base_url}/api/chat",
                json=body,
                timeout=300.0,
            ) as response:
                response.raise_for_status()

                async for line in response.aiter_lines():
                    if not line.strip():
                        continue

                    import json
                    chunk = json.loads(line)

                    # Token content
                    message = chunk.get("message", {})
                    content = message.get("content", "")
                    tool_calls_raw = message.get("tool_calls", [])

                    if content:
                        yield {"type": "token", "content": content}

                    # Tool calls (emitted in the final chunk)
                    if tool_calls_raw:
                        for tc in self._format_tool_calls(tool_calls_raw):
                            yield {"type": "tool_call", **tc}

                    # Done flag
                    if chunk.get("done", False):
                        yield {"type": "done", "model": model}
                        return

        except httpx.HTTPStatusError as e:
            raise RuntimeError(f"Ollama API error: {e.response.status_code} - {e.response.text}")
        except httpx.RequestError as e:
            raise RuntimeError(f"Ollama connection error: {str(e)}")

    # ── Detailed model listing ────────────────────────────────────────────

    async def list_models(self) -> List[str]:
        """
        List available Ollama models (names only).
        
        Returns:
            List of model names
        """
        try:
            response = await self.client.get(f"{self.base_url}/api/tags")
            response.raise_for_status()
            data = response.json()
            
            return [m.get("name", "") for m in data.get("models", [])]
        
        except Exception:
            return []

    async def list_models_detailed(self) -> List[Dict[str, Any]]:
        """
        List available Ollama models with metadata.

        Returns:
            List of dicts with name, size, modified_at, family, parameter_size, quantization_level
        """
        try:
            response = await self.client.get(f"{self.base_url}/api/tags")
            response.raise_for_status()
            data = response.json()

            models = []
            for m in data.get("models", []):
                details = m.get("details", {})
                models.append({
                    "name": m.get("name", ""),
                    "size": m.get("size", 0),
                    "modified_at": m.get("modified_at", ""),
                    "family": details.get("family", ""),
                    "parameter_size": details.get("parameter_size", ""),
                    "quantization_level": details.get("quantization_level", ""),
                })
            return models

        except Exception:
            return []

    # ── Pull model ────────────────────────────────────────────────────────

    async def pull_model(self, name: str) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Pull (download) a model from the Ollama library.

        Yields progress dicts: {"status": "...", "completed": int, "total": int}
        """
        try:
            async with self.client.stream(
                "POST",
                f"{self.base_url}/api/pull",
                json={"name": name, "stream": True},
                timeout=None,  # pulls can take a long time
            ) as response:
                response.raise_for_status()

                async for line in response.aiter_lines():
                    if not line.strip():
                        continue
                    import json
                    chunk = json.loads(line)
                    yield {
                        "status": chunk.get("status", ""),
                        "completed": chunk.get("completed", 0),
                        "total": chunk.get("total", 0),
                    }

        except httpx.HTTPStatusError as e:
            raise RuntimeError(f"Ollama pull error: {e.response.status_code} - {e.response.text}")
        except httpx.RequestError as e:
            raise RuntimeError(f"Ollama connection error: {str(e)}")

    # ── Delete model ──────────────────────────────────────────────────────

    async def delete_model(self, name: str) -> bool:
        """
        Delete a model from Ollama.

        Returns:
            True if deleted successfully
        """
        try:
            response = await self.client.request(
                "DELETE",
                f"{self.base_url}/api/delete",
                json={"name": name},
            )
            response.raise_for_status()
            return True
        except httpx.HTTPStatusError as e:
            raise RuntimeError(f"Ollama delete error: {e.response.status_code} - {e.response.text}")
        except httpx.RequestError as e:
            raise RuntimeError(f"Ollama connection error: {str(e)}")

    # ── Show model info ───────────────────────────────────────────────────

    async def show_model(self, name: str) -> Dict[str, Any]:
        """
        Get detailed information about a specific model.

        Returns:
            Dict with model info (parameters, template, family, etc.)
        """
        try:
            response = await self.client.post(
                f"{self.base_url}/api/show",
                json={"name": name},
            )
            response.raise_for_status()
            data = response.json()

            details = data.get("details", {})
            return {
                "name": name,
                "family": details.get("family", ""),
                "parameter_size": details.get("parameter_size", ""),
                "quantization_level": details.get("quantization_level", ""),
                "format": details.get("format", ""),
                "template": data.get("template", ""),
                "system": data.get("system", ""),
                "license": data.get("license", ""),
                "modelfile": data.get("modelfile", ""),
            }

        except httpx.HTTPStatusError as e:
            raise RuntimeError(f"Ollama show error: {e.response.status_code} - {e.response.text}")
        except httpx.RequestError as e:
            raise RuntimeError(f"Ollama connection error: {str(e)}")

    # ── Private helpers ───────────────────────────────────────────────────

    @staticmethod
    def _build_messages(prompt: str, system_prompt: Optional[str] = None) -> List[Dict[str, str]]:
        messages: List[Dict[str, str]] = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        return messages

    @staticmethod
    def _build_body(
        model: str,
        messages: List[Dict[str, str]],
        tools: Optional[List[Dict[str, Any]]] = None,
        stream: bool = False,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        body: Dict[str, Any] = {
            "model": model,
            "messages": messages,
            "stream": stream,
        }
        if tools:
            functions = [ts["function"] for ts in tools if "function" in ts]
            if functions:
                body["tools"] = functions
        body.update(kwargs)
        return body

    @staticmethod
    def _format_tool_calls(tool_calls: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        formatted = []
        for tc in tool_calls:
            formatted.append({
                "name": tc.get("function", {}).get("name", ""),
                "arguments": tc.get("function", {}).get("arguments", {}),
            })
        return formatted
