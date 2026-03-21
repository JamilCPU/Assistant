# Plan 02 — Chat Enhancements

## Problems (4 separate gaps)

### A. Tool calls not shown in UI
When the LLM calls a tool, the frontend receives `tool_call` events over SSE but the `onToolCall()` callback does nothing. The user has no visibility into what tools were used or what they returned.

### B. Tool results not fed back to LLM
After a tool executes, its result is appended as plain text to the response string (`[Tool X executed: ...]`). The result is never sent back to the model in a proper `tool` role message for a follow-up generation pass. This means the LLM cannot reason over the tool output.

### C. Conversations have no titles
The `sessions.title` column is always NULL. The sidebar shows raw session IDs like `"3f2a9c…"`. No auto-titling happens.

### D. No conversation export
Users cannot save their conversation history outside the app.

---

## A — Tool Call Visualization

### Frontend changes

#### `MessageBubble.tsx`
Add a new bubble variant for `role: 'tool'` (or embed inline in the assistant bubble):
- Collapsible section inside the assistant message showing each tool call
- Header: `🔧 Used tool: search_files` with expand/collapse toggle
- Expanded body: arguments as formatted key-value, result as code block (truncated to 500 chars)
- Subtle styling — not as prominent as the actual response text

#### `ChatContext.tsx`
- `onToolCall()` callback: append a new message with `role: 'tool'` containing the call name and args
- Wire `streaming` flag so tool messages appear in-order with the assistant response

---

## B — Proper Tool Result Round-trip

### Backend changes (`ollama_router.py` streaming handler, `router.py` non-streaming handler)

Replace the current "append text" approach with a proper multi-turn tool use flow:

1. First generation pass → receives tool calls from LLM
2. Execute each tool call
3. Build a `tool` role message per result: `{"role": "tool", "content": "<result>", "tool_call_id": "..."}`
4. Send the updated message list (original + assistant message with tool calls + tool result messages) back to the LLM for a second generation pass
5. Stream the follow-up response tokens to the client

This is the standard OpenAI/Ollama tool-use flow. Ollama supports `role: tool` messages natively.

### Files
- `backend/gateway/ollama_router.py` — rewrite `event_generator()` tool handling block
- `backend/gateway/router.py` — rewrite tool handling block in `/api/chat`
- `backend/services/chat_service/adapters/ollama_adapter.py` — ensure `generate()` and `generate_stream()` accept arbitrary message history including `tool` role

---

## C — Auto Session Titles

### Backend
After saving the first user message of a new session, generate a title:
- Use a short summarization prompt: send the user's first message to the LLM with `"Summarize this in 5 words or fewer as a conversation title: {message}"`
- Run as a fire-and-forget background task (do not block the response)
- Persist result with `UPDATE sessions SET title = ? WHERE session_id = ?`

Add endpoint:
```
PATCH /api/conversations/{session_id}
Body: { "title": "Custom title" }
```
So users can also rename conversations manually (right-click or edit icon in sidebar).

### Frontend
- `Sidebar.tsx`: show title instead of truncated session ID; add a small edit icon on hover to rename inline
- `ChatContext.tsx`: after `refreshSessions()` on message done, titles will appear

---

## D — Conversation Export

### Backend
```
GET /api/conversations/{session_id}/export?format=markdown|json|txt
```
- `json`: raw messages array as JSON file download
- `markdown`: formatted `# Session\n\n**User:** ...\n\n**Assistant:** ...` document
- `txt`: plain text transcript

Use `StreamingResponse` with appropriate `Content-Disposition` header.

### Frontend
- Add export button to `ChatView.tsx` top-right area (visible when a session is loaded)
- Dropdown: JSON / Markdown / Plain text
- Triggers a download via `<a href="..." download>` pattern

---

## Files to touch
- `backend/gateway/router.py`
- `backend/gateway/ollama_router.py`
- `backend/services/chat_service/adapters/ollama_adapter.py`
- `backend/storage/database.py` — add `update_session_title()` method
- `frontend-web/src/components/MessageBubble.tsx`
- `frontend-web/src/components/ChatView.tsx`
- `frontend-web/src/components/Sidebar.tsx`
- `frontend-web/src/context/ChatContext.tsx`
- `frontend-web/src/api/client.ts`

---

## Acceptance criteria
- [ ] Tool calls appear as collapsible sections inside or below the assistant message
- [ ] LLM receives tool results and generates a follow-up response based on them
- [ ] New conversations auto-title from the first message within ~2 seconds
- [ ] Sidebar shows titles instead of raw IDs
- [ ] User can rename a conversation inline in the sidebar
- [ ] Export button downloads a file in the chosen format
