# Voice Agent + MCP Architecture
## The Full Agentic Framework Integration

---

## The Big Picture: Where Information Flows

```
┌─────────────────────────────────────────────────────────────┐
│                    THE EXIT (Edge Workers)                   │
│  • Research, Strategy, Timing, Outreach agents               │
│  • Campaign orchestration                                    │
│  • Email/SMS sending via SendGrid/Twilio                    │
│  • D1 Database (leads, campaigns, conversations, events)    │
│  • Scheduler (DO alarms for future sends)                   │
└─────────────────────────────────────────────────────────────┘
                              ▲
                              │
                              │ MCP Protocol (tool calls)
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│              THE EXIT MCP SERVER (Local/Railway)             │
│  • Exposes RevOps OS API as MCP tools                        │
│  • Tools: create_campaign, add_leads, get_context, etc.     │
│  • Runs on your machine OR deployed to Railway              │
│  • Voice agents call these tools during conversations        │
└─────────────────────────────────────────────────────────────┘
                              ▲
                              │
                              │ MCP tool calls during live conversation
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                  RETELL VOICE AGENT                          │
│  • Answers inbound calls                                    │
│  • Books appointments (Calendly/Cal.com integration)         │
│  • Qualifies leads during conversation                      │
│  • Can call MCP tools to:                                   │
│    - Look up caller info (if they're a lead)                │
│    - Create new lead record                                 │
│    - Update lead status                                     │
│    - Book meeting and trigger email confirmation            │
│    - Start outreach campaign if qualified                   │
└─────────────────────────────────────────────────────────────┘
                              │
                              │ Webhook on call completion
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│         THE EXIT WEBHOOK HANDLER (Edge Worker)               │
│  • Receives Retell webhook: call_ended                      │
│  • Extracts: transcript, recording, sentiment, outcome      │
│  • Creates conversation record in D1                        │
│  • Emits event: voice_call_completed                        │
│  • Triggers next action (send email, schedule follow-up)    │
└─────────────────────────────────────────────────────────────┘
```

---

## Why MCP is Critical Here

### Without MCP:
- Voice agent gets call → qualifies lead → call ends → **data dies**
- You manually create lead in RevOps OS
- No connection between voice and email campaigns
- Agent can't check if caller is already in system
- **Totally disconnected systems**

### With MCP:
- Voice agent gets call → **calls `get_lead_by_phone` MCP tool** → sees full history
- Agent qualifies → **calls `update_lead_status` MCP tool** → marks as qualified
- Books meeting → **calls `book_appointment` MCP tool** → sends confirmation email
- Wants follow-up → **calls `start_campaign` MCP tool** → triggers email sequence
- **Fully integrated autonomous system**

---

## The EXIT MCP Server Architecture

### Location Options:

**Option 1: Local (Your Machine)**
- Runs on `http://localhost:3000`
- Only you can use it (development/testing)
- Fast for local testing
- **Use for:** Building and testing integration

**Option 2: Railway Deployment**
- Runs on `https://exit-mcp.railway.app`
- Publicly accessible (authenticated via API key)
- Retell voice agents can call it
- **Use for:** Production voice agent integration

**Option 3: Cloudflare Worker (Future)**
- MCP over HTTP directly on edge
- Ultra-low latency
- Same infrastructure as RevOps OS
- **Use when:** MCP-over-HTTP spec is finalized

---

## MCP Tools to Expose

### Core Lead Management

```typescript
// Look up lead by phone number
{
  name: "get_lead_by_phone",
  description: "Find lead record by phone number",
  parameters: {
    phone: "string" // E.164 format: +15551234567
  },
  returns: {
    lead: {
      id: "string",
      name: "string",
      email: "string",
      company: "string",
      status: "new|contacted|qualified|meeting_booked|closed",
      last_contact: "timestamp",
      campaign_id: "string",
      metadata: "object"
    }
  }
}

// Create new lead
{
  name: "create_lead",
  description: "Create new lead record",
  parameters: {
    name: "string",
    phone: "string",
    email: "string",
    company: "string",
    source: "string", // e.g., "inbound_call"
    metadata: "object"
  },
  returns: {
    lead_id: "string",
    created: true
  }
}

// Update lead status
{
  name: "update_lead_status",
  description: "Update lead qualification status",
  parameters: {
    lead_id: "string",
    status: "qualified|not_interested|meeting_booked|etc",
    notes: "string" // Agent's notes from conversation
  }
}
```

