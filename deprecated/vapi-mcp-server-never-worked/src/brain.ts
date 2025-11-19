// src/brain.ts
// Durable Object for per-client brain instances

interface Env {
  DB: D1Database
  VAPI_API_KEY: string
}

interface ClientConfig {
  client_id: string
  name: string
  ghl_api_key: string
  ghl_location_id: string
  settings: any
  active: number
}

export class VapiBrain {
  private state: DurableObjectState
  private env: Env
  private clientId: string = ''
  private clientConfig: ClientConfig | null = null

  constructor(state: DurableObjectState, env: Env) {
    this.state = state
    this.env = env
  }

  async fetch(request: Request): Promise<Response> {
    const url = new URL(request.url)
    this.clientId = url.searchParams.get('client_id') || 'default'

    console.log(`[Brain:${this.clientId}] Request: ${request.method} ${url.pathname}`)

    // Load client config if not cached
    if (!this.clientConfig) {
      try {
        await this.loadClientConfig()
      } catch (error: any) {
        return new Response(JSON.stringify({
          jsonrpc: '2.0',
          error: {
            code: -32000,
            message: `Client not configured: ${error.message}`
          }
        }), {
          status: 500,
          headers: { 'Content-Type': 'application/json' }
        })
      }
    }

    if (request.method === 'POST') {
      return this.handleMCPRequest(request)
    }

    if (request.method === 'GET') {
      return this.handleSSE(request)
    }

    return new Response('Method not allowed', { status: 405 })
  }

  async loadClientConfig(): Promise<void> {
    const result = await this.env.DB.prepare(`
      SELECT * FROM vapi_clients WHERE client_id = ? AND active = 1
    `).bind(this.clientId).first() as ClientConfig | null

    if (!result) {
      throw new Error(`Client ${this.clientId} not found or inactive`)
    }

    this.clientConfig = result
    console.log(`[Brain:${this.clientId}] Config loaded for: ${result.name}`)
  }

  async handleMCPRequest(request: Request): Promise<Response> {
    try {
      const body = await request.json() as any
      const callId = request.headers.get('X-Call-Id')

      console.log(`[Brain:${this.clientId}] MCP method: ${body.method}`, callId ? `Call: ${callId}` : '')

      if (body.method === 'tools/list') {
        return this.listTools(body.id)
      }

      if (body.method === 'tools/call') {
        return this.callTool(body.params, callId, body.id)
      }

      return new Response(JSON.stringify({
        jsonrpc: '2.0',
        id: body.id,
        error: {
          code: -32601,
          message: `Method not found: ${body.method}`
        }
      }), {
        status: 404,
        headers: { 'Content-Type': 'application/json' }
      })
    } catch (error: any) {
      console.error(`[Brain:${this.clientId}] Request error:`, error)
      return new Response(JSON.stringify({
        jsonrpc: '2.0',
        error: {
          code: -32700,
          message: `Parse error: ${error.message}`
        }
      }), {
        status: 400,
        headers: { 'Content-Type': 'application/json' }
      })
    }
  }

