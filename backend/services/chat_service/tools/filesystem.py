"""Filesystem tools: search_files, read_file, list_directory, write_file, delete_file, move_file, get_file_info, list_uploads."""

import os
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

from backend.services.chat_service.tools.base import Tool
from backend.services.chat_service.tools.guardrails import get_guardrails

# Uploads directory — always allowed for read_file and search_files
_UPLOADS_DIR = Path("./backend/storage/data/uploads").resolve()


def _path_hint() -> str:
    """Return a human-readable hint of the allowed base paths for use in tool descriptions."""
    g = get_guardrails()
    hint = g.allowed_paths_hint()
    return f"Allowed base paths: {hint}."


class SearchFilesTool(Tool):
    """Tool for searching files."""

    def __init__(self):
        g = get_guardrails()
        super().__init__(
            name="search_files",
            description=(
                f"Search for files by name or pattern within allowed directories. "
                f"{_path_hint()} Example: search_files({{\"query\": \"report.txt\"}})"
            ),
            schema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search query — filename or partial name to match"
                    }
                },
                "required": ["query"]
            },
            required_permissions=["search_files"]
        )
        self.guardrails = g

    async def execute(self, args: Dict[str, Any]) -> Dict[str, Any]:
        query = args.get("query", "")
        if not query:
            return {"files": [], "error": "Query is required"}

        results = []
        allowlist: List[str] = list(self.guardrails.allowlist) + [str(_UPLOADS_DIR)]

        MAX_DEPTH = 4  # Prevent runaway walks on large directory trees

        for allowed_dir in allowlist:
            allowed_path = Path(allowed_dir).resolve()
            if not allowed_path.exists():
                continue
            try:
                for root, dirs, files in os.walk(allowed_path):
                    # Enforce depth limit
                    depth = len(Path(root).relative_to(allowed_path).parts)
                    if depth >= MAX_DEPTH:
                        dirs.clear()
                        continue
                    for file in files:
                        if query.lower() in file.lower():
                            file_path = Path(root) / file
                            try:
                                if self.guardrails.is_path_allowed(file_path):
                                    results.append(str(file_path))
                            except Exception:
                                continue
                    if len(results) >= 50:
                        break
            except PermissionError:
                continue

        results = results[:50]
        return {"files": results, "count": len(results)}


class ReadFileTool(Tool):
    """Tool for reading files."""

    def __init__(self):
        g = get_guardrails()
        super().__init__(
            name="read_file",
            description=(
                f"Read the text contents of a file within allowed directories. "
                f"{_path_hint()} "
                f"Example: read_file({{\"path\": \"{g.allowlist[0] if g.allowlist else '/host'}/Desktop/notes.txt\"}})"
            ),
            schema={
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Full absolute path to the file to read"
                    }
                },
                "required": ["path"]
            },
            required_permissions=["read_file"]
        )
        self.guardrails = g

    async def execute(self, args: Dict[str, Any]) -> Dict[str, Any]:
        file_path_str = args.get("path") or args.get("file_path", "")
        if not file_path_str:
            return {"error": "Path is required"}

        try:
            normalized = self.guardrails.normalize_path(file_path_str)
            uploads_allowed = False
            try:
                normalized.relative_to(_UPLOADS_DIR)
                uploads_allowed = True
            except ValueError:
                pass

            file_path = normalized if uploads_allowed else self.guardrails.validate_file_path(file_path_str)
            self.guardrails.check_file_size(file_path)

            if not file_path.exists():
                return {"error": f"File not found: {file_path}"}
            if not file_path.is_file():
                return {"error": f"Path is not a file: {file_path}"}

            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()
                return {"content": content, "path": str(file_path), "encoding": "utf-8"}
            except UnicodeDecodeError:
                return {
                    "error": "File is not a text file (binary content)",
                    "path": str(file_path),
                    "size": file_path.stat().st_size
                }

        except ValueError as e:
            return {"error": str(e)}
        except Exception as e:
            return {"error": f"Error reading file: {str(e)}"}


