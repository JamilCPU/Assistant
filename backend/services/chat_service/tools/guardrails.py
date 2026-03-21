"""Permission checks, path validation, and tool execution guardrails."""

import os
from pathlib import Path
from typing import List, Optional, Dict

from backend.storage.config import get_config


class Guardrails:
    """Manages guardrails for tool execution."""
    
    def __init__(self):
        """Initialize guardrails."""
        self.config = get_config()
        self.allowlist = self.config.get("tools.filesystem_allowlist", [])
        self.max_file_size_mb = self.config.get("tools.max_file_size_mb", 10)
        self.max_file_size_bytes = self.max_file_size_mb * 1024 * 1024
    
    def normalize_path(self, path: str) -> Path:
        """
        Normalize and resolve a file path.
        
        Args:
            path: Input path
            
        Returns:
            Normalized Path object
        """
        # Convert to absolute path
        abs_path = Path(path).resolve()
        return abs_path
    
    def is_path_allowed(self, path: Path) -> bool:
        """
        Check if a path is within the allowlist.
        
        Args:
            path: Path to check
            
        Returns:
            True if path is allowed
        """
        # Normalize allowlist paths
        allowed_paths = [Path(p).resolve() for p in self.allowlist]
        
        # Check if path is within any allowed directory
        for allowed_path in allowed_paths:
            try:
                # Check if path is a subpath of allowed path
                path.relative_to(allowed_path)
                return True
            except ValueError:
                # Path is not within this allowed directory
                continue
        
        return False
    
    def validate_file_path(self, file_path: str) -> Path:
        """
        Validate and normalize a file path.
        
        Args:
            file_path: File path to validate
            
        Returns:
            Normalized Path object
            
        Raises:
            ValueError: If path is not allowed
        """
        normalized = self.normalize_path(file_path)

        if not self.is_path_allowed(normalized) and not self.is_path_in_uploads(normalized):
            raise ValueError(f"Path {normalized} is not in the allowlist")

        return normalized
    
    def check_file_size(self, file_path: Path) -> None:
        """
        Check if file size is within limits.
        
        Args:
            file_path: Path to file
            
        Raises:
            ValueError: If file is too large
        """
        if not file_path.exists():
            return
        
        size = file_path.stat().st_size
        if size > self.max_file_size_bytes:
            raise ValueError(
                f"File {file_path} is too large: {size / 1024 / 1024:.2f}MB "
                f"(max: {self.max_file_size_mb}MB)"
            )
    
    def check_permissions(self, required_permissions: List[str], mode: str = "local") -> bool:
        """
        Check if required permissions are available.
        
        Args:
            required_permissions: List of required permission names
            mode: Permission mode (local or remote)
            
        Returns:
            True if all permissions are available
        """
        if not required_permissions:
            return True
        
        # In local mode, all permissions are available
        if mode == "local":
            return True
        
        # In remote mode, check against restricted permissions
        if mode == "remote":
            restricted_permissions = self.config.get("permissions.remote_mode", "restricted")
            if restricted_permissions == "restricted":
                # Only allow safe operations in remote mode
                safe_permissions = ["read_file", "search_files"]
                return all(perm in safe_permissions for perm in required_permissions)
        
        return True
    
    def validate_tool_call(self, tool_name: str, args: Dict, mode: str = "local") -> None:
        """
        Validate a tool call before execution.

        Args:
            tool_name: Name of the tool
            args: Tool arguments
            mode: Permission mode ("local" or "remote")

        Raises:
            ValueError: If tool call is not allowed in this mode
        """
        if mode == "remote":
            restricted = self.config.get("permissions.remote_mode", "restricted")
            if restricted == "restricted":
                safe_tools = {"read_file", "search_files", "web_search", "list_uploads"}
                if tool_name not in safe_tools:
                    raise ValueError(
                        f"Tool '{tool_name}' is not available in remote mode. "
                        f"Allowed tools: {', '.join(sorted(safe_tools))}"
                    )

    def is_path_in_uploads(self, path: Path) -> bool:
        """Return True if the path is within the uploads directory (always allowed)."""
        uploads_dir = Path("./backend/storage/data/uploads").resolve()
        try:
            path.relative_to(uploads_dir)
            return True
        except ValueError:
            return False


# Global guardrails instance
_guardrails: Optional[Guardrails] = None


def get_guardrails() -> Guardrails:
    """Get global guardrails instance."""
    global _guardrails
    if _guardrails is None:
        _guardrails = Guardrails()
    return _guardrails
