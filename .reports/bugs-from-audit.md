# Additional Audit Findings (Automated Code Review)

Findings from automated deep code audit, supplementing the manual review.

---

## Findings Already Fixed in This Session

| ID | Issue | Fix Applied |
|----|-------|-------------|
| A1 | `[AGENT_LOG]` debug print + `import json as _json` in `ollama_adapter.py:146–150` | Removed |
| A2 | Missing `/uploads` proxy in `vite.config.ts` | Added `/uploads` proxy |
| A3 | Session ID path traversal in upload endpoint (`router.py:604`) | Added sanitization check |
| A4 | No DELETE endpoint for conversations | Added `DELETE /api/conversations/{session_id}` |
| A5 | Orphaned file when DB save fails in upload endpoint | Wrapped in try/finally with cleanup |
| A6 | No delete button in Sidebar for conversations | Added trash icon with confirm step |

---

## Remaining Findings

### A7: Auto-title runs as fire-and-forget with no timeout
**File:** `backend/gateway/ollama_router.py:298`
**Severity:** Low
If Ollama is slow, the auto-title task can run indefinitely after the streaming response completes. This ties up a model slot and could cause issues at high concurrency.
**Fix:** Add `asyncio.wait_for(..., timeout=10.0)` around the title generation coroutine.

---

### A8: Missing query param length limits on image search
**File:** `backend/gateway/router.py:399–402`
**Severity:** Low
`prompt` and `model` filter parameters in `GET /api/images` have no max length. Extremely long strings could slow down the SQLite LIKE query.
**Fix:** Add `max_length=500` to the `Query()` declarations.

---

### A9: JSON parse errors in Ollama adapter streaming not handled
**File:** `backend/services/chat_service/adapters/ollama_adapter.py`
**Severity:** Low
Lines that call `json.loads(line)` inside the streaming loop don't catch `json.JSONDecodeError`. A single malformed line from Ollama would crash the entire stream.
**Fix:** Wrap in try/except and `continue` on malformed lines.

---

### A10: Model name path parameter (`{name:path}`) not sanitized before Ollama call
**File:** `backend/gateway/ollama_router.py:63–70`
**Severity:** Low
The `name` path parameter allows any characters (it's a `:path` param). The value is passed directly to `_chat_service.show_model(name)` which calls the Ollama API. While Ollama itself validates model names, it's best practice to validate before forwarding.

---

### A11: `DELETE /api/conversations` clears active session in frontend — needs context dispatch
**File:** `frontend-web/src/components/Sidebar.tsx`
**Severity:** Low (handled)
The sidebar's `handleDelete` already dispatches `NEW_CHAT` if the deleted session is currently active. This is correct behavior.

---

### A12: Pydantic response type mismatch — Auto1111 endpoints return `dict` hint
**File:** `backend/gateway/router.py:174, 188, 198, 208`
**Severity:** Low (cosmetic)
The return type annotation is `-> dict` but a `response_model` is not specified, so FastAPI doesn't validate the output. These could be tightened with proper response models (e.g., `Auto1111StatusResponse`), but they function correctly as-is.

---

### A13: No connection pooling in SQLite database
**File:** `backend/storage/database.py` (throughout)
**Severity:** Low (performance)
Every database method opens and closes a new `aiosqlite` connection. For the expected workload (single-user local), this is fine. At higher concurrency, a connection pool would reduce overhead.

---

### A14: `stored_path` exposed in upload response
**File:** `backend/gateway/router.py:652–658`
**Severity:** Low (info disclosure)
Previously, the upload response included the full `stored_path` (server filesystem path). This has been removed in the current fix — the response now only returns `upload_id`, `filename`, `size`, and `session_id`.
