"""System tools: launch_app."""

import json
import subprocess
from pathlib import Path
from typing import Any, Dict

from backend.services.chat_service.tools.base import Tool


class LaunchAppTool(Tool):
    """Tool for launching applications."""
    
    def __init__(self):
        """Initialize launch app tool."""
        super().__init__(
            name="launch_app",
            description="Launch an application from the whitelist",
            schema={
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "Application name from registry"
                    }
                },
                "required": ["name"]
            },
            required_permissions=["launch_app"]
        )
        self._load_registry()
    
    def _load_registry(self) -> None:
        """Load application registry from config."""
        base_dir = Path(__file__).parent.parent.parent.parent.parent
        registry_path = base_dir / "config" / "app_registry.json"
        
        try:
            if registry_path.exists():
                with open(registry_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.registry = data.get("applications", {})
            else:
                self.registry = {}
        except Exception:
            self.registry = {}
    
    async def execute(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute app launch.
        
        Args:
            args: Tool arguments with 'name' key
            
        Returns:
            Dictionary with launch result
        """
        app_name = args.get("name", "")
        if not app_name:
            return {"error": "Application name is required"}
        
        # Check if app is in registry
        app_info = self.registry.get(app_name)
        if not app_info:
            available = list(self.registry.keys())
            return {
                "error": f"Application '{app_name}' not found in registry",
                "available_apps": available
            }
        
        try:
            # Get app path and args
            app_path = app_info.get("path", "")
            app_args = app_info.get("args", [])
            
            if not app_path:
                return {"error": f"Application '{app_name}' has no path configured"}
            
            # Launch application
            # Use subprocess.Popen to launch in background
            process = subprocess.Popen(
                [app_path] + app_args,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                creationflags=subprocess.CREATE_NO_WINDOW if hasattr(subprocess, 'CREATE_NO_WINDOW') else 0
            )
            
            return {
                "success": True,
                "app_name": app_name,
                "display_name": app_info.get("name", app_name),
                "pid": process.pid
            }
        
        except FileNotFoundError:
            return {
                "error": f"Application executable not found: {app_path}",
                "app_name": app_name
            }
        except Exception as e:
            return {
                "error": f"Error launching application: {str(e)}",
                "app_name": app_name
            }
