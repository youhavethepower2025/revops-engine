"""Tool router for executing MCP tool calls"""

import json
import logging
from typing import Dict, Any, Optional
from .types import ToolCallRequest, ToolCallResponse, TextContent
from ..tools.registry import get_registry

logger = logging.getLogger(__name__)


class ToolRouter:
    """Routes and executes tool calls"""
    
    def __init__(self):
        self.registry = get_registry()
    
    async def execute_tool(self, request: ToolCallRequest) -> ToolCallResponse:
        """
        Execute a tool call
        
        Args:
            request: Tool call request
            
        Returns:
            Tool call response with content
        """
        tool_name = request.name
        args = request.arguments
        
        # Get tool from registry
        tool = self.registry.get(tool_name)
        if not tool:
            error_msg = f"Tool '{tool_name}' not found. Available tools: {[t.name for t in self.registry.list_all()]}"
            logger.error(error_msg)
            return ToolCallResponse(
                content=[TextContent(text=json.dumps({"error": error_msg}, indent=2))],
                isError=True
            )
        
        try:
            # Validate arguments
            validated_args = tool.validate_args(args)
            
            # Execute tool
            logger.info(f"Executing tool: {tool_name} with args: {validated_args}")
            result = await tool.execute(validated_args)
            
            # Format response
            result_text = json.dumps(result, indent=2)
            return ToolCallResponse(
                content=[TextContent(text=result_text)],
                isError=False
            )
        
        except ValueError as e:
            error_msg = f"Invalid arguments for tool '{tool_name}': {str(e)}"
            logger.error(error_msg)
            return ToolCallResponse(
                content=[TextContent(text=json.dumps({"error": error_msg}, indent=2))],
                isError=True
            )
        
        except Exception as e:
            error_msg = f"Error executing tool '{tool_name}': {str(e)}"
            logger.exception(error_msg)
            return ToolCallResponse(
                content=[TextContent(text=json.dumps({"error": error_msg}, indent=2))],
                isError=True
            )

