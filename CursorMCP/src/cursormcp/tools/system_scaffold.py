"""System Scaffolding Tools - Rapid development helpers"""

from typing import Dict, Any, List
import logging
from .base import BaseTool
from ..services.cloudflare import CloudflareService, CloudflareAPIError

logger = logging.getLogger(__name__)


class CreateD1SchemaTool(BaseTool):
    """Generate and apply D1 database schema"""
    
    name = "system_create_d1_schema"
    description = "Create and apply a D1 database schema from SQL statements"
    
    input_schema = {
        "type": "object",
        "properties": {
            "database_id": {
                "type": "string",
                "description": "D1 database ID"
            },
            "schema_sql": {
                "type": "string",
                "description": "SQL schema statements (can be multiple statements separated by semicolons)"
            },
            "drop_existing": {
                "type": "boolean",
                "description": "Drop existing tables before creating (default: false)",
                "default": False
            }
        },
        "required": ["database_id", "schema_sql"]
    }
    
    async def execute(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Create D1 schema"""
        service = CloudflareService()
        database_id = args["database_id"]
        schema_sql = args["schema_sql"]
        drop_existing = args.get("drop_existing", False)
        
        try:
            # Split SQL into individual statements
            statements = [s.strip() for s in schema_sql.split(";") if s.strip()]
            
            results = []
            for statement in statements:
                if drop_existing and "CREATE TABLE" in statement.upper():
                    # Extract table name and drop if exists
                    table_name = statement.split()[2] if len(statement.split()) > 2 else None
                    if table_name:
                        drop_sql = f"DROP TABLE IF EXISTS {table_name}"
                        try:
                            await service.query_d1(database_id, drop_sql)
                        except:
                            pass  # Table might not exist
                
                result = await service.query_d1(database_id, statement)
                results.append({
                    "statement": statement[:100] + "..." if len(statement) > 100 else statement,
                    "result": result
                })
            
            return {
                "success": True,
                "database_id": database_id,
                "statements_executed": len(statements),
                "results": results
            }
        except CloudflareAPIError as e:
            return {"error": str(e), "success": False}


class DeployWorkerClusterTool(BaseTool):
    """Deploy multiple related Workers together"""
    
    name = "system_deploy_worker_cluster"
    description = "Deploy multiple related Workers as a cluster with shared bindings"
    
    input_schema = {
        "type": "object",
        "properties": {
            "workers": {
                "type": "array",
                "description": "Array of worker definitions",
                "items": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string"},
                        "script": {"type": "string"},
                        "bindings": {"type": "array", "items": {"type": "object"}}
                    },
                    "required": ["name", "script"]
                }
            },
            "shared_bindings": {
                "type": "array",
                "description": "Bindings shared across all workers",
                "items": {"type": "object"},
                "default": []
            }
        },
        "required": ["workers"]
    }
    
    async def execute(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Deploy worker cluster"""
        service = CloudflareService()
        workers = args["workers"]
        shared_bindings = args.get("shared_bindings", [])
        
        results = []
        errors = []
        
        for worker_def in workers:
            worker_name = worker_def["name"]
            script_content = worker_def["script"]
            worker_bindings = worker_def.get("bindings", [])
            
            # Merge shared and worker-specific bindings
            all_bindings = shared_bindings + worker_bindings
            
            try:
                result = await service.deploy_worker(
                    script_name=worker_name,
                    script_content=script_content,
                    bindings=all_bindings if all_bindings else None
                )
                results.append({
                    "worker": worker_name,
                    "success": True,
                    "url": f"https://{worker_name}.aijesusbro-brain.workers.dev"
                })
            except CloudflareAPIError as e:
                errors.append({
                    "worker": worker_name,
                    "error": str(e)
                })
        
        return {
            "success": len(errors) == 0,
            "deployed": len(results),
            "failed": len(errors),
            "results": results,
            "errors": errors
        }


class CreateWorkflowTool(BaseTool):
    """Generate Workflow from definition"""
    
    name = "system_create_workflow"
    description = "Create a Cloudflare Workflow from a definition"
    
    input_schema = {
        "type": "object",
        "properties": {
            "name": {
                "type": "string",
                "description": "Workflow name"
            },
            "steps": {
                "type": "array",
                "description": "Array of workflow steps",
                "items": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string"},
                        "type": {"type": "string"},  # http, worker, wait, etc.
                        "config": {"type": "object"}
                    },
                    "required": ["name", "type"]
                }
            },
            "trigger": {
                "type": "object",
                "description": "Workflow trigger configuration"
            }
        },
        "required": ["name", "steps"]
    }
    
    async def execute(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Create workflow"""
        service = CloudflareService()
        name = args["name"]
        steps = args["steps"]
        trigger = args.get("trigger", {})
        
        # Build workflow definition
        definition = {
            "steps": steps,
            "trigger": trigger
        }
        
        try:
            result = await service.create_workflow(name, definition)
            return {
                "success": True,
                "workflow": result,
                "name": name
            }
        except CloudflareAPIError as e:
            return {"error": str(e), "success": False}


class GenerateMCPServerTool(BaseTool):
    """Create MCP endpoint template for a Worker"""
    
    name = "system_generate_mcp_server"
    description = "Generate an MCP server endpoint template for deployment as a Worker"
    
    input_schema = {
        "type": "object",
        "properties": {
            "app_name": {
                "type": "string",
                "description": "Application name (e.g., 'revops', 'content')"
            },
            "tools": {
                "type": "array",
                "description": "Array of tool definitions",
                "items": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string"},
                        "description": {"type": "string"},
                        "inputSchema": {"type": "object"}
                    },
                    "required": ["name", "description", "inputSchema"]
                }
            },
            "worker_name": {
                "type": "string",
                "description": "Worker name for deployment"
            }
        },
        "required": ["app_name", "tools"]
    }
    
    async def execute(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Generate MCP server template"""
        app_name = args["app_name"]
        tools = args["tools"]
        worker_name = args.get("worker_name", f"{app_name}-mcp-server")
        
        # Generate MCP server JavaScript code
        import json as json_module
        
        # Format tools as JSON string for JavaScript
        tools_json = json_module.dumps(tools, indent=2)
        
        # Build tool cases
        tool_cases = []
        tool_handlers = []
        for tool in tools:
            tool_name = tool["name"]
            handler_name = tool_name.replace("-", "_").replace(".", "_")
            tool_cases.append(f'    case "{tool_name}":\n      return await handle_{handler_name}(args, env);')
            tool_handlers.append(f'''async function handle_{handler_name}(args, env) {{
  // TODO: Implement {tool_name}
  return {{ success: true, tool: "{tool_name}", args }};
}}''')
        
        mcp_server_code = f'''// MCP Server for {app_name}
export default {{
  async fetch(request, env) {{
    const url = new URL(request.url);
    
    // MCP endpoint
    if (url.pathname === "/mcp") {{
      return handleMCP(request, env);
    }}
    
    // Health check
    if (url.pathname === "/health") {{
      return new Response(JSON.stringify({{ status: "ok", app: "{app_name}" }}), {{
        headers: {{ "Content-Type": "application/json" }}
      }});
    }}
    
    return new Response("Not Found", {{ status: 404 }});
  }}
}};

async function handleMCP(request, env) {{
  const {{ jsonrpc, id, method, params }} = await request.json();
  
  if (method === "initialize") {{
    return json({{
      jsonrpc: "2.0",
      id,
      result: {{
        protocolVersion: "2024-11-05",
        capabilities: {{ tools: {{}} }},
        serverInfo: {{
          name: "{app_name}-mcp",
          version: "1.0.0"
        }}
      }}
    }});
  }}
  
  if (method === "tools/list") {{
    return json({{
      jsonrpc: "2.0",
      id,
      result: {{
        tools: {tools_json}
      }}
    }});
  }}
  
  if (method === "tools/call") {{
    const {{ name, arguments: args }} = params;
    const result = await executeTool(name, args, env);
    
    return json({{
      jsonrpc: "2.0",
      id,
      result: {{
        content: [{{
          type: "text",
          text: JSON.stringify(result, null, 2)
        }}]
      }}
    }});
  }}
  
  return json({{
    jsonrpc: "2.0",
    id,
    error: {{ code: -32601, message: "Method not found" }}
  }});
}}

async function executeTool(name, args, env) {{
  // Tool implementations
  switch (name) {{
{chr(10).join(tool_cases)}
    default:
      throw new Error(`Unknown tool: ${{name}}`);
  }}
}}

// Tool handler implementations
{chr(10).join(tool_handlers)}

function json(data) {{
  return new Response(JSON.stringify(data), {{
    headers: {{ "Content-Type": "application/json" }}
  }});
}}
'''
        
        return {
            "success": True,
            "app_name": app_name,
            "worker_name": worker_name,
            "code": mcp_server_code,
            "tools_count": len(tools),
            "tools": [t["name"] for t in tools]
        }

