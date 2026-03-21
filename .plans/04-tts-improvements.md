# Plan 04 — TTS Improvements

## Problems

### A. Voice detection is hardcoded
`piper_adapter.py` lines 119–133 return a hardcoded list of 3 voices instead of scanning the Piper models directory for `.onnx` files. If the user downloads additional voices, they won't appear.

### B. No voice selection in the UI
There is no dropdown to choose which voice Piper uses. The voice is locked to whatever is set in config.

### C. Duration estimate is wrong
`duration = len(text) * 0.1` (10 chars/second) is a rough guess. Piper doesn't report duration, but the actual audio file can be read after synthesis.

### D. Audio playback is broken in the frontend
`ChatResponse` has `audio_url` and `ChatContext` receives it in `onDone()`, but the URL is never played. There's no `<audio>` element rendered anywhere in the UI.

---

## A — Fix Voice Detection

### `piper_adapter.py`

Replace the hardcoded list in `list_voices()`:
```python
async def list_voices(self) -> List[str]:
    voices = []
    piper_dir = Path(self.piper_path).parent
    for onnx_file in sorted(piper_dir.glob("*.onnx")):
        voices.append(onnx_file.stem)
    return voices if voices else ["en_US-lessac-medium"]  # fallback
```

Also scan a configurable `piper_models/` subdirectory as a secondary location.

---

## B — Voice Selection UI

### Backend
The `speak()` method already accepts a `voice` parameter — it just isn't exposed via the API.

Update `POST /api/chat` and `POST /api/chat/stream` request model:
```python
class ChatRequest(BaseModel):
    ...
    tts_voice: Optional[str] = None  # if None, use config default
```

Pass `tts_voice` through to `tts_service.speak()`.

### Frontend

#### `TopBar.tsx`
Replace the current TTS toggle (on/off) with a split control:
- Toggle checkbox: TTS on/off
- When on: voice selector dropdown (populated from `GET /api/models` `tts` field)
- Persist selected voice in `ChatContext` state

#### `ChatContext.tsx`
- Add `ttsVoice: string | null` to state
- Add `SET_TTS_VOICE` action
- Pass `tts_voice` in `chatStream()` calls when TTS is enabled

---

## C — Accurate Duration

After Piper writes the `.wav` file, read its duration from the WAV header instead of estimating:

```python
import wave

def _get_wav_duration(filepath: str) -> float:
    with wave.open(filepath, 'r') as f:
        frames = f.getnframes()
        rate = f.getframerate()
        return frames / float(rate)
```

Update `piper_adapter.py` to call this after synthesis and return actual duration.

---

## D — Audio Playback in UI

### `ChatView.tsx` or `MessageBubble.tsx`

When a message has an associated `audio_url`, show a compact audio player inline below the assistant message:
- Small play/pause button
- Time display (e.g. `0:04 / 0:12`)
- Thin progress bar
- Uses native `<audio>` element styled to match the dark theme

### `ChatContext.tsx`
- Store `audioUrl` on the assistant message object after `onDone()` fires with a non-null `audio_url`
- Auto-play if TTS is enabled and auto-play option is on (add to settings)

### Static serving for audio
Add audio static file serving to `main.py` (same pattern as images):
```python
app.mount("/audio", StaticFiles(directory="./backend/storage/data/audio"), name="audio")
```
And proxy `/audio` in `vite.config.ts`.

---

## Files to touch
- `backend/services/tts_service/adapters/piper_adapter.py` — fix voice detection, fix duration
- `backend/models/chat.py` — add `tts_voice` to `ChatRequest`
- `backend/gateway/router.py` — pass `tts_voice` through to service
- `backend/gateway/ollama_router.py` — same
- `backend/gateway/main.py` — mount `/audio` static files
- `frontend-web/vite.config.ts` — proxy `/audio`
- `frontend-web/src/components/TopBar.tsx` — add voice selector
- `frontend-web/src/components/MessageBubble.tsx` — add audio player
- `frontend-web/src/context/ChatContext.tsx` — add ttsVoice state, attach audio_url to messages
- `frontend-web/src/api/client.ts` — add `tts_voice` to `ChatRequest` type

---

## Acceptance criteria
- [ ] `GET /api/models` `tts` array reflects actual `.onnx` files on disk
- [ ] Voice dropdown in TopBar shows real voices
- [ ] Selected voice is used in the next TTS generation
- [ ] Audio player appears inline below assistant messages when TTS was triggered
- [ ] Duration displayed is accurate (from WAV file, not estimated)
- [ ] Playback works (audio file is served correctly)