### Campaign Management

```typescript
// Start email campaign for a lead
{
  name: "start_campaign_for_lead",
  description: "Trigger email campaign after call qualification",
  parameters: {
    lead_id: "string",
    campaign_type: "follow_up|nurture|close",
    timing: "immediate|next_day|next_week"
  },
  returns: {
    campaign_id: "string",
    scheduled: true
  }
}

// Get campaign context (for personalized conversation)
{
  name: "get_campaign_context",
  description: "Get context about active campaigns for this lead",
  parameters: {
    lead_id: "string"
  },
  returns: {
    campaigns: [
      {
        id: "string",
        name: "string",
        last_email: "timestamp",
        reply_count: "number",
        status: "active|paused|completed"
      }
    ]
  }
}
```

### Appointment Booking

```typescript
// Book appointment and send confirmation
{
  name: "book_appointment",
  description: "Book meeting and trigger confirmation email",
  parameters: {
    lead_id: "string",
    datetime: "ISO8601",
    duration_minutes: "number",
    meeting_type: "demo|consultation|follow_up",
    calendar_link: "string" // Calendly/Cal.com event URL
  },
  returns: {
    appointment_id: "string",
    confirmation_sent: true
  }
}

// Get available time slots
{
  name: "get_available_slots",
  description: "Get your available calendar slots",
  parameters: {
    date: "YYYY-MM-DD",
    timezone: "string" // e.g., "America/Los_Angeles"
  },
  returns: {
    slots: [
      { time: "10:00", available: true },
      { time: "11:00", available: false },
      // ...
    ]
  }
}
```

### Conversation Logging

```typescript
// Log voice conversation
{
  name: "log_voice_call",
  description: "Store voice call details after call ends",
  parameters: {
    lead_id: "string",
    call_id: "string",
    duration_seconds: "number",
    transcript: "string",
    recording_url: "string",
    outcome: "qualified|not_interested|callback_requested|booked",
    sentiment: "positive|neutral|negative",
    notes: "string"
  }
}
```

---

## Retell Agent Configuration

### Voice Agent Prompt (The Brain)

```
You are a professional appointment setter for RevOps OS, an autonomous revenue
operations platform. Your goal is to qualify inbound leads and book demos.

PERSONALITY:
- Professional but conversational
- Confident without being pushy
- Genuinely curious about their business
- Technical enough to explain the platform

QUALIFICATION CRITERIA:
- Company size: $2-50M ARR or equivalent
- Current pain: Managing outbound manually OR using CRM they hate
- Decision maker: Founder, VP Sales, Revenue Ops leader
- Timeline: Looking to improve outbound in next 90 days

YOUR TOOLS (use during conversation):
- get_lead_by_phone: Check if caller is already in our system
- create_lead: Add new lead if first-time caller
- update_lead_status: Mark as qualified/not qualified
- book_appointment: Schedule demo with founder
- get_available_slots: Check calendar for meeting times

CONVERSATION FLOW:
1. Warm greeting + confirm who they are
2. Quick qualification (company size, role, pain point)
3. If qualified: Brief platform overview
4. Book demo if interested
5. If not ready: Offer to send info via email (trigger campaign)

BOOKING FLOW:
- Ask: "What does your calendar look like this week?"
- Use get_available_slots tool to check availability
- Propose 2-3 specific times
- Use book_appointment tool when they confirm
- Confirm: "Perfect, I'm sending a calendar invite to [email] right now"

HANDLING OBJECTIONS:
- "Too busy" → Offer async demo (send video + trigger campaign)
- "Not decision maker" → Get referral to right person
- "Need to think" → Offer to send case study (trigger nurture campaign)
- "Already have solution" → Ask what they don't like, position as complement

AFTER CALL:
- Always call update_lead_status with outcome
- If booked: call book_appointment
- If needs follow-up: call start_campaign_for_lead
```

### Retell Agent Config (JSON)

