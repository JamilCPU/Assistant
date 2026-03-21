"""API route handlers."""

import json
import os
import uuid
from typing import List, Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile
from fastapi.responses import StreamingResponse

from backend.gateway.auth import verify_api_key
from backend.models.chat import (
    ChatRequest, ChatResponse, ConversationResponse, SessionsListResponse
)
from backend.models.image import (
    ImageGenerateRequest, ImageGenerateResponse, ImageInfo,
    Img2ImgRequest, Img2ImgResponse,
    ImagesListResponse, ImagesPaginatedResponse,
)
from backend.models.tools import ToolsListResponse
from backend.services.chat_service.chat_service import ChatServiceManager
from backend.services.chat_service.tools.registry import get_registry
from backend.services.image_service.image_service import ImageServiceManager
from backend.services.tts_service.tts_service import TTSServiceManager
from backend.storage.database import get_database

router = APIRouter()

# Initialize service managers
chat_service = ChatServiceManager()
image_service = ImageServiceManager()
tts_service = TTSServiceManager()
tool_registry = get_registry()
db = get_database()


@router.post("/api/chat", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    api_key: str = Depends(verify_api_key)
) -> ChatResponse:
    """
    Chat with LLM, optionally with TTS output.
    
    Handles tool calling and orchestrates tool execution.
    """
    # Generate session ID if not provided
    session_id = request.session_id or str(uuid.uuid4())
    
    # Get tool schemas for LLM
    tool_schemas = tool_registry.get_tool_schemas()
    
    # Save user message
    await db.save_message(session_id, "user", request.message)
    
    # Build full conversation history to send to the model so it has context.
    # The user message was just saved, so get_conversation now includes it.
    history = await db.get_conversation(session_id)
    ollama_messages = []
    if request.system_prompt:
        ollama_messages.append({"role": "system", "content": request.system_prompt})
    for msg in history:
        if msg["role"] in ("user", "assistant"):
            ollama_messages.append({"role": msg["role"], "content": msg["content"]})

    # Inject upload context if upload_ids provided
    if request.upload_ids:
        uploads = []
        for uid in request.upload_ids:
            u = await db.get_upload(uid)
            if u:
                uploads.append(u)
        if uploads:
            file_list = "\n".join(
                f"- {u['original_filename']} at {u['stored_path']}" for u in uploads
            )
            upload_msg = (
                "The user has uploaded the following files that you can read with the read_file tool:\n"
                + file_list
            )
            ollama_messages.insert(0, {"role": "system", "content": upload_msg})

    # Generate response with tools
    result = await chat_service.generate(
        prompt=request.message,
        system_prompt=request.system_prompt,
        messages=ollama_messages if ollama_messages else None,
        tools=tool_schemas if tool_schemas else None,
        model=request.model
    )
    
    response_text = result.get("text", "")
    tool_calls = result.get("tool_calls")

    # Execute tool calls and perform a follow-up generation pass
    if tool_calls:
        # Persist the assistant message that contains the tool calls
        assistant_msg_id = await db.save_message(
            session_id,
            "assistant",
            response_text,
            metadata={"tool_calls": tool_calls},
        )

        # Build an updated message list with tool results
        updated_messages = list(ollama_messages)
        updated_messages.append({"role": "assistant", "content": response_text})

        for tool_call in tool_calls:
            tool_name = tool_call.get("name")
            tool_args = tool_call.get("arguments", {})
            try:
                tool_result = await tool_registry.execute_tool(tool_name, tool_args)
                await db.log_tool_execution(
                    session_id,
                    assistant_msg_id,
                    tool_name,
                    tool_args,
                    tool_result,
                    success=True,
                )
                updated_messages.append({
                    "role": "tool",
                    "content": json.dumps(tool_result),
                    "name": tool_name,
                })
            except Exception as e:
                await db.log_tool_execution(
                    session_id,
                    assistant_msg_id,
                    tool_name,
                    tool_args,
                    {"error": str(e)},
                    success=False,
                )
                updated_messages.append({
                    "role": "tool",
                    "content": json.dumps({"error": str(e)}),
                    "name": tool_name,
                })

        # Second generation pass with tool results
        follow_up = await chat_service.generate(
            prompt=request.message,
            system_prompt=request.system_prompt,
            messages=updated_messages,
            tools=tool_schemas if tool_schemas else None,
            model=request.model,
        )
        response_text = follow_up.get("text", "")

    # Save assistant response
    await db.save_message(session_id, "assistant", response_text)
    
    # Generate TTS if requested
    audio_url = None
    if request.speak:
        try:
            tts_result = await tts_service.speak(response_text, voice=request.tts_voice)
            audio_url = tts_result.get("audio_url") or tts_result.get("audio_path")
        except Exception as e:
            # TTS failure shouldn't break the response
            print(f"TTS error: {e}")
    
    return ChatResponse(
        response=response_text,
        session_id=session_id,
        tool_calls=[tool_call for tool_call in (tool_calls or [])],
        audio_url=audio_url
    )