  async listTools(requestId: any): Promise<Response> {
    const tools = [
      {
        name: 'ghl_search_contact',
        description: 'Search for a contact in the CRM by phone number. Use this immediately when a call starts to identify the caller.',
        inputSchema: {
          type: 'object',
          properties: {
            phone: {
              type: 'string',
              description: 'Phone number (10 digits, no formatting): 5551234567'
            }
          },
          required: ['phone']
        }
      },
      {
        name: 'ghl_create_appointment',
        description: 'Book an appointment for a contact. Only use after confirming date and time with the caller.',
        inputSchema: {
          type: 'object',
          properties: {
            contactId: {
              type: 'string',
              description: 'GHL contact ID from ghl_search_contact result'
            },
            startTime: {
              type: 'string',
              description: 'ISO 8601 datetime with timezone: 2025-01-15T10:00:00-08:00'
            },
            title: {
              type: 'string',
              description: 'Appointment title/purpose (e.g., "Roof Inspection", "Follow-up Call")'
            }
          },
          required: ['contactId', 'startTime', 'title']
        }
      },
      {
        name: 'ghl_add_note',
        description: 'Add a note to a contact record in the CRM. Use to log important information from the call.',
        inputSchema: {
          type: 'object',
          properties: {
            contactId: {
              type: 'string',
              description: 'GHL contact ID'
            },
            note: {
              type: 'string',
              description: 'Note content (what was discussed, actions needed, etc.)'
            }
          },
          required: ['contactId', 'note']
        }
      },
      {
        name: 'ghl_get_calendar_slots',
        description: 'Check available calendar slots for booking. Calendar ID is already configured - no need to ask for it. Just call this when someone wants to schedule.',
        inputSchema: {
          type: 'object',
          properties: {
            start_date: {
              type: 'string',
              description: 'Start date for availability check (ISO 8601). Defaults to today if not provided.'
            },
            end_date: {
              type: 'string',
              description: 'End date for availability check (ISO 8601). Defaults to 7 days from start if not provided.'
            }
          },
          required: []
        }
      },
      {
        name: 'send_followup_sms',
        description: 'Send a follow-up SMS after the call. Use for confirmations, reminders, or sending links.',
        inputSchema: {
          type: 'object',
          properties: {
            phone: {
              type: 'string',
              description: 'Phone number to send SMS to'
            },
            message: {
              type: 'string',
              description: 'SMS message content (keep under 160 characters if possible)'
            }
          },
          required: ['phone', 'message']
        }
      }
    ]

    return new Response(JSON.stringify({
      jsonrpc: '2.0',
      id: requestId,
      result: { tools }
    }), {
      headers: {
        'Content-Type': 'application/json',
        'Access-Control-Allow-Origin': '*'
      }
    })
  }

  async callTool(params: any, callId: string | null, requestId: any): Promise<Response> {
    const startTime = Date.now()
    const { name, arguments: args } = params

    console.log(`[Brain:${this.clientId}] Calling tool: ${name}`, args)

    try {
      let result: any

      if (name === 'ghl_search_contact') {
        result = await this.searchGHLContact(args.phone)
      } else if (name === 'ghl_get_calendar_slots') {
        result = await this.ghl_get_calendar_slots(args)
      } else if (name === 'ghl_create_appointment') {
        result = await this.createGHLAppointment(args)
      } else if (name === 'ghl_add_note') {
        result = await this.addGHLNote(args)
      } else if (name === 'send_followup_sms') {
        result = await this.sendSMS(args)
      } else if (name === 'vapi_list_calls') {
        result = await this.vapi_list_calls(args)
      } else if (name === 'vapi_get_call') {
        result = await this.vapi_get_call(args)
      } else if (name === 'vapi_get_transcript') {
        result = await this.vapi_get_transcript(args)
      } else if (name === 'remember') {
        result = await this.remember(args)
      } else if (name === 'recall') {
        result = await this.recall(args)
      } else {
        throw new Error(`Unknown tool: ${name}`)
      }

      const executionTime = Date.now() - startTime

      // Log tool execution
      if (callId) {
        await this.logToolCall(callId, name, args, result, true, null, executionTime)
      }

      console.log(`[Brain:${this.clientId}] Tool ${name} completed in ${executionTime}ms`)

      return new Response(JSON.stringify({
        jsonrpc: '2.0',
        id: requestId,
        result: {
          content: [
            {
              type: 'text',
              text: JSON.stringify(result, null, 2)
            }
          ]
        }
      }), {
        headers: {
          'Content-Type': 'application/json',
          'Access-Control-Allow-Origin': '*'
        }
      })
    } catch (error: any) {
      const executionTime = Date.now() - startTime

      console.error(`[Brain:${this.clientId}] Tool ${name} failed:`, error.message)

      // Log error
      if (callId) {
        await this.logToolCall(callId, name, args, null, false, error.message, executionTime)
      }

      return new Response(JSON.stringify({
        jsonrpc: '2.0',
        id: requestId,
        error: {
          code: -32000,
          message: error.message,
          data: { tool: name, executionTime }
        }
      }), {
        status: 500,
        headers: {
          'Content-Type': 'application/json',
          'Access-Control-Allow-Origin': '*'
        }
      })
    }
  }

