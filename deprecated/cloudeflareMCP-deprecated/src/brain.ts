// Durable Object: ClientBrain
// Each client gets their own stateful brain instance

import { Env, MCPRequest, MCPResponse, RetellWebhook } from './types';
import { MCP_TOOLS } from './tools';

export class ClientBrain {
  private state: DurableObjectState;
  private env: Env;
  private clientId: string;

  constructor(state: DurableObjectState, env: Env) {
    this.state = state;
    this.env = env;
    this.clientId = ''; // Will be set on first request
  }

  async fetch(request: Request): Promise<Response> {
    const url = new URL(request.url);

    // Extract client_id from request
    if (!this.clientId) {
      const body = await request.clone().json().catch(() => ({}));
      this.clientId = body.client_id || url.searchParams.get('client_id') || 'unknown';
    }

    // Route by path
    if (url.pathname === '/mcp' && request.method === 'POST') {
      return this.handleMCP(request);
    }

    if (url.pathname === '/retell/webhook' && request.method === 'POST') {
      return this.handleRetellWebhook(request);
    }

    if (url.pathname === '/ghl/webhook' && request.method === 'POST') {
      return this.handleGHLWebhook(request);
    }

    if (url.pathname === '/health') {
      return new Response(JSON.stringify({
        status: 'healthy',
        client_id: this.clientId,
        timestamp: Date.now()
      }), {
        headers: { 'Content-Type': 'application/json' }
      });
    }

    return new Response('Not Found', { status: 404 });
  }

  // ============ MCP PROTOCOL HANDLER ============
  async handleMCP(request: Request): Promise<Response> {
    try {
      const body: MCPRequest = await request.json();

      // Handle notifications (no id field) - return 202
      if (!body.id) {
        console.log(`[${this.clientId}] ✓ Notification: ${body.method}`);
        return new Response(null, { status: 202 });
      }

      // Handle requests (has id field)
      console.log(`[${this.clientId}] → MCP Request: ${body.method}`, body.params ? `params: ${JSON.stringify(body.params).substring(0, 100)}` : '');

      const response = await this.processMCPRequest(body);

      console.log(`[${this.clientId}] ← MCP Response: ${body.method}`, response.error ? `ERROR: ${response.error.message}` : '✓');

      return new Response(JSON.stringify(response), {
        headers: { 'Content-Type': 'application/json' }
      });

    } catch (error: any) {
      console.error(`[${this.clientId}] ✗ MCP Error:`, error.message, error.stack);
      return new Response(JSON.stringify({
        jsonrpc: "2.0",
        id: null,
        error: {
          code: -32603,
          message: error.message || 'Internal error'
        }
      }), {
        status: 500,
        headers: { 'Content-Type': 'application/json' }
      });
    }
  }

  async processMCPRequest(req: MCPRequest): Promise<MCPResponse> {
    const { method, params, id } = req;

    switch (method) {
      case 'initialize':
        return {
          jsonrpc: "2.0",
          id,
          result: {
            protocolVersion: params?.protocolVersion || "2024-11-05",
            capabilities: {
              tools: { listChanged: true },
              resources: {},
              prompts: {}
            },
            serverInfo: {
              name: "retell-brain-mcp",
              version: "1.0.0"
            }
          }
        };

      case 'tools/list':
        return {
          jsonrpc: "2.0",
          id,
          result: { tools: MCP_TOOLS }
        };

      case 'tools/call':
        const toolResult = await this.executeTool(params?.name, params?.arguments || {});
        return {
          jsonrpc: "2.0",
          id,
          result: toolResult
        };

      default:
        return {
          jsonrpc: "2.0",
          id,
          error: {
            code: -32601,
            message: `Method not found: ${method}`
          }
        };
    }
  }

