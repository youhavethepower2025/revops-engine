// TypeScript types for the MCP server

export interface Env {
  BRAIN: DurableObjectNamespace;
  DB: D1Database;
  AI?: any; // Workers AI binding (optional)

  // Secrets (set via wrangler secret put)
  RETELL_API_KEY: string;
  GHL_API_KEY: string;
  GHL_LOCATION_ID: string;
  ANTHROPIC_API_KEY?: string;
  OPENAI_API_KEY?: string;

  ENVIRONMENT: string;
}

export interface MCPRequest {
  jsonrpc: "2.0";
  id?: number | string;
  method: string;
  params?: any;
}

export interface MCPResponse {
  jsonrpc: "2.0";
  id?: number | string;
  result?: any;
  error?: {
    code: number;
    message: string;
    data?: any;
  };
}

export interface MCPTool {
  name: string;
  description: string;
  inputSchema: {
    type: "object";
    properties: Record<string, any>;
    required?: string[];
  };
}

export interface ClientConfig {
  client_id: string;
  name: string;
  tier: string;
  ghl_api_key?: string;
  ghl_location_id?: string;
  retell_api_key?: string;
  config?: Record<string, any>;
  status: string;
}

export interface RetellWebhook {
  event_type: string;
  call: {
    call_id: string;
    agent_id: string;
    from_number: string;
    to_number: string;
    direction: string;
    status: string;
    transcript?: any;
    metadata?: Record<string, any>;
  };
}