@router.get("/api/auto1111/status")
async def auto1111_status(api_key: str = Depends(verify_api_key)) -> dict:
    """Check whether Automatic1111 is reachable."""
    online = await image_service.health()
    model_count = 0
    if online:
        try:
            models = await image_service.list_models()
            model_count = len(models)
        except Exception:
            pass
    return {"online": online, "model_count": model_count}


@router.get("/api/auto1111/samplers")
async def auto1111_samplers(api_key: str = Depends(verify_api_key)) -> dict:
    """List available samplers from Automatic1111."""
    try:
        samplers = await image_service.list_samplers()
        return {"samplers": samplers}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error listing samplers: {str(e)}")


@router.get("/api/auto1111/upscalers")
async def auto1111_upscalers(api_key: str = Depends(verify_api_key)) -> dict:
    """List available upscalers from Automatic1111."""
    try:
        upscalers = await image_service.list_upscalers()
        return {"upscalers": upscalers}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error listing upscalers: {str(e)}")


@router.get("/api/auto1111/styles")
async def auto1111_styles(api_key: str = Depends(verify_api_key)) -> dict:
    """List available prompt styles from Automatic1111."""
    try:
        styles = await image_service.list_styles()
        return {"styles": styles}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error listing styles: {str(e)}")


@router.post("/api/image/generate", response_model=ImageGenerateResponse)
async def generate_image(
    request: ImageGenerateRequest,
    api_key: str = Depends(verify_api_key)
) -> ImageGenerateResponse:
    """Generate an image."""
    try:
        result = await image_service.generate(
            prompt=request.prompt,
            negative_prompt=request.negative_prompt,
            model=request.model,
            width=request.width,
            height=request.height,
            steps=request.steps,
            cfg_scale=request.cfg_scale,
            sampler=request.sampler,
            lora=request.lora,
            seed=request.seed,
            batch_size=request.batch_size,
            batch_count=request.batch_count,
            restore_faces=request.restore_faces,
            tiling=request.tiling,
            clip_skip=request.clip_skip,
            enable_hr=request.enable_hr,
            hr_scale=request.hr_scale,
            hr_upscaler=request.hr_upscaler,
            hr_second_pass_steps=request.hr_second_pass_steps,
            denoising_strength=request.denoising_strength,
            hr_resize_x=request.hr_resize_x,
            hr_resize_y=request.hr_resize_y,
            styles=request.styles,
        )

        # Save image metadata to database
        from pathlib import Path
        image_path = Path(result["image_path"])

        await db.save_image_metadata(
            filename=result["filename"],
            filepath=str(image_path.relative_to(Path.cwd())),
            prompt=request.prompt,
            negative_prompt=request.negative_prompt,
            model_name=request.model,
            lora_used=request.lora,
            parameters={
                "width": request.width,
                "height": request.height,
                "steps": request.steps,
                "cfg_scale": request.cfg_scale,
                "sampler": request.sampler or "Euler a",
                "seed": request.seed,
                "batch_size": request.batch_size,
                "batch_count": request.batch_count,
            },
            file_size=image_path.stat().st_size,
            width=request.width,
            height=request.height
        )

        return ImageGenerateResponse(**result)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Image generation failed: {str(e)}")


