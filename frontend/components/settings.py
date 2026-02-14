"""Settings management for frontend."""

import json
from pathlib import Path
from typing import Any, Dict, Optional


class Settings:
    """Manages frontend settings."""
    
    def __init__(self, settings_path: Optional[str] = None):
        """
        Initialize settings.
        
        Args:
            settings_path: Path to settings file
        """
        if settings_path is None:
            base_dir = Path(__file__).parent.parent.parent
            settings_path = base_dir / "frontend" / "settings.json"
        
        self.settings_path = Path(settings_path)
        self._settings: Dict[str, Any] = self._load()
    
    def _load(self) -> Dict[str, Any]:
        """Load settings from file."""
        if self.settings_path.exists():
            try:
                with open(self.settings_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception:
                pass
        
        # Default settings
        return {
            "api_url": "http://localhost:8000",
            "api_key": "",
            "window_width": 1200,
            "window_height": 800
        }
    
    def _save(self) -> None:
        """Save settings to file."""
        self.settings_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.settings_path, 'w', encoding='utf-8') as f:
            json.dump(self._settings, f, indent=2)
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get setting value."""
        return self._settings.get(key, default)
    
    def set(self, key: str, value: Any) -> None:
        """Set setting value."""
        self._settings[key] = value
        self._save()
    
    def get_all(self) -> Dict[str, Any]:
        """Get all settings."""
        return self._settings.copy()
