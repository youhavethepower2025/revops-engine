import Anthropic from '@anthropic-ai/sdk';

interface Env {
  DB: D1Database;
  CONVERSATION: DurableObjectNamespace;
  AI: Ai;
  MCP: Fetcher;  // Service binding to CloudflareMCP
  CLOUDFLAREMCP_URL: string;
  REVOPS_OS_URL: string;
  ANTHROPIC_API_KEY: string;
}

interface ChatRequest {
  agent_role: string;
  message: string;
  conversation_id?: string;
}

export default {
  async fetch(request: Request, env: Env): Promise<Response> {
    const url = new URL(request.url);
    const client_id = url.searchParams.get('client_id') || 'aijesusbro';

    // CORS headers for browser access
    const corsHeaders = {
      'Access-Control-Allow-Origin': '*',
      'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
      'Access-Control-Allow-Headers': 'Content-Type',
    };

    // Handle CORS preflight
    if (request.method === 'OPTIONS') {
      return new Response(null, { headers: corsHeaders });
    }

    try {
      // Health check endpoint
      if (url.pathname === '/health') {
        return Response.json({
          status: 'ok',
          client_id,
          timestamp: Date.now()
        }, { headers: corsHeaders });
      }

      // List agents endpoint
      if (url.pathname === '/agents' && request.method === 'GET') {
        const agents = await env.DB.prepare(
          'SELECT id, name, role, description, color, position, emoji FROM spectrum_agents WHERE client_id = ? AND enabled = 1 ORDER BY position'
        ).bind(client_id).all();

        return Response.json({
          agents: agents.results
        }, { headers: corsHeaders });
      }

      // List conversations endpoint
      if (url.pathname === '/conversations' && request.method === 'GET') {
        const agent_role = url.searchParams.get('agent_role');

        let query = `
          SELECT
            c.id,
            c.started_at,
            c.message_count,
            a.name as agent_name,
            a.role as agent_role,
            (SELECT content FROM spectrum_messages WHERE conversation_id = c.id ORDER BY created_at DESC LIMIT 1) as last_message
          FROM spectrum_conversations c
          JOIN spectrum_agents a ON c.agent_id = a.id
          WHERE c.client_id = ?
        `;

        const bindings: any[] = [client_id];

        if (agent_role) {
          query += ' AND a.role = ?';
          bindings.push(agent_role);
        }

        query += ' ORDER BY c.last_message_at DESC LIMIT 20';

        const convos = await env.DB.prepare(query).bind(...bindings).all();

        return Response.json({
          conversations: convos.results
        }, { headers: corsHeaders });
      }

      // Get conversation messages endpoint
      if (url.pathname.startsWith('/conversations/') && url.pathname.endsWith('/messages') && request.method === 'GET') {
        const pathParts = url.pathname.split('/');
        const conversation_id = pathParts[2];

        if (!conversation_id) {
          return Response.json({
            error: 'Missing conversation_id'
          }, { status: 400, headers: corsHeaders });
        }

        // Verify conversation belongs to client
        const conversation = await env.DB.prepare(
          'SELECT * FROM spectrum_conversations WHERE id = ? AND client_id = ?'
        ).bind(conversation_id, client_id).first();

        if (!conversation) {
          return Response.json({
            error: 'Conversation not found'
          }, { status: 404, headers: corsHeaders });
        }

        // Load messages
        const messages = await env.DB.prepare(
          'SELECT role, content, created_at FROM spectrum_messages WHERE conversation_id = ? ORDER BY created_at ASC'
        ).bind(conversation_id).all();

        return Response.json({
          conversation_id,
          messages: messages.results
        }, { headers: corsHeaders });
      }

      // Chat endpoint
      if (url.pathname === '/chat/send' && request.method === 'POST') {
        const body = await request.json() as ChatRequest;

        // Validate input
        if (!body.agent_role || !body.message) {
          return Response.json({
            error: 'Missing agent_role or message'
          }, { status: 400, headers: corsHeaders });
        }

        // Load agent from database
        const agent = await env.DB.prepare(
          'SELECT * FROM spectrum_agents WHERE client_id = ? AND role = ? AND enabled = 1'
        ).bind(client_id, body.agent_role).first();

        if (!agent) {
          return Response.json({
            error: 'Agent not found'
          }, { status: 404, headers: corsHeaders });
        }

        // Load or create conversation
        let conversation_id = body.conversation_id;
        let messages: any[] = [];

        if (conversation_id) {
          // Load existing conversation
          const convo = await env.DB.prepare(
            'SELECT * FROM spectrum_conversations WHERE id = ? AND client_id = ?'
          ).bind(conversation_id, client_id).first();

          if (convo) {
            // Load last 10 messages for context
            const msg_results = await env.DB.prepare(
              'SELECT role, content FROM spectrum_messages WHERE conversation_id = ? ORDER BY created_at ASC LIMIT 10'
            ).bind(conversation_id).all();

            messages = msg_results.results.map((m: any) => ({
              role: m.role,
              content: m.content
            }));
          } else {
            // Invalid conversation_id, create new one
            conversation_id = crypto.randomUUID();
          }
        } else {
          // Create new conversation
          conversation_id = crypto.randomUUID();
          await env.DB.prepare(
            'INSERT INTO spectrum_conversations (id, client_id, agent_id) VALUES (?, ?, ?)'
          ).bind(conversation_id, client_id, agent.id).run();
        }

        // Build system prompt with current date
        const system_prompt = (agent.system_prompt as string).replace(
          '{current_date}',
          new Date().toLocaleDateString('en-US', {
            weekday: 'long',
            year: 'numeric',
            month: 'long',
            day: 'numeric'
          })
        );

        // Add current user message to history
        messages.push({
          role: 'user',
          content: body.message
        });

        // Determine if we should enable tools based on conversation context
        // Only enable tools if the conversation has progressed beyond initial greetings
        const conversationText = messages.map(m => m.content).join(' ').toLowerCase();
        const hasSubstantiveContext = messages.length > 2 ||
          conversationText.includes('call') ||
          conversationText.includes('appointment') ||
          conversationText.includes('booking') ||
          conversationText.includes('schedule') ||
          conversationText.includes('contact') ||
          conversationText.includes('transcript') ||
          conversationText.includes('remember');

        // Define available tools for the agent (matching CloudflareMCP)
        const tools = [
          {
            name: 'ghl_search_contact',
            description: 'Search for a contact in CRM by phone number or email',
            parameters: {
              type: 'object',
              properties: {
                phone: {
                  type: 'string',
                  description: 'Phone number to search'
                },
                email: {
                  type: 'string',
                  description: 'Email to search'
                }
              }
            }
          },
          {
            name: 'ghl_get_contact',
            description: 'Get full contact details by ID',
            parameters: {
              type: 'object',
              properties: {
                contact_id: {
                  type: 'string',
                  description: 'GHL contact ID'
                }
              },
              required: ['contact_id']
            }
          },
          {
            name: 'ghl_get_calendar_slots',
            description: 'Check available appointment times in calendar',
            parameters: {
              type: 'object',
              properties: {
                calendar_id: {
                  type: 'string',
                  description: 'GHL calendar ID'
                },
                start_date: {
                  type: 'string',
                  description: 'Start date ISO string (optional, defaults to today)'
                },
                end_date: {
                  type: 'string',
                  description: 'End date ISO string (optional, defaults to 7 days from now)'
                }
              },
              required: ['calendar_id']
            }
          },
          {
            name: 'ghl_create_appointment',
            description: 'Create a calendar appointment',
            parameters: {
              type: 'object',
              properties: {
                contact_id: { type: 'string' },
                calendar_id: { type: 'string' },
                start_time: { type: 'string', description: 'ISO 8601 timestamp' },
                end_time: { type: 'string', description: 'ISO 8601 timestamp' },
                title: { type: 'string' }
              },
              required: ['contact_id', 'calendar_id', 'start_time', 'end_time']
            }
          },
          {
            name: 'vapi_list_calls',
            description: 'Get recent call logs from Vapi voice system',
            parameters: {
              type: 'object',
              properties: {
                limit: {
                  type: 'number',
                  description: 'Number of calls to retrieve (default 10)'
                },
                phone_number: {
                  type: 'string',
                  description: 'Filter by phone number'
                }
              }
            }
          },
          {
            name: 'vapi_get_call',
            description: 'Get details of a specific Vapi call including transcript',
            parameters: {
              type: 'object',
              properties: {
                call_id: {
                  type: 'string',
                  description: 'Vapi call ID'
                }
              },
              required: ['call_id']
            }
          },
          {
            name: 'vapi_get_transcript',
            description: 'Get the full transcript of a Vapi call',
            parameters: {
              type: 'object',
              properties: {
                call_id: {
                  type: 'string',
                  description: 'Vapi call ID'
                }
              },
              required: ['call_id']
            }
          },
          {
            name: 'remember',
            description: 'Store information in memory for later recall',
            parameters: {
              type: 'object',
              properties: {
                key: { type: 'string', description: 'Memory key' },
                value: { type: 'string', description: 'Value to store' },
                metadata: { type: 'object', description: 'Optional metadata' }
              },
              required: ['key', 'value']
            }
          },
          {
            name: 'recall',
            description: 'Retrieve previously stored information from memory',
            parameters: {
              type: 'object',
              properties: {
                key: { type: 'string', description: 'Memory key to retrieve' }
              },
              required: ['key']
            }
          }
        ];

        // Call Claude API
        console.log('[Spectrum] Calling Claude Haiku 4.5 with', messages.length, 'messages');

        const anthropic = new Anthropic({
          apiKey: env.ANTHROPIC_API_KEY
        });

        let claudeResponse;
        try {
          // Convert messages to Claude format
          const claudeMessages = messages.map((m: any) => ({
            role: m.role,
            content: m.content
          }));

          // Prepare Claude API call
          const claudeParams: any = {
            model: "claude-haiku-4-5-20251001",
            max_tokens: 4096,
            system: system_prompt,
            messages: claudeMessages,
            temperature: agent.temperature as number || 0.7
          };

          // Add tools (Claude has better discretion than Llama, so we can always pass them)
          claudeParams.tools = tools.map(t => ({
            name: t.name,
            description: t.description,
            input_schema: t.parameters
          }));

          claudeResponse = await anthropic.messages.create(claudeParams);
          console.log('[Spectrum] Claude response received, stop_reason:', claudeResponse.stop_reason);
        } catch (aiError: any) {
          console.error('[Spectrum] Claude API error:', aiError.message, aiError);
          throw new Error(`Claude API call failed: ${aiError.message}`);
        }

        // Parse Claude response
        let reply = '';
        const rawToolCalls: any[] = [];

        // Claude returns content blocks - text or tool_use
        for (const block of claudeResponse.content) {
          if (block.type === 'text') {
            reply += block.text;
          } else if (block.type === 'tool_use') {
            rawToolCalls.push({
              id: block.id,
              name: block.name,
              arguments: block.input
            });
          }
        }

        console.log('[Spectrum] Tool calls detected:', rawToolCalls.length);

        if (rawToolCalls.length > 0) {
          // Execute each tool call via CloudflareMCP
          const toolResults = [];

          for (let i = 0; i < rawToolCalls.length; i++) {
            const toolCall = rawToolCalls[i];
            // Workers AI returns: {name, arguments}
            // We need to add id for tracking
            const toolCallId = `call_${Date.now()}_${i}`;
            try {
              console.log('[Spectrum] Executing tool:', toolCall.name, 'with args:', JSON.stringify(toolCall.arguments).substring(0, 100));

              // Call CloudflareMCP using JSON-RPC 2.0 format
              const mcpRequest = {
                jsonrpc: "2.0",
                id: Date.now(),
                method: "tools/call",
                params: {
                  name: toolCall.name,
                  arguments: toolCall.arguments
                }
              };

              const mcpUrl = `/mcp?client_id=${client_id}`;
              console.log('[Spectrum] Calling MCP via Service Binding:', mcpUrl);

              const toolResponse = await env.MCP.fetch(new Request(`https://mcp${mcpUrl}`, {
                method: 'POST',
                headers: {
                  'Content-Type': 'application/json'
                },
                body: JSON.stringify(mcpRequest)
              }));

              console.log('[Spectrum] MCP response status:', toolResponse.status);

              let mcpResponse;
              const responseText = await toolResponse.text();
              console.log('[Spectrum] MCP raw response:', responseText.substring(0, 300));

              try {
                mcpResponse = JSON.parse(responseText);
              } catch (parseError) {
                console.error('[Spectrum] Failed to parse MCP response:', parseError);
                throw new Error(`MCP returned invalid JSON: ${responseText.substring(0, 100)}`);
              }

              console.log('[Spectrum] MCP parsed response:', JSON.stringify(mcpResponse).substring(0, 200));

              // Extract result from MCP response
              let resultText = '';
              if (mcpResponse.result && mcpResponse.result.content) {
                resultText = mcpResponse.result.content
                  .filter((c: any) => c.type === 'text')
                  .map((c: any) => c.text)
                  .join('\n');
              } else if (mcpResponse.error) {
                resultText = `Error: ${mcpResponse.error.message}`;
              }

              toolResults.push({
                tool_use_id: toolCall.id,
                type: 'tool_result',
                content: resultText
              });
            } catch (error: any) {
              console.error(`Tool call ${toolCall.name} failed:`, error);
              toolResults.push({
                tool_use_id: toolCall.id,
                type: 'tool_result',
                content: `Error: ${error.message}`,
                is_error: true
              });
            }
          }

          // Add assistant message with tool uses, then user message with tool results (Claude format)
          messages.push({
            role: 'assistant',
            content: claudeResponse.content
          });
          messages.push({
            role: 'user',
            content: toolResults
          });
          console.log('[Spectrum] Added', toolResults.length, 'tool results to context');

          // Call Claude again with tool results to get final response
          const finalClaudeMessages = messages.map((m: any) => ({
            role: m.role,
            content: m.content
          }));

          const claudeTools = tools.map(t => ({
            name: t.name,
            description: t.description,
            input_schema: t.parameters
          }));

          const finalResponse = await anthropic.messages.create({
            model: "claude-haiku-4-5-20251001",
            max_tokens: 4096,
            system: system_prompt,
            messages: finalClaudeMessages,
            tools: claudeTools,
            temperature: agent.temperature as number || 0.7
          });

          // Extract text from final response
          reply = '';
          for (const block of finalResponse.content) {
            if (block.type === 'text') {
              reply += block.text;
            }
          }

          if (!reply) {
            reply = 'Sorry, I could not generate a response.';
          }
        }

        // Fallback if no response
        if (!reply) {
          reply = 'Sorry, I could not generate a response.';
        }

        // Store user message
        await env.DB.prepare(
          'INSERT INTO spectrum_messages (id, conversation_id, role, content) VALUES (?, ?, ?, ?)'
        ).bind(crypto.randomUUID(), conversation_id, 'user', body.message).run();

        // Store assistant response
        await env.DB.prepare(
          'INSERT INTO spectrum_messages (id, conversation_id, role, content) VALUES (?, ?, ?, ?)'
        ).bind(crypto.randomUUID(), conversation_id, 'assistant', reply).run();

        // Update conversation metadata
        await env.DB.prepare(
          'UPDATE spectrum_conversations SET last_message_at = unixepoch(), message_count = message_count + 2 WHERE id = ?'
        ).bind(conversation_id).run();

        return Response.json({
          agent: agent.name,
          message: reply,
          conversation_id: conversation_id,
          model: 'claude-haiku-4-5-20251001'
        }, { headers: corsHeaders });
      }

      // ========================================
      // ADMIN ENDPOINTS
      // ========================================

      // Get all agents with full prompts (admin only)
      if (url.pathname === '/admin/agents' && request.method === 'GET') {
        const agents = await env.DB.prepare(
          'SELECT id, name, role, description, color, emoji, system_prompt, enabled, position FROM spectrum_agents WHERE client_id = ? ORDER BY position'
        ).bind(client_id).all();

        return Response.json({
          agents: agents.results
        }, { headers: corsHeaders });
      }

      // Get single agent with full prompt (admin only)
      if (url.pathname.startsWith('/admin/agents/') && request.method === 'GET') {
        const role = url.pathname.split('/').pop();

        const agent = await env.DB.prepare(
          'SELECT id, name, role, description, color, emoji, system_prompt, enabled, position FROM spectrum_agents WHERE client_id = ? AND role = ?'
        ).bind(client_id, role).first();

        if (!agent) {
          return Response.json({
            error: 'Agent not found'
          }, { status: 404, headers: corsHeaders });
        }

        return Response.json({
          agent
        }, { headers: corsHeaders });
      }

      // Update agent prompt (admin only)
      if (url.pathname.startsWith('/admin/agents/') && request.method === 'PUT') {
        const role = url.pathname.split('/').pop();
        const body: any = await request.json();

        if (!body.system_prompt) {
          return Response.json({
            error: 'Missing system_prompt in request body'
          }, { status: 400, headers: corsHeaders });
        }

        // Update the agent's system prompt
        await env.DB.prepare(
          'UPDATE spectrum_agents SET system_prompt = ?, updated_at = CURRENT_TIMESTAMP WHERE client_id = ? AND role = ?'
        ).bind(body.system_prompt, client_id, role).run();

        // Fetch and return updated agent
        const updated = await env.DB.prepare(
          'SELECT id, name, role, description, color, emoji, system_prompt, enabled, position FROM spectrum_agents WHERE client_id = ? AND role = ?'
        ).bind(client_id, role).first();

        return Response.json({
          success: true,
          agent: updated
        }, { headers: corsHeaders });
      }

      // 404 for unknown routes
      return Response.json({
        error: 'Not found',
        available_endpoints: ['/health', '/agents', '/chat/send', '/admin/agents']
      }, { status: 404, headers: corsHeaders });

    } catch (error: any) {
      console.error('Error:', error);
      return Response.json({
        error: 'Internal server error',
        message: error.message
      }, { status: 500, headers: corsHeaders });
    }
  }
};

// Durable Object for conversation state (Phase 1.2)
export class ConversationState implements DurableObject {
  constructor(private state: DurableObjectState, private env: Env) {}

  async fetch(request: Request): Promise<Response> {
    // Will implement in Phase 1.2
    return new Response('Conversation state - coming in Phase 1.2');
  }
}
