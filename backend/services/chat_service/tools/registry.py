"""Tool registry system."""

from typing import Dict, List, Optional, Any

from backend.services.chat_service.tools.base import Tool
from backend.services.chat_service.tools.filesystem import (
    DeleteFileTool,
    GetFileInfoTool,
    ListDirectoryTool,
    ListUploadsTool,
    MoveFileTool,
    ReadFileTool,
    SearchFilesTool,
    WriteFileTool,
)
from backend.services.chat_service.tools.web import FetchUrlTool, WebSearchTool
from backend.services.chat_service.tools.system import LaunchAppTool


class ToolRegistry:
    """Manages tool registration and lookup."""
    
    def __init__(self):
        """Initialize tool registry."""
        self._tools: Dict[str, Tool] = {}
        self._register_default_tools()
    
    def _register_default_tools(self) -> None:
        """Register default tools.

        HOW TO ADD A NEW TOOL:
          1. Create a class in the appropriate tools/*.py file that extends Tool.
          2. Implement __init__ (name, description, schema, required_permissions)
             and async execute(args) -> dict.
          3. Import it here and call self.register(YourTool()) below.
          That's it — the tool is automatically included in every chat request.
        """
        # Filesystem — read
        self.register(SearchFilesTool())
        self.register(ReadFileTool())
        self.register(ListDirectoryTool())
        self.register(GetFileInfoTool())

        # Filesystem — write
        self.register(WriteFileTool())
        self.register(DeleteFileTool())
        self.register(MoveFileTool())

        # Uploads
        self.register(ListUploadsTool())

        # Web tools
        self.register(WebSearchTool())
        self.register(FetchUrlTool())

        # System tools
        self.register(LaunchAppTool())
    
    def register(self, tool: Tool) -> None:
        """
        Register a tool.
        
        Args:
            tool: Tool instance to register
        """
        self._tools[tool.name] = tool
    
    def get_tool(self, name: str) -> Optional[Tool]:
        """
        Get a tool by name.
        
        Args:
            name: Tool name
            
        Returns:
            Tool instance or None if not found
        """
        return self._tools.get(name)
    
    def list_tools(self) -> List[str]:
        """
        List all registered tool names.
        
        Returns:
            List of tool names
        """
        return list(self._tools.keys())
    
    def get_tool_schemas(self) -> List[Dict]:
        """
        Get JSON schemas for all tools (for LLM function calling).
        
        Returns:
            List of tool schemas
        """
        return [tool.get_schema() for tool in self._tools.values()]
    
    async def execute_tool(self, name: str, args: Dict) -> Any:
        """
        Execute a tool.
        
        Args:
            name: Tool name
            args: Tool arguments
            
        Returns:
            Tool execution result
            
        Raises:
            ValueError: If tool not found
        """
        tool = self.get_tool(name)
        if not tool:
            raise ValueError(f"Tool '{name}' not found")
        
        return await tool.execute(args)


# Global tool registry instance
_registry: Optional[ToolRegistry] = None


def get_registry() -> ToolRegistry:
    """Get global tool registry instance."""
    global _registry
    if _registry is None:
        _registry = ToolRegistry()
    return _registry
