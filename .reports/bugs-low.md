# Low Severity Bugs & Improvement Notes

---

## BUG-L1: Default filesystem allowlist exposes entire user home directory

**File:** `backend/storage/config.py:67–68`
**Severity:** Low
**Impact:** The default config ships with `["C:/Users", "D:/Documents"]` in `tools.filesystem_allowlist`. This grants the AI assistant's filesystem tools read/write access to the entire `C:/Users` tree (all user profiles, AppData, etc.) on a fresh install. A user who doesn't adjust this is unknowingly giving the model broad access to sensitive files.

### Recommendation
Change the default to an explicit opt-in, e.g. `[]` (empty) with a note in the config file, or a safe example like `["C:/Users/Public/Documents"]`.

---

## BUG-L2: Filename collision for batch images generated within the same second

**File:** `backend/services/image_service/adapters/auto1111_adapter.py:147–159`
**Severity:** Low
**Impact:** If two txt2img or img2img requests complete within the same second, the first image of each batch will have the same filename (`image_YYYYMMDD_HHMMSS.png`), causing one to silently overwrite the other on disk.

### Root Cause
```python
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
filename = f"image_{timestamp}.png"
```
No uniqueness guarantee at sub-second resolution.

### Fix
Append a short UUID fragment or microseconds:
```python
from uuid import uuid4
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
filename = f"image_{timestamp}_{uuid4().hex[:6]}.png"
```

---

## BUG-L3: Image/binary file uploads can't be read by the LLM

**File:** `backend/gateway/router.py:564–567`
**Severity:** Low (UX)
**Impact:** The upload extension allowlist includes `.png`, `.jpg`, `.jpeg`, `.gif`, `.webp`. If a user uploads an image file and then asks the AI to "look at this file", the LLM's `read_file` tool will return raw binary bytes (or a UnicodeDecodeError) instead of meaningful content. The upload succeeds with no error, creating a confusing dead-end.

### Recommendation
Either:
1. Remove image types from the text-file allowlist (images could have a separate vision pipeline)
2. Add a clear error if `read_file` is called on a binary file
3. Document in the UI that image uploads are "stored only" and not readable via tools

---

## BUG-L4: `GET /api/conversations/{session_id}/export` — response says 404 for empty sessions, not 404 for missing sessions

**File:** `backend/gateway/router.py:361–362`
**Severity:** Low
**Impact:** The endpoint returns 404 when there are no messages for a `session_id`. But a session might legitimately exist (row in `sessions` table) with zero messages in `conversations`. More practically, the error message says "Session not found or has no messages" — the "or has no messages" qualifier is confusing. A session with 0 messages is a valid edge case, not a 404.

### Fix
Separate the checks:
```python
if not messages:
    raise HTTPException(status_code=404, detail="Session not found or contains no messages")
```
Or return an empty export rather than an error.

---

## BUG-L5: `ollamaModelInfo` URL-encodes model names — incompatible with `:path` route

**File:** `frontend-web/src/api/client.ts:316`, `backend/gateway/ollama_router.py:63`
**Severity:** Low (edge case)
**Impact:** The frontend uses `encodeURIComponent(name)` which encodes `/` as `%2F`. The backend uses `{name:path}` which captures literal slashes but may or may not URL-decode `%2F`. For typical Ollama names (`llama3:latest`) this works, but namespaced models like `namespace/model:tag` may arrive at the backend as `namespace%2Fmodel%3Atag` instead of the literal path `namespace/model:tag`, causing Ollama API calls to fail with a "model not found" error.

### Fix
Don't use `encodeURIComponent` for the path portion; instead pass the model name as a query parameter:
```
GET /api/ollama/models?name=namespace/model:tag
```
Or ensure the route explicitly URL-decodes the captured path parameter.

---

## BUG-L6: SQL LIMIT injected via f-string (low risk but bad practice)

**File:** `backend/storage/database.py:258–259`
**Severity:** Low (code quality)

```python
if limit:
    query += f" LIMIT {limit}"
```

`limit` is typed `Optional[int]`, so the actual SQL injection risk is zero. However, this is a bad pattern that could become dangerous if the type annotation is relaxed. Replace with a parameterized query:

```python
params_list = [session_id]
if limit:
    query += " LIMIT ?"
    params_list.append(limit)
async with db.execute(query, params_list) as cursor:
```

---

## BUG-L7: `NEW_CHAT` action clears `selectedPersona` but doesn't clear `ttsVoice`

**File:** `frontend-web/src/context/ChatContext.tsx:184–192`
**Severity:** Low (UX)
**Impact:** When the user clicks "New Chat", the selected persona is cleared (`selectedPersona: null`) but `ttsVoice` stays set to whatever the last persona set. If the last conversation used a persona with a specific voice, the next conversation will still use that voice even though no persona is active.

### Fix
Add `ttsVoice: null` to the `NEW_CHAT` case in the reducer (or reset to the default voice from settings).

---

## BUG-L8: Auto-title prompt uses the model selected for chat — may hallucinate titles

**File:** `backend/gateway/ollama_router.py:285–293`
**Severity:** Low (UX)
**Impact:** The auto-title generation uses the same model the user selected for conversation (e.g., a code model, a large slow model). For a short title generation task, this is wasteful. If the user is using a slow 70B model, title generation blocks the model for several extra seconds.

### Recommendation
Use a smaller/faster model for title generation, e.g. hardcode `llama3.2:3b` or `qwen2.5:1.5b` with a fallback to the selected model if unavailable.

---

## BUG-L9: `GalleryView` constructs image URLs from `filename` only — path traversal not checked

**File:** `frontend-web/src/components/GalleryView.tsx:25`
**Severity:** Low
**Impact:** Image URLs are constructed as `/images/${image.filename}`. If `filename` somehow contained `../` (e.g., from a manually crafted DB entry), a client could request arbitrary files from the server. FastAPI's `StaticFiles` mount should prevent this in practice (it normalizes paths), but the DB field should be treated as untrusted.

### Recommendation
Store only the base filename (no path separators) in the database. Validate on insert in `save_image_metadata`.

---

## NOTE-1: `GET /api/settings` should document that API key changes require restart

The settings API allows changing the API key at runtime, but the CORS `allow_origins` is computed at startup. Changing the API key from `""` to a value via the settings modal will enable API key verification immediately, but CORS won't lock down until restart. This should be communicated to the user in the UI (e.g., a banner "Restart required for CORS changes to take effect").

---

## NOTE-2: `upload_ids` in chat body exposed in `stored_path` field of upload response

**File:** `backend/gateway/router.py:640–646`

The upload response includes `"stored_path"` — the full filesystem path of the uploaded file. While this is only visible to the uploading client, leaking internal file paths is a minor information disclosure. Consider omitting `stored_path` from the response and keeping it server-side only.
