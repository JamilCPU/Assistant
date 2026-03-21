# High Severity Bugs

---

## BUG-H1: Session `created_at` resets on every message

**File:** `backend/storage/database.py:224–228`
**Severity:** High
**Impact:** All sessions in the sidebar will show the timestamp of their *last message* as their creation date, not their actual creation date. Ordering "by date" becomes meaningless.

### Root Cause
`save_message()` uses `INSERT OR REPLACE INTO sessions` to upsert the session row. SQLite's `REPLACE` strategy deletes the old row and inserts a new one. The new row uses `DEFAULT CURRENT_TIMESTAMP` for `created_at` since that column is not in the INSERT column list.

```python
await db.execute("""
    INSERT OR REPLACE INTO sessions (session_id, last_activity, title)
    VALUES (?, CURRENT_TIMESTAMP,
        COALESCE((SELECT title FROM sessions WHERE session_id = ?), NULL))
""", (session_id, session_id))
```

### Fix
Use `INSERT OR IGNORE` to create the session row (preserving `created_at`), then `UPDATE` only `last_activity`:

```python
await db.execute(
    "INSERT OR IGNORE INTO sessions (session_id) VALUES (?)", (session_id,)
)
await db.execute(
    "UPDATE sessions SET last_activity = CURRENT_TIMESTAMP WHERE session_id = ?",
    (session_id,),
)
```

---

## BUG-H2: Remote tool restrictions never enforced

**File:** `backend/gateway/middleware.py`, `backend/gateway/router.py`, `backend/gateway/ollama_router.py`, `backend/services/chat_service/tools/guardrails.py`
**Severity:** High
**Impact:** The designed remote-mode tool lockdown (blocking `write_file`, `execute_command`, etc. for WireGuard clients) does not work at all. Remote users have full tool access identical to local users.

### Root Cause
`LoggingMiddleware` correctly sets `request.state.is_remote`, but neither `router.py` nor `ollama_router.py` reads this value and passes `mode="remote"` to `guardrails.validate_tool_call()`. The guardrails `validate_tool_call()` defaults to `mode="local"`, so restrictions are never applied.

```python
# guardrails.py — validate_tool_call has mode param but...
def validate_tool_call(self, tool_name: str, args: Dict, mode: str = "local") -> None:
    ...  # only restricts when mode="remote"

# router.py / ollama_router.py — mode is never passed
tool_result = await tool_registry.execute_tool(tool_name, tool_args)
# ↑ validate_tool_call is never called here at all
```

### Fix
In `router.py` and `ollama_router.py`, before executing each tool call, call `guardrails.validate_tool_call()` with the request's remote status:

```python
from backend.services.chat_service.tools.guardrails import get_guardrails

guardrails = get_guardrails()
mode = "remote" if request.state.is_remote else "local"
for tc in collected_tool_calls:
    guardrails.validate_tool_call(tc["name"], tc.get("arguments", {}), mode=mode)
    tool_result = await tool_registry.execute_tool(tc["name"], tc["arguments"])
```

---

## BUG-H3: Batch image generation — only first image saved to gallery

**File:** `backend/gateway/router.py:251–274` (txt2img) and `backend/gateway/router.py:530–554` (img2img)
**Severity:** High
**Impact:** When a user generates a batch (e.g., `batch_size=4`), the backend returns all 4 image URLs in `images[]` and they display correctly in ImageView. However, only the first image is saved to the `generated_images` database table. The other 3 images are inaccessible from the Gallery and will be "orphaned" files on disk.

### Root Cause
`db.save_image_metadata()` is called once using `result["image_path"]` (the first image), before iterating over `result["images"]`.

### Fix
Iterate over `result["images"]` and save metadata for each:

```python
for img_url in result["images"]:
    img_filename = img_url.split("/")[-1]
    img_path = Path("./backend/storage/data/images") / img_filename
    await db.save_image_metadata(
        filename=img_filename,
        filepath=str(img_path.relative_to(Path.cwd())),
        ...
    )
```

---

## BUG-H4: X-Forwarded-For header can be spoofed to bypass remote detection

**File:** `backend/gateway/middleware.py:39–40`
**Severity:** High
**Impact:** Any external user can set the `X-Forwarded-For: 127.0.0.1` header in their HTTP request, causing `_is_local_ip()` to return `True`. This sets `request.state.is_remote = False`, which — once BUG-H2 is fixed — would allow a remote user to bypass all tool guardrails.

### Root Cause
The middleware unconditionally trusts the `X-Forwarded-For` header without checking whether the request is coming from a trusted reverse proxy:

```python
forwarded_for = request.headers.get("X-Forwarded-For")
if forwarded_for:
    client_ip = forwarded_for.split(",")[0].strip()  # fully trusted
```

### Fix
Only read `X-Forwarded-For` when operating behind a known trusted proxy (e.g., when `request.client.host` is `127.0.0.1`). Otherwise, use the actual TCP connection IP:

```python
client_ip = request.client.host if request.client else "unknown"
# Only trust X-Forwarded-For from local/trusted proxies
if request.client and _is_local_ip(request.client.host):
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        client_ip = forwarded_for.split(",")[0].strip()
```
