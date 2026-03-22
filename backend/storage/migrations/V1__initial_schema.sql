CREATE TABLE IF NOT EXISTS conversations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL,
    role TEXT NOT NULL,
    content TEXT NOT NULL,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    metadata TEXT
);

CREATE INDEX IF NOT EXISTS idx_conversations_session_id ON conversations(session_id);

CREATE TABLE IF NOT EXISTS tool_executions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL,
    message_id INTEGER,
    tool_name TEXT NOT NULL,
    arguments TEXT NOT NULL,
    result TEXT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    success BOOLEAN DEFAULT 1,
    FOREIGN KEY (message_id) REFERENCES conversations(id)
);

CREATE INDEX IF NOT EXISTS idx_tool_executions_session_id ON tool_executions(session_id);

CREATE TABLE IF NOT EXISTS sessions (
    session_id TEXT PRIMARY KEY,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    last_activity DATETIME DEFAULT CURRENT_TIMESTAMP,
    title TEXT
);

CREATE TABLE IF NOT EXISTS generated_images (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    filename TEXT NOT NULL,
    filepath TEXT NOT NULL,
    prompt TEXT NOT NULL,
    negative_prompt TEXT,
    model_name TEXT,
    lora_used TEXT,
    parameters TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    file_size INTEGER,
    width INTEGER,
    height INTEGER
);

CREATE TABLE IF NOT EXISTS personas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    system_prompt TEXT NOT NULL,
    default_model TEXT,
    icon TEXT DEFAULT '🤖',
    is_builtin INTEGER DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS uploads (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    upload_id TEXT NOT NULL UNIQUE,
    session_id TEXT,
    original_filename TEXT NOT NULL,
    stored_path TEXT NOT NULL,
    file_size INTEGER,
    mime_type TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_uploads_session_id ON uploads(session_id)
