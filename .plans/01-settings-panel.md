# Plan 01 — Settings Panel & User Configuration

## Problem
A Settings button exists in the sidebar but does nothing. There is no UI for the user to configure anything — model defaults, TTS voice, API key, filesystem allowlist, etc. Currently the only way to change config is to edit `config/default_config.json` by hand.

## Scope
Full settings modal with backend endpoints, covering all user-relevant config values.

---

## Backend

### New endpoints (add to `router.py`)

```
GET  /api/settings          → returns current user-facing config
PUT  /api/settings          → saves partial or full config update
```

Response shape:
```json
{
  "chat": {
    "default_model": "llama3",
    "system_prompt": ""
  },
  "image": {
    "default_model": "",
    "default_sampler": "Euler a",
    "default_steps": 20,
    "default_cfg": 7.0,
    "default_width": 512,
    "default_height": 512
  },
  "tts": {
    "enabled": true,
    "default_voice": "en_US-lessac-medium"
  },
  "tools": {
    "filesystem_allowlist": ["C:/Users", "D:/Documents"],
    "max_file_size_mb": 10
  },
  "server": {
    "api_key": ""
  }
}
```

Only expose keys that the user should be able to change. Strip sensitive internals (paths, host/port).

### Storage
Persist changes through the existing `ConfigManager.set()` / `ConfigManager.save()` mechanism already in `backend/storage/config.py`.

---

## Frontend

### New component: `SettingsModal.tsx`
- Full-screen modal (not a separate page) triggered by the sidebar Settings button
- Tabbed layout: **Chat · Image · TTS · Tools · Server**

#### Chat tab
- Default model dropdown (populated from chat models list)
- System prompt textarea (persisted, sent with every new conversation)
- Toggle: stream responses

#### Image tab
- Default checkpoint dropdown
- Default sampler dropdown
- Default steps / CFG sliders
- Default width × height presets

#### TTS tab
- Enable/disable TTS checkbox
- Default voice dropdown (populated from `GET /api/models` `tts` field)
- Test button: sends a sample phrase through TTS to verify voice

#### Tools tab
- Filesystem allowlist: editable list of directory paths (add/remove entries)
- Max file size slider (1–100 MB)

#### Server tab
- API key input (password field, shows/hides)
- Save button + confirmation

### State changes in `ChatContext`
- Load settings on mount, store in context
- `system_prompt` from settings pre-fills every new chat request
- `default_model` pre-selects the model dropdown
- `tts.enabled` pre-sets the TTS toggle

---

## Files to touch
- `backend/gateway/router.py` — add GET/PUT /api/settings
- `backend/storage/config.py` — expose a `get_user_settings()` / `update_user_settings()` helper
- `frontend-web/src/components/SettingsModal.tsx` — new file
- `frontend-web/src/components/Sidebar.tsx` — wire Settings button to open modal
- `frontend-web/src/context/ChatContext.tsx` — load + store settings, apply defaults
- `frontend-web/src/api/client.ts` — add `getSettings()`, `updateSettings()` functions

---

## Acceptance criteria
- [ ] Settings modal opens from sidebar button
- [ ] All fields load from live config
- [ ] Saving updates config file on disk
- [ ] System prompt from settings is applied to new chats
- [ ] Default model pre-selects in TopBar dropdown
- [ ] TTS default voice is used when TTS is triggered
- [ ] Page refresh preserves all settings (they come from server)
