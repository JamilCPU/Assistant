"""HTTP client for communicating with FastAPI backend."""

import httpx
from typing import Any, Dict, Optional


class APIClient:
    """Client for FastAPI backend."""
    
    def __init__(self, base_url: str = "http://localhost:8000", api_key: Optional[str] = None):
        """
        Initialize API client.
        
        Args:
            base_url: FastAPI server base URL
            api_key: API key for authentication
        """
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        self.client = httpx.AsyncClient(timeout=300.0)
    
    def _get_headers(self) -> Dict[str, str]:
        """Get request headers with API key."""
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["X-API-Key"] = self.api_key
        return headers
    
    async def chat(
        self,
        message: str,
        session_id: Optional[str] = None,
        model: Optional[str] = None,
        speak: bool = False,
        system_prompt: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Send chat message.
        
        Args:
            message: User message
            session_id: Optional session ID
            model: Optional model name
            speak: Whether to generate TTS
            system_prompt: Optional system prompt
            
        Returns:
            Chat response dictionary
        """
        response = await self.client.post(
            f"{self.base_url}/api/chat",
            json={
                "message": message,
                "session_id": session_id,
                "model": model,
                "speak": speak,
                "system_prompt": system_prompt
            },
            headers=self._get_headers()
        )
        response.raise_for_status()
        return response.json()
    
    async def generate_image(
        self,
        prompt: str,
        negative_prompt: Optional[str] = None,
        model: Optional[str] = None,
        width: int = 512,
        height: int = 512,
        steps: int = 20,
        cfg_scale: float = 7.0,
        sampler: Optional[str] = None,
        lora: Optional[list] = None
    ) -> Dict[str, Any]:
        """
        Generate an image.
        
        Args:
            prompt: Image generation prompt
            negative_prompt: Optional negative prompt
            model: Optional model name
            width: Image width
            height: Image height
            steps: Number of steps
            cfg_scale: CFG scale
            sampler: Sampler name
            lora: Optional LoRA list
            
        Returns:
            Image generation response
        """
        response = await self.client.post(
            f"{self.base_url}/api/image/generate",
            json={
                "prompt": prompt,
                "negative_prompt": negative_prompt,
                "model": model,
                "width": width,
                "height": height,
                "steps": steps,
                "cfg_scale": cfg_scale,
                "sampler": sampler,
                "lora": lora
            },
            headers=self._get_headers()
        )
        response.raise_for_status()
        return response.json()
    
    async def list_models(self) -> Dict[str, Any]:
        """List available models."""
        response = await self.client.get(
            f"{self.base_url}/api/models",
            headers=self._get_headers()
        )
        response.raise_for_status()
        return response.json()
    
    async def list_tools(self) -> Dict[str, Any]:
        """List available tools."""
        response = await self.client.get(
            f"{self.base_url}/api/tools",
            headers=self._get_headers()
        )
        response.raise_for_status()
        return response.json()
    
    async def list_conversations(self) -> Dict[str, Any]:
        """List conversation sessions."""
        response = await self.client.get(
            f"{self.base_url}/api/conversations",
            headers=self._get_headers()
        )
        response.raise_for_status()
        return response.json()
    
    async def get_conversation(self, session_id: str) -> Dict[str, Any]:
        """Get conversation messages."""
        response = await self.client.get(
            f"{self.base_url}/api/conversations/{session_id}",
            headers=self._get_headers()
        )
        response.raise_for_status()
        return response.json()
    
    async def list_images(self) -> Dict[str, Any]:
        """List generated images."""
        response = await self.client.get(
            f"{self.base_url}/api/images",
            headers=self._get_headers()
        )
        response.raise_for_status()
        return response.json()
    
    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()
