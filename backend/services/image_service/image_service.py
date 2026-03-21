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

    async def health(self) -> bool:
        """Return True if the Auto1111 backend is reachable."""
        if not self.adapter:
            return False
        return await self.adapter.health()

    async def generate(self, prompt: str, **kwargs) -> Dict[str, Any]:
        """
        Generate an image.

        Args:
            prompt: Image generation prompt
            **kwargs: All additional parameters passed through to the adapter

        Returns:
            Dictionary with image path and metadata
        """
        if not self.adapter:
            raise RuntimeError("Image service adapter not initialized")

        # Use default model if not specified
        if kwargs.get("model") is None:
            kwargs["model"] = self.config.get("models.image.default", None)

        return await self.adapter.generate(prompt=prompt, **kwargs)

    async def img2img(self, prompt: str, init_image: str, **kwargs) -> Dict[str, Any]:
        """
        Run img2img or inpainting.

        Args:
            prompt: Image generation prompt
            init_image: Base64-encoded image or /images/ URL
            **kwargs: All additional parameters passed through to the adapter

        Returns:
            Dictionary with image path and metadata
        """
        if not self.adapter:
            raise RuntimeError("Image service adapter not initialized")

        if kwargs.get("model") is None:
            kwargs["model"] = self.config.get("models.image.default", None)

        return await self.adapter.img2img(prompt=prompt, init_image=init_image, **kwargs)

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

    async def list_samplers(self) -> List[str]:
        """List available samplers."""
        if not self.adapter:
            raise RuntimeError("Image service adapter not initialized")

        return await self.adapter.list_samplers()

    async def list_upscalers(self) -> List[str]:
        """List available upscalers."""
        if not self.adapter:
            raise RuntimeError("Image service adapter not initialized")

        return await self.adapter.list_upscalers()

    async def list_styles(self) -> List[str]:
        """List available prompt styles."""
        if not self.adapter:
            raise RuntimeError("Image service adapter not initialized")

        return await self.adapter.list_styles()
