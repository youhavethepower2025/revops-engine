"""Base tool class for all CursorMCP tools"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List
from pydantic import BaseModel, Field


class ToolInputSchema(BaseModel):
    """Tool input schema definition"""
    type: str = "object"
    properties: Dict[str, Any] = Field(default_factory=dict)
    required: List[str] = Field(default_factory=list)


class BaseTool(ABC):
    """Base class for all MCP tools"""
    
    name: str
    description: str
    input_schema: Dict[str, Any]
    
    def __init__(self):
        """Initialize tool"""
        if not hasattr(self, 'name') or not self.name:
            raise ValueError(f"Tool {self.__class__.__name__} must define 'name'")
        if not hasattr(self, 'description') or not self.description:
            raise ValueError(f"Tool {self.__class__.__name__} must define 'description'")
        if not hasattr(self, 'input_schema') or not self.input_schema:
            raise ValueError(f"Tool {self.__class__.__name__} must define 'input_schema'")
    
    @abstractmethod
    async def execute(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the tool with given arguments
        
        Args:
            args: Tool arguments (validated against input_schema)
            
        Returns:
            Dictionary with tool results
            
        Raises:
            ValueError: If arguments are invalid
            Exception: For tool-specific errors
        """
        pass
    
    def to_mcp_tool(self) -> Dict[str, Any]:
        """Convert tool to MCP tool definition"""
        return {
            "name": self.name,
            "description": self.description,
            "inputSchema": self.input_schema
        }
    
    def validate_args(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate arguments against input schema
        
        Args:
            args: Arguments to validate
            
        Returns:
            Validated arguments
            
        Raises:
            ValueError: If validation fails
        """
        schema = self.input_schema
        required = schema.get("required", [])
        properties = schema.get("properties", {})
        
        # Check required fields
        for field in required:
            if field not in args:
                raise ValueError(f"Missing required argument: {field}")
        
        # Validate types (basic validation)
        validated = {}
        for key, value in args.items():
            if key in properties:
                prop = properties[key]
                expected_type = prop.get("type")
                
                # Basic type checking
                if expected_type == "string" and not isinstance(value, str):
                    raise ValueError(f"Argument '{key}' must be a string")
                elif expected_type == "integer" and not isinstance(value, int):
                    raise ValueError(f"Argument '{key}' must be an integer")
                elif expected_type == "boolean" and not isinstance(value, bool):
                    raise ValueError(f"Argument '{key}' must be a boolean")
                elif expected_type == "array" and not isinstance(value, list):
                    raise ValueError(f"Argument '{key}' must be an array")
                elif expected_type == "object" and not isinstance(value, dict):
                    raise ValueError(f"Argument '{key}' must be an object")
            
            validated[key] = value
        
        return validated

