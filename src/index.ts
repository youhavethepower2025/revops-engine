/**
 * RevOps MCP Engine - Main Worker Entry Point
 *
 * Routes requests to appropriate tenant Durable Objects.
 * Handles authentication, rate limiting, and routing.
 */

import { MCPServer } from './mcp-server';
import type { Env } from './types';

export { MCPServer };

/**
 * Main Worker - Routes to tenant-specific Durable Objects
 */
export default {
  async fetch(request: Request, env: Env, ctx: ExecutionContext): Promise<Response> {
    const url = new URL(request.url);

    // CORS handling
    if (request.method === 'OPTIONS') {
      return new Response(null, {
        headers: {
          'Access-Control-Allow-Origin': '*',
          'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
          'Access-Control-Allow-Headers': 'Content-Type, Authorization, X-Tenant-ID',
        },
      });
    }

    try {
      // Health check
      if (url.pathname === '/health') {
        return jsonResponse({ status: 'healthy', version: '1.0.0' });
      }

      // API documentation
      if (url.pathname === '/' || url.pathname === '/docs') {
        return new Response(getAPIDocumentation(), {
          headers: { 'Content-Type': 'text/html' },
        });
      }

      // Tenant management endpoints
      if (url.pathname.startsWith('/tenants')) {
        return handleTenantManagement(request, env);
      }

      // MCP endpoints - require authentication
      if (url.pathname.startsWith('/mcp') || url.pathname.startsWith('/tools')) {
        const authResult = await authenticateRequest(request, env);

        if (!authResult.success) {
          return jsonResponse({ error: authResult.error }, 401);
        }

        // Route to tenant's Durable Object
        const tenantId = authResult.tenantId!;
        const stub = await getTenantMCPServer(tenantId, env);

        // Forward request to Durable Object
        return await stub.fetch(request);
      }

      return jsonResponse({ error: 'Not found' }, 404);
    } catch (error: any) {
      console.error('Worker error:', error);
      return jsonResponse({ error: error.message || 'Internal server error' }, 500);
    }
  },
};

/**
 * Authenticate request and extract tenant ID
 */
async function authenticateRequest(
  request: Request,
  env: Env
): Promise<{ success: boolean; tenantId?: string; error?: string }> {
  // Extract authentication - support multiple methods:
  // 1. X-Tenant-ID header (for development)
  // 2. Authorization: Bearer <api_key>
  // 3. Authorization: Bearer <jwt_token>

  const tenantIdHeader = request.headers.get('X-Tenant-ID');
  if (tenantIdHeader) {
    // Development mode - direct tenant ID
    return { success: true, tenantId: tenantIdHeader };
  }

  const authHeader = request.headers.get('Authorization');
  if (!authHeader || !authHeader.startsWith('Bearer ')) {
    return { success: false, error: 'Missing or invalid Authorization header' };
  }

  const token = authHeader.substring(7);

  // Check if it's an API key (starts with 'revops_')
  if (token.startsWith('revops_')) {
    return await validateAPIKey(token, env);
  }

  // Otherwise, treat as JWT
  return await validateJWT(token, env);
}

/**
 * Validate API key and return tenant ID
 */
async function validateAPIKey(apiKey: string, env: Env): Promise<{ success: boolean; tenantId?: string; error?: string }> {
  // Hash the API key
  const encoder = new TextEncoder();
  const data = encoder.encode(apiKey);
  const hashBuffer = await crypto.subtle.digest('SHA-256', data);
  const hashArray = Array.from(new Uint8Array(hashBuffer));
  const keyHash = hashArray.map((b) => b.toString(16).padStart(2, '0')).join('');

  // Look up API key in database
  const result = await env.DB.prepare(
    `SELECT tenant_id, is_active, expires_at
     FROM api_keys
     WHERE key_hash = ? AND is_active = 1`
  )
    .bind(keyHash)
    .first<{ tenant_id: string; is_active: number; expires_at: string | null }>();

  if (!result) {
    return { success: false, error: 'Invalid API key' };
  }

  // Check expiration
  if (result.expires_at && new Date(result.expires_at) < new Date()) {
    return { success: false, error: 'API key expired' };
  }

  // Update last used timestamp
  await env.DB.prepare('UPDATE api_keys SET last_used_at = datetime("now") WHERE key_hash = ?').bind(keyHash).run();

  return { success: true, tenantId: result.tenant_id };
}

/**
 * Validate JWT token and extract tenant ID
 */