```json
{
  "agent_name": "RevOps OS - Inbound Qualifier",
  "voice_id": "professional_male_v2",
  "language": "en-US",
  "llm_config": {
    "model": "claude-3-5-sonnet",
    "temperature": 0.7,
    "max_tokens": 500
  },
  "tools": [
    {
      "type": "mcp",
      "server_url": "https://exit-mcp.railway.app",
      "api_key": "${EXIT_MCP_API_KEY}",
      "available_tools": [
        "get_lead_by_phone",
        "create_lead",
        "update_lead_status",
        "book_appointment",
        "get_available_slots",
        "start_campaign_for_lead"
      ]
    },
    {
      "type": "calendly",
      "api_key": "${CALENDLY_API_KEY}",
      "event_type": "30min-demo"
    }
  ],
  "webhook_url": "https://revopsOS-dev.aijesusbro-brain.workers.dev/api/webhooks/retell",
  "recording_enabled": true,
  "transcription_enabled": true
}
```

---

## The Full Call Flow (Step by Step)

### Inbound Call Received

```
1. Prospect dials your number
2. Retell routes to voice agent
3. Agent: "Hi, this is Alex with RevOps OS. Who am I speaking with?"
4. Caller: "This is John from Acme Corp"
```

### MCP Tool Call #1: Check If Lead Exists

```
Agent internally calls:
  get_lead_by_phone(phone="+15551234567")

Response:
  {
    "lead": {
      "id": "lead_abc123",
      "name": "John Doe",
      "company": "Acme Corp",
      "status": "contacted",
      "last_contact": 1234567890,
      "campaign_id": "campaign_xyz"
    }
  }

Agent now knows:
  - John is already in system
  - We contacted him via email campaign
  - He's responding to outreach (warm lead!)
```

### Agent Adjusts Approach

```
Agent: "Great to hear from you, John! I see we reached out recently
about autonomous outreach. What prompted you to call in?"

[Agent uses context from campaign to personalize conversation]
```

### Qualification Conversation

```
Agent: "Tell me a bit about your current outbound process..."
John: "We have 2 BDRs but struggling to scale..."
Agent: "Got it. What size is your team?"
John: "About $5M ARR, 25 employees"
[QUALIFIED - meets criteria]
```

### MCP Tool Call #2: Update Status

```
Agent internally calls:
  update_lead_status(
    lead_id="lead_abc123",
    status="qualified",
    notes="$5M ARR, 2 BDRs, wants to scale outbound. Warm and engaged."
  )
```

### Booking Flow

```
Agent: "I'd love to show you how we replace BDR teams with autonomous
agents. What does your calendar look like this week?"

Agent internally calls:
  get_available_slots(
    date="2025-10-10",
    timezone="America/Los_Angeles"
  )

Response:
  {
    "slots": [
      { "time": "10:00", "available": true },
      { "time": "14:00", "available": true }
    ]
  }

Agent: "I have Thursday at 10am or 2pm Pacific. Which works better?"
John: "10am works great"
```

### MCP Tool Call #3: Book Appointment

```
Agent internally calls:
  book_appointment(
    lead_id="lead_abc123",
    datetime="2025-10-10T10:00:00-07:00",
    duration_minutes=30,
    meeting_type="demo",
    calendar_link="https://cal.com/aijesusbro/demo"
  )

RevOps OS receives this tool call and:
  1. Creates appointment record in D1
  2. Sends calendar invite to john@acmecorp.com
  3. Sends confirmation email with prep questions
  4. Emits event: appointment_booked
  5. Updates lead status to "meeting_booked"
```

### Agent Confirms

```
Agent: "Perfect! I just sent a calendar invite to your email.
You should see it for Thursday, October 10th at 10am Pacific.
We'll show you exactly how the system works with your target market.
Sound good?"

John: "Sounds great, thanks!"
Agent: "Looking forward to it. Have a great day!"
```

### Call Ends - Webhook Fires

```
Retell sends webhook to:
  POST https://revopsOS-dev.aijesusbro-brain.workers.dev/api/webhooks/retell

Payload:
  {
    "call_id": "call_xyz789",
    "from": "+15551234567",
    "duration": 245,
    "transcript": "[full conversation transcript]",
    "recording_url": "https://retell-recordings.s3...",
    "custom_data": {
      "lead_id": "lead_abc123",
      "outcome": "qualified_and_booked"
    }
  }

RevOps OS webhook handler:
  1. Creates conversation record with transcript
  2. Emits event: voice_call_completed
  3. Updates lead timeline
  4. Triggers follow-up campaign (send prep email day before meeting)
```

