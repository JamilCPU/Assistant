"""Image generation request/response models."""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel


class ImageGenerateRequest(BaseModel):
    """Image generation request model."""
    prompt: str
    negative_prompt: Optional[str] = None
    model: Optional[str] = None          # checkpoint name
    width: int = 512
    height: int = 512
    steps: int = 20
    cfg_scale: float = 7.0
    sampler: Optional[str] = None
    lora: Optional[List[str]] = None
    seed: int = -1                        # -1 = random
    batch_size: int = 1                   # images per batch
    batch_count: int = 1                  # n_iter
    restore_faces: bool = False
    tiling: bool = False
    clip_skip: int = 1                    # CLIP stop at N layers
    # Hires fix
    enable_hr: bool = False
    hr_scale: float = 2.0
    hr_upscaler: Optional[str] = None
    hr_second_pass_steps: int = 0
    denoising_strength: float = 0.7
    hr_resize_x: int = 0
    hr_resize_y: int = 0
    # Styles
    styles: Optional[List[str]] = None


class ImageGenerateResponse(BaseModel):
    """Image generation response model."""
    image_path: str
    image_url: Optional[str] = None
    images: List[str] = []     # all image URLs (batch)
    metadata: Dict[str, Any]
    filename: str


class ImageInfo(BaseModel):
    """Image information model."""
    id: int
    filename: str
    filepath: str
    prompt: str
    negative_prompt: Optional[str] = None
    model_name: Optional[str] = None
    lora_used: Optional[List[str]] = None
    parameters: Dict[str, Any]
    created_at: str
    file_size: int
    width: int
    height: int


class ImagesListResponse(BaseModel):
    """Images list response model."""
    images: List[ImageInfo]


class ImagesPaginatedResponse(BaseModel):
    """Paginated images list response model."""
    images: List[ImageInfo]
    total: int
    page: int
    per_page: int


class Img2ImgRequest(BaseModel):
    """img2img / inpainting request model."""
    prompt: str
    negative_prompt: Optional[str] = None
    model: Optional[str] = None
    width: int = 512
    height: int = 512
    steps: int = 20
    cfg_scale: float = 7.0
    sampler: Optional[str] = None
    lora: Optional[List[str]] = None
    seed: int = -1
    batch_size: int = 1
    restore_faces: bool = False
    tiling: bool = False
    clip_skip: int = 1
    styles: Optional[List[str]] = None
    # img2img specific
    init_image: str                       # base64 or /images/ URL
    denoising_strength: float = 0.75
    resize_mode: int = 0                  # 0=just resize, 1=crop+resize, 2=resize+fill
    # Inpainting
    mask: Optional[str] = None            # base64 PNG mask
    mask_blur: int = 4
    inpainting_fill: int = 1              # 0=fill, 1=original, 2=latent noise, 3=latent nothing
    inpaint_full_res: bool = True
    inpaint_full_res_padding: int = 32


class Img2ImgResponse(BaseModel):
    """img2img / inpainting response model."""
    image_path: str
    image_url: Optional[str] = None
    images: List[str] = []
    metadata: Dict[str, Any]
    filename: str
