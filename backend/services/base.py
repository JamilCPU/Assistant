"""Base service interfaces for all model services."""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional


class ChatService(ABC):
    """Base interface for chat/LLM services."""
    
    @abstractmethod
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
            Dictionary with:
                - text: Generated response text
                - tool_calls: Optional list of tool calls from LLM
                - finish_reason: Reason for completion
        """
        pass
    
    @abstractmethod
    async def list_models(self) -> List[str]:
        """List available models."""
        pass


class ImageService(ABC):
    """Base interface for image generation services."""
    
    @abstractmethod
    async def generate(
        self,
        prompt: str,
        negative_prompt: Optional[str] = None,
        model: Optional[str] = None,
        width: int = 512,
        height: int = 512,
        steps: int = 20,
        cfg_scale: float = 7.0,
        sampler: Optional[str] = None,
        lora: Optional[List[str]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Generate an image.
        
        Args:
            prompt: Image generation prompt
            negative_prompt: Optional negative prompt
            model: Optional model/checkpoint name
            width: Image width
            height: Image height
            steps: Number of inference steps
            cfg_scale: CFG scale value
            sampler: Sampler name
            lora: Optional list of LoRA names to apply
            **kwargs: Additional model-specific parameters
            
        Returns:
            Dictionary with:
                - image_path: Path to saved image file
                - image_url: Optional URL to image
                - metadata: Generation metadata
        """
        pass
    
    @abstractmethod
    async def list_models(self) -> List[str]:
        """List available models/checkpoints."""
        pass
    
    @abstractmethod
    async def list_loras(self) -> List[str]:
        """List available LoRAs."""
        pass


class TTSService(ABC):
    """Base interface for text-to-speech services."""
    
    @abstractmethod
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
            Dictionary with:
                - audio_path: Path to audio file
                - audio_url: Optional URL to audio
                - duration: Audio duration in seconds
        """
        pass
    
    @abstractmethod
    async def list_voices(self) -> List[str]:
        """List available voices."""
        pass
