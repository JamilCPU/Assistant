"""Filesystem tools: search_files, read_file."""

import os
from pathlib import Path
from typing import Any, Dict

from backend.services.chat_service.tools.base import Tool
from backend.services.chat_service.tools.guardrails import get_guardrails


class SearchFilesTool(Tool):
    """Tool for searching files."""
    
    def __init__(self):
        """Initialize search files tool."""
        super().__init__(
            name="search_files",
            description="Search for files by name or pattern within allowed directories",
            schema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search query (filename or pattern)"
                    }
                },
                "required": ["query"]
            },
            required_permissions=["search_files"]
        )
        self.guardrails = get_guardrails()
    
    async def execute(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute file search.
        
        Args:
            args: Tool arguments with 'query' key
            
        Returns:
            Dictionary with 'files' list
        """
        query = args.get("query", "")
        if not query:
            return {"files": [], "error": "Query is required"}
        
        results = []
        allowlist = self.guardrails.allowlist
        
        for allowed_dir in allowlist:
            allowed_path = Path(allowed_dir).resolve()
            
            if not allowed_path.exists():
                continue
            
            # Search recursively
            try:
                for root, dirs, files in os.walk(allowed_path):
                    # Filter files matching query
                    for file in files:
                        if query.lower() in file.lower():
                            file_path = Path(root) / file
                            try:
                                # Verify it's still in allowlist
                                if self.guardrails.is_path_allowed(file_path):
                                    results.append(str(file_path))
                            except Exception:
                                continue
            except PermissionError:
                # Skip directories we can't access
                continue
        
        # Limit results to prevent overwhelming response
        results = results[:50]
        
        return {
            "files": results,
            "count": len(results)
        }


class ReadFileTool(Tool):
    """Tool for reading files."""
    
    def __init__(self):
        """Initialize read file tool."""
        super().__init__(
            name="read_file",
            description="Read the contents of a file within allowed directories",
            schema={
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Path to the file to read"
                    }
                },
                "required": ["path"]
            },
            required_permissions=["read_file"]
        )
        self.guardrails = get_guardrails()
    
    async def execute(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute file read.
        
        Args:
            args: Tool arguments with 'path' key
            
        Returns:
            Dictionary with 'content' and 'path'
        """
        file_path_str = args.get("path", "")
        if not file_path_str:
            return {"error": "Path is required"}
        
        try:
            # Validate and normalize path
            file_path = self.guardrails.validate_file_path(file_path_str)
            
            # Check file size
            self.guardrails.check_file_size(file_path)
            
            # Read file
            if not file_path.exists():
                return {"error": f"File not found: {file_path}"}
            
            if not file_path.is_file():
                return {"error": f"Path is not a file: {file_path}"}
            
            # Try to read as text first
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                return {
                    "content": content,
                    "path": str(file_path),
                    "encoding": "utf-8"
                }
            except UnicodeDecodeError:
                # If text fails, return binary info
                return {
                    "error": "File is not a text file (binary content)",
                    "path": str(file_path),
                    "size": file_path.stat().st_size
                }
        
        except ValueError as e:
            return {"error": str(e)}
        except Exception as e:
            return {"error": f"Error reading file: {str(e)}"}
