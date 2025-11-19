// MCP Server Template for Cloudflare Workers
// Use this as a starting point for application MCP servers

export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    
    // MCP endpoint
    if (url.pathname === "/mcp") {
      return handleMCP(request, env);
    }
    
    // Health check
    if (url.pathname === "/health") {
      return new Response(JSON.stringify({ status: "ok" }), {
        headers: { "Content-Type": "application/json" }
      });
    }
    
    return new Response("Not Found", { status: 404 });
  }
};

async function handleMCP(request, env) {
  const { jsonrpc, id, method, params } = await request.json();
  
  if (method === "initialize") {
    return json({
      jsonrpc: "2.0",
      id,
      result: {
        protocolVersion: "2024-11-05",
        capabilities: { tools: {} },
        serverInfo: {
          name: "app-mcp-server",
          version: "1.0.0"
        }
      }
    });
  }
  
  if (method === "tools/list") {
    return json({
      jsonrpc: "2.0",
      id,
      result: {
        tools: [
          // Add your tool definitions here
          {
            name: "example_tool",
            description: "Example tool",
            inputSchema: {
              type: "object",
              properties: {
                param: { type: "string" }
              },
              required: ["param"]
            }
          }
        ]
      }
    });
  }
  
  if (method === "tools/call") {
    const { name, arguments: args } = params;
    const result = await executeTool(name, args, env);
    
    return json({
      jsonrpc: "2.0",
      id,
      result: {
        content: [{
          type: "text",
          text: JSON.stringify(result, null, 2)
        }]
      }
    });
  }
  
  return json({
    jsonrpc: "2.0",
    id,
    error: { code: -32601, message: "Method not found" }
  });
}

async function executeTool(name, args, env) {
  switch (name) {
    case "example_tool":
      return await handle_example_tool(args, env);
    default:
      throw new Error(`Unknown tool: ${name}`);
  }
}

async function handle_example_tool(args, env) {
  // Implement your tool logic here
  return { success: true, param: args.param };
}

function json(data) {
  return new Response(JSON.stringify(data), {
    headers: { "Content-Type": "application/json" }
  });
}


