"""Configuration management using JSON files."""

import json
import os
from pathlib import Path
from typing import Any, Dict, Optional


class ConfigManager:
    """Manages application configuration from JSON files."""
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize config manager.
        
        Args:
            config_path: Path to config file. If None, uses default.
        """
        if config_path is None:
            # Default to config/default_config.json
            base_dir = Path(__file__).parent.parent.parent
            config_path = base_dir / "config" / "default_config.json"
        
        self.config_path = Path(config_path)
        self._config: Optional[Dict[str, Any]] = None
        self._load()
    
    def _load(self) -> None:
        """Load configuration from file."""
        if self.config_path.exists():
            with open(self.config_path, 'r', encoding='utf-8') as f:
                self._config = json.load(f)
        else:
            # Create default config if file doesn't exist
            self._config = self._get_default_config()
            self._save()
    
    def _save(self) -> None:
        """Save configuration to file."""
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.config_path, 'w', encoding='utf-8') as f:
            json.dump(self._config, f, indent=2)
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration."""
        return {
            "server": {
                "host": "0.0.0.0",
                "port": 8000
            },
            "models": {
                "chat": {
                    "default": "llama3",
                    "ollama_url": "http://localhost:11434"
                },
                "image": {
                    "default": "stable-diffusion-xl",
                    "auto1111_url": "http://localhost:7860",
                    "save_path": "./backend/storage/data/images"
                },
                "tts": {
                    "default_voice": "en_US-lessac-medium",
                    "piper_path": "./piper"
                }
            },
            "tools": {
                "filesystem_allowlist": ["C:/Users", "D:/Documents"],
                "max_file_size_mb": 10
            },
            "permissions": {
                "local_mode": "full",
                "remote_mode": "restricted"
            },
            "storage": {
                "data_dir": "./backend/storage/data",
                "images_dir": "./backend/storage/data/images",
                "conversations_db": "./backend/storage/data/conversations/assistant.db"
            }
        }
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get configuration value by dot-separated key.
        
        Args:
            key: Dot-separated key (e.g., "server.port")
            default: Default value if key not found
            
        Returns:
            Configuration value
        """
        keys = key.split('.')
        value = self._config
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value
    
    def set(self, key: str, value: Any) -> None:
        """
        Set configuration value by dot-separated key.
        
        Args:
            key: Dot-separated key (e.g., "server.port")
            value: Value to set
        """
        keys = key.split('.')
        config = self._config
        
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        
        config[keys[-1]] = value
        self._save()
    
    def get_all(self) -> Dict[str, Any]:
        """Get entire configuration."""
        return self._config.copy()
    
    def reload(self) -> None:
        """Reload configuration from file."""
        self._load()


# Global config instance
_config_manager: Optional[ConfigManager] = None


def get_config(config_path: Optional[str] = None) -> ConfigManager:
    """Get global config manager instance."""
    global _config_manager
    if _config_manager is None:
        _config_manager = ConfigManager(config_path)
    return _config_manager
