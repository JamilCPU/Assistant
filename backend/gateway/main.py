"""FastAPI application entry point."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.gateway.middleware import LoggingMiddleware
from backend.gateway.router import router
from backend.storage.config import get_config
from backend.storage.database import get_database


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    # Startup
    print("Initializing database...")
    db = get_database()
    await db.initialize()
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

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict this
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add logging middleware
app.add_middleware(LoggingMiddleware)

# Include routers
app.include_router(router)


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