async function validateJWT(token: string, env: Env): Promise<{ success: boolean; tenantId?: string; error?: string }> {
  try {
    // Simple JWT validation (in production, use a proper JWT library)
    const parts = token.split('.');
    if (parts.length !== 3) {
      return { success: false, error: 'Invalid JWT format' };
    }

    const payload = JSON.parse(atob(parts[1]));

    // Check expiration
    if (payload.exp && payload.exp < Date.now() / 1000) {
      return { success: false, error: 'Token expired' };
    }

    if (!payload.tenant_id) {
      return { success: false, error: 'Missing tenant_id in token' };
    }

    // In production, verify signature with JWT_SECRET
    // For now, we trust the payload (development mode)

    return { success: true, tenantId: payload.tenant_id };
  } catch (error) {
    return { success: false, error: 'Invalid JWT token' };
  }
}

/**
 * Get or create tenant's MCP Server Durable Object
 */
async function getTenantMCPServer(tenantId: string, env: Env): Promise<DurableObjectStub> {
  // Create unique Durable Object ID for this tenant
  const doId = env.MCP_SERVER.idFromName(`tenant:${tenantId}`);
  return env.MCP_SERVER.get(doId);
}

/**
 * Handle tenant management operations
 */
async function handleTenantManagement(request: Request, env: Env): Promise<Response> {
  const url = new URL(request.url);

  // POST /tenants - Create new tenant
  if (request.method === 'POST' && url.pathname === '/tenants') {
    const body = await request.json<{
      name: string;
      domain?: string;
      subscription_tier?: string;
    }>();

    const tenantId = crypto.randomUUID();
    const apiKey = await generateAPIKey();
    const keyHash = await hashString(apiKey);

    // Create tenant
    await env.DB.prepare(
      `INSERT INTO tenants (id, name, domain, subscription_tier, api_key_hash)
       VALUES (?, ?, ?, ?, ?)`
    )
      .bind(tenantId, body.name, body.domain || null, body.subscription_tier || 'starter', keyHash)
      .run();

    // Create default API key
    const apiKeyId = crypto.randomUUID();
    const keyPrefix = apiKey.substring(0, 16);

    await env.DB.prepare(
      `INSERT INTO api_keys (id, tenant_id, key_hash, key_prefix, name, scopes)
       VALUES (?, ?, ?, ?, ?, ?)`
    )
      .bind(apiKeyId, tenantId, keyHash, keyPrefix, 'Default API Key', JSON.stringify(['read', 'write']))
      .run();

    return jsonResponse({
      tenant_id: tenantId,
      api_key: apiKey, // Only shown once!
      mcp_endpoint: `${url.origin}/mcp`,
      message: 'Tenant created successfully. Store your API key securely - it will not be shown again.',
    });
  }

  // GET /tenants/:id - Get tenant info
  if (request.method === 'GET' && url.pathname.startsWith('/tenants/')) {
    const tenantId = url.pathname.split('/')[2];

    const tenant = await env.DB.prepare('SELECT id, name, domain, subscription_tier, created_at FROM tenants WHERE id = ?')
      .bind(tenantId)
      .first();

    if (!tenant) {
      return jsonResponse({ error: 'Tenant not found' }, 404);
    }

    return jsonResponse(tenant);
  }

  return jsonResponse({ error: 'Method not allowed' }, 405);
}

/**
 * Generate secure API key
 */
async function generateAPIKey(): Promise<string> {
  const randomBytes = crypto.getRandomValues(new Uint8Array(32));
  const randomString = Array.from(randomBytes)
    .map((b) => b.toString(16).padStart(2, '0'))
    .join('');

  return `revops_live_${randomString}`;
}

/**
 * Hash string using SHA-256
 */
async function hashString(str: string): Promise<string> {
  const encoder = new TextEncoder();
  const data = encoder.encode(str);
  const hashBuffer = await crypto.subtle.digest('SHA-256', data);
  const hashArray = Array.from(new Uint8Array(hashBuffer));
  return hashArray.map((b) => b.toString(16).padStart(2, '0')).join('');
}

/**
 * JSON response helper
 */
function jsonResponse(data: any, status: number = 200): Response {
  return new Response(JSON.stringify(data, null, 2), {
    status,
    headers: {
      'Content-Type': 'application/json',
      'Access-Control-Allow-Origin': '*',
    },
  });
}

/**
 * API Documentation (HTML)
 */
