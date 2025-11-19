"""Cloudflare Workflows tools"""

from typing import Dict, Any, List, Optional
import logging
from ..base import BaseTool
from ...services.cloudflare import CloudflareService, CloudflareAPIError

logger = logging.getLogger(__name__)


class ListWorkflowsTool(BaseTool):
    """List all Cloudflare Workflows"""
    
    name = "cloudflare_list_workflows"
    description = "List all Cloudflare Workflows in your account"
    
    input_schema = {
        "type": "object",
        "properties": {},
        "required": []
    }
    
    async def execute(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """List workflows"""
        service = CloudflareService()
        try:
            workflows = await service.list_workflows()
            return {
                "workflows": workflows,
                "count": len(workflows)
            }
        except CloudflareAPIError as e:
            return {"error": str(e)}


class GetWorkflowTool(BaseTool):
    """Get details of a specific Workflow"""
    
    name = "cloudflare_get_workflow"
    description = "Get detailed information about a Cloudflare Workflow"
    
    input_schema = {
        "type": "object",
        "properties": {
            "workflow_id": {
                "type": "string",
                "description": "Workflow ID"
            }
        },
        "required": ["workflow_id"]
    }
    
    async def execute(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Get workflow details"""
        service = CloudflareService()
        workflow_id = args["workflow_id"]
        
        try:
            workflow = await service.get_workflow(workflow_id)
            return workflow
        except CloudflareAPIError as e:
            return {"error": str(e)}


class CreateWorkflowTool(BaseTool):
    """Create a new Cloudflare Workflow"""
    
    name = "cloudflare_create_workflow"
    description = "Create a new Cloudflare Workflow"
    
    input_schema = {
        "type": "object",
        "properties": {
            "name": {
                "type": "string",
                "description": "Workflow name"
            },
            "definition": {
                "type": "object",
                "description": "Workflow definition (steps, triggers, etc.)"
            }
        },
        "required": ["name", "definition"]
    }
    
    async def execute(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Create workflow"""
        service = CloudflareService()
        name = args["name"]
        definition = args["definition"]
        
        try:
            result = await service.create_workflow(name, definition)
            return {
                "success": True,
                "workflow": result
            }
        except CloudflareAPIError as e:
            return {"error": str(e), "success": False}


class TriggerWorkflowTool(BaseTool):
    """Trigger a Cloudflare Workflow"""
    
    name = "cloudflare_trigger_workflow"
    description = "Trigger execution of a Cloudflare Workflow"
    
    input_schema = {
        "type": "object",
        "properties": {
            "workflow_id": {
                "type": "string",
                "description": "Workflow ID to trigger"
            },
            "input": {
                "type": "object",
                "description": "Input data for the workflow",
                "default": {}
            }
        },
        "required": ["workflow_id"]
    }
    
    async def execute(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Trigger workflow"""
        service = CloudflareService()
        workflow_id = args["workflow_id"]
        input_data = args.get("input", {})
        
        try:
            result = await service.trigger_workflow(workflow_id, input_data)
            return {
                "success": True,
                "execution_id": result.get("id"),
                "result": result
            }
        except CloudflareAPIError as e:
            return {"error": str(e), "success": False}


class GetWorkflowExecutionTool(BaseTool):
    """Get status of a Workflow execution"""
    
    name = "cloudflare_get_workflow_execution"
    description = "Get status and results of a Workflow execution"
    
    input_schema = {
        "type": "object",
        "properties": {
            "workflow_id": {
                "type": "string",
                "description": "Workflow ID"
            },
            "execution_id": {
                "type": "string",
                "description": "Execution ID"
            }
        },
        "required": ["workflow_id", "execution_id"]
    }
    
    async def execute(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Get workflow execution"""
        service = CloudflareService()
        workflow_id = args["workflow_id"]
        execution_id = args["execution_id"]
        
        try:
            execution = await service.get_workflow_execution(workflow_id, execution_id)
            return execution
        except CloudflareAPIError as e:
            return {"error": str(e)}

