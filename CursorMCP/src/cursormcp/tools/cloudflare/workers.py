"""Cloudflare Workers tools"""

from typing import Dict, Any
import logging
from ..base import BaseTool
from ...services.cloudflare import CloudflareService, CloudflareAPIError

logger = logging.getLogger(__name__)


class ListWorkersTool(BaseTool):
    """List all Cloudflare Workers"""
    
    name = "cloudflare_list_workers"
    description = "List all Cloudflare Workers in your account"
    
    input_schema = {
        "type": "object",
        "properties": {},
        "required": []
    }
    
    async def execute(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """List workers"""
        service = CloudflareService()
        try:
            workers = await service.list_workers()
            return {
                "workers": workers,
                "count": len(workers)
            }
        except CloudflareAPIError as e:
            return {"error": str(e)}


class GetWorkerTool(BaseTool):
    """Get details of a specific Worker"""
    
    name = "cloudflare_get_worker"
    description = "Get detailed information about a specific Cloudflare Worker"
    
    input_schema = {
        "type": "object",
        "properties": {
            "script_name": {
                "type": "string",
                "description": "Name of the Worker script"
            }
        },
        "required": ["script_name"]
    }
    
    async def execute(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Get worker details"""
        service = CloudflareService()
        script_name = args["script_name"]
        
        try:
            worker = await service.get_worker(script_name)
            return worker
        except CloudflareAPIError as e:
            return {"error": str(e)}


class DeployWorkerTool(BaseTool):
    """Deploy or update a Cloudflare Worker"""
    
    name = "cloudflare_deploy_worker"
    description = "Deploy or update a Cloudflare Worker script"
    
    input_schema = {
        "type": "object",
        "properties": {
            "script_name": {
                "type": "string",
                "description": "Name for the Worker script"
            },
            "script_content": {
                "type": "string",
                "description": "JavaScript/TypeScript code for the Worker"
            },
            "bindings": {
                "type": "array",
                "description": "Optional bindings (KV, D1, Durable Objects, etc.)",
                "items": {"type": "object"},
                "default": []
            }
        },
        "required": ["script_name", "script_content"]
    }
    
    async def execute(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Deploy worker"""
        service = CloudflareService()
        script_name = args["script_name"]
        script_content = args["script_content"]
        bindings = args.get("bindings", [])
        
        try:
            result = await service.deploy_worker(
                script_name=script_name,
                script_content=script_content,
                bindings=bindings if bindings else None
            )
            return {
                "success": True,
                "script_name": script_name,
                "result": result,
                "url": f"https://{script_name}.aijesusbro-brain.workers.dev"
            }
        except CloudflareAPIError as e:
            return {"error": str(e), "success": False}


class DeleteWorkerTool(BaseTool):
    """Delete a Cloudflare Worker"""
    
    name = "cloudflare_delete_worker"
    description = "Delete a Cloudflare Worker"
    
    input_schema = {
        "type": "object",
        "properties": {
            "script_name": {
                "type": "string",
                "description": "Name of the Worker to delete"
            }
        },
        "required": ["script_name"]
    }
    
    async def execute(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Delete worker"""
        service = CloudflareService()
        script_name = args["script_name"]
        
        try:
            result = await service.delete_worker(script_name)
            return {
                "success": True,
                "script_name": script_name,
                "result": result
            }
        except CloudflareAPIError as e:
            return {"error": str(e), "success": False}


class GetWorkerLogsTool(BaseTool):
    """Get logs for a Cloudflare Worker"""
    
    name = "cloudflare_get_worker_logs"
    description = "Get logs for a Cloudflare Worker (may require Workers Analytics Engine)"
    
    input_schema = {
        "type": "object",
        "properties": {
            "script_name": {
                "type": "string",
                "description": "Name of the Worker"
            },
            "start_time": {
                "type": "string",
                "description": "Start time for logs (ISO 8601 format)"
            },
            "end_time": {
                "type": "string",
                "description": "End time for logs (ISO 8601 format)"
            }
        },
        "required": ["script_name"]
    }
    
    async def execute(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Get worker logs"""
        service = CloudflareService()
        script_name = args["script_name"]
        start_time = args.get("start_time")
        end_time = args.get("end_time")
        
        try:
            logs = await service.get_worker_logs(
                script_name=script_name,
                start_time=start_time,
                end_time=end_time
            )
            return {
                "script_name": script_name,
                "logs": logs,
                "count": len(logs)
            }
        except CloudflareAPIError as e:
            return {"error": str(e)}

