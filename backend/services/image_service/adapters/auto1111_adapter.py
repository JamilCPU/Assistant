"""Automatic1111 adapter for image generation service."""

import base64
import httpx
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from backend.services.base import ImageService


class Auto1111Adapter(ImageService):
    """Adapter for Automatic1111 Stable Diffusion WebUI."""
    
    def __init__(self, base_url: str = "http://localhost:7860", save_path: str = "./backend/storage/data/images"):
        """
        Initialize Auto1111 adapter.
        
        Args:
            base_url: Automatic1111 API base URL
            save_path: Path to save generated images
        """
        self.base_url = base_url.rstrip('/')
        self.save_path = Path(save_path)
        self.save_path.mkdir(parents=True, exist_ok=True)
        self.client = httpx.AsyncClient(timeout=300.0)  # 5 minute timeout
    
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
        Generate an image using Automatic1111.
        
        Args:
            prompt: Image generation prompt
            negative_prompt: Optional negative prompt
            model: Optional checkpoint name
            width: Image width
            height: Image height
            steps: Number of inference steps
            cfg_scale: CFG scale value
            sampler: Sampler name
            lora: Optional list of LoRA names
            **kwargs: Additional parameters
            
        Returns:
            Dictionary with image_path and metadata
        """
        # Prepare request body for txt2img
        body = {
            "prompt": prompt,
            "negative_prompt": negative_prompt or "",
            "width": width,
            "height": height,
            "steps": steps,
            "cfg_scale": cfg_scale,
            "sampler_name": sampler or "Euler a",
            "save_images": False,  # We'll save manually
            "send_images": True
        }
        
        # Add LoRAs if specified
        if lora:
            # Auto1111 uses special syntax for LoRAs in prompt
            lora_prompts = [f"<lora:{l}:1.0>" for l in lora]
            body["prompt"] = ", ".join(lora_prompts) + ", " + body["prompt"]
        
        # Add checkpoint if specified
        if model:
            # Note: Auto1111 checkpoint switching might require separate API call
            # For now, assume checkpoint is already loaded
            pass
        
        # Add any additional parameters
        body.update(kwargs)
        
        try:
            response = await self.client.post(
                f"{self.base_url}/sdapi/v1/txt2img",
                json=body
            )
            response.raise_for_status()
            data = response.json()
            
            # Get generated image (base64 encoded)
            images = data.get("images", [])
            if not images:
                raise RuntimeError("No images generated")
            
            # Decode and save image
            image_data = base64.b64decode(images[0])
            
            # Generate filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"image_{timestamp}.png"
            filepath = self.save_path / filename
            
            # Save image
            with open(filepath, 'wb') as f:
                f.write(image_data)
            
            # Get image info/metadata
            info = data.get("info", "{}")
            
            return {
                "image_path": str(filepath),
                "image_url": None,  # Could be served via static file endpoint
                "metadata": {
                    "prompt": prompt,
                    "negative_prompt": negative_prompt,
                    "width": width,
                    "height": height,
                    "steps": steps,
                    "cfg_scale": cfg_scale,
                    "sampler": sampler or "Euler a",
                    "lora": lora,
                    "info": info
                },
                "filename": filename
            }
        
        except httpx.HTTPStatusError as e:
            raise RuntimeError(f"Auto1111 API error: {e.response.status_code} - {e.response.text}")
        except httpx.RequestError as e:
            raise RuntimeError(f"Auto1111 connection error: {str(e)}")
        except Exception as e:
            raise RuntimeError(f"Error generating image: {str(e)}")
    
    async def list_models(self) -> List[str]:
        """
        List available checkpoints.
        
        Returns:
            List of checkpoint names
        """
        try:
            response = await self.client.get(f"{self.base_url}/sdapi/v1/sd-models")
            response.raise_for_status()
            data = response.json()
            
            models = []
            for model_info in data:
                models.append(model_info.get("title", model_info.get("model_name", "")))
            
            return models
        
        except Exception:
            # If we can't list models, return empty list
            return []
    
    async def list_loras(self) -> List[str]:
        """
        List available LoRAs.
        
        Returns:
            List of LoRA names
        """
        try:
            response = await self.client.get(f"{self.base_url}/sdapi/v1/loras")
            response.raise_for_status()
            data = response.json()
            
            loras = []
            for lora_info in data:
                loras.append(lora_info.get("name", ""))
            
            return loras
        
        except Exception:
            # If we can't list LoRAs, return empty list
            return []