class ListDirectoryTool(Tool):
    """Tool for listing directory contents."""

    def __init__(self):
        g = get_guardrails()
        super().__init__(
            name="list_directory",
            description=(
                f"List the contents of a directory (files and subdirectories). "
                f"{_path_hint()} "
                f"Example: list_directory({{\"path\": \"{g.allowlist[0] if g.allowlist else '/host'}/Desktop\"}})"
            ),
            schema={
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Full absolute path to the directory to list"
                    },
                    "show_hidden": {
                        "type": "boolean",
                        "description": "Include hidden files/folders (starting with '.'). Defaults to false."
                    }
                },
                "required": ["path"]
            },
            required_permissions=["search_files"]
        )
        self.guardrails = g

    async def execute(self, args: Dict[str, Any]) -> Dict[str, Any]:
        dir_path_str = args.get("path") or args.get("directory", "")
        if not dir_path_str:
            return {"error": "Path is required"}

        show_hidden = args.get("show_hidden", False)

        try:
            dir_path = self.guardrails.validate_file_path(dir_path_str)
        except ValueError as e:
            return {"error": str(e)}

        if not dir_path.exists():
            return {"error": f"Directory not found: {dir_path}"}
        if not dir_path.is_dir():
            return {"error": f"Path is not a directory: {dir_path}"}

        try:
            entries = []
            for entry in sorted(dir_path.iterdir(), key=lambda e: (e.is_file(), e.name.lower())):
                if not show_hidden and entry.name.startswith("."):
                    continue
                try:
                    stat = entry.stat()
                    entries.append({
                        "name": entry.name,
                        "type": "file" if entry.is_file() else "directory",
                        "size": stat.st_size if entry.is_file() else None,
                        "modified": datetime.fromtimestamp(stat.st_mtime).isoformat()
                    })
                except PermissionError:
                    entries.append({"name": entry.name, "type": "unknown", "error": "permission denied"})

            return {"path": str(dir_path), "entries": entries, "count": len(entries)}
        except PermissionError:
            return {"error": f"Permission denied: {dir_path}"}
        except Exception as e:
            return {"error": f"Error listing directory: {str(e)}"}


class GetFileInfoTool(Tool):
    """Tool for getting file or directory metadata."""

    def __init__(self):
        g = get_guardrails()
        super().__init__(
            name="get_file_info",
            description=(
                f"Get metadata about a file or directory: size, type, created/modified timestamps. "
                f"{_path_hint()} "
                f"Example: get_file_info({{\"path\": \"{g.allowlist[0] if g.allowlist else '/host'}/Desktop/notes.txt\"}})"
            ),
            schema={
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Full absolute path to the file or directory"
                    }
                },
                "required": ["path"]
            },
            required_permissions=["search_files"]
        )
        self.guardrails = g

    async def execute(self, args: Dict[str, Any]) -> Dict[str, Any]:
        path_str = args.get("path") or args.get("file_path", "")
        if not path_str:
            return {"error": "Path is required"}

        try:
            path = self.guardrails.validate_file_path(path_str)
        except ValueError as e:
            return {"error": str(e)}

        if not path.exists():
            return {"error": f"Path not found: {path}"}

        try:
            stat = path.stat()
            return {
                "path": str(path),
                "name": path.name,
                "type": "file" if path.is_file() else "directory",
                "size": stat.st_size,
                "created": datetime.fromtimestamp(stat.st_ctime).isoformat(),
                "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                "extension": path.suffix if path.is_file() else None,
            }
        except Exception as e:
            return {"error": f"Error getting file info: {str(e)}"}


class WriteFileTool(Tool):
    """Tool for writing (creating or overwriting) a text file."""

    def __init__(self):
        g = get_guardrails()
        super().__init__(
            name="write_file",
            description=(
                f"Create or overwrite a text file with the given content. "
                f"{_path_hint()} "
                f"Example: write_file({{\"path\": \"{g.allowlist[0] if g.allowlist else '/host'}/Desktop/notes.txt\", \"content\": \"Hello\"}})"
            ),
            schema={
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Full absolute path to the file to create or overwrite"
                    },
                    "content": {
                        "type": "string",
                        "description": "Text content to write to the file"
                    },
                    "create_dirs": {
                        "type": "boolean",
                        "description": "Create parent directories if they don't exist. Defaults to false."
                    }
                },
                "required": ["path", "content"]
            },
            required_permissions=["write_file"]
        )
        self.guardrails = g

    async def execute(self, args: Dict[str, Any]) -> Dict[str, Any]:
        path_str = args.get("path") or args.get("file_path", "")
        content = args.get("content", "")
        create_dirs = args.get("create_dirs", False)

        if not path_str:
            return {"error": "Path is required"}

        try:
            file_path = self.guardrails.validate_file_path(path_str)
        except ValueError as e:
            return {"error": str(e)}

        try:
            if create_dirs:
                file_path.parent.mkdir(parents=True, exist_ok=True)
            elif not file_path.parent.exists():
                return {"error": f"Parent directory does not exist: {file_path.parent}"}

            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)

            return {
                "success": True,
                "path": str(file_path),
                "bytes_written": len(content.encode("utf-8"))
            }
        except PermissionError:
            return {"error": f"Permission denied: {file_path}"}
        except Exception as e:
            return {"error": f"Error writing file: {str(e)}"}


