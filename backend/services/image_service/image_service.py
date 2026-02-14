"""Image service implementation."""

from typing import Any, Dict, List, Optional

from backend.services.base import ImageService
from backend.services.image_service.adapters.auto1111_adapter import Auto1111Adapter
from backend.storage.config import get_config


class ImageServiceManager:
    """Manages image service and adapter lifecycle."""
    
    def __init__(self):
        """Initialize image service manager."""
        self.config = get_config()
        self.adapter: Optional[ImageService] = None
        self._initialize_adapter()
    
    def _initialize_adapter(self) -> None:
        """Initialize the image service adapter."""
        auto1111_url = self.config.get("models.image.auto1111_url", "http://localhost:7860")
        save_path = self.config.get("models.image.save_path", "./backend/storage/data/images")
        self.adapter = Auto1111Adapter(auto1111_url, save_path)
    
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
            Dictionary with image path and metadata
        """
        if not self.adapter:
            raise RuntimeError("Image service adapter not initialized")
        
        # Use default model if not specified
        if model is None:
            model = self.config.get("models.image.default", "stable-diffusion-xl")
        
        return await self.adapter.generate(
            prompt=prompt,
            negative_prompt=negative_prompt,
            model=model,
            width=width,
            height=height,
            steps=steps,
            cfg_scale=cfg_scale,
            sampler=sampler,
            lora=lora,
            **kwargs
        )
    
    async def list_models(self) -> List[str]:
        """List available models/checkpoints."""
        if not self.adapter:
            raise RuntimeError("Image service adapter not initialized")
        
        return await self.adapter.list_models()
    
    async def list_loras(self) -> List[str]:
        """List available LoRAs."""
        if not self.adapter:
            raise RuntimeError("Image service adapter not initialized")
        
        return await self.adapter.list_loras()
