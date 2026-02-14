"""Image generation request/response models."""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel


class ImageGenerateRequest(BaseModel):
    """Image generation request model."""
    prompt: str
    negative_prompt: Optional[str] = None
    model: Optional[str] = None
    width: int = 512
    height: int = 512
    steps: int = 20
    cfg_scale: float = 7.0
    sampler: Optional[str] = None
    lora: Optional[List[str]] = None


class ImageGenerateResponse(BaseModel):
    """Image generation response model."""
    image_path: str
    image_url: Optional[str] = None
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
