# Application State Assessment
*Date: 2026-03-21*

---

## Summary

The application is a local-first AI assistant platform with a FastAPI backend and React/TypeScript/Vite frontend. After the Plans 01–08 overhaul, the feature set is substantial and the TypeScript compiler reports zero errors. All Python imports pass. Below is a function-by-function readiness evaluation.

---

## Backend

### Routing Layer (`backend/gateway/`)

| Component | Status | Notes |
|-----------|--------|-------|
| `main.py` | ✅ Functional | CORS, static mounts, lifespan setup all correct |
| `router.py` | ✅ Functional | All endpoints present and importable |
| `ollama_router.py` | ✅ Functional | Streaming SSE, tool round-trip, auto-title |
| `settings_router.py` | ✅ Functional | GET/PUT settings backed by config file |
| `middleware.py` | ⚠️ Partial | Sets `is_remote` but it is never consumed (BUG-H2) |
| `auth.py` | ✅ Functional | API key verification via `X-API-Key` header |

### Models (`backend/models/`)

| Model | Status | Notes |
|-------|--------|-------|
| `chat.py` | ✅ | `ChatRequest` includes `upload_ids`, `tts_voice`, `system_prompt` |
| `image.py` | ✅ | `ImageGenerateRequest`, `Img2ImgRequest`, `ImageInfo`, `ImagesPaginatedResponse` |
| `tools.py` | ✅ | Unchanged |

### Services

| Service | Status | Notes |
|---------|--------|-------|
| Chat (Ollama) | ✅ | Generate, stream, tool calling, model listing |
| Image (Auto1111) | ✅ Requires restart | Must launch Auto1111 with `--api` flag |
| TTS (Piper) | ✅ | Voice scanning works; Piper binary must be present |
| Filesystem tools | ✅ | Read, search, list uploads all registered |

### Storage

| Component | Status | Notes |
|-----------|--------|-------|
| SQLite database | ✅ | All tables created on startup |
| Config manager | ✅ | JSON-backed, persists to disk on `set()` |
| Generated images | ✅ | Saved to `backend/storage/data/images/` |
| Uploaded files | ✅ | Saved to `backend/storage/data/uploads/<session>/` |
| Audio files | ✅ | Saved to `backend/storage/data/audio/` |

---

## Frontend

### Core Infrastructure

| Component | Status | Notes |
|-----------|--------|-------|
| `api/client.ts` | ✅ | All endpoints covered, correct types |
| `context/ChatContext.tsx` | ✅ | All state actions handled in reducer |
| `App.tsx` | ✅ | All 4 modes routed correctly |

### Components

| Component | Status | Notes |
|-----------|--------|-------|
| `ChatView.tsx` | ✅ | Export, system prompt editor, conversation history |
| `InputBar.tsx` | ✅ | Text input, file attachments, drag-and-drop |
| `MessageBubble.tsx` | ✅ | User/assistant/tool/system roles, audio player |
| `Sidebar.tsx` | ✅ | Sessions list, rename, settings button, gallery mode |
| `TopBar.tsx` | ✅ | Model selector, TTS toggle, voice picker |
| `WelcomeScreen.tsx` | ✅ | Persona chips, new chat CTA |
| `ImageView.tsx` | ✅ | txt2img / img2img / inpainting tabs, full param set |
| `GalleryView.tsx` | ✅ | Paginated grid, detail modal, use-as-template |
| `ModelManager.tsx` | ✅ | Ollama model list, pull, delete |
| `SettingsModal.tsx` | ✅ | Tabbed settings, persists to backend |
| `PersonaPicker.tsx` | ✅ | Persona cards, create/delete custom |
| `OllamaStatus.tsx` | ✅ | Status dot, model count |
| `Auto1111Status.tsx` | ✅ | Status dot, navigates to image mode |

---

## Integration Points

### Chat Flow (working)
```
User types → InputBar → sendMessage() → POST /api/chat/stream (SSE)
→ Token events → APPEND_TOKEN → Assistant bubble updates in real time
→ Done event → FINISH_STREAMING + SET_SESSION + refreshSessions
```

### Tool Call Flow (working in code, remote restriction broken)
```
LLM responds with tool_call → tool executed → role:tool message built
→ Second generation pass → follow-up response streamed to user
```

### Image Generation Flow (working)
```
ImageView → POST /api/image/generate → Auto1111 txt2img API
→ Response: image_url + images[] → displayed in ImageView
→ DB metadata saved → visible in Gallery
```

### Auto1111 Dependency
Auto1111 must be running with `--api` enabled. The `webui-user.bat` file has been updated but requires a manual restart of Auto1111.

---

## Known Broken / Not Wired Up

1. **Remote tool restrictions** — `is_remote` is set in middleware but never used (BUG-H2)
2. **Session `created_at`** — resets on every message (BUG-H1)
3. **Batch image gallery** — only first image per batch saved (BUG-H3)
4. **API key exposure** — `GET /api/settings` returns the raw key (BUG-M1)
5. **CORS not dynamic** — changing API key via settings doesn't update CORS until restart (BUG-M3)

---

## Startup Checklist

```
□ Start Ollama:         ollama serve
□ Start Auto1111:       .\webui-user.bat  (must have --api in COMMANDLINE_ARGS)
□ Start backend+frontend: .\scripts\start.ps1
□ First time only:      let DB initialize (personas seeded automatically)
```

---

## Playwright Test Infrastructure

Playwright 1.58.2 is installed in `tests/`. Config exists at `tests/playwright.config.ts`. No test specs exist yet (specs directory is empty). The config correctly points to:
- Frontend: `http://localhost:5173` (Vite dev server)
- Backend: `http://localhost:8000/health`

Both servers use `reuseExistingServer: true` so tests can be run against an already-running dev setup.
