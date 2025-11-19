"""Cloudflare Durable Objects tools"""

from typing import Dict, Any, List
import logging
from ..base import BaseTool
from ...services.cloudflare import CloudflareService, CloudflareAPIError

logger = logging.getLogger(__name__)


class ListDurableObjectNamespacesTool(BaseTool):
    """List all Durable Object namespaces"""
    
    name = "cloudflare_list_durable_object_namespaces"
    description = "List all Durable Object namespaces in your Cloudflare account"
    
    input_schema = {
        "type": "object",
        "properties": {},
        "required": []
    }
    
    async def execute(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """List Durable Object namespaces"""
        service = CloudflareService()
        try:
            namespaces = await service.list_durable_object_namespaces()
            return {
                "namespaces": namespaces,
                "count": len(namespaces)
            }
        except CloudflareAPIError as e:
            return {"error": str(e)}


class GetDurableObjectNamespaceTool(BaseTool):
    """Get details of a Durable Object namespace"""
    
    name = "cloudflare_get_durable_object_namespace"
    description = "Get detailed information about a Durable Object namespace"
    
    input_schema = {
        "type": "object",
        "properties": {
            "namespace_id": {
                "type": "string",
                "description": "Durable Object namespace ID"
            }
        },
        "required": ["namespace_id"]
    }
    
    async def execute(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Get namespace details"""
        service = CloudflareService()
        namespace_id = args["namespace_id"]
        
        try:
            namespace = await service.get_durable_object_namespace(namespace_id)
            return namespace
        except CloudflareAPIError as e:
            return {"error": str(e)}


class ListDurableObjectsTool(BaseTool):
    """List Durable Objects in a namespace"""
    
    name = "cloudflare_list_durable_objects"
    description = "List all Durable Objects in a namespace"
    
    input_schema = {
        "type": "object",
        "properties": {
            "namespace_id": {
                "type": "string",
                "description": "Durable Object namespace ID"
            },
            "limit": {
                "type": "integer",
                "description": "Maximum number of objects to return",
                "default": 100
            }
        },
        "required": ["namespace_id"]
    }
    
    async def execute(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """List Durable Objects"""
        service = CloudflareService()
        namespace_id = args["namespace_id"]
        limit = args.get("limit", 100)
        
        try:
            objects = await service.list_durable_objects(namespace_id, limit=limit)
            return {
                "namespace_id": namespace_id,
                "objects": objects,
                "count": len(objects)
            }
        except CloudflareAPIError as e:
            return {"error": str(e)}


class GetDurableObjectTool(BaseTool):
    """Get details of a specific Durable Object"""
    
    name = "cloudflare_get_durable_object"
    description = "Get detailed information about a specific Durable Object"
    
    input_schema = {
        "type": "object",
        "properties": {
            "namespace_id": {
                "type": "string",
                "description": "Durable Object namespace ID"
            },
            "object_id": {
                "type": "string",
                "description": "Durable Object ID"
            }
        },
        "required": ["namespace_id", "object_id"]
    }
    
    async def execute(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Get Durable Object details"""
        service = CloudflareService()
        namespace_id = args["namespace_id"]
        object_id = args["object_id"]
        
        try:
            obj = await service.get_durable_object(namespace_id, object_id)
            return obj
        except CloudflareAPIError as e:
            return {"error": str(e)}