@router.get("/api/models")
async def list_models(api_key: str = Depends(verify_api_key)) -> dict:
    """List available models."""
    try:
        chat_models = await chat_service.list_models()
        image_models = await image_service.list_models()
        loras = await image_service.list_loras()
        voices = await tts_service.list_voices()
        
        return {
            "chat": chat_models,
            "image": image_models,
            "loras": loras,
            "tts": voices
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error listing models: {str(e)}")


@router.get("/api/tools", response_model=ToolsListResponse)
async def list_tools(api_key: str = Depends(verify_api_key)) -> ToolsListResponse:
    """List available tools."""
    tool_schemas = tool_registry.get_tool_schemas()
    
    # Convert to response format
    tools = []
    for schema in tool_schemas:
        func = schema.get("function", {})
        tools.append({
            "name": func.get("name", ""),
            "description": func.get("description", ""),
            "parameters": func.get("parameters", {})
        })
    
    return ToolsListResponse(tools=tools)


@router.get("/api/conversations", response_model=SessionsListResponse)
async def list_conversations(api_key: str = Depends(verify_api_key)) -> SessionsListResponse:
    """List all conversation sessions."""
    sessions = await db.list_sessions()
    return SessionsListResponse(sessions=sessions)


@router.get("/api/conversations/{session_id}", response_model=ConversationResponse)
async def get_conversation(
    session_id: str,
    api_key: str = Depends(verify_api_key)
) -> ConversationResponse:
    """Get conversation messages for a session."""
    messages = await db.get_conversation(session_id)
    return ConversationResponse(session_id=session_id, messages=messages)


@router.patch("/api/conversations/{session_id}")
async def rename_conversation(
    session_id: str,
    body: dict,
    api_key: str = Depends(verify_api_key),
) -> dict:
    """Rename a conversation session."""
    title = body.get("title", "").strip()
    if not title:
        raise HTTPException(status_code=422, detail="title must be a non-empty string")
    await db.update_session_title(session_id, title)
    return {"session_id": session_id, "title": title}


@router.get("/api/conversations/{session_id}/export")
async def export_conversation(
    session_id: str,
    format: str = "markdown",
    api_key: str = Depends(verify_api_key),
) -> StreamingResponse:
    """Export conversation as json, markdown, or txt."""
    if format not in ("json", "markdown", "txt"):
        raise HTTPException(status_code=422, detail="format must be json, markdown, or txt")

    messages = await db.get_conversation(session_id)
    if not messages:
        raise HTTPException(status_code=404, detail="Session not found or has no messages")

    if format == "json":
        content = json.dumps(messages, indent=2, default=str)
        media_type = "application/json"
        filename = "conversation.json"
    elif format == "markdown":
        lines = ["# Conversation\n"]
        for m in messages:
            role_label = m["role"].capitalize()
            lines.append(f"**{role_label}:** {m['content']}\n")
        content = "\n".join(lines)
        media_type = "text/markdown"
        filename = "conversation.md"
    else:  # txt
        lines = []
        for m in messages:
            role_label = m["role"].upper()
            lines.append(f"[{role_label}]\n{m['content']}\n")
        content = "\n".join(lines)
        media_type = "text/plain"
        filename = "conversation.txt"

    return StreamingResponse(
        iter([content]),
        media_type=media_type,
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
        },
    )


