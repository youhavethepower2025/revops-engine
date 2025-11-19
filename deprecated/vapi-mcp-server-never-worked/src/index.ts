// src/index.ts
// Main entry point for VAPI MCP Server

export { VapiBrain } from './brain'

interface Env {
  DB: D1Database
  VAPI_BRAIN: DurableObjectNamespace
  VAPI_API_KEY: string
  ENVIRONMENT: string
  SERVICE_NAME: string
}

export default {
  async fetch(request: Request, env: Env): Promise<Response> {
    const url = new URL(request.url)

    // CORS preflight
    if (request.method === 'OPTIONS') {
      return new Response(null, {
        headers: {
          'Access-Control-Allow-Origin': '*',
          'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
          'Access-Control-Allow-Headers': 'Content-Type, Authorization, X-Call-Id, X-Chat-Id',
          'Access-Control-Max-Age': '86400',
        }
      })
    }

    // Health check
    if (url.pathname === '/health') {
      return new Response(JSON.stringify({
        status: 'ok',
        service: env.SERVICE_NAME || 'vapi-mcp-server',
        environment: env.ENVIRONMENT || 'production',
        timestamp: new Date().toISOString()
      }), {
        headers: {
          'Content-Type': 'application/json',
          'Access-Control-Allow-Origin': '*'
        }
      })
    }

    // MCP endpoint (the core functionality)
    if (url.pathname === '/mcp') {
      return handleMCP(request, env)
    }

    // VAPI webhooks
    if (url.pathname.startsWith('/webhooks/vapi')) {
      return handleVapiWebhook(request, env)
    }

    // Admin endpoints
    if (url.pathname.startsWith('/admin/clients')) {
      return handleAdminClients(request, env)
    }

    if (url.pathname.startsWith('/admin/calls')) {
      return handleAdminCalls(request, env)
    }

    return new Response(JSON.stringify({
      error: 'Not found',
      path: url.pathname
    }), {
      status: 404,
      headers: { 'Content-Type': 'application/json' }
    })
  }
}

async function handleMCP(request: Request, env: Env): Promise<Response> {
  const url = new URL(request.url)
  const clientId = url.searchParams.get('client_id') || 'default'

  console.log(`[MCP] Request for client: ${clientId}`)

  // Get Durable Object for this client
  const id = env.VAPI_BRAIN.idFromName(clientId)
  const brain = env.VAPI_BRAIN.get(id)

  // Forward request to Durable Object
  return brain.fetch(request)
}

async function handleVapiWebhook(request: Request, env: Env): Promise<Response> {
  try {
    const body = await request.json() as any
    const messageType = body.message?.type

    console.log('[Webhook] VAPI event:', messageType)

    if (messageType === 'end-of-call-report') {
      await processEndOfCallReport(body.message, env)
    } else if (messageType === 'status-update') {
      console.log('[Webhook] Status update:', body.message.status)
    }

    return new Response(JSON.stringify({ received: true }), {
      headers: {
        'Content-Type': 'application/json',
        'Access-Control-Allow-Origin': '*'
      }
    })
  } catch (error: any) {
    console.error('[Webhook] Error:', error.message)
    return new Response(JSON.stringify({
      error: 'Webhook processing failed',
      message: error.message
    }), {
      status: 500,
      headers: { 'Content-Type': 'application/json' }
    })
  }
}

async function processEndOfCallReport(message: any, env: Env): Promise<void> {
  const call = message.call
  const clientId = extractClientIdFromCall(call)

  console.log(`[Webhook] Processing call ${call.id} for client ${clientId}`)

  // Insert call record
  await env.DB.prepare(`
    INSERT INTO vapi_calls (
      id, client_id, assistant_id, phone_number, caller_name,
      direction, started_at, ended_at, duration_seconds,
      status, cost_cents, recording_url
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
  `).bind(
    call.id,
    clientId,
    call.assistantId || 'unknown',
    call.customer?.number || null,
    call.customer?.name || null,
    call.type || 'inbound',
    call.startedAt,
    call.endedAt,
    call.duration || 0,
    call.status || 'completed',
    Math.round((call.cost || 0) * 100),
    call.recordingUrl || null
  ).run()

  // Insert transcript messages
  if (call.transcript && Array.isArray(call.transcript)) {
    for (const msg of call.transcript) {
      await env.DB.prepare(`
        INSERT INTO vapi_transcripts (id, call_id, role, content, timestamp)
        VALUES (?, ?, ?, ?, ?)
      `).bind(
        crypto.randomUUID(),
        call.id,
        msg.role,
        msg.message || msg.content || '',
        msg.time || msg.timestamp || new Date().toISOString()
      ).run()
    }
  }

  // Insert tool call logs
  if (call.messages && Array.isArray(call.messages)) {
    for (const msg of call.messages) {
      if (msg.toolCalls && Array.isArray(msg.toolCalls)) {
        for (const toolCall of msg.toolCalls) {
          await env.DB.prepare(`
            INSERT INTO vapi_tool_calls (
              id, call_id, client_id, tool_name, arguments,
              result, success, error, timestamp
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
          `).bind(
            crypto.randomUUID(),
            call.id,
            clientId,
            toolCall.function?.name || 'unknown',
            JSON.stringify(toolCall.function?.arguments || {}),
            JSON.stringify(toolCall.result || null),
            toolCall.error ? 0 : 1,
            toolCall.error || null,
            msg.time || new Date().toISOString()
          ).run()
        }
      }
    }
  }

  console.log(`[Webhook] Stored call ${call.id} with transcript and tool calls`)
}

