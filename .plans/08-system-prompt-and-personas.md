# Plan 08 — System Prompt & Personas

## Problem
The `ChatRequest` model already has a `system_prompt` field, but there is no UI to set it. Users cannot configure what "personality" the assistant has, what its instructions are, or save reusable personas (e.g. "Code Reviewer", "Creative Writer", "SQL Expert").

---

## Features

### A. Persistent system prompt
- User types a system prompt that applies to all new conversations
- Saved in settings (see Plan 01)
- Pre-filled on every new `ChatRequest`

### B. Per-conversation system prompt override
- Before sending the first message in a new conversation, user can set a custom system prompt just for that session
- Editable inline above the input bar (collapsed by default, expand icon to show)
- Once the conversation starts, system prompt is locked (can view but not change mid-conversation)

### C. Persona library
- A saved list of named presets: `{name, system_prompt, default_model?, icon?}`
- Quick-pick from the sidebar or top bar before starting a conversation
- Built-in defaults: General Assistant, Code Assistant, Creative Writer, Data Analyst
- User can create/edit/delete their own personas

---

## Backend

### Personas storage
Add a `personas` table to SQLite:
```sql
CREATE TABLE personas (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    system_prompt TEXT NOT NULL,
    default_model TEXT,
    icon TEXT,
    is_builtin BOOLEAN DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
)
```

Seed built-in personas on first startup.

### New endpoints
```
GET    /api/personas              — list all personas
POST   /api/personas              — create new persona
PUT    /api/personas/{id}         — update persona
DELETE /api/personas/{id}         — delete (non-builtins only)
```

### Session-level system prompt
When saving the first message of a session, also save the system prompt used:
```sql
ALTER TABLE sessions ADD COLUMN system_prompt TEXT;
```
This allows the conversation history to reconstruct context properly.

---

## Frontend

### Persona picker — `PersonaPicker.tsx`
A dropdown accessible from the `WelcomeScreen` and from a button in the `TopBar`:
- Grid of persona cards: icon + name + first line of system prompt
- Click to select → system prompt field fills in
- "Custom" option to type free-form
- "New persona" option opens a small form (name + system prompt textarea + icon picker)

### System prompt editor — inline in `ChatView`
Above the `InputBar`, a collapsible section (closed by default):
- When open: shows a textarea with the current system prompt
- Hint text: "Set a system prompt for this conversation (apply before first message)"
- Lock icon appears after first message is sent: view-only after that

### `WelcomeScreen.tsx`
Replace the bare welcome text with:
- "How can I help you today?"
- Row of persona quick-select chips: General · Code · Creative · Data · +Custom
- Clicking one selects the persona and focuses the input bar

### `ChatContext.tsx`
- Add `systemPrompt: string` and `selectedPersona: Persona | null` to state
- `sendMessage()` passes `systemPrompt` on every message (not just first)
- `NEW_CHAT` resets persona and system prompt to defaults

---

## Files to touch
- `backend/storage/database.py` — `personas` table, `sessions.system_prompt`, CRUD methods
- `backend/gateway/router.py` — persona CRUD endpoints
- `backend/models/chat.py` — no changes needed (system_prompt already in ChatRequest)
- `frontend-web/src/api/client.ts` — persona API functions
- `frontend-web/src/components/PersonaPicker.tsx` — new file
- `frontend-web/src/components/WelcomeScreen.tsx` — add persona chips
- `frontend-web/src/components/ChatView.tsx` — add collapsible system prompt editor
- `frontend-web/src/components/TopBar.tsx` — add persona picker button
- `frontend-web/src/context/ChatContext.tsx` — add persona + system prompt state

---

## Built-in Personas (seed data)

| Name | Icon | System Prompt |
|------|------|---------------|
| General Assistant | 🤖 | You are a helpful, accurate, and concise assistant. |
| Code Assistant | 💻 | You are an expert programmer. Provide clean, well-commented code. Prefer explaining the "why" alongside the "what". |
| Creative Writer | ✍️ | You are a creative writing assistant with a vivid imagination. Help the user craft engaging stories, dialogue, and prose. |
| Data Analyst | 📊 | You are a data analysis expert. Help interpret data, write queries, suggest visualizations, and explain statistical concepts clearly. |
| SQL Expert | 🗄️ | You specialize in SQL. Write efficient queries, explain execution plans, and help with schema design. |

---

## Acceptance criteria
- [ ] WelcomeScreen shows persona quick-pick chips
- [ ] Selecting a persona fills the system prompt field
- [ ] System prompt is sent with every message in that conversation
- [ ] System prompt is locked (read-only) after first message sent
- [ ] User can create, edit, and delete custom personas
- [ ] Personas persist across page refreshes (stored in DB)
- [ ] Built-in personas always present and cannot be deleted
