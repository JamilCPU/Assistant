# Changelog — Plans 01–08 Platform Overhaul

**Commit:** `f76996a`
**Date:** 2026-03-21
**Files changed:** 40 files (+6466 / -409 lines)

---

## Plan 01 — Settings Panel

### What was added
A full-page settings modal accessible from the sidebar gear icon, backed by a new `/api/settings` endpoint.

**Backend — `backend/gateway/settings_router.py`** (new)
- `GET /api/settings` — returns current values for all user-configurable keys
- `PUT /api/settings` — writes a partial or full settings object back to config

**Frontend — `frontend-web/src/components/SettingsModal.tsx`** (new)
- Tabbed modal: **Chat**, **Image**, **TTS**, **Tools**, **Server**
- **Chat tab**: default model selector, system prompt textarea, streaming toggle
- **Image tab**: default checkpoint, sampler, steps, CFG scale, default resolution
- **TTS tab**: enable toggle, default voice picker
- **Tools tab**: filesystem allowlist paths (add/remove), max file size
- **Server tab**: API key field, CORS origins list
- Loads settings on open, saves on submit with toast feedback

**`frontend-web/src/components/Sidebar.tsx`** — gear button opens SettingsModal

---

## Plan 02 — Chat Enhancements

### What was added

**Tool call round-trip (`backend/gateway/ollama_router.py`)**
- After executing a tool, builds a `{"role": "tool", "content": "<json>", "name": "<tool_name>"}` message
- Feeds it back to `generate_stream()` so the model produces a follow-up natural-language response
- The tool call and result are displayed to the user in a collapsible bubble

**Auto-title generation**
- Detects first message in a session via `db.is_first_message(session_id)`
- Fires `asyncio.create_task(_generate_title())` after streaming begins — non-blocking
- Title is a one-shot Ollama call: "Generate a short 3–6 word title for this conversation"
- Written back with `db.update_session_title()` and reflected live in the sidebar

**Conversation rename**
- `PATCH /api/conversations/{session_id}` — accepts `{"title": "..."}`, validates non-empty
- Sidebar shows a pencil icon on hover; clicking puts the title into an inline `<input>`

**Conversation export**
- `GET /api/conversations/{session_id}/export?format=markdown|json|txt`
- Returns a `StreamingResponse` with appropriate `Content-Disposition` header
- Frontend ChatView adds a download (↓) button with a dropdown for format selection

**Frontend changes**
- `MessageBubble.tsx` — `role: 'tool'` messages render as a collapsible `🔧 tool_name` block with JSON args in `<pre>`
- `ChatView.tsx` — export dropdown button in top-right; collapsible system prompt editor above the input bar (locked after first message to prevent mid-session changes)

---

## Plan 03 — Image History Gallery

### What was added

**Backend**
- `GET /api/images?page=1&per_page=20&search=&sort_by=created_at` — paginated image list
- `GET /api/images/{id}` — single image with full metadata
- `DELETE /api/images/{id}` — removes file from disk and DB record
- `database.py` — `get_images_paginated()`, `get_image()`, `delete_image()` methods

**Frontend — `frontend-web/src/components/GalleryView.tsx`** (new)
- Masonry-style grid of all generated images
- Search bar filters by prompt; sort by date or filename
- Clicking a thumbnail opens a detail modal with:
  - Full-size image view
  - All generation metadata (model, sampler, steps, CFG, seed, size)
  - "Use as template" button — copies params back to ImageView
  - Delete button with confirmation dialog
- "→ img2img" hover button sends image directly to img2img tab

**`frontend-web/src/App.tsx`** — renders `<GalleryView />` for `state.mode === 'gallery'`
**`frontend-web/src/components/Sidebar.tsx`** — gallery mode button (🖼️)
**`frontend-web/src/context/ChatContext.tsx`** — `AppMode` extended with `'gallery'`

---

## Plan 04 — TTS Improvements

### What was added

**`backend/services/tts_service/adapters/piper_adapter.py`**
- `list_voices()` now recursively scans for `.onnx` files in both the piper binary directory and a `piper_models/` subdirectory
- `speak()` returns `audio_url: /audio/<filename>` so the frontend can play the audio inline
- `_get_wav_duration()` reads the actual WAV header (sample rate × frame count) instead of guessing from text length

**`frontend-web/src/components/TopBar.tsx`**
- Voice selector dropdown appears when TTS is enabled, populated from `state.ttsVoices`
- Selected voice stored in `state.ttsVoice`, sent with each chat request

**`frontend-web/src/components/MessageBubble.tsx`**
- `<audio controls>` player rendered below assistant messages that carry an `audioUrl`

**`frontend-web/src/context/ChatContext.tsx`**
- Added `ttsVoice`, `ttsVoices` state
- `refreshModels()` fetches and dispatches available TTS voices
- `sendMessage()` passes selected `tts_voice` in the request body
- `SET_AUDIO_URL` action updates the last assistant message's `audioUrl` when TTS completes

---

## Plan 05 — File Upload

### What was added

**Backend**
- `POST /api/upload` — multipart endpoint; accepts any file up to `tools.max_file_size_mb`
- Extension allowlist: `.txt`, `.md`, `.py`, `.js`, `.ts`, `.json`, `.csv`, `.pdf`, `.png`, `.jpg`, `.jpeg`, `.gif`, `.webp`
- PDF text extraction via `pypdf` (optional — falls back gracefully if extraction fails)
- Files saved to `backend/storage/data/uploads/<session_id>/`
- `database.py` — `uploads` table, `save_upload()`, `get_session_uploads()`, `get_upload()`
- `ollama_router.py` — when `upload_ids` is non-empty, injects a system message listing the uploaded file paths so the model can reference them with `read_file`
- `ListUploadsTool` — new tool that lists uploads for the current session, registered in `registry.py`

