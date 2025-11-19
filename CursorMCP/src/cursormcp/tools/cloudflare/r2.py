"""Cloudflare R2 Storage tools"""

from typing import Dict, Any
import logging
from ..base import BaseTool
from ...services.cloudflare import CloudflareService, CloudflareAPIError

logger = logging.getLogger(__name__)


class ListR2BucketsTool(BaseTool):
    """List all R2 buckets"""
    
    name = "cloudflare_list_r2_buckets"
    description = "List all R2 buckets in your Cloudflare account"
    
    input_schema = {
        "type": "object",
        "properties": {},
        "required": []
    }
    
    async def execute(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """List R2 buckets"""
        service = CloudflareService()
        try:
            buckets = await service.list_r2_buckets()
            return {
                "buckets": buckets,
                "count": len(buckets)
            }
        except CloudflareAPIError as e:
            return {"error": str(e)}


class CreateR2BucketTool(BaseTool):
    """Create a new R2 bucket"""
    
    name = "cloudflare_create_r2_bucket"
    description = "Create a new R2 bucket"
    
    input_schema = {
        "type": "object",
        "properties": {
            "name": {
                "type": "string",
                "description": "Name for the R2 bucket"
            },
            "location": {
                "type": "string",
                "description": "Optional location hint for bucket placement"
            }
        },
        "required": ["name"]
    }
    
    async def execute(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Create R2 bucket"""
        service = CloudflareService()
        name = args["name"]
        location = args.get("location")
        
        try:
            result = await service.create_r2_bucket(name, location)
            return {
                "success": True,
                "bucket": result
            }
        except CloudflareAPIError as e:
            return {"error": str(e), "success": False}


class UploadR2ObjectTool(BaseTool):
    """Upload object to R2 bucket"""
    
    name = "cloudflare_upload_r2_object"
    description = "Upload an object to an R2 bucket"
    
    input_schema = {
        "type": "object",
        "properties": {
            "bucket_name": {
                "type": "string",
                "description": "R2 bucket name"
            },
            "object_key": {
                "type": "string",
                "description": "Object key (path) in bucket"
            },
            "content": {
                "type": "string",
                "description": "Content to upload (text or base64)"
            },
            "content_type": {
                "type": "string",
                "description": "Content type (e.g., text/plain, application/json)",
                "default": "text/plain"
            }
        },
        "required": ["bucket_name", "object_key", "content"]
    }
    
    async def execute(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Upload R2 object"""
        service = CloudflareService()
        bucket_name = args["bucket_name"]
        object_key = args["object_key"]
        content = args["content"]
        content_type = args.get("content_type", "text/plain")
        
        try:
            result = await service.upload_r2_object(
                bucket_name=bucket_name,
                object_key=object_key,
                content=content,
                content_type=content_type
            )
            return {
                "success": True,
                "bucket": bucket_name,
                "key": object_key,
                "result": result
            }
        except CloudflareAPIError as e:
            return {"error": str(e), "success": False}


class GetR2ObjectTool(BaseTool):
    """Get object from R2 bucket"""
    
    name = "cloudflare_get_r2_object"
    description = "Get an object from an R2 bucket"
    
    input_schema = {
        "type": "object",
        "properties": {
            "bucket_name": {
                "type": "string",
                "description": "R2 bucket name"
            },
            "object_key": {
                "type": "string",
                "description": "Object key (path) in bucket"
            }
        },
        "required": ["bucket_name", "object_key"]
    }
    
    async def execute(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Get R2 object"""
        service = CloudflareService()
        bucket_name = args["bucket_name"]
        object_key = args["object_key"]
        
        try:
            result = await service.get_r2_object(bucket_name, object_key)
            return {
                "bucket": bucket_name,
                "key": object_key,
                "content": result.get("content"),
                "content_type": result.get("content_type"),
                "size": result.get("size")
            }
        except CloudflareAPIError as e:
            return {"error": str(e)}


class DeleteR2ObjectTool(BaseTool):
    """Delete object from R2 bucket"""
    
    name = "cloudflare_delete_r2_object"
    description = "Delete an object from an R2 bucket"
    
    input_schema = {
        "type": "object",
        "properties": {
            "bucket_name": {
                "type": "string",
                "description": "R2 bucket name"
            },
            "object_key": {
                "type": "string",
                "description": "Object key (path) in bucket"
            }
        },
        "required": ["bucket_name", "object_key"]
    }
    
    async def execute(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Delete R2 object"""
        service = CloudflareService()
        bucket_name = args["bucket_name"]
        object_key = args["object_key"]
        
        try:
            result = await service.delete_r2_object(bucket_name, object_key)
            return {
                "success": True,
                "bucket": bucket_name,
                "key": object_key,
                "result": result
            }
        except CloudflareAPIError as e:
            return {"error": str(e), "success": False}


