"""Tool schema models."""

from typing import Any, Dict, List
from pydantic import BaseModel


class ToolSchema(BaseModel):
    """Tool schema model."""
    name: str
    description: str
    parameters: Dict[str, Any]


class ToolsListResponse(BaseModel):
    """Tools list response model."""
    tools: List[ToolSchema]