class DeleteFileTool(Tool):
    """Tool for deleting a file."""

    def __init__(self):
        g = get_guardrails()
        super().__init__(
            name="delete_file",
            description=(
                f"Delete a single file (not directories). "
                f"{_path_hint()} "
                f"Example: delete_file({{\"path\": \"{g.allowlist[0] if g.allowlist else '/host'}/Desktop/old.txt\"}})"
            ),
            schema={
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Full absolute path to the file to delete"
                    }
                },
                "required": ["path"]
            },
            required_permissions=["write_file"]
        )
        self.guardrails = g

    async def execute(self, args: Dict[str, Any]) -> Dict[str, Any]:
        path_str = args.get("path") or args.get("file_path", "")
        if not path_str:
            return {"error": "Path is required"}

        try:
            file_path = self.guardrails.validate_file_path(path_str)
        except ValueError as e:
            return {"error": str(e)}

        if not file_path.exists():
            return {"error": f"File not found: {file_path}"}
        if file_path.is_dir():
            return {"error": "This tool only deletes files, not directories."}

        try:
            file_path.unlink()
            return {"success": True, "path": str(file_path)}
        except PermissionError:
            return {"error": f"Permission denied: {file_path}"}
        except Exception as e:
            return {"error": f"Error deleting file: {str(e)}"}


class MoveFileTool(Tool):
    """Tool for moving or renaming a file."""

    def __init__(self):
        g = get_guardrails()
        ex_base = g.allowlist[0] if g.allowlist else "/host"
        super().__init__(
            name="move_file",
            description=(
                f"Move or rename a file. Both source and destination must be in allowed paths. "
                f"{_path_hint()} "
                f"Example: move_file({{\"source\": \"{ex_base}/Desktop/old.txt\", \"destination\": \"{ex_base}/Desktop/new.txt\"}})"
            ),
            schema={
                "type": "object",
                "properties": {
                    "source": {
                        "type": "string",
                        "description": "Full absolute path of the file to move"
                    },
                    "destination": {
                        "type": "string",
                        "description": "Full absolute destination path (new name or new directory)"
                    }
                },
                "required": ["source", "destination"]
            },
            required_permissions=["write_file"]
        )
        self.guardrails = g

    async def execute(self, args: Dict[str, Any]) -> Dict[str, Any]:
        source_str = args.get("source") or args.get("src", "")
        dest_str = args.get("destination") or args.get("dest", "")

        if not source_str or not dest_str:
            return {"error": "Both source and destination are required"}

        try:
            source = self.guardrails.validate_file_path(source_str)
            destination = self.guardrails.validate_file_path(dest_str)
        except ValueError as e:
            return {"error": str(e)}

        if not source.exists():
            return {"error": f"Source not found: {source}"}

        try:
            shutil.move(str(source), str(destination))
            return {"success": True, "source": str(source), "destination": str(destination)}
        except PermissionError:
            return {"error": "Permission denied"}
        except Exception as e:
            return {"error": f"Error moving file: {str(e)}"}


class ListUploadsTool(Tool):
    """Tool for listing uploaded files in the current session."""

    def __init__(self):
        super().__init__(
            name="list_uploads",
            description="List files the user has uploaded in this session that you can read with read_file",
            schema={
                "type": "object",
                "properties": {
                    "session_id": {
                        "type": "string",
                        "description": "The current session ID",
                    }
                },
                "required": ["session_id"],
            },
            required_permissions=["read_file"],
        )

    async def execute(self, args: Dict[str, Any]) -> Dict[str, Any]:
        session_id = args.get("session_id", "")
        if not session_id:
            return {"uploads": [], "error": "session_id is required"}

        try:
            from backend.storage.database import get_database
            db = get_database()
            rows = await db.get_session_uploads(session_id)
            uploads = [
                {
                    "filename": r["original_filename"],
                    "path": r["stored_path"],
                    "size": r["file_size"],
                }
                for r in rows
            ]
            return {"uploads": uploads, "count": len(uploads)}
        except Exception as e:
            return {"uploads": [], "error": f"Error listing uploads: {str(e)}"}
