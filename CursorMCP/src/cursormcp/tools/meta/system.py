"""Meta tools for system introspection"""

import json
import logging
from typing import Dict, Any
from ..base import BaseTool
from ..registry import get_registry
from ...config import get_settings

logger = logging.getLogger(__name__)


class ListToolsTool(BaseTool):
    """List all available tools"""
    
    name = "list_tools"
    description = "List all available MCP tools with their descriptions and schemas"
    
    input_schema = {
        "type": "object",
        "properties": {
            "category": {
                "type": "string",
                "description": "Optional category filter (e.g., 'cloudflare', 'development')"
            }
        },
        "required": []
    }
    
    async def execute(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """List all tools"""
        registry = get_registry()
        tools = registry.list_mcp_tools()
        
        category = args.get("category")
        if category:
            # Filter by category if provided (tools can have category in description)
            tools = [
                t for t in tools
                if category.lower() in t.get("description", "").lower()
            ]
        
        return {
            "tools": tools,
            "count": len(tools)
        }


class GetToolInfoTool(BaseTool):
    """Get detailed information about a specific tool"""
    
    name = "get_tool_info"
    description = "Get detailed information and documentation for a specific tool"
    
    input_schema = {
        "type": "object",
        "properties": {
            "tool_name": {
                "type": "string",
                "description": "Name of the tool to get information about"
            }
        },
        "required": ["tool_name"]
    }
    
    async def execute(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Get tool information"""
        registry = get_registry()
        tool_name = args["tool_name"]
        
        tool = registry.get(tool_name)
        if not tool:
            return {
                "error": f"Tool '{tool_name}' not found",
                "available_tools": [t.name for t in registry.list_all()]
            }
        
        return {
            "name": tool.name,
            "description": tool.description,
            "input_schema": tool.input_schema,
            "class": tool.__class__.__name__
        }


class GetServerStatusTool(BaseTool):
    """Get server status and health information"""
    
    name = "get_server_status"
    description = "Get CursorMCP server status, version, and health information"
    
    input_schema = {
        "type": "object",
        "properties": {},
        "required": []
    }
    
    async def execute(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Get server status"""
        settings = get_settings()
        registry = get_registry()
        
        return {
            "status": "healthy",
            "server_name": settings.mcp_server_name,
            "version": settings.mcp_server_version,
            "tools_registered": registry.count(),
            "workspace_root": str(settings.workspace_root),
            "log_level": settings.log_level
        }

