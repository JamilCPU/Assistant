"""SQLite database for conversation history and tool execution logs."""

import aiosqlite
import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from backend.storage.config import get_config


class Database:
    """Manages SQLite database for conversations and tool logs."""
    
    def __init__(self, db_path: Optional[str] = None):
        """
        Initialize database.
        
        Args:
            db_path: Path to database file. If None, uses config.
        """
        if db_path is None:
            config = get_config()
            db_path = config.get("storage.conversations_db", "./backend/storage/data/conversations/assistant.db")
        
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
    
    async def initialize(self) -> None:
        """Initialize database tables."""
        async with aiosqlite.connect(str(self.db_path)) as db:
            # Conversations table
            await db.execute("""
                CREATE TABLE IF NOT EXISTS conversations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    metadata TEXT
                )
            """)
            
            # Create index for conversations
            await db.execute("""
                CREATE INDEX IF NOT EXISTS idx_conversations_session_id 
                ON conversations(session_id)
            """)
            
            # Tool executions table
            await db.execute("""
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
                )
            """)
            
            # Create index for tool_executions
            await db.execute("""
                CREATE INDEX IF NOT EXISTS idx_tool_executions_session_id 
                ON tool_executions(session_id)
            """)
            
            # Sessions table
            await db.execute("""
                CREATE TABLE IF NOT EXISTS sessions (
                    session_id TEXT PRIMARY KEY,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    last_activity DATETIME DEFAULT CURRENT_TIMESTAMP,
                    title TEXT
                )
            """)
            
            # Generated images table
            await db.execute("""
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
                )
            """)

            # Personas table
            await db.execute("""
                CREATE TABLE IF NOT EXISTS personas (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    system_prompt TEXT NOT NULL,
                    default_model TEXT,
                    icon TEXT DEFAULT '🤖',
                    is_builtin INTEGER DEFAULT 0,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Uploads table
            await db.execute("""
                CREATE TABLE IF NOT EXISTS uploads (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    upload_id TEXT NOT NULL UNIQUE,
                    session_id TEXT,
                    original_filename TEXT NOT NULL,
                    stored_path TEXT NOT NULL,
                    file_size INTEGER,
                    mime_type TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Index for uploads by session
            await db.execute("""
                CREATE INDEX IF NOT EXISTS idx_uploads_session_id
                ON uploads(session_id)
            """)

            await db.commit()

    async def save_upload(
        self,
        upload_id: str,
        session_id: Optional[str],
        original_filename: str,
        stored_path: str,
        file_size: Optional[int],
        mime_type: Optional[str],
    ) -> int:
        """
        Save upload metadata to the database.

        Returns:
            Record ID
        """
        async with aiosqlite.connect(str(self.db_path)) as db:
            cursor = await db.execute(
                """
                INSERT INTO uploads (upload_id, session_id, original_filename, stored_path, file_size, mime_type)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (upload_id, session_id, original_filename, stored_path, file_size, mime_type),
            )
            await db.commit()
            return cursor.lastrowid

    async def get_session_uploads(self, session_id: str) -> List[Dict[str, Any]]:
        """Return all uploads for a given session."""
        async with aiosqlite.connect(str(self.db_path)) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                """
                SELECT upload_id, session_id, original_filename, stored_path, file_size, mime_type, created_at
                FROM uploads
                WHERE session_id = ?
                ORDER BY created_at ASC
                """,
                (session_id,),
            ) as cursor:
                rows = await cursor.fetchall()
                return [dict(row) for row in rows]

    async def get_upload(self, upload_id: str) -> Optional[Dict[str, Any]]:
        """Return a single upload record by upload_id, or None."""
        async with aiosqlite.connect(str(self.db_path)) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                """
                SELECT upload_id, session_id, original_filename, stored_path, file_size, mime_type, created_at
                FROM uploads
                WHERE upload_id = ?
                """,
                (upload_id,),
            ) as cursor:
                row = await cursor.fetchone()
                if row is None:
                    return None
                return dict(row)

    async def save_message(
        self,
        session_id: str,
        role: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> int:
        """
        Save a message to the database.
        
        Args:
            session_id: Session identifier
            role: Message role (user, assistant, system)
            content: Message content
            metadata: Optional metadata dictionary
            
        Returns:
            Message ID
        """
        async with aiosqlite.connect(str(self.db_path)) as db:
            metadata_json = json.dumps(metadata) if metadata else None
            
            cursor = await db.execute("""
                INSERT INTO conversations (session_id, role, content, metadata)
                VALUES (?, ?, ?, ?)
            """, (session_id, role, content, metadata_json))
            
            await db.commit()
            
            # Update session last_activity (preserve created_at and title)
            await db.execute("""
                INSERT INTO sessions (session_id, created_at, last_activity, title)
                VALUES (?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, NULL)
                ON CONFLICT(session_id) DO UPDATE SET
                    last_activity = CURRENT_TIMESTAMP
            """, (session_id,))
            
            await db.commit()
            
            return cursor.lastrowid
    
    async def get_conversation(
        self,
        session_id: str,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Get conversation messages for a session.
        
        Args:
            session_id: Session identifier
            limit: Optional limit on number of messages
            
        Returns:
            List of message dictionaries
        """
        async with aiosqlite.connect(str(self.db_path)) as db:
            db.row_factory = aiosqlite.Row
            
            query = """
                SELECT id, role, content, timestamp, metadata
                FROM conversations
                WHERE session_id = ?
                ORDER BY timestamp ASC
            """
            
            if limit:
                query += f" LIMIT {limit}"
            
            async with db.execute(query, (session_id,)) as cursor:
                rows = await cursor.fetchall()
                
                messages = []
                for row in rows:
                    msg = {
                        "id": row["id"],
                        "role": row["role"],
                        "content": row["content"],
                        "timestamp": row["timestamp"],
                        "metadata": json.loads(row["metadata"]) if row["metadata"] else None
                    }
                    messages.append(msg)
                
                return messages
    
    async def list_sessions(self) -> List[Dict[str, Any]]:
        """
        List all conversation sessions.
        
        Returns:
            List of session dictionaries
        """
        async with aiosqlite.connect(str(self.db_path)) as db:
            db.row_factory = aiosqlite.Row
            
            async with db.execute("""
                SELECT session_id, created_at, last_activity, title
                FROM sessions
                ORDER BY last_activity DESC
            """) as cursor:
                rows = await cursor.fetchall()
                
                sessions = []
                for row in rows:
                    session = {
                        "session_id": row["session_id"],
                        "created_at": row["created_at"],
                        "last_activity": row["last_activity"],
                        "title": row["title"]
                    }
                    sessions.append(session)
                
                return sessions
    
    async def update_session_title(self, session_id: str, title: str) -> None:
        """
        Update the title of a session.

        Args:
            session_id: Session identifier
            title: New title string
        """
        async with aiosqlite.connect(str(self.db_path)) as db:
            await db.execute(
                "UPDATE sessions SET title = ? WHERE session_id = ?",
                (title, session_id),
            )
            await db.commit()

    async def is_first_message(self, session_id: str) -> bool:
        """
        Return True if there is exactly one message saved for this session.

        Use this *after* saving the first user message to decide whether to
        generate an auto-title.

        Args:
            session_id: Session identifier
        """
        async with aiosqlite.connect(str(self.db_path)) as db:
            async with db.execute(
                "SELECT COUNT(*) FROM conversations WHERE session_id = ?",
                (session_id,),
            ) as cursor:
                row = await cursor.fetchone()
                count = row[0] if row else 0
                return count == 1

    async def delete_session(self, session_id: str) -> None:
        """
        Delete a conversation session.
        
        Args:
            session_id: Session identifier
        """
        async with aiosqlite.connect(str(self.db_path)) as db:
            await db.execute("DELETE FROM conversations WHERE session_id = ?", (session_id,))
            await db.execute("DELETE FROM tool_executions WHERE session_id = ?", (session_id,))
            await db.execute("DELETE FROM sessions WHERE session_id = ?", (session_id,))
            await db.commit()
    
    async def log_tool_execution(
        self,
        session_id: str,
        message_id: Optional[int],
        tool_name: str,
        arguments: Dict[str, Any],
        result: Any,
        success: bool = True
    ) -> None:
        """
        Log a tool execution.
        
        Args:
            session_id: Session identifier
            message_id: Optional message ID that triggered the tool
            tool_name: Name of the tool
            arguments: Tool arguments
            result: Tool execution result
            success: Whether execution was successful
        """
        async with aiosqlite.connect(str(self.db_path)) as db:
            await db.execute("""
                INSERT INTO tool_executions 
                (session_id, message_id, tool_name, arguments, result, success)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                session_id,
                message_id,
                tool_name,
                json.dumps(arguments),
                json.dumps(result) if result is not None else None,
                success
            ))
            await db.commit()
    
    async def save_image_metadata(
        self,
        filename: str,
        filepath: str,
        prompt: str,
        negative_prompt: Optional[str],
        model_name: Optional[str],
        lora_used: Optional[List[str]],
        parameters: Dict[str, Any],
        file_size: int,
        width: int,
        height: int
    ) -> int:
        """
        Save image generation metadata.
        
        Args:
            filename: Image filename
            filepath: Relative filepath
            prompt: Generation prompt
            negative_prompt: Optional negative prompt
            model_name: Model/checkpoint name
            lora_used: Optional list of LoRA names
            parameters: Generation parameters
            file_size: File size in bytes
            width: Image width
            height: Image height
            
        Returns:
            Image record ID
        """
        async with aiosqlite.connect(str(self.db_path)) as db:
            cursor = await db.execute("""
                INSERT INTO generated_images 
                (filename, filepath, prompt, negative_prompt, model_name, 
                 lora_used, parameters, file_size, width, height)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                filename,
                filepath,
                prompt,
                negative_prompt,
                model_name,
                json.dumps(lora_used) if lora_used else None,
                json.dumps(parameters),
                file_size,
                width,
                height
            ))
            await db.commit()
            return cursor.lastrowid
    
    async def get_images_paginated(
        self,
        page: int = 1,
        per_page: int = 24,
        prompt_filter: Optional[str] = None,
        model_filter: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Return a paginated, optionally filtered list of generated images.

        Args:
            page: 1-based page number
            per_page: records per page
            prompt_filter: optional substring to match against prompt
            model_filter: optional substring to match against model_name

        Returns:
            Dict with keys: images, total, page, per_page
        """
        async with aiosqlite.connect(str(self.db_path)) as db:
            db.row_factory = aiosqlite.Row

            conditions: List[str] = []
            params: List[Any] = []

            if prompt_filter:
                conditions.append("prompt LIKE ?")
                params.append(f"%{prompt_filter}%")
            if model_filter:
                conditions.append("model_name LIKE ?")
                params.append(f"%{model_filter}%")

            where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""

            count_query = f"SELECT COUNT(*) FROM generated_images {where_clause}"
            async with db.execute(count_query, params) as cursor:
                row = await cursor.fetchone()
                total: int = row[0] if row else 0

            offset = (page - 1) * per_page
            data_query = f"""
                SELECT id, filename, filepath, prompt, negative_prompt,
                       model_name, lora_used, parameters, created_at,
                       file_size, width, height
                FROM generated_images
                {where_clause}
                ORDER BY created_at DESC
                LIMIT ? OFFSET ?
            """
            async with db.execute(data_query, params + [per_page, offset]) as cursor:
                rows = await cursor.fetchall()

                images = []
                for row in rows:
                    img = {
                        "id": row["id"],
                        "filename": row["filename"],
                        "filepath": row["filepath"],
                        "prompt": row["prompt"],
                        "negative_prompt": row["negative_prompt"],
                        "model_name": row["model_name"],
                        "lora_used": json.loads(row["lora_used"]) if row["lora_used"] else None,
                        "parameters": json.loads(row["parameters"]),
                        "created_at": row["created_at"],
                        "file_size": row["file_size"],
                        "width": row["width"],
                        "height": row["height"],
                    }
                    images.append(img)

            return {"images": images, "total": total, "page": page, "per_page": per_page}

    async def get_image(self, image_id: int) -> Optional[Dict[str, Any]]:
        """
        Return a single image record by ID.

        Args:
            image_id: primary key of the generated_images row

        Returns:
            Image metadata dict, or None if not found
        """
        async with aiosqlite.connect(str(self.db_path)) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                """
                SELECT id, filename, filepath, prompt, negative_prompt,
                       model_name, lora_used, parameters, created_at,
                       file_size, width, height
                FROM generated_images
                WHERE id = ?
                """,
                (image_id,),
            ) as cursor:
                row = await cursor.fetchone()
                if row is None:
                    return None
                return {
                    "id": row["id"],
                    "filename": row["filename"],
                    "filepath": row["filepath"],
                    "prompt": row["prompt"],
                    "negative_prompt": row["negative_prompt"],
                    "model_name": row["model_name"],
                    "lora_used": json.loads(row["lora_used"]) if row["lora_used"] else None,
                    "parameters": json.loads(row["parameters"]),
                    "created_at": row["created_at"],
                    "file_size": row["file_size"],
                    "width": row["width"],
                    "height": row["height"],
                }

    async def delete_image(self, image_id: int) -> Optional[str]:
        """
        Delete an image record and return its filepath so the caller can
        remove the file from disk.

        Args:
            image_id: primary key of the generated_images row

        Returns:
            filepath string if the record existed, else None
        """
        async with aiosqlite.connect(str(self.db_path)) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                "SELECT filepath FROM generated_images WHERE id = ?",
                (image_id,),
            ) as cursor:
                row = await cursor.fetchone()
            if row is None:
                return None
            filepath = row["filepath"]
            await db.execute("DELETE FROM generated_images WHERE id = ?", (image_id,))
            await db.commit()
            return filepath

    async def list_images(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        List generated images.

        Args:
            limit: Optional limit on number of images

        Returns:
            List of image metadata dictionaries
        """
        async with aiosqlite.connect(str(self.db_path)) as db:
            db.row_factory = aiosqlite.Row
            
            query = """
                SELECT id, filename, filepath, prompt, negative_prompt, 
                       model_name, lora_used, parameters, created_at, 
                       file_size, width, height
                FROM generated_images
                ORDER BY created_at DESC
            """
            
            if limit:
                query += f" LIMIT {limit}"
            
            async with db.execute(query) as cursor:
                rows = await cursor.fetchall()
                
                images = []
                for row in rows:
                    img = {
                        "id": row["id"],
                        "filename": row["filename"],
                        "filepath": row["filepath"],
                        "prompt": row["prompt"],
                        "negative_prompt": row["negative_prompt"],
                        "model_name": row["model_name"],
                        "lora_used": json.loads(row["lora_used"]) if row["lora_used"] else None,
                        "parameters": json.loads(row["parameters"]),
                        "created_at": row["created_at"],
                        "file_size": row["file_size"],
                        "width": row["width"],
                        "height": row["height"]
                    }
                    images.append(img)
                
                return images


    # ── Persona CRUD ──────────────────────────────────────────────────────

    BUILTIN_PERSONAS = [
        {
            "name": "General Assistant",
            "icon": "🤖",
            "system_prompt": "You are a helpful, accurate, and concise assistant.",
            "is_builtin": 1,
        },
        {
            "name": "Code Assistant",
            "icon": "💻",
            "system_prompt": (
                "You are an expert programmer. Provide clean, well-commented code. "
                "Prefer explaining the 'why' alongside the 'what'."
            ),
            "is_builtin": 1,
        },
        {
            "name": "Creative Writer",
            "icon": "✍️",
            "system_prompt": (
                "You are a creative writing assistant with a vivid imagination. "
                "Help craft engaging stories, dialogue, and prose."
            ),
            "is_builtin": 1,
        },
        {
            "name": "Data Analyst",
            "icon": "📊",
            "system_prompt": (
                "You are a data analysis expert. Help interpret data, write queries, "
                "suggest visualizations, and explain statistical concepts clearly."
            ),
            "is_builtin": 1,
        },
        {
            "name": "SQL Expert",
            "icon": "🗄️",
            "system_prompt": (
                "You specialize in SQL. Write efficient queries, explain execution "
                "plans, and help with schema design."
            ),
            "is_builtin": 1,
        },
    ]

    async def seed_builtin_personas(self) -> None:
        """Insert built-in personas if the table is empty."""
        async with aiosqlite.connect(str(self.db_path)) as db:
            async with db.execute("SELECT COUNT(*) FROM personas WHERE is_builtin = 1") as cursor:
                row = await cursor.fetchone()
                count = row[0] if row else 0

            if count == 0:
                for p in self.BUILTIN_PERSONAS:
                    await db.execute(
                        """
                        INSERT OR IGNORE INTO personas (name, system_prompt, icon, is_builtin)
                        VALUES (?, ?, ?, ?)
                        """,
                        (p["name"], p["system_prompt"], p["icon"], p["is_builtin"]),
                    )
                await db.commit()

    async def list_personas(self) -> List[Dict[str, Any]]:
        """Return all personas as a list of dicts."""
        async with aiosqlite.connect(str(self.db_path)) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                "SELECT id, name, system_prompt, default_model, icon, is_builtin, created_at "
                "FROM personas ORDER BY is_builtin DESC, id ASC"
            ) as cursor:
                rows = await cursor.fetchall()
                return [
                    {
                        "id": row["id"],
                        "name": row["name"],
                        "system_prompt": row["system_prompt"],
                        "default_model": row["default_model"],
                        "icon": row["icon"],
                        "is_builtin": bool(row["is_builtin"]),
                        "created_at": row["created_at"],
                    }
                    for row in rows
                ]

    async def create_persona(
        self,
        name: str,
        system_prompt: str,
        icon: str = "🤖",
        default_model: Optional[str] = None,
    ) -> int:
        """Insert a new custom persona and return its id."""
        async with aiosqlite.connect(str(self.db_path)) as db:
            cursor = await db.execute(
                """
                INSERT INTO personas (name, system_prompt, icon, default_model, is_builtin)
                VALUES (?, ?, ?, ?, 0)
                """,
                (name, system_prompt, icon, default_model),
            )
            await db.commit()
            return cursor.lastrowid

    async def update_persona(
        self,
        persona_id: int,
        name: Optional[str] = None,
        system_prompt: Optional[str] = None,
        icon: Optional[str] = None,
        default_model: Optional[str] = None,
    ) -> None:
        """Update fields on a persona (only non-None values are applied)."""
        async with aiosqlite.connect(str(self.db_path)) as db:
            fields: List[str] = []
            params: List[Any] = []
            if name is not None:
                fields.append("name = ?")
                params.append(name)
            if system_prompt is not None:
                fields.append("system_prompt = ?")
                params.append(system_prompt)
            if icon is not None:
                fields.append("icon = ?")
                params.append(icon)
            if default_model is not None:
                fields.append("default_model = ?")
                params.append(default_model)
            if not fields:
                return
            params.append(persona_id)
            await db.execute(
                f"UPDATE personas SET {', '.join(fields)} WHERE id = ?",
                params,
            )
            await db.commit()

    async def delete_persona(self, persona_id: int) -> bool:
        """
        Delete a persona if it is not a built-in.

        Returns True if deleted, False if the persona is built-in or not found.
        """
        async with aiosqlite.connect(str(self.db_path)) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                "SELECT is_builtin FROM personas WHERE id = ?", (persona_id,)
            ) as cursor:
                row = await cursor.fetchone()
            if row is None or row["is_builtin"]:
                return False
            await db.execute("DELETE FROM personas WHERE id = ?", (persona_id,))
            await db.commit()
            return True


# Global database instance
_db: Optional[Database] = None


def get_database(db_path: Optional[str] = None) -> Database:
    """Get global database instance."""
    global _db
    if _db is None:
        _db = Database(db_path)
    return _db
