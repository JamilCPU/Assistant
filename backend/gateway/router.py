"""API route handlers."""

import uuid
from typing import List

from fastapi import APIRouter, Depends, HTTPException

from backend.gateway.auth import verify_api_key
from backend.models.chat import (
    ChatRequest, ChatResponse, ConversationResponse, SessionsListResponse
)
from backend.models.image import (
    ImageGenerateRequest, ImageGenerateResponse, ImagesListResponse
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
    
    # Execute tool calls if any
    if tool_calls:
        for tool_call in tool_calls:
            tool_name = tool_call.get("name")
            tool_args = tool_call.get("arguments", {})
            
            try:
                # Execute tool
                tool_result = await tool_registry.execute_tool(tool_name, tool_args)
                
                # Log tool execution
                message_id = await db.save_message(
                    session_id,
                    "assistant",
                    response_text,
                    metadata={"tool_calls": [tool_call]}
                )
                await db.log_tool_execution(
                    session_id,
                    message_id,
                    tool_name,
                    tool_args,
                    tool_result,
                    success=True
                )
                
                # Add tool result to context for follow-up
                # In a more sophisticated implementation, you'd send tool results back to LLM
                response_text += f"\n\n[Tool {tool_name} executed: {str(tool_result)[:100]}...]"
            
            except Exception as e:
                # Log failed tool execution
                await db.log_tool_execution(
                    session_id,
                    None,
                    tool_name,
                    tool_args,
                    {"error": str(e)},
                    success=False
                )
                response_text += f"\n\n[Tool {tool_name} failed: {str(e)}]"
    
    # Save assistant response
    await db.save_message(session_id, "assistant", response_text)
    
    # Generate TTS if requested
    audio_url = None
    if request.speak:
        try:
            tts_result = await tts_service.speak(response_text)
            audio_url = tts_result.get("audio_path")
        except Exception as e:
            # TTS failure shouldn't break the response
            print(f"TTS error: {e}")
    
    return ChatResponse(
        response=response_text,
        session_id=session_id,
        tool_calls=[tool_call for tool_call in (tool_calls or [])],
        audio_url=audio_url
    )


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
            lora=request.lora
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
                "sampler": request.sampler or "Euler a"
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


@router.get("/api/images", response_model=ImagesListResponse)
async def list_images(api_key: str = Depends(verify_api_key)) -> ImagesListResponse:
    """List generated images."""
    images = await db.list_images()
    return ImagesListResponse(images=images)
