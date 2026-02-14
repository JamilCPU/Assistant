"""Piper adapter for TTS service."""

import asyncio
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Optional

from backend.services.base import TTSService


class PiperAdapter(TTSService):
    """Adapter for Piper TTS."""
    
    def __init__(self, piper_path: str = "./piper"):
        """
        Initialize Piper adapter.
        
        Args:
            piper_path: Path to Piper executable or directory
        """
        self.piper_path = Path(piper_path)
        # If it's a directory, look for piper executable
        if self.piper_path.is_dir():
            # Try common executable names
            for exe_name in ["piper", "piper.exe"]:
                exe_path = self.piper_path / exe_name
                if exe_path.exists():
                    self.piper_path = exe_path
                    break
    
    async def speak(
        self,
        text: str,
        voice: Optional[str] = None,
        speed: float = 1.0,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Convert text to speech using Piper.
        
        Args:
            text: Text to convert to speech
            voice: Voice name (e.g., "en_US-lessac-medium")
            speed: Speech speed multiplier
            **kwargs: Additional parameters
            
        Returns:
            Dictionary with audio_path and metadata
        """
        if not text:
            raise ValueError("Text cannot be empty")
        
        # Default voice if not specified
        voice = voice or "en_US-lessac-medium"
        
        # Create temporary output file
        import tempfile
        import os
        from datetime import datetime
        
        output_dir = Path("./backend/storage/data/audio")
        output_dir.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = output_dir / f"tts_{timestamp}.wav"
        
        # Build piper command
        # Piper CLI: piper --model <model> --output_file <output> --text <text>
        # For now, we'll use a simplified approach
        # In production, you'd need to handle model file paths properly
        
        try:
            # Run piper in subprocess
            # Note: This is a simplified implementation
            # Actual Piper usage may vary based on your setup
            cmd = [
                str(self.piper_path),
                "--model", f"{voice}.onnx",  # Assuming model files are available
                "--output_file", str(output_file),
                "--text", text
            ]
            
            # Run command asynchronously
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode != 0:
                raise RuntimeError(f"Piper failed: {stderr.decode()}")
            
            # Check if file was created
            if not output_file.exists():
                raise RuntimeError("Piper did not create output file")
            
            # Get file size
            file_size = output_file.stat().st_size
            
            # Estimate duration (rough approximation)
            # This would ideally come from Piper or audio analysis
            duration = len(text) * 0.1  # Rough estimate: 0.1 seconds per character
            
            return {
                "audio_path": str(output_file),
                "audio_url": None,  # Could be served via static file endpoint
                "duration": duration,
                "voice": voice,
                "text_length": len(text)
            }
        
        except FileNotFoundError:
            raise RuntimeError(f"Piper executable not found at {self.piper_path}")
        except Exception as e:
            raise RuntimeError(f"Error generating speech: {str(e)}")
    
    async def list_voices(self) -> List[str]:
        """
        List available voices.
        
        Returns:
            List of voice names
        """
        # Piper voices are typically model files
        # This would need to scan for .onnx files in the model directory
        # For now, return a default list
        return [
            "en_US-lessac-medium",
            "en_US-lessac-low",
            "en_US-amy-medium"
        ]
