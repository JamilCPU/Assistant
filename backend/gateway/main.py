"""FastAPI application entry point."""

import os
from contextlib import asynccontextmanager

from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from backend.gateway.middleware import LoggingMiddleware
from backend.gateway.router import router
from backend.gateway.ollama_router import ollama_router
from backend.gateway.settings_router import settings_router
from backend.storage.config import get_config
from backend.storage.database import get_database
from backend.storage.migrate import run_migrations

# Ensure the images directory exists before mounting
_images_dir = Path("./backend/storage/data/images")
_images_dir.mkdir(parents=True, exist_ok=True)

# Ensure the audio directory exists before mounting
_audio_dir = Path("./backend/storage/data/audio")
_audio_dir.mkdir(parents=True, exist_ok=True)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    # Allow environment variables to override config-file URLs so that
    # Docker deployments can point services at containerised endpoints.
    _cfg_startup = get_config()
    _auto1111_url = os.environ.get("AUTO1111_URL")
    if _auto1111_url:
        _cfg_startup.set("models.image.auto1111_url", _auto1111_url)
    _ollama_url = os.environ.get("OLLAMA_URL")
    if _ollama_url:
        _cfg_startup.set("models.chat.ollama_url", _ollama_url)

    # Startup
    print("Initializing database...")
    db = get_database()
    await run_migrations(str(db.db_path))
    await db.initialize()
    await db.seed_builtin_personas()
    print("Database initialized.")
    
    yield
    
    # Shutdown
    print("Shutting down...")


# Create FastAPI app
app = FastAPI(
    title="Local AI Assistant Platform",
    description="Local-first AI dashboard gateway",
    version="1.0.0",
    lifespan=lifespan
)

# CORS — restrict to configured origins when an API key is set (production/VPN mode)
_cfg = get_config()
_api_key_set = bool(_cfg.get("server.api_key"))
_allowed_origins = _cfg.get("server.allowed_origins") or (
    # When a key is set, default to VPN subnet + localhost only
    ["http://10.0.0.1:8000", "http://localhost:8000", "http://localhost:5173"]
    if _api_key_set
    else ["*"]
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=_allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add logging middleware
app.add_middleware(LoggingMiddleware)

# Include routers
app.include_router(router)
app.include_router(ollama_router)
app.include_router(settings_router)

# Serve generated images as static files
app.mount("/images", StaticFiles(directory=str(_images_dir)), name="images")

# Serve generated audio files as static files
app.mount("/audio", StaticFiles(directory=str(_audio_dir)), name="audio")

# Serve uploaded files
_uploads_dir = Path("./backend/storage/data/uploads")
_uploads_dir.mkdir(parents=True, exist_ok=True)

# Serve built frontend (if dist exists) — enables VPN/remote access without a separate dev server
_frontend_dist = Path("./frontend-web/dist")
if _frontend_dist.exists():
    app.mount("/ui", StaticFiles(directory=str(_frontend_dist), html=True), name="frontend")


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Local AI Assistant Platform API",
        "version": "1.0.0"
    }


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    
    config = get_config()
    host = config.get("server.host", "0.0.0.0")
    port = config.get("server.port", 8000)
    
    uvicorn.run(
        "backend.gateway.main:app",
        host=host,
        port=port,
        reload=True
    )
