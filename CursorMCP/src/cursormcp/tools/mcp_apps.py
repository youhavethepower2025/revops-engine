"""MCP App Connection Tools - Connect to application MCP servers"""

from typing import Dict, Any, Optional
import httpx
import logging
from .base import BaseTool

logger = logging.getLogger(__name__)

# Global app connections registry
_app_connections: Dict[str, Dict[str, Any]] = {}


class ConnectAppMCPTool(BaseTool):
    """Connect to an application's MCP server"""
    
    name = "mcp_connect_app"
    description = "Connect to a Cloudflare application's MCP server and discover its tools"
    
    input_schema = {
        "type": "object",
        "properties": {
            "app_name": {
                "type": "string",
                "description": "Name identifier for this app (e.g., 'revops', 'content')"
            },
            "worker_url": {
                "type": "string",
                "description": "Worker URL (e.g., 'revops-engine-dev.aijesusbro-brain.workers.dev')"
            },
            "mcp_endpoint": {
                "type": "string",
                "description": "MCP endpoint path (default: '/mcp')",
                "default": "/mcp"
            }
        },
        "required": ["app_name", "worker_url"]
    }
    
    async def execute(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Connect to app MCP server"""
        global _app_connections
        
        app_name = args["app_name"]
        worker_url = args["worker_url"]
        mcp_endpoint = args.get("mcp_endpoint", "/mcp")
        
        # Construct full URL
        if not worker_url.startswith("http"):
            worker_url = f"https://{worker_url}"
        
        mcp_url = f"{worker_url}{mcp_endpoint}"
        
        try:
            # Test connection and discover tools
            async with httpx.AsyncClient(timeout=10.0) as client:
                # Initialize
                init_response = await client.post(
                    mcp_url,
                    json={
                        "jsonrpc": "2.0",
                        "id": 1,
                        "method": "initialize",
                        "params": {}
                    }
                )
                init_response.raise_for_status()
                
                # List tools
                tools_response = await client.post(
                    mcp_url,
                    json={
                        "jsonrpc": "2.0",
                        "id": 2,
                        "method": "tools/list",
                        "params": {}
                    }
                )
                tools_response.raise_for_status()
                
                tools_data = tools_response.json()
                tools = tools_data.get("result", {}).get("tools", [])
                
                # Store connection
                _app_connections[app_name] = {
                    "url": mcp_url,
                    "worker_url": worker_url,
                    "tools": tools,
                    "connected_at": __import__("time").time()
                }
                
                return {
                    "success": True,
                    "app_name": app_name,
                    "url": mcp_url,
                    "tools_count": len(tools),
                    "tools": [t.get("name") for t in tools]
                }
        
        except httpx.HTTPStatusError as e:
            error_msg = f"HTTP {e.response.status_code}: Failed to connect to {mcp_url}"
            logger.error(error_msg)
            return {"error": error_msg, "success": False}
        except Exception as e:
            error_msg = f"Connection error: {str(e)}"
            logger.exception(error_msg)
            return {"error": error_msg, "success": False}


class ListConnectedAppsTool(BaseTool):
    """List all connected application MCP servers"""
    
    name = "mcp_list_connected_apps"
    description = "List all currently connected application MCP servers"
    
    input_schema = {
        "type": "object",
        "properties": {},
        "required": []
    }
    
    async def execute(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """List connected apps"""
        global _app_connections
        
        apps = []
        for app_name, conn in _app_connections.items():
            apps.append({
                "app_name": app_name,
                "url": conn["url"],
                "tools_count": len(conn.get("tools", [])),
                "connected_at": conn.get("connected_at")
            })
        
        return {
            "apps": apps,
            "count": len(apps)
        }


class CallAppToolTool(BaseTool):
    """Call a tool on a connected application MCP server"""
    
    name = "mcp_call_app_tool"
    description = "Call a tool on a connected application MCP server"
    
    input_schema = {
        "type": "object",
        "properties": {
            "app_name": {
                "type": "string",
                "description": "Name of the connected app"
            },
            "tool_name": {
                "type": "string",
                "description": "Name of the tool to call"
            },
            "arguments": {
                "type": "object",
                "description": "Tool arguments",
                "default": {}
            }
        },
        "required": ["app_name", "tool_name"]
    }
    
    async def execute(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Call app tool"""
        global _app_connections
        
        app_name = args["app_name"]
        tool_name = args["tool_name"]
        tool_args = args.get("arguments", {})
        
        # Get connection
        connection = _app_connections.get(app_name)
        if not connection:
            return {
                "error": f"App '{app_name}' not connected. Use mcp_connect_app first.",
                "available_apps": list(_app_connections.keys())
            }
        
        mcp_url = connection["url"]
        
        try:
            # Forward tool call to app MCP server
            async with httpx.AsyncClient(timeout=120.0) as client:
                response = await client.post(
                    mcp_url,
                    json={
                        "jsonrpc": "2.0",
                        "id": 1,
                        "method": "tools/call",
                        "params": {
                            "name": tool_name,
                            "arguments": tool_args
                        }
                    }
                )
                response.raise_for_status()
                result = response.json()
                
                # Extract content from MCP response
                if "result" in result:
                    content = result["result"].get("content", [])
                    if content and len(content) > 0:
                        # Parse text content
                        text_content = content[0].get("text", "")
                        try:
                            import json
                            parsed = json.loads(text_content)
                            return parsed
                        except:
                            return {"text": text_content}
                
                return result
        
        except httpx.HTTPStatusError as e:
            error_msg = f"HTTP {e.response.status_code}: {e.response.text}"
            logger.error(f"Error calling {app_name}.{tool_name}: {error_msg}")
            return {"error": error_msg}
        except Exception as e:
            error_msg = f"Error calling app tool: {str(e)}"
            logger.exception(error_msg)
            return {"error": error_msg}


class DiscoverAppToolsTool(BaseTool):
    """Auto-discover tools from an application MCP server"""
    
    name = "mcp_discover_app_tools"
    description = "Discover and list all tools available from an application MCP server"
    
    input_schema = {
        "type": "object",
        "properties": {
            "app_name": {
                "type": "string",
                "description": "Name of the connected app"
            }
        },
        "required": ["app_name"]
    }
    
    async def execute(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Discover app tools"""
        global _app_connections
        
        app_name = args["app_name"]
        connection = _app_connections.get(app_name)
        
        if not connection:
            return {
                "error": f"App '{app_name}' not connected",
                "available_apps": list(_app_connections.keys())
            }
        
        tools = connection.get("tools", [])
        
        return {
            "app_name": app_name,
            "tools": tools,
            "count": len(tools),
            "tool_names": [t.get("name") for t in tools]
        }