@router.get("/api/images", response_model=ImagesPaginatedResponse)
async def list_images(
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=24, ge=1, le=100),
    prompt: Optional[str] = Query(default=None),
    model: Optional[str] = Query(default=None),
    api_key: str = Depends(verify_api_key),
) -> ImagesPaginatedResponse:
    """List generated images with optional pagination and filtering."""
    result = await db.get_images_paginated(
        page=page,
        per_page=per_page,
        prompt_filter=prompt,
        model_filter=model,
    )
    return ImagesPaginatedResponse(**result)


@router.get("/api/images/{image_id}", response_model=ImageInfo)
async def get_image(
    image_id: int,
    api_key: str = Depends(verify_api_key),
) -> ImageInfo:
    """Get a single image by ID."""
    img = await db.get_image(image_id)
    if img is None:
        raise HTTPException(status_code=404, detail="Image not found")
    return ImageInfo(**img)


@router.delete("/api/images/{image_id}")
async def delete_image(
    image_id: int,
    api_key: str = Depends(verify_api_key),
) -> dict:
    """Delete an image record and file from disk."""
    filepath = await db.delete_image(image_id)
    if filepath is None:
        raise HTTPException(status_code=404, detail="Image not found")
    # Attempt to remove the file from disk (best-effort)
    try:
        if os.path.exists(filepath):
            os.remove(filepath)
    except OSError:
        pass
    return {"deleted": image_id}


# ── Persona endpoints ─────────────────────────────────────────────────────

@router.get("/api/personas")
async def list_personas(api_key: str = Depends(verify_api_key)) -> dict:
    """List all personas."""
    personas = await db.list_personas()
    return {"personas": personas}


@router.post("/api/personas", status_code=201)
async def create_persona(
    body: dict,
    api_key: str = Depends(verify_api_key),
) -> dict:
    """Create a new custom persona."""
    name = body.get("name", "").strip()
    system_prompt = body.get("system_prompt", "").strip()
    icon = body.get("icon", "🤖")
    default_model = body.get("default_model")
    if not name or not system_prompt:
        raise HTTPException(status_code=422, detail="name and system_prompt are required")
    persona_id = await db.create_persona(name, system_prompt, icon, default_model)
    return {"id": persona_id}


@router.put("/api/personas/{persona_id}")
async def update_persona(
    persona_id: int,
    body: dict,
    api_key: str = Depends(verify_api_key),
) -> dict:
    """Update a persona by id."""
    name = body.get("name")
    system_prompt = body.get("system_prompt")
    icon = body.get("icon")
    default_model = body.get("default_model")
    await db.update_persona(persona_id, name, system_prompt, icon, default_model)
    return {"updated": persona_id}


@router.delete("/api/personas/{persona_id}")
async def delete_persona(
    persona_id: int,
    api_key: str = Depends(verify_api_key),
) -> dict:
    """Delete a non-builtin persona by id."""
    deleted = await db.delete_persona(persona_id)
    if not deleted:
        raise HTTPException(status_code=403, detail="Cannot delete a built-in persona or persona not found")
    return {"deleted": persona_id}


# ── img2img / inpainting ──────────────────────────────────────────────────

