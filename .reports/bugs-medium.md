# Medium Severity Bugs

---

## BUG-M1: API key returned in plaintext from GET /api/settings

**File:** `backend/gateway/settings_router.py:117`
**Severity:** Medium (Security)
**Impact:** `GET /api/settings` returns `{"server": {"api_key": "<the_actual_key>"}}`. This means any client that can reach the API (including unauthenticated ones if no key is set yet) can retrieve the key. Even with a key set, any authenticated client can learn the key value.

### Root Cause
```python
"server": {
    "api_key": cfg.get("server.api_key", ""),  # returns raw key
},
```

### Fix
Never return the API key value. Instead, return a boolean or masked string:
```python
"server": {
    "api_key_set": bool(cfg.get("server.api_key", "")),
    # never return the actual key
},
```
The frontend settings modal should show "API key is configured ✓" rather than the key value.

---

## BUG-M2: `Path.stat()` called on image path after generation — can throw unclearly

**File:** `backend/gateway/router.py:270–271`, `backend/gateway/router.py:550–551`
**Severity:** Medium
**Impact:** If for any reason the image file was not written (e.g., disk full, permission error), `image_path.stat().st_size` raises `FileNotFoundError` inside the `try/except Exception` block. The resulting 500 response will say "Image generation failed: [Errno 2] No such file or directory: '...'" which is misleading since the image was generated — the failure is in saving.

### Root Cause
```python
image_path = Path(result["image_path"])
await db.save_image_metadata(
    ...
    file_size=image_path.stat().st_size,  # ← can throw
    ...
)
```

### Fix
Wrap the stat call or get the file size from the already-decoded image bytes in the adapter:
```python
file_size = image_path.stat().st_size if image_path.exists() else 0
```

---

## BUG-M3: Settings changes to API key don't update CORS until server restart

**File:** `backend/gateway/main.py:52–59`
**Severity:** Medium
**Impact:** The CORS `allow_origins` list is computed once at module import time. If a user sets an API key via `PUT /api/settings` to lock down the server, the CORS policy remains `["*"]` until the backend is restarted. This is a configuration footgun — the user may believe they've secured the server when they haven't.

### Root Cause
```python
_api_key_set = bool(_cfg.get("server.api_key"))  # computed once at startup
_allowed_origins = ...  # never recalculated
```

### Fix
Either:
1. Document clearly that CORS/API key changes require a server restart, or
2. Use a dynamic origin check via a custom `allow_origin_regex` or `dispatch` override that reads the current config value on each request.

---

## BUG-M4: `is_first_message()` check is unreliable for concurrent sessions

**File:** `backend/gateway/ollama_router.py:129`, `backend/storage/database.py:321–338`
**Severity:** Medium
**Impact:** In high-concurrency scenarios (multiple tabs or rapid messages), `is_first_message()` checks `COUNT(*) == 1` after saving the user message. If two messages are saved near-simultaneously, the count could be 2 when checked, causing no auto-title to be generated even for a new session.

### Root Cause
There is a TOCTOU (time-of-check/time-of-use) window between `save_message()` and `is_first_message()`:
```python
await _db.save_message(session_id, "user", request.message)  # saves msg
is_first = await _db.is_first_message(session_id)            # checks count
```

### Fix
Pass the saved message ID back from `save_message()` and check if it equals 1 (the first autoincrement ID for the session is a session-level concept, not global). Alternatively, use a `SELECT COUNT(*) FROM conversations WHERE session_id = ? AND id <= ?` check, or rely on the sessions table `created_at` vs `last_activity` comparison.

---

## BUG-M5: `httpx.AsyncClient` in Auto1111Adapter is never closed

**File:** `backend/services/image_service/adapters/auto1111_adapter.py:27`
**Severity:** Medium
**Impact:** The `httpx.AsyncClient` is created in `__init__` but no shutdown hook closes it. Over the lifetime of the application, this may generate resource leak warnings and eventually cause connection pool exhaustion if the service is restarted many times in the same process.

### Root Cause
```python
self.client = httpx.AsyncClient(timeout=300.0)
# ↑ never closed
```

### Fix
Implement `async def close(self)` and call it in the FastAPI lifespan shutdown event, or use `async with httpx.AsyncClient() as client:` per-request (simpler but slightly slower):

```python
# In main.py lifespan:
async with lifespan_context:
    yield
    await image_service._adapter.close()  # or expose close() on ImageServiceManager
```

---

## BUG-M6: Relative upload paths stored in DB — breaks if app run from different directory

**File:** `backend/gateway/router.py:604`
**Severity:** Medium
**Impact:** The stored path saved to the database for uploads is relative: `./backend/storage/data/uploads/<session>/<file>`. If the application is ever started from a directory other than the project root, all existing upload paths become invalid and `read_file` will fail on them.

### Root Cause
```python
upload_dir = pathlib.Path("./backend/storage/data/uploads") / bucket
```

### Fix
Use absolute paths by anchoring to the project root:
```python
project_root = Path(__file__).parent.parent.parent
upload_dir = project_root / "backend/storage/data/uploads" / bucket
```
Apply the same fix to the image save path in `auto1111_adapter.py`.
