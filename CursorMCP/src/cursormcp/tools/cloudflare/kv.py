"""Cloudflare KV Storage tools"""

from typing import Dict, Any
import logging
from ..base import BaseTool
from ...services.cloudflare import CloudflareService, CloudflareAPIError

logger = logging.getLogger(__name__)


class ListKVNamespacesTool(BaseTool):
    """List all KV namespaces"""
    
    name = "cloudflare_list_kv_namespaces"
    description = "List all KV namespaces in your Cloudflare account"
    
    input_schema = {
        "type": "object",
        "properties": {},
        "required": []
    }
    
    async def execute(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """List KV namespaces"""
        service = CloudflareService()
        try:
            namespaces = await service.list_kv_namespaces()
            return {
                "namespaces": namespaces,
                "count": len(namespaces)
            }
        except CloudflareAPIError as e:
            return {"error": str(e)}


class CreateKVNamespaceTool(BaseTool):
    """Create a new KV namespace"""
    
    name = "cloudflare_create_kv_namespace"
    description = "Create a new KV namespace"
    
    input_schema = {
        "type": "object",
        "properties": {
            "title": {
                "type": "string",
                "description": "Title for the KV namespace"
            }
        },
        "required": ["title"]
    }
    
    async def execute(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Create KV namespace"""
        service = CloudflareService()
        title = args["title"]
        
        try:
            result = await service.create_kv_namespace(title)
            return {
                "success": True,
                "namespace": result
            }
        except CloudflareAPIError as e:
            return {"error": str(e), "success": False}


class GetKVValueTool(BaseTool):
    """Get value from KV storage"""
    
    name = "cloudflare_get_kv_value"
    description = "Get a value from KV storage by key"
    
    input_schema = {
        "type": "object",
        "properties": {
            "namespace_id": {
                "type": "string",
                "description": "KV namespace ID"
            },
            "key": {
                "type": "string",
                "description": "Key to retrieve"
            }
        },
        "required": ["namespace_id", "key"]
    }
    
    async def execute(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Get KV value"""
        service = CloudflareService()
        namespace_id = args["namespace_id"]
        key = args["key"]
        
        try:
            value = await service.get_kv_value(namespace_id, key)
            if value is None:
                return {
                    "key": key,
                    "value": None,
                    "found": False
                }
            return {
                "key": key,
                "value": value,
                "found": True
            }
        except CloudflareAPIError as e:
            return {"error": str(e)}


class SetKVValueTool(BaseTool):
    """Set value in KV storage"""
    
    name = "cloudflare_set_kv_value"
    description = "Set a value in KV storage"
    
    input_schema = {
        "type": "object",
        "properties": {
            "namespace_id": {
                "type": "string",
                "description": "KV namespace ID"
            },
            "key": {
                "type": "string",
                "description": "Key to set"
            },
            "value": {
                "type": "string",
                "description": "Value to store"
            }
        },
        "required": ["namespace_id", "key", "value"]
    }
    
    async def execute(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Set KV value"""
        service = CloudflareService()
        namespace_id = args["namespace_id"]
        key = args["key"]
        value = args["value"]
        
        try:
            result = await service.put_kv_value(namespace_id, key, value)
            return {
                "success": True,
                "key": key,
                "result": result
            }
        except CloudflareAPIError as e:
            return {"error": str(e), "success": False}


class DeleteKVValueTool(BaseTool):
    """Delete value from KV storage"""
    
    name = "cloudflare_delete_kv_value"
    description = "Delete a value from KV storage"
    
    input_schema = {
        "type": "object",
        "properties": {
            "namespace_id": {
                "type": "string",
                "description": "KV namespace ID"
            },
            "key": {
                "type": "string",
                "description": "Key to delete"
            }
        },
        "required": ["namespace_id", "key"]
    }
    
    async def execute(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Delete KV value"""
        service = CloudflareService()
        namespace_id = args["namespace_id"]
        key = args["key"]
        
        try:
            result = await service.delete_kv_value(namespace_id, key)
            return {
                "success": True,
                "key": key,
                "result": result
            }
        except CloudflareAPIError as e:
            return {"error": str(e), "success": False}