---

## Implementation Plan

### Phase 1: Build MCP Server (Week 1)

**File:** `/mcp-servers/revopsOS/index.js`

```javascript
import { Server } from '@modelcontextprotocol/sdk/server/index.js';
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js';

const EXIT_API_URL = process.env.EXIT_API_URL || 'https://revopsOS-dev.aijesusbro-brain.workers.dev';
const EXIT_API_KEY = process.env.EXIT_API_KEY;

const server = new Server({
  name: 'revopsOS-mcp',
  version: '1.0.0',
}, {
  capabilities: {
    tools: {}
  }
});

// Tool: get_lead_by_phone
server.setRequestHandler('tools/call', async (request) => {
  if (request.params.name === 'get_lead_by_phone') {
    const { phone } = request.params.arguments;

    const response = await fetch(`${EXIT_API_URL}/api/leads/search?phone=${phone}`, {
      headers: { 'Authorization': `Bearer ${EXIT_API_KEY}` }
    });

    const data = await response.json();
    return { content: [{ type: 'text', text: JSON.stringify(data) }] };
  }

  // ... other tools
});

// Start server
const transport = new StdioServerTransport();
await server.connect(transport);
```

**Deploy to Railway:**
```bash
cd mcp-servers/revopsOS
railway init
railway up
# Get public URL: https://exit-mcp.railway.app
```

### Phase 2: Build Retell Agent (Week 1)

1. **Create Retell account** → Get API key
2. **Create agent** with prompt above
3. **Configure MCP integration:**
   - Point to Railway MCP server
   - Add EXIT_API_KEY for auth
4. **Test with test call:**
   - Call test number
   - Verify tools are callable
   - Check webhook fires

### Phase 3: Build Webhook Handler (Week 1)

**File:** `/workers/webhooks/retell.js`

```javascript
export async function handleRetellWebhook(request, env) {
  const payload = await request.json();

  const { call_id, from, transcript, recording_url, custom_data } = payload;

  // Create conversation record
  await env.DB.prepare(`
    INSERT INTO conversations (
      id, lead_id, channel, messages,
      status, metadata, created_at
    ) VALUES (?, ?, ?, ?, ?, ?, ?)
  `).bind(
    generateId(),
    custom_data.lead_id,
    'voice',
    JSON.stringify([{
      type: 'voice_call',
      call_id,
      transcript,
      recording_url,
      duration: payload.duration
    }]),
    'active',
    JSON.stringify({ outcome: custom_data.outcome }),
    Date.now()
  ).run();

  // Emit event
  await emitEvent(env.DB, {
    trace_id: generateTraceId(),
    account_id: custom_data.account_id,
    event_type: 'voice_call_completed',
    entity_type: 'lead',
    entity_id: custom_data.lead_id,
    payload: {
      call_id,
      duration: payload.duration,
      outcome: custom_data.outcome
    }
  });

  return new Response(JSON.stringify({ success: true }), {
    headers: { 'Content-Type': 'application/json' }
  });
}
```

---

## The META Part: Voice Agent Sells Voice Agent

**Once this is built:**

Your outreach emails say:
> *"Want to see it work? Call this number: +1 (555) 123-4567"*
>
> *The AI will qualify you, answer questions, and book a demo. That's the system you're buying.*

**That's the ultimate meta proof.**

- They call expecting a demo
- They GET the demo during the call
- The voice agent books the actual demo meeting
- Email confirmation comes automatically
- **They've experienced the full autonomous flow**

---

## Next Steps (Prioritized)

1. **Add SendGrid key** (5 mins) ← Do this now
2. **Build MCP server** (4 hours)
3. **Deploy MCP to Railway** (30 mins)
4. **Create Retell agent** (1 hour)
5. **Build webhook handler** (2 hours)
6. **Test full flow** (2 hours)
7. **Add phone number to outreach emails** (5 mins)

**Total time:** ~2 days to full voice integration

Then you have:
- Email campaigns that actually send
- Voice agent that qualifies and books
- Full MCP integration
- **The system proving the system**

Ready to build the MCP server?
