# Local AI Assistant Platform

A local-first AI dashboard that runs on a personal GPU workstation and exposes multiple AI capabilities through a unified interface.

## Features

- **Chat Mode**: Conversation with local LLM (Ollama) with optional TTS output
- **Image Generation**: Stable Diffusion via Automatic1111
- **Modular Architecture**: Easy to add new models and tools
- **Tool System**: Filesystem, web search, and system automation tools
- **VPN Access**: Accessible via VPN mesh for remote devices
- **Desktop UI**: PySide6 desktop app

## Architecture

```
PySide Desktop App → FastAPI Gateway → Model Services (Ollama/Auto1111/Piper)
```

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Copy `.env.example` to `.env` and configure:
```bash
cp .env.example .env
```

3. Ensure external services are running:
   - Ollama (localhost:11434)
   - Automatic1111 (localhost:7860)
   - Piper TTS (configured path)

4. Start the FastAPI server:
```bash
python -m backend.gateway.main
```

5. Start the PySide desktop app:
```bash
python -m frontend.main
```

## Project Structure

- `backend/` - FastAPI gateway, services, tools, storage
- `frontend/` - PySide6 desktop application
- `config/` - Configuration files
