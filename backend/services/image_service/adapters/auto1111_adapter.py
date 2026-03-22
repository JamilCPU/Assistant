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
        seed: int = -1,
        batch_size: int = 1,
        batch_count: int = 1,
        restore_faces: bool = False,
        tiling: bool = False,
        clip_skip: int = 1,
        enable_hr: bool = False,
        hr_scale: float = 2.0,
        hr_upscaler: Optional[str] = None,
        hr_second_pass_steps: int = 0,
        denoising_strength: float = 0.7,
        hr_resize_x: int = 0,
        hr_resize_y: int = 0,
        styles: Optional[List[str]] = None,
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
            seed: Random seed (-1 for random)
            batch_size: Images per batch
            batch_count: Number of batches (n_iter)
            restore_faces: Enable face restoration
            tiling: Enable tiling
            clip_skip: CLIP stop at N layers
            enable_hr: Enable hires fix
            hr_scale: Hires fix upscale factor
            hr_upscaler: Hires fix upscaler name
            hr_second_pass_steps: Hires fix second pass steps
            denoising_strength: Denoising strength for hires fix
            hr_resize_x: Hires fix resize width (0 = use hr_scale)
            hr_resize_y: Hires fix resize height (0 = use hr_scale)
            styles: List of style names to apply
            **kwargs: Additional parameters

        Returns:
            Dictionary with image_path, image_url, images list, metadata, and filename
        """
        # Add LoRAs to prompt using Auto1111 syntax
        full_prompt = prompt
        if lora:
            lora_prompts = [f"<lora:{l}:1.0>" for l in lora]
            full_prompt = ", ".join(lora_prompts) + ", " + prompt

        # Prepare request body for txt2img
        body = {
            "prompt": full_prompt,
            "negative_prompt": negative_prompt or "",
            "seed": seed,
            "width": width,
            "height": height,
            "steps": steps,
            "cfg_scale": cfg_scale,
            "sampler_name": sampler or "Euler a",
            "batch_size": batch_size,
            "n_iter": batch_count,
            "restore_faces": restore_faces,
            "tiling": tiling,
            "save_images": False,
            "send_images": True,
            "styles": styles or [],
        }

        if enable_hr:
            body.update({
                "enable_hr": True,
                "hr_scale": hr_scale,
                "hr_upscaler": hr_upscaler or "Latent",
                "hr_second_pass_steps": hr_second_pass_steps,
                "denoising_strength": denoising_strength,
                "hr_resize_x": hr_resize_x,
                "hr_resize_y": hr_resize_y,
            })

        override = {}
        if model:
            override["sd_model_checkpoint"] = model
        if clip_skip > 1:
            override["CLIP_stop_at_last_layers"] = clip_skip
        if override:
            body["override_settings"] = override
            body["override_settings_restore_afterwards"] = True

        try:
            response = await self.client.post(
                f"{self.base_url}/sdapi/v1/txt2img",
                json=body
            )
            response.raise_for_status()
            data = response.json()

            # Get generated images (base64 encoded)
            images = data.get("images", [])
            if not images:
                raise RuntimeError("No images generated")

            # Generate timestamp for filenames
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

            all_filenames = []
            for idx, img_b64 in enumerate(images):
                image_data = base64.b64decode(img_b64)
                if idx == 0:
                    filename = f"image_{timestamp}.png"
                else:
                    filename = f"image_{timestamp}_{idx}.png"
                filepath = self.save_path / filename
                with open(filepath, 'wb') as f:
                    f.write(image_data)
                all_filenames.append(filename)

            first_filename = all_filenames[0]
            first_filepath = self.save_path / first_filename

            # Get image info/metadata
            info = data.get("info", "{}")

            return {
                "image_path": str(first_filepath),
                "image_url": f"/images/{first_filename}",
                "images": [f"/images/{fn}" for fn in all_filenames],
                "metadata": {
                    "prompt": prompt,
                    "negative_prompt": negative_prompt,
                    "width": width,
                    "height": height,
                    "steps": steps,
                    "cfg_scale": cfg_scale,
                    "sampler": sampler or "Euler a",
                    "lora": lora,
                    "seed": seed,
                    "batch_size": batch_size,
                    "batch_count": batch_count,
                    "restore_faces": restore_faces,
                    "tiling": tiling,
                    "clip_skip": clip_skip,
                    "enable_hr": enable_hr,
                    "model": model,
                    "info": info
                },
                "filename": first_filename,
            }

        except httpx.HTTPStatusError as e:
            raise RuntimeError(f"Auto1111 API error: {e.response.status_code} - {e.response.text}")
        except httpx.RequestError as e:
            raise RuntimeError(f"Auto1111 connection error: {str(e)}")
        except Exception as e:
            raise RuntimeError(f"Error generating image: {str(e)}")

    async def img2img(
        self,
        prompt: str,
        init_image: str,
        negative_prompt: Optional[str] = None,
        model: Optional[str] = None,
        width: int = 512,
        height: int = 512,
        steps: int = 20,
        cfg_scale: float = 7.0,
        sampler: Optional[str] = None,
        lora: Optional[List[str]] = None,
        seed: int = -1,
        batch_size: int = 1,
        restore_faces: bool = False,
        tiling: bool = False,
        clip_skip: int = 1,
        styles: Optional[List[str]] = None,
        denoising_strength: float = 0.75,
        resize_mode: int = 0,
        mask: Optional[str] = None,
        mask_blur: int = 4,
        inpainting_fill: int = 1,
        inpaint_full_res: bool = True,
        inpaint_full_res_padding: int = 32,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Run img2img (or inpainting when mask is provided) via Automatic1111.

        Args:
            prompt: Image generation prompt
            init_image: Base64-encoded image or a /images/<filename> URL
            negative_prompt: Optional negative prompt
            model: Optional checkpoint name
            width: Image width
            height: Image height
            steps: Number of inference steps
            cfg_scale: CFG scale value
            sampler: Sampler name
            lora: Optional list of LoRA names
            seed: Random seed (-1 for random)
            batch_size: Images per batch
            restore_faces: Enable face restoration
            tiling: Enable tiling
            clip_skip: CLIP stop at N layers
            styles: List of style names to apply
            denoising_strength: How much to deviate from the source image (0.0–1.0)
            resize_mode: 0=just resize, 1=crop+resize, 2=resize+fill
            mask: Base64-encoded PNG mask for inpainting (white=regenerate)
            mask_blur: Blur radius for mask edges
            inpainting_fill: Fill mode (0=fill, 1=original, 2=latent noise, 3=latent nothing)
            inpaint_full_res: Use full resolution for inpainting
            inpaint_full_res_padding: Padding in pixels for full-res inpainting
            **kwargs: Additional parameters (ignored)

        Returns:
            Dictionary with image_path, image_url, images list, metadata, and filename
        """
        # Resolve init_image: if it's a /images/ URL load from disk
        if init_image.startswith('/images/'):
            rel = init_image[len('/images/'):]  # e.g. "image_20240101_120000.png"
            file_path = self.save_path / rel
            with open(file_path, 'rb') as f:
                init_image_b64 = base64.b64encode(f.read()).decode('utf-8')
        else:
            init_image_b64 = init_image

        # Add LoRAs to prompt
        full_prompt = prompt
        if lora:
            lora_prompts = [f"<lora:{l}:1.0>" for l in lora]
            full_prompt = ", ".join(lora_prompts) + ", " + prompt

        body: Dict[str, Any] = {
            "init_images": [init_image_b64],
            "prompt": full_prompt,
            "negative_prompt": negative_prompt or "",
            "seed": seed,
            "width": width,
            "height": height,
            "steps": steps,
            "cfg_scale": cfg_scale,
            "sampler_name": sampler or "Euler a",
            "batch_size": batch_size,
            "denoising_strength": denoising_strength,
            "resize_mode": resize_mode,
            "restore_faces": restore_faces,
            "tiling": tiling,
            "styles": styles or [],
            "save_images": False,
            "send_images": True,
        }

        if mask:
            body.update({
                "mask": mask,
                "mask_blur": mask_blur,
                "inpainting_fill": inpainting_fill,
                "inpaint_full_res": inpaint_full_res,
                "inpaint_full_res_padding": inpaint_full_res_padding,
            })

        override: Dict[str, Any] = {}
        if model:
            override["sd_model_checkpoint"] = model
        if clip_skip > 1:
            override["CLIP_stop_at_last_layers"] = clip_skip
        if override:
            body["override_settings"] = override
            body["override_settings_restore_afterwards"] = True

        try:
            response = await self.client.post(
                f"{self.base_url}/sdapi/v1/img2img",
                json=body
            )
            response.raise_for_status()
            data = response.json()

            images = data.get("images", [])
            if not images:
                raise RuntimeError("No images generated")

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

            all_filenames = []
            for idx, img_b64 in enumerate(images):
                image_data = base64.b64decode(img_b64)
                if idx == 0:
                    filename = f"img2img_{timestamp}.png"
                else:
                    filename = f"img2img_{timestamp}_{idx}.png"
                filepath = self.save_path / filename
                with open(filepath, 'wb') as f:
                    f.write(image_data)
                all_filenames.append(filename)

            first_filename = all_filenames[0]
            first_filepath = self.save_path / first_filename
            info = data.get("info", "{}")

            return {
                "image_path": str(first_filepath),
                "image_url": f"/images/{first_filename}",
                "images": [f"/images/{fn}" for fn in all_filenames],
                "metadata": {
                    "prompt": prompt,
                    "negative_prompt": negative_prompt,
                    "width": width,
                    "height": height,
                    "steps": steps,
                    "cfg_scale": cfg_scale,
                    "sampler": sampler or "Euler a",
                    "lora": lora,
                    "seed": seed,
                    "batch_size": batch_size,
                    "restore_faces": restore_faces,
                    "tiling": tiling,
                    "clip_skip": clip_skip,
                    "model": model,
                    "denoising_strength": denoising_strength,
                    "resize_mode": resize_mode,
                    "has_mask": mask is not None,
                    "info": info,
                },
                "filename": first_filename,
            }

        except httpx.HTTPStatusError as e:
            raise RuntimeError(f"Auto1111 API error: {e.response.status_code} - {e.response.text}")
        except httpx.RequestError as e:
            raise RuntimeError(f"Auto1111 connection error: {str(e)}")
        except Exception as e:
            raise RuntimeError(f"Error in img2img: {str(e)}")

    async def health(self) -> bool:
        """Return True if Automatic1111 is reachable with API enabled."""
        try:
            response = await self.client.get(f"{self.base_url}/sdapi/v1/sd-models", timeout=5.0)
            return response.status_code == 200
        except Exception:
            return False

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
            return []

    async def list_samplers(self) -> List[str]:
        """
        List available samplers.

        Returns:
            List of sampler name strings
        """
        try:
            response = await self.client.get(f"{self.base_url}/sdapi/v1/samplers")
            response.raise_for_status()
            data = response.json()
            return [s.get("name", "") for s in data if s.get("name")]
        except Exception:
            return []

    async def list_upscalers(self) -> List[str]:
        """
        List available upscalers.

        Returns:
            List of upscaler name strings
        """
        try:
            response = await self.client.get(f"{self.base_url}/sdapi/v1/upscalers")
            response.raise_for_status()
            data = response.json()
            return [u.get("name", "") for u in data if u.get("name")]
        except Exception:
            return []

    async def list_styles(self) -> List[str]:
        """
        List available prompt styles.

        Returns:
            List of style name strings
        """
        try:
            response = await self.client.get(f"{self.base_url}/sdapi/v1/prompt-styles")
            response.raise_for_status()
            data = response.json()
            return [s.get("name", "") for s in data if s.get("name")]
        except Exception:
            return []

    async def refresh_checkpoints(self) -> bool:
        """
        Tell Automatic1111 to rescan its models directory for new checkpoints.

        Returns:
            True if the refresh succeeded, False otherwise.
        """
        try:
            response = await self.client.post(
                f"{self.base_url}/sdapi/v1/refresh-checkpoints",
                json={},
                timeout=30.0,
            )
            return response.status_code == 200
        except Exception:
            return False
