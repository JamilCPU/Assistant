# Plan 05 — File Upload & Document Chat

## Problem
There is no way to upload a file into the chat. The LLM tool `read_file` can only access files already on the server's filesystem. Users cannot share documents, images, or data files from their own machine for the assistant to reason about.

---

## Scope
Multipart file upload endpoint + frontend drag-and-drop / file picker, with the uploaded file made readable by the `read_file` tool within the session.

---

## Backend

### New endpoint
```
POST /api/upload
Content-Type: multipart/form-data
Body: file (UploadFile), session_id (optional)
```

Response:
```json
{
  "upload_id": "abc123",
  "filename": "report.pdf",
  "size": 204800,
  "path": "/uploads/abc123_report.pdf",
  "session_id": "session-xyz"
}
```

Implementation:
- Save to `./backend/storage/data/uploads/{session_id}/` (or a temp dir if no session)
- Enforce file size limit (use config `tools.max_file_size_mb`)
- Accept: `.txt`, `.md`, `.csv`, `.json`, `.pdf` (extract text from PDF), `.py`, `.js`, `.ts`, `.html`, common code files
- Reject: executables, archives, audio/video (configurable allowlist of extensions)
- PDF text extraction: use `pypdf` or `pdfminer.six` to extract text to a `.txt` sidecar file

### Database
Add an `uploads` table:
```sql
CREATE TABLE uploads (
    id INTEGER PRIMARY KEY,
    upload_id TEXT NOT NULL,
    session_id TEXT,
    original_filename TEXT NOT NULL,
    stored_path TEXT NOT NULL,
    file_size INTEGER,
    mime_type TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
)
```

### Tool integration
Add the upload directory to the filesystem allowlist dynamically for the session so `read_file` can access it:
- When a file is uploaded to a session, inject its path into the tool call context for that session
- The system prompt (or a hidden injected message) informs the LLM: `"The user has uploaded: report.pdf. You can read it with read_file('/uploads/session-xyz/abc123_report.pdf')"`

### New tool: `list_uploads`
```json
{
  "name": "list_uploads",
  "description": "List files the user has uploaded in this session",
  "parameters": {}
}
```
Returns list of `{filename, path, size}` for the current session.

---

## Frontend

### `InputBar.tsx`
Add a paperclip/attachment button to the left of the text input:
- Click: opens file picker dialog
- Drag file onto the input area: triggers upload
- Shows an attachment preview chip above the input: filename + size + remove ✕
- Multiple files can be queued

### Upload flow
1. User selects file → client uploads immediately via `POST /api/upload` (before send)
2. Progress indicator on the chip (uploading… → ✓ filename.pdf)
3. When user sends the message, the upload_id(s) are included in the chat request
4. Backend injects an invisible system message into conversation context informing the LLM about the uploaded file
5. LLM will naturally call `read_file` or `list_uploads` when relevant

### `ChatRequest` update
```typescript
interface ChatRequest {
  ...
  upload_ids?: string[]  // uploaded file references for this turn
}
```

### File display in chat
Uploaded files appear as attachment badges in the user's message bubble:
- 📄 filename.pdf (12 KB)

---

## Files to touch
- `backend/gateway/router.py` — add `POST /api/upload`
- `backend/storage/database.py` — add `uploads` table, `save_upload()`, `get_session_uploads()`
- `backend/models/chat.py` — add `upload_ids` to `ChatRequest`
- `backend/services/chat_service/tools/filesystem.py` — add `ListUploadsTool`
- `backend/services/chat_service/tools/registry.py` — register new tool
- `frontend-web/src/components/InputBar.tsx` — add attachment button + drag-drop
- `frontend-web/src/api/client.ts` — add `uploadFile()` function
- `frontend-web/src/components/MessageBubble.tsx` — render attachment badges
- `frontend-web/src/context/ChatContext.tsx` — track pending uploads per message

---

## Acceptance criteria
- [ ] Clicking paperclip opens file picker
- [ ] Dragging a file onto the input area triggers upload
- [ ] Upload progress shows on the attachment chip
- [ ] Uploaded file is referenced in the chat message
- [ ] LLM is informed of the upload and can read the file
- [ ] PDF files are text-extracted so LLM can read them
- [ ] File size limit enforced (blocked with error message)
- [ ] Session uploads are isolated (other sessions cannot access them)
