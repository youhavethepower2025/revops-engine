"""MCP Protocol Type Definitions"""

from typing import Any, Dict, List, Optional, Literal
from pydantic import BaseModel, Field


class TextContent(BaseModel):
    """Text content in MCP response"""
    type: Literal["text"] = "text"
    text: str


class ImageContent(BaseModel):
    """Image content in MCP response"""
    type: Literal["image"] = "image"
    data: str  # Base64 encoded
    mimeType: str


Content = TextContent | ImageContent


class Tool(BaseModel):
    """MCP Tool definition"""
    name: str
    description: str
    inputSchema: Dict[str, Any]


class Resource(BaseModel):
    """MCP Resource definition"""
    uri: str
    name: str
    description: Optional[str] = None
    mimeType: Optional[str] = None


class Prompt(BaseModel):
    """MCP Prompt template"""
    name: str
    description: str
    arguments: Optional[List[Dict[str, Any]]] = None


class MCPRequest(BaseModel):
    """Base MCP request"""
    jsonrpc: Literal["2.0"] = "2.0"
    id: Optional[int | str] = None
    method: str
    params: Optional[Dict[str, Any]] = None


class MCPResponse(BaseModel):
    """Base MCP response"""
    jsonrpc: Literal["2.0"] = "2.0"
    id: Optional[int | str] = None
    result: Optional[Dict[str, Any]] = None
    error: Optional[Dict[str, Any]] = None


class ToolCallRequest(BaseModel):
    """Tool call request"""
    name: str
    arguments: Dict[str, Any]


class ToolCallResponse(BaseModel):
    """Tool call response"""
    content: List[Content]
    isError: Optional[bool] = False


class ListToolsResponse(BaseModel):
    """List tools response"""
    tools: List[Tool]


class ListResourcesResponse(BaseModel):
    """List resources response"""
    resources: List[Resource]