function getAPIDocumentation(): string {
  return `
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>RevOps MCP Engine - API Documentation</title>
    <style>
        body {
            font-family: system-ui, -apple-system, sans-serif;
            max-width: 1200px;
            margin: 0 auto;
            padding: 2rem;
            background: #0f1419;
            color: #e6edf3;
        }
        h1 { color: #58a6ff; }
        h2 { color: #79c0ff; margin-top: 2rem; }
        code {
            background: #161b22;
            padding: 0.2rem 0.4rem;
            border-radius: 4px;
            font-family: 'Monaco', monospace;
        }
        pre {
            background: #161b22;
            padding: 1rem;
            border-radius: 8px;
            overflow-x: auto;
            border-left: 4px solid #58a6ff;
        }
        .endpoint {
            background: #0d1117;
            padding: 1rem;
            margin: 1rem 0;
            border-radius: 8px;
            border: 1px solid #30363d;
        }
        .method {
            display: inline-block;
            padding: 0.25rem 0.5rem;
            border-radius: 4px;
            font-weight: bold;
            font-size: 0.875rem;
        }
        .post { background: #238636; color: white; }
        .get { background: #1f6feb; color: white; }
    </style>
</head>
<body>
    <h1>🚀 RevOps MCP Engine</h1>
    <p>Cloud-native CRM built on Cloudflare Durable Objects with native MCP protocol support.</p>

    <h2>Quick Start</h2>
    <pre><code># 1. Create a tenant
curl -X POST https://mcp.revops.ai/tenants \\
  -H "Content-Type: application/json" \\
  -d '{"name": "My Company", "subscription_tier": "professional"}'

# 2. Use the API key to call MCP tools
curl -X POST https://mcp.revops.ai/mcp \\
  -H "Authorization: Bearer revops_live_..." \\
  -H "Content-Type: application/json" \\
  -d '{
    "jsonrpc": "2.0",
    "id": 1,
    "method": "tools/call",
    "params": {
      "name": "create_contact",
      "arguments": {
        "FirstName": "John",
        "LastName": "Doe",
        "Email": "john@example.com"
      }
    }
  }'</code></pre>

    <h2>Tenant Management</h2>

    <div class="endpoint">
        <span class="method post">POST</span> <code>/tenants</code>
        <p>Create a new tenant and get an API key.</p>
        <pre><code>{
  "name": "Acme Corporation",
  "domain": "acme.com",
  "subscription_tier": "professional"
}</code></pre>
    </div>

    <div class="endpoint">
        <span class="method get">GET</span> <code>/tenants/:id</code>
        <p>Get tenant information.</p>
    </div>

    <h2>MCP Protocol</h2>

    <div class="endpoint">
        <span class="method post">POST</span> <code>/mcp</code>
        <p>MCP JSON-RPC endpoint. All tool calls go through here.</p>
        <p><strong>Authentication:</strong> Bearer token (API key or JWT)</p>
    </div>

    <div class="endpoint">
        <span class="method get">GET</span> <code>/tools</code>
        <p>List all available MCP tools.</p>
    </div>

    <h2>Available CRM Tools</h2>
    <ul>
        <li><code>create_contact</code> - Create a new contact</li>
        <li><code>get_contact</code> - Get contact by ID</li>
        <li><code>search_contacts</code> - Search contacts</li>
        <li><code>update_contact</code> - Update contact fields</li>
        <li><code>create_account</code> - Create a new account (company)</li>
        <li><code>get_account</code> - Get account by ID</li>
        <li><code>search_accounts</code> - Search accounts</li>
        <li><code>create_opportunity</code> - Create a new opportunity</li>
        <li><code>get_opportunity</code> - Get opportunity by ID</li>
        <li><code>update_opportunity_stage</code> - Update deal stage</li>
        <li><code>search_opportunities</code> - Search opportunities</li>
        <li><code>create_task</code> - Create a new task</li>
        <li><code>get_tasks</code> - Get tasks with filters</li>
    </ul>

    <h2>Example: Creating a Contact</h2>
    <pre><code>{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "tools/call",
  "params": {
    "name": "create_contact",
    "arguments": {
      "FirstName": "Sarah",
      "LastName": "Johnson",
      "Email": "sarah@enterprisetech.example",
      "Phone": "415-555-0100",
      "Title": "VP of Sales",
      "Department": "Sales",
      "LeadSource": "Web"
    }
  }
}</code></pre>

    <h2>MCP Client Configuration</h2>
    <p>Add to your Claude Desktop or MCP client config:</p>
    <pre><code>{
  "mcpServers": {
    "revops-crm": {
      "command": "node",
      "args": ["/path/to/mcp-client.js"],
      "env": {
        "REVOPS_API_KEY": "revops_live_...",
        "REVOPS_ENDPOINT": "https://mcp.revops.ai/mcp"
      }
    }
  }
}</code></pre>

    <footer style="margin-top: 3rem; padding-top: 2rem; border-top: 1px solid #30363d; color: #8b949e;">
        <p>RevOps MCP Engine v1.0.0 | Built on Cloudflare Workers + Durable Objects</p>
    </footer>
</body>
</html>
  `;
}
