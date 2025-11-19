"""Cloudflare D1 Database tools"""

from typing import Dict, Any, List, Optional
import logging
from ..base import BaseTool
from ...services.cloudflare import CloudflareService, CloudflareAPIError

logger = logging.getLogger(__name__)


class ListD1DatabasesTool(BaseTool):
    """List all D1 databases"""
    
    name = "cloudflare_list_d1_databases"
    description = "List all D1 databases in your Cloudflare account"
    
    input_schema = {
        "type": "object",
        "properties": {},
        "required": []
    }
    
    async def execute(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """List D1 databases"""
        service = CloudflareService()
        try:
            databases = await service.list_d1_databases()
            return {
                "databases": databases,
                "count": len(databases)
            }
        except CloudflareAPIError as e:
            return {"error": str(e)}


class CreateD1DatabaseTool(BaseTool):
    """Create a new D1 database"""
    
    name = "cloudflare_create_d1_database"
    description = "Create a new D1 database"
    
    input_schema = {
        "type": "object",
        "properties": {
            "name": {
                "type": "string",
                "description": "Name for the D1 database"
            }
        },
        "required": ["name"]
    }
    
    async def execute(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Create D1 database"""
        service = CloudflareService()
        name = args["name"]
        
        try:
            result = await service.create_d1_database(name)
            return {
                "success": True,
                "database": result
            }
        except CloudflareAPIError as e:
            return {"error": str(e), "success": False}


class QueryD1Tool(BaseTool):
    """Execute SQL query on D1 database"""
    
    name = "cloudflare_query_d1"
    description = "Execute a SQL query on a D1 database"
    
    input_schema = {
        "type": "object",
        "properties": {
            "database_id": {
                "type": "string",
                "description": "D1 database ID"
            },
            "query": {
                "type": "string",
                "description": "SQL query to execute"
            },
            "params": {
                "type": "array",
                "description": "Optional query parameters",
                "items": {"type": "string"},
                "default": []
            }
        },
        "required": ["database_id", "query"]
    }
    
    async def execute(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Query D1 database"""
        service = CloudflareService()
        database_id = args["database_id"]
        query = args["query"]
        params = args.get("params", [])
        
        try:
            result = await service.query_d1(
                database_id=database_id,
                query=query,
                params=params if params else None
            )
            return {
                "success": True,
                "result": result
            }
        except CloudflareAPIError as e:
            return {"error": str(e), "success": False}

