# Local AI Assistant Platform

A local-first AI assistant that runs on a personal GPU workstation and puts several capabilities behind one web UI: chat with a local LLM (with tool calling), Stable Diffusion image generation (text-to-image and img2img), text-to-speech, personas, saved conversation history and an image gallery. A FastAPI gateway talks to the model services; a React front end talks to the gateway. Nothing is sent to a hosted AI API.

## Stack

- Backend: Python, FastAPI, Uvicorn, httpx, Pydantic, SQLite (`aiosqlite`) with SQL migrations, SSE streaming
- Model services (run separately): Ollama for chat, Automatic1111 for images, Piper for TTS
- Front end: React 19, TypeScript, Vite, Tailwind CSS (`frontend-web/`)
- Tests: Playwright specs in `tests/` (UI and API contracts)
- Docker Compose for the backend, front end and an optional Automatic1111 container; optional WireGuard setup script for remote access

## Architecture

```
React web UI  ->  FastAPI gateway  ->  Ollama (chat, tools)
                                   ->  Automatic1111 (images)
                                   ->  Piper (TTS)
                                   ->  SQLite (conversations, images, personas, settings)
```

Chat tools live in `backend/services/chat_service/tools/` (filesystem, web, system) behind an allowlist/guardrail layer. The list of models the project was set up around is in [MODELS.md](MODELS.md).

## Running

Prerequisites: Python 3.11+, Node.js, and the model services you want to use (Ollama on `localhost:11434`, Automatic1111 on `localhost:7860` started with `--api`, Piper for TTS).

```bash
python -m venv .venv
.venv/bin/pip install -r requirements.txt     # Windows: .venv\Scripts\pip
.venv/bin/python -m backend.gateway.main      # API on http://localhost:8000

cd frontend-web
npm install
npm run dev                                   # UI on http://localhost:5173
```

On Windows, `scripts/start.ps1` starts the backend and the Vite dev server (`-Dev`, default) or builds the front end and serves it from the backend at `/ui` (`-Prod`).

With Docker:

```bash
docker compose up --build              # backend :8000, web UI :3000
docker compose --profile sd up --build # also starts an Automatic1111 container (NVIDIA GPU)
```

The compose file mounts a host directory so the filesystem tools can reach it; edit the `volumes` entry and `tools.filesystem_allowlist` in `config/default_config.json` to match your own paths.

### Configuration

- `config/default_config.json` - server, model, tool and storage settings
- `OLLAMA_URL`, `AUTO1111_URL` - override the service URLs from the config (used by the compose file)
- `API_KEY` (or `server.api_key` in the config) - when set, API requests require the key and CORS is restricted to the configured origins

## Tests

```bash
cd tests
npm install
npx playwright test
```

The specs need the backend and front end running; `live-integration.spec.ts` also needs the model services.

## Project layout

- `backend/gateway/` - FastAPI app, routers, auth and request middleware
- `backend/services/` - chat, image and TTS services with adapters
- `backend/storage/` - config, database layer and SQL migrations
- `frontend-web/` - React UI
- `.plans/`, `.reports/`, `plans/` - design plans and audit notes written while building the project

## Status

Working personal project under active development. It is designed for a trusted machine or private network, not for exposure to the public internet.