  // ============ TOOL EXECUTION ============
  async executeTool(toolName: string, args: any): Promise<any> {
    const startTime = Date.now();
    console.log(`[${this.clientId}] → Tool: ${toolName}`, JSON.stringify(args).substring(0, 100));

    try {
      // Memory tools
      if (toolName === 'remember') {
        await this.env.DB.prepare(
          'INSERT INTO memory (client_id, key, value, metadata) VALUES (?, ?, ?, ?) ON CONFLICT(client_id, key) DO UPDATE SET value = ?, metadata = ?, updated_at = unixepoch()'
        ).bind(
          this.clientId,
          args.key,
          JSON.stringify(args.value),
          JSON.stringify(args.metadata || {}),
          JSON.stringify(args.value),
          JSON.stringify(args.metadata || {})
        ).run();

        return {
          content: [{
            type: "text",
            text: `Remembered: ${args.key}`
          }]
        };
      }

      if (toolName === 'recall') {
        const result = await this.env.DB.prepare(
          'SELECT value FROM memory WHERE client_id = ? AND key = ?'
        ).bind(this.clientId, args.key).first();

        return {
          content: [{
            type: "text",
            text: result ? result.value : `No memory found for key: ${args.key}`
          }]
        };
      }

      if (toolName === 'search_memory') {
        const results = await this.env.DB.prepare(
          'SELECT key, value FROM memory WHERE client_id = ? AND (key LIKE ? OR value LIKE ?) LIMIT ?'
        ).bind(
          this.clientId,
          `%${args.query}%`,
          `%${args.query}%`,
          args.limit || 10
        ).all();

        return {
          content: [{
            type: "text",
            text: JSON.stringify(results.results)
          }]
        };
      }

      // Retell tools
      if (toolName.startsWith('retell_')) {
        return await this.executeRetellTool(toolName, args);
      }

      // GHL tools
      if (toolName.startsWith('ghl_')) {
        return await this.executeGHLTool(toolName, args);
      }

      return {
        content: [{
          type: "text",
          text: `Unknown tool: ${toolName}`
        }]
      };

    } catch (error: any) {
      const duration = Date.now() - startTime;
      console.error(`[${this.clientId}] ✗ Tool failed: ${toolName} (${duration}ms)`, error.message);
      return {
        content: [{
          type: "text",
          text: `Error: ${error.message}`
        }],
        isError: true
      };
    } finally {
      const duration = Date.now() - startTime;
      console.log(`[${this.clientId}] ← Tool: ${toolName} completed (${duration}ms)`);
    }
  }

  // ============ RETELL API INTEGRATION ============
  async executeRetellTool(toolName: string, args: any): Promise<any> {
    const apiKey = this.env.RETELL_API_KEY;
    const baseUrl = 'https://api.retellai.com';

    const callRetellAPI = async (method: string, endpoint: string, data?: any) => {
      try {
        const response = await fetch(`${baseUrl}${endpoint}`, {
          method,
          headers: {
            'Authorization': `Bearer ${apiKey}`,
            'Content-Type': 'application/json'
          },
          body: data ? JSON.stringify(data) : undefined
        });

        // Defensive: Check response status before parsing
        if (!response.ok) {
          const errorText = await response.text();
          console.error(`[${this.clientId}] Retell API error ${response.status}:`, errorText);
          throw new Error(`Retell API failed (${response.status}): ${errorText}`);
        }

        return await response.json();
      } catch (error: any) {
        console.error(`[${this.clientId}] Retell API call failed:`, error);
        throw error;
      }
    };

    switch (toolName) {
      case 'retell_get_call':
        const call = await callRetellAPI('GET', `/get-call/${args.call_id}`);
        return { content: [{ type: "text", text: JSON.stringify(call) }] };

      case 'retell_list_calls':
        const calls = await callRetellAPI('POST', '/list-calls', {
          limit: args.limit || 10,
          phone_number: args.phone_number
        });
        return { content: [{ type: "text", text: JSON.stringify(calls) }] };

      case 'retell_create_phone_call':
        const newCall = await callRetellAPI('POST', '/create-phone-call', {
          from_number: args.from_number,
          to_number: args.to_number,
          agent_id: args.agent_id,
          metadata: { ...args.metadata, client_id: this.clientId }
        });
        return { content: [{ type: "text", text: JSON.stringify(newCall) }] };

      case 'retell_get_call_transcript':
        const transcript = await callRetellAPI('GET', `/get-call-transcript/${args.call_id}`);
        return { content: [{ type: "text", text: JSON.stringify(transcript) }] };

      default:
        return { content: [{ type: "text", text: `Retell tool not implemented: ${toolName}` }] };
    }
  }

