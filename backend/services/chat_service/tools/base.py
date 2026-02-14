"""Base tool interface."""

from abc import ABC, abstractmethod
from typing import Any, Dict, List


class Tool(ABC):
    """Base class for all tools."""
    
    def __init__(self, name: str, description: str, schema: Dict[str, Any], required_permissions: List[str] = None):
        """
        Initialize tool.
        
        Args:
            name: Tool name
            description: Tool description
            schema: JSON schema for tool arguments
            required_permissions: List of required permission names
        """
        self.name = name
        self.description = description
        self.schema = schema
        self.required_permissions = required_permissions or []
    
    @abstractmethod
    async def execute(self, args: Dict[str, Any]) -> Any:
        """
        Execute the tool.
        
        Args:
            args: Tool arguments (validated against schema)
            
        Returns:
            Tool execution result
        """
        pass
    
    def get_schema(self) -> Dict[str, Any]:
        """Get JSON schema for this tool."""
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.schema
            }
        }
