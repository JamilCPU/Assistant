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
            
            await db.commit()
    
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
            
            # Update session last_activity
            await db.execute("""
                INSERT OR REPLACE INTO sessions (session_id, last_activity, title)
                VALUES (?, CURRENT_TIMESTAMP, 
                    COALESCE((SELECT title FROM sessions WHERE session_id = ?), NULL))
            """, (session_id, session_id))
            
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


# Global database instance
_db: Optional[Database] = None


def get_database(db_path: Optional[str] = None) -> Database:
    """Get global database instance."""
    global _db
    if _db is None:
        _db = Database(db_path)
    return _db