  // ============ GHL API INTEGRATION ============
  async executeGHLTool(toolName: string, args: any): Promise<any> {
    const apiKey = this.env.GHL_API_KEY;
    const locationId = this.env.GHL_LOCATION_ID;
    const baseUrl = 'https://rest.gohighlevel.com/v1';

    const callGHLAPI = async (method: string, endpoint: string, data?: any) => {
      try {
        const response = await fetch(`${baseUrl}${endpoint}`, {
          method,
          headers: {
            'Authorization': `Bearer ${apiKey}`,
            'Content-Type': 'application/json'
          },
          body: data ? JSON.stringify(data) : undefined
        });

        // Defensive: Check response status before parsing
        if (!response.ok) {
          const errorText = await response.text();
          console.error(`[${this.clientId}] GHL API error ${response.status}:`, errorText);
          throw new Error(`GHL API failed (${response.status}): ${errorText}`);
        }

        return await response.json();
      } catch (error: any) {
        console.error(`[${this.clientId}] GHL API call failed:`, error);
        throw error;
      }
    };

    switch (toolName) {
      case 'ghl_search_contact':
        const searchResults = await callGHLAPI('GET',
          `/locations/${locationId}/contacts?${args.phone ? `phone=${args.phone}` : `email=${args.email}`}`
        );
        return { content: [{ type: "text", text: JSON.stringify(searchResults) }] };

      case 'ghl_get_contact':
        const contact = await callGHLAPI('GET', `/locations/${locationId}/contacts/${args.contact_id}`);
        return { content: [{ type: "text", text: JSON.stringify(contact) }] };

      case 'ghl_create_contact':
        const newContact = await callGHLAPI('POST', `/locations/${locationId}/contacts`, args);
        return { content: [{ type: "text", text: JSON.stringify(newContact) }] };

      case 'ghl_update_contact':
        const updatedContact = await callGHLAPI('PUT', `/locations/${locationId}/contacts/${args.contact_id}`, args);
        return { content: [{ type: "text", text: JSON.stringify(updatedContact) }] };

      case 'ghl_add_note':
        const note = await callGHLAPI('POST', `/locations/${locationId}/contacts/${args.contact_id}/notes`, {
          body: args.note
        });
        return { content: [{ type: "text", text: JSON.stringify(note) }] };

      case 'ghl_create_opportunity':
        const opp = await callGHLAPI('POST', `/locations/${locationId}/opportunities`, args);
        return { content: [{ type: "text", text: JSON.stringify(opp) }] };

      default:
        return { content: [{ type: "text", text: `GHL tool not implemented: ${toolName}` }] };
    }
  }

  // ============ WEBHOOK HANDLERS ============
  async handleRetellWebhook(request: Request): Promise<Response> {
    try {
      const webhook: RetellWebhook = await request.json();
      console.log(`[${this.clientId}] 📞 Retell webhook: ${webhook.event_type}`, `call_id: ${webhook.call?.call_id}`);

      // Store call in D1
      if (webhook.event_type === 'call_ended') {
        await this.env.DB.prepare(
          'INSERT INTO calls (call_id, client_id, agent_id, phone_number, direction, status, transcript, metadata, started_at, ended_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)'
        ).bind(
          webhook.call.call_id,
          this.clientId,
          webhook.call.agent_id,
          webhook.call.from_number,
          webhook.call.direction,
          webhook.call.status,
          JSON.stringify(webhook.call.transcript || {}),
          JSON.stringify(webhook.call.metadata || {}),
          Date.now(),
          Date.now()
        ).run();

        // Auto-update GHL contact if phone number exists
        if (webhook.call.from_number) {
          await this.autoUpdateGHLContact(webhook);
        }
      }

      return new Response(JSON.stringify({ success: true }), {
        headers: { 'Content-Type': 'application/json' }
      });

    } catch (error: any) {
      console.error(`[${this.clientId}] ✗ Retell webhook error:`, error.message, error.stack);
      return new Response(JSON.stringify({ error: error.message }), {
        status: 500,
        headers: { 'Content-Type': 'application/json' }
      });
    }
  }

  async handleGHLWebhook(request: Request): Promise<Response> {
    try {
      const webhook = await request.json();
      console.log(`[${this.clientId}] GHL webhook:`, webhook.type);

      // Process GHL events and store relevant data
      // Add logic based on your GHL workflow needs

      return new Response(JSON.stringify({ success: true }), {
        headers: { 'Content-Type': 'application/json' }
      });

    } catch (error: any) {
      console.error(`[${this.clientId}] GHL webhook error:`, error);
      return new Response(JSON.stringify({ error: error.message }), {
        status: 500,
        headers: { 'Content-Type': 'application/json' }
      });
    }
  }

  // ============ INTELLIGENT AUTOMATION ============
  async autoUpdateGHLContact(webhook: RetellWebhook): Promise<void> {
    try {
      // Search for existing contact by phone
      const searchResults = await this.executeGHLTool('ghl_search_contact', {
        phone: webhook.call.from_number
      });

      const contacts = JSON.parse(searchResults.content[0].text);

      if (contacts && contacts.contacts && contacts.contacts.length > 0) {
        const contactId = contacts.contacts[0].id;

        // Add note about the call
        await this.executeGHLTool('ghl_add_note', {
          contact_id: contactId,
          note: `Call ${webhook.call.status} - Duration: ${webhook.call.metadata?.duration || 'unknown'}s`
        });

        console.log(`[${this.clientId}] Auto-updated GHL contact: ${contactId}`);
      }
    } catch (error) {
      console.error(`[${this.clientId}] Auto-update GHL failed:`, error);
    }
  }
}
