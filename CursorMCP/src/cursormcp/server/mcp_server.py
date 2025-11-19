"""Main MCP server implementation"""

import json
import sys
import asyncio
import logging
from typing import Dict, Any, Optional
from .types import (
    MCPRequest,
    MCPResponse,
    ToolCallRequest,
    ListToolsResponse,
    Tool,
)
from .router import ToolRouter
from ..tools.registry import get_registry
from ..services.logger import setup_logging
from ..config import get_settings

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)


class MCPServer:
    """Main MCP server handling JSON-RPC protocol"""
    
    def __init__(self):
        self.router = ToolRouter()
        self.registry = get_registry()
        self.settings = get_settings()
        self._initialize_tools()
    
    def _initialize_tools(self):
        """Initialize and register all tools"""
        from ..tools.meta import ListToolsTool, GetToolInfoTool, GetServerStatusTool
        from ..tools.development import (
            ReadFileTool,
            WriteFileTool,
            ListDirectoryTool,
            SearchFilesTool,
        )
        from ..tools.cloudflare import (
            ListWorkersTool,
            GetWorkerTool,
            DeployWorkerTool,
            DeleteWorkerTool,
            GetWorkerLogsTool,
            ListD1DatabasesTool,
            CreateD1DatabaseTool,
            QueryD1Tool,
            ListKVNamespacesTool,
            CreateKVNamespaceTool,
            GetKVValueTool,
            SetKVValueTool,
            DeleteKVValueTool,
            ListDurableObjectNamespacesTool,
            GetDurableObjectNamespaceTool,
            ListDurableObjectsTool,
            GetDurableObjectTool,
            ListWorkflowsTool,
            GetWorkflowTool,
            CreateWorkflowTool,
            TriggerWorkflowTool,
            GetWorkflowExecutionTool,
            ListR2BucketsTool,
            CreateR2BucketTool,
            UploadR2ObjectTool,
            GetR2ObjectTool,
            DeleteR2ObjectTool,
            ListVectorizeIndexesTool,
            CreateVectorizeIndexTool,
            UpsertVectorsTool,
            QueryVectorsTool,
        )
        from ..tools.mcp_apps import (
            ConnectAppMCPTool,
            ListConnectedAppsTool,
            CallAppToolTool,
            DiscoverAppToolsTool,
        )
        from ..tools.system_scaffold import (
            CreateD1SchemaTool,
            DeployWorkerClusterTool,
            CreateWorkflowTool as SystemCreateWorkflowTool,
            GenerateMCPServerTool,
        )
        
        # Register meta tools
        self.registry.register(ListToolsTool())
        self.registry.register(GetToolInfoTool())
        self.registry.register(GetServerStatusTool())
        
        # Register development tools
        self.registry.register(ReadFileTool())
        self.registry.register(WriteFileTool())
        self.registry.register(ListDirectoryTool())
        self.registry.register(SearchFilesTool())
        
        # Register Cloudflare tools
        self.registry.register(ListWorkersTool())
        self.registry.register(GetWorkerTool())
        self.registry.register(DeployWorkerTool())
        self.registry.register(DeleteWorkerTool())
        self.registry.register(GetWorkerLogsTool())
        self.registry.register(ListD1DatabasesTool())
        self.registry.register(CreateD1DatabaseTool())
        self.registry.register(QueryD1Tool())
        self.registry.register(ListKVNamespacesTool())
        self.registry.register(CreateKVNamespaceTool())
        self.registry.register(GetKVValueTool())
        self.registry.register(SetKVValueTool())
        self.registry.register(DeleteKVValueTool())
        self.registry.register(ListDurableObjectNamespacesTool())
        self.registry.register(GetDurableObjectNamespaceTool())
        self.registry.register(ListDurableObjectsTool())
        self.registry.register(GetDurableObjectTool())
        self.registry.register(ListWorkflowsTool())
        self.registry.register(GetWorkflowTool())
        self.registry.register(CreateWorkflowTool())
        self.registry.register(TriggerWorkflowTool())
        self.registry.register(GetWorkflowExecutionTool())
        self.registry.register(ListR2BucketsTool())
        self.registry.register(CreateR2BucketTool())
        self.registry.register(UploadR2ObjectTool())
        self.registry.register(GetR2ObjectTool())
        self.registry.register(DeleteR2ObjectTool())
        self.registry.register(ListVectorizeIndexesTool())
        self.registry.register(CreateVectorizeIndexTool())
        self.registry.register(UpsertVectorsTool())
        self.registry.register(QueryVectorsTool())
        self.registry.register(ConnectAppMCPTool())
        self.registry.register(ListConnectedAppsTool())
        self.registry.register(CallAppToolTool())
        self.registry.register(DiscoverAppToolsTool())
        self.registry.register(CreateD1SchemaTool())
        self.registry.register(DeployWorkerClusterTool())
        self.registry.register(SystemCreateWorkflowTool())
        self.registry.register(GenerateMCPServerTool())
        
        logger.info(f"Initialized {self.registry.count()} tools")
    
    async def handle_request(self, request: MCPRequest) -> MCPResponse:
        """Handle an MCP request"""
        method = request.method
        params = request.params or {}
        
        try:
            # Route to appropriate handler
            if method == "initialize":
                result = await self._handle_initialize(params)
            elif method == "tools/list":
                result = await self._handle_list_tools()
            elif method == "tools/call":
                result = await self._handle_tool_call(params)
            elif method == "ping":
                result = {"pong": True}
            else:
                raise ValueError(f"Unknown method: {method}")
            
            return MCPResponse(
                jsonrpc="2.0",
                id=request.id,
                result=result
            )
        
        except Exception as e:
            logger.exception(f"Error handling request: {method}")
            return MCPResponse(
                jsonrpc="2.0",
                id=request.id,
                error={
                    "code": -32603,
                    "message": f"Internal error: {str(e)}"
                }
            )
    
    async def _handle_initialize(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle initialize request"""
        return {
            "protocolVersion": "2024-11-05",
            "capabilities": {
                "tools": {}
            },
            "serverInfo": {
                "name": self.settings.mcp_server_name,
                "version": self.settings.mcp_server_version
            }
        }
    
    async def _handle_list_tools(self) -> Dict[str, Any]:
        """Handle list tools request"""
        tools = self.registry.list_mcp_tools()
        return {"tools": tools}
    
    async def _handle_tool_call(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle tool call request"""
        request = ToolCallRequest(**params)
        response = await self.router.execute_tool(request)
        
        # Convert to MCP format
        return {
            "content": [
                {
                    "type": content.type,
                    "text": content.text if hasattr(content, "text") else None,
                    "data": content.data if hasattr(content, "data") else None,
                    "mimeType": content.mimeType if hasattr(content, "mimeType") else None,
                }
                for content in response.content
            ],
            "isError": response.isError
        }
    
    async def run(self):
        """Run the MCP server (stdio mode)"""
        logger.info("Starting CursorMCP server...")
        logger.info(f"Server: {self.settings.mcp_server_name} v{self.settings.mcp_server_version}")
        logger.info(f"Tools registered: {self.registry.count()}")
        
        # Read from stdin, write to stdout
        while True:
            try:
                # Read line from stdin
                line = await asyncio.get_event_loop().run_in_executor(
                    None, sys.stdin.readline
                )
                
                if not line:
                    break
                
                line = line.strip()
                if not line:
                    continue
                
                # Parse JSON-RPC request
                try:
                    request_data = json.loads(line)
                    request = MCPRequest(**request_data)
                except json.JSONDecodeError as e:
                    logger.error(f"Invalid JSON: {e}")
                    response = MCPResponse(
                        jsonrpc="2.0",
                        id=None,
                        error={
                            "code": -32700,
                            "message": "Parse error"
                        }
                    )
                    print(json.dumps(response.model_dump(exclude_none=True)))
                    sys.stdout.flush()
                    continue
                
                # Handle request
                response = await self.handle_request(request)
                
                # Send response
                response_json = json.dumps(
                    response.model_dump(exclude_none=True),
                    ensure_ascii=False
                )
                print(response_json)
                sys.stdout.flush()
            
            except KeyboardInterrupt:
                logger.info("Shutting down...")
                break
            except Exception as e:
                logger.exception("Unexpected error in main loop")
                response = MCPResponse(
                    jsonrpc="2.0",
                    id=None,
                    error={
                        "code": -32603,
                        "message": f"Internal error: {str(e)}"
                    }
                )
                print(json.dumps(response.model_dump(exclude_none=True)))
                sys.stdout.flush()


async def main():
    """Main entry point"""
    server = MCPServer()
    await server.run()


if __name__ == "__main__":
    asyncio.run(main())