**Frontend — `frontend-web/src/components/InputBar.tsx`** (rewritten)
- Paperclip button opens file picker (multiple files)
- Full drag-and-drop zone on the input area
- Attachment chips show filename + size; status indicator: uploading / done / error
- Upload fires immediately on file selection; IDs collected and sent with message

**`frontend-web/src/components/MessageBubble.tsx`** — attachment badges shown on user messages
**`frontend-web/src/api/client.ts`** — `uploadFile()` function, `upload_ids` field on `ChatRequest`

---

## Plan 06 — Remote Access / VPN

### What was added

**`backend/gateway/middleware.py`**
- `_is_local_ip()` — checks RFC-1918 + loopback + WireGuard (10.0.0.x) ranges using `ipaddress` stdlib
- `RemoteTagMiddleware` — tags every request with `request.state.is_remote` and `request.state.client_ip`

**`backend/gateway/main.py`**
- Configurable CORS: when `server.api_key` is set, restricts `allow_origins` to `["http://10.0.0.1:8000", "http://localhost:8000", "http://localhost:5173"]` instead of `*`
- Mounts `frontend-web/dist` at `/ui` if it exists (enables VPN access without a separate Vite process)
- Mounts `/images`, `/audio` static directories
- Creates `backend/storage/data/uploads` on startup

**`backend/services/chat_service/tools/guardrails.py`**
- `validate_tool_call()` enforces remote-mode restrictions: only `read_file`, `search_files`, `web_search`, `list_uploads` allowed when `mode == "remote"` and config is `restricted`
- Added `is_path_in_uploads()` — uploads directory always readable regardless of allowlist
- `validate_file_path()` now also checks `is_path_in_uploads()`

**`scripts/setup-wireguard.ps1`** (new)
- Requires Administrator; verifies WireGuard is installed
- Auto-detects public IP via `api.ipify.org`; prompts for DDNS hostname override
- Generates server + per-client keypairs using `wg genkey | wg pubkey`
- Writes `wg0.conf` (server) and `<name>.conf` (each client) in split-tunnel mode (`AllowedIPs = 10.0.0.0/24`)
- Installs WireGuard as Windows service (`wireguard.exe /installtunnelservice`)
- Generates QR code PNGs for mobile clients if `qrencode` is available
- Prints router port-forwarding instructions (UDP 51820)

**`scripts/start.ps1`** (new)
- `.\scripts\start.ps1` or `-Dev` — opens backend in a new PowerShell window, runs Vite dev server in foreground
- `.\scripts\start.ps1 -Prod` — runs `npm run build`, then serves everything from FastAPI on port 8000

**`frontend-web/vite.config.ts`**
- `server.host: '0.0.0.0'` — dev server accessible over LAN/VPN
- Added `/audio` proxy alongside `/api` and `/images`
- `build.outDir: 'dist'` — output to location FastAPI can serve

---

## Plan 07 — img2img and Inpainting

### What was added

**Backend**
- `POST /api/image/img2img` — accepts `Img2ImgRequest` (Pydantic model)
- `Img2ImgRequest` fields: `init_image` (URL or base64), `denoising_strength`, `resize_mode`, `mask` (base64), `mask_blur`, `inpainting_fill`, `inpaint_full_res`, `inpaint_full_res_padding`, plus all standard txt2img fields
- `auto1111_adapter.py` — `img2img()` method: resolves `/images/<file>` URLs by reading from disk and base64-encoding, builds Auto1111 payload, saves output images with `img2img_` prefix

**Frontend — `frontend-web/src/components/ImageView.tsx`**
- Mode tabs: **txt2img** / **img2img** / **Inpainting**
- **img2img tab**: drop zone for init image (file picker + thumbnail preview), denoising strength slider (0–1), resize mode select, "Use generated image" button to pull from session history
- **Inpainting tab**: canvas overlay on top of init image — draw mask with brush (configurable size), clear/invert controls, mask blur slider, fill mode select, full-resolution inpainting toggle
- `handleGenerate()` branches on current mode — calls `client.img2img()` for img2img/inpaint, `client.generateImage()` for txt2img
- Gallery hover button "→ img2img" sends any past image into img2img mode

---

## Plan 08 — System Prompt and Personas

### What was added

**Backend**
- Personas CRUD: `GET/POST /api/personas`, `PUT/DELETE /api/personas/{id}`
- `database.py` — `personas` table, `seed_builtin_personas()` (called at startup), `list_personas()`, `create_persona()`, `update_persona()`, `delete_persona()`
- 6 built-in personas: Default Assistant, Code Expert, Creative Writer, Data Analyst, Teacher, Concise Responder — each with a preset system prompt and optional TTS voice

**Frontend**
- **`PersonaPicker.tsx`** (new) — 3-column grid of persona cards; selected persona is highlighted; custom persona inline creation form; delete on non-builtin personas
- **`WelcomeScreen.tsx`** — first 5 persona chips displayed below greeting; "+Custom" chip opens PersonaPicker
- **`ChatView.tsx`** — collapsible system prompt editor above InputBar; shows current persona's prompt; locked (🔒) after first message to prevent mid-session confusion
- **`ChatContext.tsx`** — `personas`, `selectedPersona`, `systemPrompt` state; `SELECT_PERSONA` action; `sendMessage()` passes `system_prompt` from selected persona

---

## Infrastructure

- `requirements.txt` — added `python-multipart>=0.0.9` (FastAPI file upload), `pypdf>=4.0.0` (PDF text extraction)
- All 8 feature plans documented in `.plans/01-settings-panel.md` through `.plans/08-system-prompt-and-personas.md`
- WireGuard setup script and start launcher added to `scripts/`
