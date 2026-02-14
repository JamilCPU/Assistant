"""TTS service implementation."""

from typing import Any, Dict, List, Optional

from backend.services.base import TTSService
from backend.services.tts_service.adapters.piper_adapter import PiperAdapter
from backend.storage.config import get_config


class TTSServiceManager:
    """Manages TTS service and adapter lifecycle."""
    
    def __init__(self):
        """Initialize TTS service manager."""
        self.config = get_config()
        self.adapter: Optional[TTSService] = None
        self._initialize_adapter()
    
    def _initialize_adapter(self) -> None:
        """Initialize the TTS service adapter."""
        piper_path = self.config.get("models.tts.piper_path", "./piper")
        self.adapter = PiperAdapter(piper_path)
    
    async def speak(
        self,
        text: str,
        voice: Optional[str] = None,
        speed: float = 1.0,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Convert text to speech.
        
        Args:
            text: Text to convert to speech
            voice: Optional voice name/ID
            speed: Speech speed multiplier
            **kwargs: Additional model-specific parameters
            
        Returns:
            Dictionary with audio path and metadata
        """
        if not self.adapter:
            raise RuntimeError("TTS service adapter not initialized")
        
        # Use default voice if not specified
        if voice is None:
            voice = self.config.get("models.tts.default_voice", "en_US-lessac-medium")
        
        return await self.adapter.speak(
            text=text,
            voice=voice,
            speed=speed,
            **kwargs
        )
    
    async def list_voices(self) -> List[str]:
        """List available voices."""
        if not self.adapter:
            raise RuntimeError("TTS service adapter not initialized")
        
        return await self.adapter.list_voices()