function extractClientIdFromCall(call: any): string {
  // Extract client_id from MCP server URL in assistant config
  try {
    const tools = call.assistant?.tools || []
    for (const tool of tools) {
      if (tool.type === 'mcp' && tool.serverUrl) {
        const url = new URL(tool.serverUrl)
        const clientId = url.searchParams.get('client_id')
        if (clientId) return clientId
      }
    }
  } catch (e) {
    console.warn('Could not extract client_id from call:', e)
  }
  return 'default'
}

async function handleAdminClients(request: Request, env: Env): Promise<Response> {
  const url = new URL(request.url)

  try {
    if (request.method === 'GET') {
      // List all clients
      const result = await env.DB.prepare(`
        SELECT client_id, name, active, created_at
        FROM vapi_clients
        WHERE active = 1
        ORDER BY created_at DESC
      `).all()

      return new Response(JSON.stringify({
        clients: result.results,
        count: result.results?.length || 0
      }), {
        headers: {
          'Content-Type': 'application/json',
          'Access-Control-Allow-Origin': '*'
        }
      })
    }

    if (request.method === 'POST') {
      // Create new client
      const body = await request.json() as any

      if (!body.client_id || !body.name || !body.ghl_api_key || !body.ghl_location_id) {
        return new Response(JSON.stringify({
          error: 'Missing required fields',
          required: ['client_id', 'name', 'ghl_api_key', 'ghl_location_id']
        }), {
          status: 400,
          headers: { 'Content-Type': 'application/json' }
        })
      }

      await env.DB.prepare(`
        INSERT INTO vapi_clients (client_id, name, ghl_api_key, ghl_location_id, settings)
        VALUES (?, ?, ?, ?, ?)
      `).bind(
        body.client_id,
        body.name,
        body.ghl_api_key,
        body.ghl_location_id,
        JSON.stringify(body.settings || {})
      ).run()

      return new Response(JSON.stringify({
        success: true,
        client_id: body.client_id,
        mcp_url: `https://vapi-mcp-server.aijesusbro.workers.dev/mcp?client_id=${body.client_id}`
      }), {
        headers: {
          'Content-Type': 'application/json',
          'Access-Control-Allow-Origin': '*'
        }
      })
    }

    return new Response('Method not allowed', { status: 405 })
  } catch (error: any) {
    return new Response(JSON.stringify({
      error: 'Database error',
      message: error.message
    }), {
      status: 500,
      headers: { 'Content-Type': 'application/json' }
    })
  }
}

async function handleAdminCalls(request: Request, env: Env): Promise<Response> {
  const url = new URL(request.url)
  const clientId = url.searchParams.get('client_id')
  const limit = parseInt(url.searchParams.get('limit') || '50')

  try {
    let query = `
      SELECT id, client_id, phone_number, caller_name, direction,
             started_at, ended_at, duration_seconds, status, cost_cents
      FROM vapi_calls
    `

    const params: any[] = []

    if (clientId) {
      query += ' WHERE client_id = ?'
      params.push(clientId)
    }

    query += ' ORDER BY started_at DESC LIMIT ?'
    params.push(limit)

    const result = await env.DB.prepare(query).bind(...params).all()

    return new Response(JSON.stringify({
      calls: result.results,
      count: result.results?.length || 0
    }), {
      headers: {
        'Content-Type': 'application/json',
        'Access-Control-Allow-Origin': '*'
      }
    })
  } catch (error: any) {
    return new Response(JSON.stringify({
      error: 'Database error',
      message: error.message
    }), {
      status: 500,
      headers: { 'Content-Type': 'application/json' }
    })
  }
}