  async searchGHLContact(phone: string): Promise<any> {
    if (!this.clientConfig) throw new Error('Client config not loaded')

    const cleanPhone = phone.replace(/\D/g, '')

    console.log(`[Brain:${this.clientId}] Searching GHL for phone: ${cleanPhone}`)

    const response = await fetch(
      `https://rest.gohighlevel.com/v1/contacts/?locationId=${this.clientConfig.ghl_location_id}&query=${cleanPhone}`,
      {
        headers: {
          'Authorization': `Bearer ${this.clientConfig.ghl_api_key}`,
          'Version': '2021-07-28'
        }
      }
    )

    if (!response.ok) {
      throw new Error(`GHL API error: ${response.status} ${response.statusText}`)
    }

    const data = await response.json()

    if (data.contacts && data.contacts.length > 0) {
      const contact = data.contacts[0]
      return {
        found: true,
        id: contact.id,
        name: contact.name || 'Unknown',
        email: contact.email || null,
        phone: contact.phone,
        company: contact.companyName || null,
        tags: contact.tags || [],
        source: contact.source || null,
        lastContacted: contact.dateUpdated
      }
    }

    return {
      found: false,
      message: 'No contact found for this phone number. This may be a new caller.'
    }
  }

  async createGHLAppointment(args: any): Promise<any> {
    if (!this.clientConfig) throw new Error('Client config not loaded')

    console.log(`[Brain:${this.clientId}] Creating appointment for contact: ${args.contactId}`)

    const response = await fetch(
      'https://rest.gohighlevel.com/v1/appointments/',
      {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${this.clientConfig.ghl_api_key}`,
          'Content-Type': 'application/json',
          'Version': '2021-07-28'
        },
        body: JSON.stringify({
          contactId: args.contactId,
          startTime: args.startTime,
          title: args.title,
          appointmentStatus: 'confirmed'
        })
      }
    )

    if (!response.ok) {
      const errorText = await response.text()
      throw new Error(`Failed to create appointment: ${response.status} - ${errorText}`)
    }

    const appointment = await response.json()

    return {
      success: true,
      appointmentId: appointment.id,
      startTime: args.startTime,
      title: args.title,
      message: 'Appointment booked successfully'
    }
  }

  async addGHLNote(args: any): Promise<any> {
    if (!this.clientConfig) throw new Error('Client config not loaded')

    console.log(`[Brain:${this.clientId}] Adding note to contact: ${args.contactId}`)

    // GHL notes endpoint
    const response = await fetch(
      `https://rest.gohighlevel.com/v1/contacts/${args.contactId}/notes`,
      {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${this.clientConfig.ghl_api_key}`,
          'Content-Type': 'application/json',
          'Version': '2021-07-28'
        },
        body: JSON.stringify({
          body: args.note,
          userId: 'vapi-assistant'
        })
      }
    )

    if (!response.ok) {
      throw new Error(`Failed to add note: ${response.status}`)
    }

    return {
      success: true,
      message: 'Note added to contact'
    }
  }

  async sendSMS(args: any): Promise<any> {
    // TODO: Implement via Twilio, GHL SMS, or your SMS provider
    // For now, just return success (you can implement this later)
    console.log(`[Brain:${this.clientId}] SMS queued for ${args.phone}: ${args.message}`)

    return {
      success: true,
      message: 'SMS queued for delivery',
      phone: args.phone,
      preview: args.message.substring(0, 50)
    }
  }

  async ghl_get_calendar_slots(args: any): Promise<any> {
    if (!this.clientConfig) throw new Error('Client config not loaded')

    // Use provided calendar_id or default from client settings
    const settings = this.clientConfig.settings ? JSON.parse(this.clientConfig.settings as string) : {}
    const calendar_id = args.calendar_id || settings.default_calendar_id

    if (!calendar_id) {
      throw new Error('No calendar_id provided and no default_calendar_id in client settings')
    }

    const start_date = args.start_date || new Date().toISOString()
    const end_date = args.end_date || new Date(Date.now() + 7 * 24 * 60 * 60 * 1000).toISOString()

    console.log(`[Brain:${this.clientId}] Getting calendar slots for ${calendar_id}`)

    // GHL Calendar API endpoint
    const response = await fetch(
      `https://services.leadconnectorhq.com/calendars/${calendar_id}/free-slots?startDate=${encodeURIComponent(start_date)}&endDate=${encodeURIComponent(end_date)}`,
      {
        headers: {
          'Authorization': `Bearer ${this.clientConfig.ghl_api_key}`,
          'Version': '2021-04-15'
        }
      }
    )

    if (!response.ok) {
      // If calendar API fails, return Google Calendar link fallback
      console.error(`[Brain:${this.clientId}] Calendar API returned ${response.status}`)
      const responseText = await response.text()
      console.error(`[Brain:${this.clientId}] API Error:`, responseText)

      return {
        calendar_id,
        slots: [],
        error: `Unable to fetch calendar slots. Please use my booking link.`,
        booking_link: 'https://calendar.google.com/calendar/u/0/appointments/schedules/AcZssZ2FERmLVeQ5K3wBrKGU_V7mIRRKiPw_6sYlHgBQQJ0KvxUVfQBfCUn0aQCKSK3KeS_R9xV8QzU',
        total_slots: 0
      }
    }

    const data = await response.json()

    // Format slots for easy display
    const formattedSlots = (data.slots || []).map((slot: any) => {
      const date = new Date(slot.startTime)
      return {
        startTime: slot.startTime,
        endTime: slot.endTime,
        displayTime: date.toLocaleString('en-US', {
          weekday: 'long',
          month: 'short',
          day: 'numeric',
          hour: 'numeric',
          minute: '2-digit'
        })
      }
    })

    return {
      calendar_id,
      slots: formattedSlots,
      timezone: data.timezone || 'America/Los_Angeles',
      total_slots: formattedSlots.length
    }
  }

  async vapi_list_calls(args: any): Promise<any> {
    const limit = args.limit || 10
    const phone_number = args.phone_number

    console.log(`[Brain:${this.clientId}] Listing Vapi calls (limit: ${limit})`)

    try {
      let query = `
        SELECT id as call_id, phone_number, status, started_at, ended_at, duration_seconds, cost_cents as cost, ended_reason
        FROM vapi_calls
        WHERE client_id = ?
      `
      const bindings: any[] = [this.clientId]

      if (phone_number) {
        query += ' AND phone_number = ?'
        bindings.push(phone_number)
      }

      query += ' ORDER BY started_at DESC LIMIT ?'
      bindings.push(limit)

      const result = await this.env.DB.prepare(query).bind(...bindings).all()

      if (result.results.length === 0) {
        return {
          found: false,
          message: 'No calls found in the database.'
        }
      }

      const calls = result.results.map((call: any) => {
        const duration = call.duration_seconds
          ? `${Math.floor(call.duration_seconds / 60)}m ${call.duration_seconds % 60}s`
          : 'N/A'

        return {
          call_id: call.call_id,
          phone: call.phone_number,
          status: call.status,
          duration,
          started: new Date(call.started_at).toLocaleString(),
          ended_reason: call.ended_reason || 'N/A'
        }
      })

      return {
        found: true,
        count: calls.length,
        calls
      }
    } catch (error: any) {
      console.error(`[Brain:${this.clientId}] Error listing calls:`, error.message)
      throw error
    }
  }

  async vapi_get_call(args: any): Promise<any> {
    if (!args.call_id) {
      throw new Error('call_id is required')
    }

    console.log(`[Brain:${this.clientId}] Getting Vapi call: ${args.call_id}`)

    try {
      const call = await this.env.DB.prepare(
        'SELECT * FROM vapi_calls WHERE id = ? AND client_id = ?'
      ).bind(args.call_id, this.clientId).first()

      if (!call) {
        return {
          found: false,
          message: `Call ${args.call_id} not found`
        }
      }

      const duration = call.duration_seconds
        ? `${Math.floor(call.duration_seconds / 60)}m ${call.duration_seconds % 60}s`
        : 'N/A'

      return {
        found: true,
        call_id: call.id,
        phone: call.phone_number,
        status: call.status,
        duration,
        started: new Date(call.started_at).toLocaleString(),
        ended: call.ended_at ? new Date(call.ended_at).toLocaleString() : 'In progress',
        cost: `$${(call.cost_cents / 100).toFixed(2) || '0.00'}`,
        ended_reason: call.ended_reason || 'N/A',
        summary: call.summary || null
      }
    } catch (error: any) {
      console.error(`[Brain:${this.clientId}] Error getting call:`, error.message)
      throw error
    }
  }

  async vapi_get_transcript(args: any): Promise<any> {
    if (!args.call_id) {
      throw new Error('call_id is required')
    }

    console.log(`[Brain:${this.clientId}] Getting transcript for call: ${args.call_id}`)

    try {
      const transcript = await this.env.DB.prepare(
        'SELECT * FROM vapi_transcripts WHERE call_id = ? ORDER BY timestamp ASC'
      ).bind(args.call_id).all()

      if (transcript.results.length === 0) {
        return {
          found: false,
          message: `No transcript found for call ${args.call_id}`
        }
      }

      const messages = transcript.results.map((entry: any) => {
        return {
          time: new Date(entry.timestamp).toLocaleTimeString(),
          role: entry.role,
          text: entry.content
        }
      })

      return {
        found: true,
        call_id: args.call_id,
        message_count: messages.length,
        transcript: messages
      }
    } catch (error: any) {
      console.error(`[Brain:${this.clientId}] Error getting transcript:`, error.message)
      throw error
    }
  }

  async remember(args: any): Promise<any> {
    if (!args.key || !args.value) {
      throw new Error('key and value are required')
    }

    console.log(`[Brain:${this.clientId}] Storing memory: ${args.key}`)

    try {
      const metadata = args.metadata ? JSON.stringify(args.metadata) : '{}'

      // Check if key exists
      const existing = await this.env.DB.prepare(
        'SELECT id FROM vapi_client_memory WHERE client_id = ? AND key = ?'
      ).bind(this.clientId, args.key).first()

      if (existing) {
        // Update existing
        await this.env.DB.prepare(`
          UPDATE vapi_client_memory
          SET value = ?, metadata = ?, updated_at = datetime('now')
          WHERE client_id = ? AND key = ?
        `).bind(args.value, metadata, this.clientId, args.key).run()
      } else {
        // Insert new
        await this.env.DB.prepare(`
          INSERT INTO vapi_client_memory (id, client_id, key, value, metadata)
          VALUES (?, ?, ?, ?, ?)
        `).bind(
          crypto.randomUUID(),
          this.clientId,
          args.key,
          args.value,
          metadata
        ).run()
      }

      return {
        success: true,
        message: `Remembered: ${args.key} = ${args.value}`
      }
    } catch (error: any) {
      console.error(`[Brain:${this.clientId}] Error storing memory:`, error.message)
      throw error
    }
  }

  async recall(args: any): Promise<any> {
    if (!args.key) {
      throw new Error('key is required')
    }

    console.log(`[Brain:${this.clientId}] Recalling memory: ${args.key}`)

    try {
      const memory = await this.env.DB.prepare(
        'SELECT value, metadata, created_at FROM vapi_client_memory WHERE client_id = ? AND key = ?'
      ).bind(this.clientId, args.key).first()

      if (!memory) {
        return {
          found: false,
          message: `No memory found for key: ${args.key}`
        }
      }

      return {
        found: true,
        key: args.key,
        value: memory.value,
        metadata: memory.metadata !== '{}' ? JSON.parse(memory.metadata) : null,
        stored_on: new Date(memory.created_at).toLocaleString()
      }
    } catch (error: any) {
      console.error(`[Brain:${this.clientId}] Error recalling memory:`, error.message)
      throw error
    }
  }

  async logToolCall(
    callId: string,
    toolName: string,
    args: any,
    result: any,
    success: boolean,
    error: string | null,
    executionTimeMs: number
  ): Promise<void> {
    try {
      await this.env.DB.prepare(`
        INSERT INTO vapi_tool_calls (
          id, call_id, client_id, tool_name, arguments, result,
          success, error, execution_time_ms, timestamp
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
      `).bind(
        crypto.randomUUID(),
        callId,
        this.clientId,
        toolName,
        JSON.stringify(args),
        result ? JSON.stringify(result) : null,
        success ? 1 : 0,
        error,
        executionTimeMs,
        new Date().toISOString()
      ).run()
    } catch (e) {
      console.error(`[Brain:${this.clientId}] Failed to log tool call:`, e)
    }
  }

  async handleSSE(request: Request): Promise<Response> {
    // SSE stream for Streamable HTTP protocol
    const { readable, writable } = new TransformStream()
    const writer = writable.getWriter()
    const encoder = new TextEncoder()

    // Send initial connected message
    writer.write(encoder.encode(`data: {"type":"connected","clientId":"${this.clientId}"}\n\n`))

    // Keep-alive ping every 30 seconds
    const interval = setInterval(() => {
      try {
        writer.write(encoder.encode(': ping\n\n'))
      } catch {
        clearInterval(interval)
      }
    }, 30000)

    // Clean up on close
    request.signal.addEventListener('abort', () => {
      clearInterval(interval)
      writer.close()
    })

    return new Response(readable, {
      headers: {
        'Content-Type': 'text/event-stream',
        'Cache-Control': 'no-cache',
        'Connection': 'keep-alive',
        'Access-Control-Allow-Origin': '*'
      }
    })
  }
}