@router.post("/api/image/img2img", response_model=Img2ImgResponse)
async def img2img_generate(
    request: Img2ImgRequest,
    api_key: str = Depends(verify_api_key),
) -> Img2ImgResponse:
    """Generate an image using img2img or inpainting."""
    try:
        result = await image_service.img2img(
            prompt=request.prompt,
            init_image=request.init_image,
            negative_prompt=request.negative_prompt,
            model=request.model,
            width=request.width,
            height=request.height,
            steps=request.steps,
            cfg_scale=request.cfg_scale,
            sampler=request.sampler,
            lora=request.lora,
            seed=request.seed,
            batch_size=request.batch_size,
            restore_faces=request.restore_faces,
            tiling=request.tiling,
            clip_skip=request.clip_skip,
            styles=request.styles,
            denoising_strength=request.denoising_strength,
            resize_mode=request.resize_mode,
            mask=request.mask,
            mask_blur=request.mask_blur,
            inpainting_fill=request.inpainting_fill,
            inpaint_full_res=request.inpaint_full_res,
            inpaint_full_res_padding=request.inpaint_full_res_padding,
        )

        # Save image metadata to database
        from pathlib import Path
        image_path = Path(result["image_path"])

        await db.save_image_metadata(
            filename=result["filename"],
            filepath=str(image_path.relative_to(Path.cwd())),
            prompt=request.prompt,
            negative_prompt=request.negative_prompt,
            model_name=request.model,
            lora_used=request.lora,
            parameters={
                "width": request.width,
                "height": request.height,
                "steps": request.steps,
                "cfg_scale": request.cfg_scale,
                "sampler": request.sampler or "Euler a",
                "seed": request.seed,
                "batch_size": request.batch_size,
                "denoising_strength": request.denoising_strength,
                "mode": "inpaint" if request.mask else "img2img",
            },
            file_size=image_path.stat().st_size,
            width=request.width,
            height=request.height,
        )

        return Img2ImgResponse(**result)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"img2img generation failed: {str(e)}")


# ── File upload ───────────────────────────────────────────────────────────

_UPLOAD_ALLOWED_EXTENSIONS = {
    ".txt", ".md", ".csv", ".json", ".py", ".js", ".ts", ".tsx",
    ".html", ".css", ".yaml", ".yml", ".xml", ".log", ".pdf",
}


@router.post("/api/upload")
async def upload_file(
    file: UploadFile = File(...),
    session_id: Optional[str] = Form(None),
    api_key: str = Depends(verify_api_key),
) -> dict:
    """Upload a file and make it available to the LLM via read_file."""
    import pathlib

    from backend.storage.config import get_config as _get_config

    cfg = _get_config()
    max_mb: float = cfg.get("tools.max_file_size_mb", 10)
    max_bytes = int(max_mb * 1024 * 1024)

    # Validate extension
    original_filename = file.filename or "upload"
    ext = pathlib.Path(original_filename).suffix.lower()
    if ext not in _UPLOAD_ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=415,
            detail=f"File type '{ext}' is not allowed. Allowed: {', '.join(sorted(_UPLOAD_ALLOWED_EXTENSIONS))}",
        )

    # Read file content
    content = await file.read()
    if len(content) > max_bytes:
        raise HTTPException(
            status_code=413,
            detail=f"File too large: {len(content) / 1024 / 1024:.1f} MB (max {max_mb} MB)",
        )

    upload_id = str(uuid.uuid4())
    bucket = session_id or "anonymous"
    upload_dir = pathlib.Path("./backend/storage/data/uploads") / bucket
    upload_dir.mkdir(parents=True, exist_ok=True)

    stored_filename = f"{upload_id}{ext}"
    stored_path = upload_dir / stored_filename
    with open(stored_path, "wb") as fh:
        fh.write(content)

    mime_type = file.content_type or "application/octet-stream"

    # PDF text extraction (best-effort)
    if ext == ".pdf":
        try:
            import io
            from pypdf import PdfReader  # type: ignore
            reader = PdfReader(io.BytesIO(content))
            pages_text = []
            for page in reader.pages:
                pages_text.append(page.extract_text() or "")
            extracted = "\n\n".join(pages_text)
            sidecar_path = upload_dir / f"{upload_id}.txt"
            with open(sidecar_path, "w", encoding="utf-8") as fh:
                fh.write(extracted)
        except Exception:
            pass  # PDF extraction is best-effort

    # Save to DB
    await db.save_upload(
        upload_id=upload_id,
        session_id=session_id,
        original_filename=original_filename,
        stored_path=str(stored_path),
        file_size=len(content),
        mime_type=mime_type,
    )

    return {
        "upload_id": upload_id,
        "filename": original_filename,
        "size": len(content),
        "stored_path": str(stored_path),
        "session_id": session_id,
    }
