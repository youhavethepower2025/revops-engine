"""File system tools for development"""

import os
from pathlib import Path
from typing import Dict, Any, List
import logging
from ..base import BaseTool
from ...config import get_settings

logger = logging.getLogger(__name__)


def _validate_path(path: str) -> Path:
    """Validate and resolve path within workspace"""
    settings = get_settings()
    workspace = settings.workspace_root
    
    # Resolve path
    if os.path.isabs(path):
        resolved = Path(path).resolve()
    else:
        resolved = (workspace / path).resolve()
    
    # Ensure path is within workspace
    try:
        resolved.relative_to(workspace.resolve())
    except ValueError:
        raise ValueError(f"Path '{path}' is outside workspace root: {workspace}")
    
    return resolved


class ReadFileTool(BaseTool):
    """Read contents of a file"""
    
    name = "read_file"
    description = "Read the contents of a file. Paths are relative to workspace root or absolute."
    
    input_schema = {
        "type": "object",
        "properties": {
            "path": {
                "type": "string",
                "description": "Path to file (relative to workspace or absolute)"
            }
        },
        "required": ["path"]
    }
    
    async def execute(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Read file"""
        path = _validate_path(args["path"])
        
        if not path.exists():
            raise FileNotFoundError(f"File not found: {path}")
        
        if not path.is_file():
            raise ValueError(f"Path is not a file: {path}")
        
        try:
            content = path.read_text(encoding="utf-8")
            return {
                "content": content,
                "path": str(path),
                "size": len(content),
                "lines": len(content.splitlines())
            }
        except UnicodeDecodeError:
            return {
                "error": f"File '{path}' is not a text file (binary or invalid encoding)",
                "path": str(path)
            }


class WriteFileTool(BaseTool):
    """Write contents to a file"""
    
    name = "write_file"
    description = "Write contents to a file. Creates file if it doesn't exist, overwrites if it does."
    
    input_schema = {
        "type": "object",
        "properties": {
            "path": {
                "type": "string",
                "description": "Path to file (relative to workspace or absolute)"
            },
            "content": {
                "type": "string",
                "description": "Content to write to file"
            },
            "append": {
                "type": "boolean",
                "description": "Append to file instead of overwriting (default: false)",
                "default": False
            }
        },
        "required": ["path", "content"]
    }
    
    async def execute(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Write file"""
        path = _validate_path(args["path"])
        content = args["content"]
        append = args.get("append", False)
        
        # Create parent directories if needed
        path.parent.mkdir(parents=True, exist_ok=True)
        
        # Write file
        mode = "a" if append else "w"
        with path.open(mode, encoding="utf-8") as f:
            f.write(content)
        
        return {
            "path": str(path),
            "written": len(content),
            "mode": "append" if append else "overwrite"
        }


class ListDirectoryTool(BaseTool):
    """List contents of a directory"""
    
    name = "list_directory"
    description = "List files and directories in a given path"
    
    input_schema = {
        "type": "object",
        "properties": {
            "path": {
                "type": "string",
                "description": "Path to directory (default: workspace root)",
                "default": "."
            },
            "recursive": {
                "type": "boolean",
                "description": "List recursively (default: false)",
                "default": False
            }
        },
        "required": []
    }
    
    async def execute(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """List directory"""
        path_str = args.get("path", ".")
        path = _validate_path(path_str)
        recursive = args.get("recursive", False)
        
        if not path.exists():
            raise FileNotFoundError(f"Directory not found: {path}")
        
        if not path.is_dir():
            raise ValueError(f"Path is not a directory: {path}")
        
        items = []
        if recursive:
            for item in path.rglob("*"):
                if item.is_file():
                    items.append({
                        "name": item.name,
                        "path": str(item.relative_to(path)),
                        "type": "file",
                        "size": item.stat().st_size
                    })
                elif item.is_dir():
                    items.append({
                        "name": item.name,
                        "path": str(item.relative_to(path)),
                        "type": "directory"
                    })
        else:
            for item in sorted(path.iterdir()):
                if item.is_file():
                    items.append({
                        "name": item.name,
                        "type": "file",
                        "size": item.stat().st_size
                    })
                elif item.is_dir():
                    items.append({
                        "name": item.name,
                        "type": "directory"
                    })
        
        return {
            "path": str(path),
            "items": items,
            "count": len(items)
        }


class SearchFilesTool(BaseTool):
    """Search for files by name pattern"""
    
    name = "search_files"
    description = "Search for files matching a pattern in the workspace"
    
    input_schema = {
        "type": "object",
        "properties": {
            "pattern": {
                "type": "string",
                "description": "File name pattern to search for (supports * wildcard)"
            },
            "directory": {
                "type": "string",
                "description": "Directory to search in (default: workspace root)",
                "default": "."
            },
            "max_results": {
                "type": "integer",
                "description": "Maximum number of results (default: 50)",
                "default": 50
            }
        },
        "required": ["pattern"]
    }
    
    async def execute(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Search files"""
        pattern = args["pattern"]
        directory = args.get("directory", ".")
        max_results = args.get("max_results", 50)
        
        dir_path = _validate_path(directory)
        
        if not dir_path.is_dir():
            raise ValueError(f"Path is not a directory: {dir_path}")
        
        # Convert pattern to glob pattern
        if "*" not in pattern:
            pattern = f"*{pattern}*"
        
        matches = []
        for path in dir_path.rglob(pattern):
            if path.is_file():
                matches.append({
                    "name": path.name,
                    "path": str(path.relative_to(dir_path)),
                    "full_path": str(path),
                    "size": path.stat().st_size
                })
                if len(matches) >= max_results:
                    break
        
        return {
            "pattern": pattern,
            "matches": matches,
            "count": len(matches),
            "truncated": len(matches) >= max_results
        }

