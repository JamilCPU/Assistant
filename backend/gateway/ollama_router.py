"""Ollama management and streaming chat routes."""

import json
import uuid

from fastapi import APIRouter, Depends, HTTPException
from sse_starlette.sse import EventSourceResponse

from backend.gateway.auth import verify_api_key
from backend.models.chat import (
    ChatRequest,
    OllamaModelDetail,
    OllamaModelsListResponse,
    OllamaPullRequest,
    OllamaStatusResponse,
)
from backend.services.chat_service.chat_service import ChatServiceManager
from backend.services.chat_service.tools.registry import get_registry
from backend.services.tts_service.tts_service import TTSServiceManager
from backend.storage.database import get_database

ollama_router = APIRouter()

# Re-use the same service singletons created at module level.
# In a larger app you'd use proper DI; this mirrors the existing router.py pattern.
_chat_service = ChatServiceManager()
_tts_service = TTSServiceManager()
_tool_registry = get_registry()
_db = get_database()


# ── Ollama status ─────────────────────────────────────────────────────────

@ollama_router.get("/api/ollama/status", response_model=OllamaStatusResponse)
async def ollama_status(api_key: str = Depends(verify_api_key)):
    """Check whether Ollama is online and how many models are available."""
    online = await _chat_service.health()
    model_count = 0
    if online:
        try:
            models = await _chat_service.list_models()
            model_count = len(models)
        except Exception:
            pass
    return OllamaStatusResponse(online=online, model_count=model_count)


# ── Ollama models (list) ──────────────────────────────────────────────────

@ollama_router.get("/api/ollama/models", response_model=OllamaModelsListResponse)
async def ollama_models(api_key: str = Depends(verify_api_key)):
    """List all Ollama models with metadata."""
    try:
        models = await _chat_service.list_models_detailed()
        return OllamaModelsListResponse(models=models)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Ollama unreachable: {e}")


# ── Ollama model detail ───────────────────────────────────────────────────

@ollama_router.get("/api/ollama/models/{name:path}", response_model=OllamaModelDetail)
async def ollama_model_detail(name: str, api_key: str = Depends(verify_api_key)):
    """Get detailed info about a specific model."""
    try:
        info = await _chat_service.show_model(name)
        return OllamaModelDetail(**info)
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e))


# ── Ollama model delete ──────────────────────────────────────────────────

@ollama_router.delete("/api/ollama/models/{name:path}", status_code=204)
async def ollama_model_delete(name: str, api_key: str = Depends(verify_api_key)):
    """Delete a model from Ollama."""
    try:
        await _chat_service.delete_model(name)
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e))


# ── Ollama pull (SSE) ────────────────────────────────────────────────────

@ollama_router.post("/api/ollama/pull")
async def ollama_pull(req: OllamaPullRequest, api_key: str = Depends(verify_api_key)):
    """Pull/download a model. Returns an SSE stream with progress events."""

    async def event_generator():
        try:
            async for progress in _chat_service.pull_model(req.name):
                yield {
                    "event": "progress",
                    "data": json.dumps(progress),
                }
            yield {
                "event": "done",
                "data": json.dumps({"status": "success"}),
            }
        except Exception as e:
            yield {
                "event": "error",
                "data": json.dumps({"error": str(e)}),
            }

    return EventSourceResponse(event_generator())


# ── Streaming chat (SSE) ─────────────────────────────────────────────────

@ollama_router.post("/api/chat/stream")
async def chat_stream(request: ChatRequest, api_key: str = Depends(verify_api_key)):
    """
    Streaming chat endpoint.

    SSE events emitted:
        event: token   – data: {"content": "..."}
        event: tool_call – data: {"name": "...", "arguments": {...}}
        event: done    – data: {"session_id": "...", "audio_url": null}
        event: error   – data: {"error": "..."}
    """
    session_id = request.session_id or str(uuid.uuid4())

    # Save user message before streaming begins
    await _db.save_message(session_id, "user", request.message)

    # Build full conversation history so the model has context across turns.
    # The user message was just saved, so get_conversation includes it.
    history = await _db.get_conversation(session_id)
    ollama_messages = []
    if request.system_prompt:
        ollama_messages.append({"role": "system", "content": request.system_prompt})
    for msg in history:
        if msg["role"] in ("user", "assistant"):
            ollama_messages.append({"role": msg["role"], "content": msg["content"]})

    tool_schemas = _tool_registry.get_tool_schemas() or None

    async def event_generator():
        full_text = ""
        collected_tool_calls = []

        try:
            async for chunk in _chat_service.generate_stream(
                prompt=request.message,
                system_prompt=request.system_prompt,
                messages=ollama_messages if ollama_messages else None,
                tools=tool_schemas,
                model=request.model,
            ):
                kind = chunk.get("type")

                if kind == "token":
                    content = chunk["content"]
                    full_text += content
                    yield {
                        "event": "token",
                        "data": json.dumps({"content": content}),
                    }

                elif kind == "tool_call":
                    tc = {"name": chunk["name"], "arguments": chunk["arguments"]}
                    collected_tool_calls.append(tc)
                    yield {
                        "event": "tool_call",
                        "data": json.dumps(tc),
                    }

                elif kind == "done":
                    pass  # handled below

        except Exception as e:
            yield {
                "event": "error",
                "data": json.dumps({"error": str(e)}),
            }
            return

        # ── Post-stream processing ────────────────────────────────────

        # Execute any tool calls
        if collected_tool_calls:
            for tc in collected_tool_calls:
                tool_name = tc["name"]
                tool_args = tc.get("arguments", {})
                try:
                    tool_result = await _tool_registry.execute_tool(tool_name, tool_args)
                    message_id = await _db.save_message(
                        session_id, "assistant", full_text,
                        metadata={"tool_calls": [tc]},
                    )
                    await _db.log_tool_execution(
                        session_id, message_id, tool_name,
                        tool_args, tool_result, success=True,
                    )
                    full_text += f"\n\n[Tool {tool_name} executed: {str(tool_result)[:100]}...]"
                except Exception as e:
                    await _db.log_tool_execution(
                        session_id, None, tool_name,
                        tool_args, {"error": str(e)}, success=False,
                    )
                    full_text += f"\n\n[Tool {tool_name} failed: {str(e)}]"

        # Persist final assistant message
        await _db.save_message(session_id, "assistant", full_text)

        # TTS (optional)
        audio_url = None
        if request.speak:
            try:
                tts_result = await _tts_service.speak(full_text)
                audio_url = tts_result.get("audio_path")
            except Exception:
                pass

        yield {
            "event": "done",
            "data": json.dumps({
                "session_id": session_id,
                "audio_url": audio_url,
            }),
        }

    return EventSourceResponse(event_generator())
