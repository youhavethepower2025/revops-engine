"""Tool registry for discovering and managing tools"""

from typing import Dict, List, Optional
import logging
from .base import BaseTool

logger = logging.getLogger(__name__)


class ToolRegistry:
    """Registry for managing MCP tools"""
    
    def __init__(self):
        self._tools: Dict[str, BaseTool] = {}
        self._initialized = False
    
    def register(self, tool: BaseTool) -> None:
        """Register a tool"""
        if tool.name in self._tools:
            logger.warning(f"Tool '{tool.name}' already registered, overwriting")
        
        self._tools[tool.name] = tool
        logger.debug(f"Registered tool: {tool.name}")
    
    def register_all(self, tools: List[BaseTool]) -> None:
        """Register multiple tools"""
        for tool in tools:
            self.register(tool)
    
    def get(self, name: str) -> Optional[BaseTool]:
        """Get a tool by name"""
        return self._tools.get(name)
    
    def list_all(self) -> List[BaseTool]:
        """List all registered tools"""
        return list(self._tools.values())
    
    def list_mcp_tools(self) -> List[Dict]:
        """List all tools in MCP format"""
        return [tool.to_mcp_tool() for tool in self._tools.values()]
    
    def has_tool(self, name: str) -> bool:
        """Check if a tool is registered"""
        return name in self._tools
    
    def count(self) -> int:
        """Get number of registered tools"""
        return len(self._tools)


# Global registry instance
_registry: Optional[ToolRegistry] = None


def get_registry() -> ToolRegistry:
    """Get or create global tool registry"""
    global _registry
    if _registry is None:
        _registry = ToolRegistry()
    return _registry

