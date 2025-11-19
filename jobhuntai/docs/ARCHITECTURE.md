# JobHunt AI - System Architecture

**Version:** 1.0
**Last Updated:** October 10, 2025
**Status:** Production-Ready

---

## Table of Contents

1. [System Overview](#system-overview)
2. [Architecture Diagram](#architecture-diagram)
3. [Component Stack](#component-stack)
4. [Voice Agent Flow](#voice-agent-flow)
5. [MCP Integration](#mcp-integration)
6. [Database Schema](#database-schema)
7. [Deployment Architecture](#deployment-architecture)
8. [Security & Authentication](#security--authentication)
9. [Monitoring & Observability](#monitoring--observability)
10. [Scaling Considerations](#scaling-considerations)

---

## System Overview

JobHunt AI is an **MCP-native autonomous revenue operations platform** designed to replace traditional BDR teams through AI-powered voice agents and intelligent workflow automation.

### Core Capabilities

- **Voice Agent Qualification:** Inbound call handling with caller ID, qualification, and booking
- **MCP Tool Integration:** Real-time database interaction during live conversations
- **Calendar Integration:** Direct Cal.com API booking with automated invites
- **Campaign Management:** Multi-campaign lead tracking and progression
- **Event Tracking:** Comprehensive audit trail of all interactions

### Key Differentiators

- MCP-first architecture (agents call any API as tools)
- Multi-state conversation flows (not single-prompt agents)
- Edge-native deployment (Cloudflare Workers + D1)
- Real-time tool calling during voice conversations
- Persistent organizational memory across all interactions

---

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                         CLIENT LAYER                            │
└─────────────────────────────────────────────────────────────────┘
                                 │
                    ┌────────────┴────────────┐
                    │                         │
            ┌───────▼───────┐         ┌──────▼──────┐
            │  Phone Calls  │         │  Dashboard  │
            │   (Retell)    │         │  (React)    │
            └───────┬───────┘         └──────┬──────┘
                    │                         │
┌───────────────────┴─────────────────────────┴───────────────────┐
│                      CLOUDFLARE EDGE                             │
│  ┌────────────────────────────────────────────────────────┐     │
│  │           Workers (MCP Server + API)                   │     │
│  │  - MCP Tool Endpoints                                  │     │
│  │  - REST API                                            │     │
│  │  - Webhook Handlers                                    │     │
│  │  - Authentication                                      │     │
│  └────────────┬───────────────────┬───────────────────────┘     │
│               │                   │                             │
│      ┌────────▼────────┐   ┌─────▼──────┐                      │
│      │   D1 Database   │   │ Vectorize  │                      │
│      │   (SQLite)      │   │  (Future)  │                      │
│      └─────────────────┘   └────────────┘                      │
└──────────────────────────────────────────────────────────────────┘
                    │                         │
         ┌──────────┴──────────┐   ┌─────────▼─────────┐
         │   Retell AI API     │   │   Cal.com API     │
         │   - LLM Config      │   │   - Bookings      │
         │   - Agent Control   │   │   - Invites       │
         │   - Call Analytics  │   │   - Event Types   │
         └─────────────────────┘   └───────────────────┘
```

---

## Component Stack

### Frontend (Dashboard)
- **Framework:** React + Vite
- **Deployment:** Cloudflare Pages
- **URL:** https://aijesusbro.com/crm
- **Features:**
  - Campaign management UI
  - Lead tracking
  - Analytics dashboard
  - System configuration

### Backend (MCP Server + API)
- **Runtime:** Cloudflare Workers
- **Language:** JavaScript
- **Entry Point:** `workers/mcp-server.js`
- **Deployment:**
  - Dev: `jobhunt-ai-dev.aijesusbro-brain.workers.dev`
  - MCP: `jobhunt-ai-mcp-dev.aijesusbro-brain.workers.dev`

### Database
- **Type:** Cloudflare D1 (SQLite at edge)
- **Name:** `jobhunt-ai-dev`
- **Schema:** See [Database Schema](#database-schema)
- **Backups:** Automatic (Cloudflare managed)

### Voice Agent (Retell AI)
- **LLM ID:** `llm_ccbc353b3b7340be2be926d64dfe`
- **Agent ID:** `agent_589dbbbf5c860b1336bade6684`
- **Model:** GPT-4o (temperature: 0.3)
- **Voice:** 11labs-Adrian
- **Architecture:** Multi-state (qualification → booking)

### Calendar Integration
- **Provider:** Cal.com
- **API Key:** `cal_live_74b37896967e5c4cc1955b62095e7fec`
- **Features:**
  - Real-time availability checking
  - Automated booking creation
  - Email invites with calendar files
  - Meeting metadata tracking

---

## Voice Agent Flow

### State Machine Architecture

```
┌─────────────────────────────────────────────────────────┐
│                  QUALIFICATION STATE                     │
│                                                          │
│  Tools Available:                                        │
│  - get_lead_by_phone (caller ID lookup)                │
│  - create_lead (record creation)                        │
│  - update_lead_status (mark qualified/unqualified)      │
│  - end_call (graceful termination)                      │
│                                                          │
│  Process:                                                │
│  1. Greet caller                                         │
│  2. Check if returning (get_lead_by_phone)              │
│  3. Gather: name, company, revenue, sales process       │
│  4. Create lead record (create_lead)                    │
│  5. Apply qualification logic                           │
│                                                          │
│  Decision:                                               │
│  ┌─────────────────────┬─────────────────────┐         │
│  │   QUALIFIED         │    NOT QUALIFIED    │         │
│  │   (B2B, $1M+,       │   (B2C, pre-rev,    │         │
│  │    outbound, CRM)   │    no outbound)     │         │
│  └──────────┬──────────┴──────────┬──────────┘         │
│             │                     │                     │
│             ▼                     ▼                     │
│      ┌─────────────┐      ┌─────────────┐              │
│      │ TRANSITION  │      │  END CALL   │              │
│      │ TO BOOKING  │      │  (politely) │              │
│      └──────┬──────┘      └─────────────┘              │
│             │                                            │
└─────────────┼────────────────────────────────────────────┘
              │
              │ Edge Parameters:
              │ - user_name
              │ - user_email
              │ - company
              │ - phone
              │ - lead_id
              │ - qualification_notes
              │
              ▼
┌─────────────────────────────────────────────────────────┐
│                    BOOKING STATE                         │
│                                                          │
│  Dynamic Variables Inherited:                            │
│  - {{user_name}}                                         │
│  - {{user_email}}                                        │
│  - {{company}}                                           │
│  - {{lead_id}}                                           │
│  - {{qualification_notes}}                               │
│                                                          │
│  Tools Available:                                        │
│  - book_appointment (Cal.com + database)                │
│  - update_lead_status (mark as qualified)               │
│  - end_call (after booking complete)                    │
│                                                          │
│  Process:                                                │
│  1. Ask about calendar availability                     │
│  2. Gather preferred time (natural language)            │
│  3. Confirm date/time explicitly                        │
│  4. Convert to ISO 8601 format                          │
│  5. Call book_appointment tool                          │
│  6. Confirm booking with calendar URL                   │
│  7. Update lead status to "qualified"                   │
│  8. End call gracefully                                 │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

### Conversation Example

**Caller:** "Hi, I'm calling about JobHunt AI"

**Agent:** [Immediately calls `get_lead_by_phone`]
"Hey there! Thanks for calling JobHunt AI. I'm the AI qualification agent. What brought you to reach out today?"

**Caller:** "I saw a demo and I'm interested"

**Agent:** "Awesome. Before I dive in - what kind of business are you with?"

**Caller:** "We're a B2B SaaS company doing about $5M ARR"

**Agent:** "Great! How are you currently handling outbound sales?"

**Caller:** "We have a 3-person BDR team using HubSpot"

**Agent:** [Calls `create_lead` with collected info]
"And what made you interested in JobHunt AI specifically?"

**Caller:** "We're spending too much on headcount and want to scale"

**Agent:** [Determines QUALIFIED]
"This sounds like a great fit. The best next step is to get you on the calendar for a 30-minute discovery call."
[Transitions to BOOKING state with edge parameters]

**Agent:** "Perfect! Let me get you on the calendar. What does your schedule look like this week?"

**Caller:** "How about tomorrow at 2 PM?"

**Agent:** "Just to confirm, that's Thursday, October 11th at 2 PM Pacific, correct?"

**Caller:** "Yes, that works"

**Agent:** [Calls `book_appointment` with ISO 8601 time]
"Perfect! I've got you booked for Thursday at 2 PM. You'll get a calendar invite at your email. Looking forward to it!"
[Calls `update_lead_status` with qualified]
"Thanks for calling! Talk to you Thursday!"
[Calls `end_call`]

---

## MCP Integration

### What is MCP?

**Model Context Protocol** (MCP) is a standardized way for AI agents to use external tools via HTTP. Instead of hard-coding function calls, MCP provides:

- **Tool Discovery:** Agents query available tools at runtime
- **Dynamic Schema:** Tool parameters defined via JSON Schema
- **Tool Execution:** POST requests to call tools with arguments
- **Response Handling:** Structured JSON responses back to agent

### MCP Server Implementation

**Location:** `workers/mcp-server.js`
**Base URL:** `https://jobhunt-ai-mcp-dev.aijesusbro-brain.workers.dev`

**Endpoints:**

```javascript
// MCP Discovery
GET /mcp
→ Returns available tools and their schemas

// Tool Execution
POST /mcp/call-tool
Body: {
  "name": "create_lead",
  "arguments": {
    "phone": "+14155551234",
    "name": "John Doe",
    "email": "john@example.com"
  }
}
→ Executes tool and returns result
```

### Available Tools

#### 1. get_lead_by_phone
**Purpose:** Caller ID lookup for returning customers

**Arguments:**
```json
{
  "phone": "+14155551234"
}
```

**Returns:**
```json
{
  "found": true,
  "lead": {
    "id": "lead_123",
    "name": "John Doe",
    "email": "john@example.com",
    "company": "Acme Inc",
    "status": "new"
  },
  "campaign": {
    "name": "Inbound Q4 2025",
    "stage": "qualification"
  },
  "recent_events": [
    {
      "type": "call_received",
      "timestamp": "2025-10-09T10:30:00Z"
    }
  ]
}
```

#### 2. create_lead
**Purpose:** Create new lead record

**Arguments:**
```json
{
  "phone": "+14155551234",
  "name": "John Doe",
  "email": "john@example.com",
  "company": "Acme Inc",
  "source": "inbound_call"
}
```

**Returns:**
```json
{
  "success": true,
  "lead_id": "lead_456",
  "message": "Lead created successfully"
}
```

#### 3. update_lead_status
**Purpose:** Update qualification status

**Arguments:**
```json
{
  "lead_id": "lead_456",
  "status": "qualified",
  "notes": "B2B SaaS, $5M ARR, 3-person BDR team"
}
```

**Returns:**
```json
{
  "success": true,
  "message": "Lead status updated to qualified"
}
```

#### 4. book_appointment
**Purpose:** Schedule discovery call (Cal.com + database)

**Arguments:**
```json
{
  "lead_id": "lead_456",
  "scheduled_at": "2025-10-11T14:00:00-08:00",
  "duration_minutes": 30,
  "meeting_type": "Discovery Call",
  "notes": "Interested in BDR replacement"
}
```

**Returns:**
```json
{
  "success": true,
  "appointment": {
    "id": "appt_789",
    "scheduled_at": "2025-10-11T14:00:00-08:00",
    "duration_minutes": 30
  },
  "calendar_url": "https://cal.com/booking/abc123",
  "calendar_integrated": true,
  "message": "Appointment booked for Oct 11 at 2:00 PM - Calendar invite sent!"
}
```

#### 5. get_campaign_context
**Purpose:** Retrieve campaign information

**Arguments:**
```json
{
  "lead_id": "lead_456"
}
```

**Returns:**
```json
{
  "campaign": {
    "id": "camp_123",
    "name": "Inbound Q4 2025",
    "stage": "qualification",
    "created_at": "2025-10-01T00:00:00Z"
  }
}
```

### Tool Calling Flow

```
┌──────────────┐
│ Retell Agent │ (during live call)
└──────┬───────┘
       │
       │ 1. Agent decides to call tool
       │    (based on prompt instructions)
       │
       ▼
┌──────────────────────────────────────────┐
│ POST /mcp/call-tool                      │
│ {                                        │
│   "name": "create_lead",                 │
│   "arguments": {                         │
│     "phone": "+14155551234",             │
│     "name": "John Doe"                   │
│   }                                      │
│ }                                        │
└──────┬───────────────────────────────────┘
       │
       │ 2. MCP server authenticates request
       │    (checks Authorization header)
       │
       ▼
┌──────────────────────────────────────────┐
│ Workers MCP Handler                      │
│ - Validates arguments against schema     │
│ - Calls database API                     │
│ - Formats response                       │
└──────┬───────────────────────────────────┘
       │
       │ 3. Database operation
       │
       ▼
┌──────────────────────────────────────────┐
│ D1 Database                              │
│ INSERT INTO leads ...                    │
└──────┬───────────────────────────────────┘
       │
       │ 4. Success response
       │
       ▼
┌──────────────────────────────────────────┐
│ Returns to Agent                         │
│ {                                        │
│   "success": true,                       │
│   "lead_id": "lead_456"                  │
│ }                                        │
└──────────────────────────────────────────┘
```

---

## Database Schema

### Tables

#### leads
```sql
CREATE TABLE leads (
  id TEXT PRIMARY KEY,
  campaign_id TEXT,
  phone TEXT,
  email TEXT,
  name TEXT,
  company TEXT,
  status TEXT DEFAULT 'new',  -- new, qualified, unqualified, contacted, nurturing
  source TEXT,  -- inbound_call, outbound_call, manual, import
  metadata TEXT,  -- JSON blob
  created_at INTEGER DEFAULT (strftime('%s', 'now')),
  updated_at INTEGER DEFAULT (strftime('%s', 'now'))
);
```

#### campaigns
```sql
CREATE TABLE campaigns (
  id TEXT PRIMARY KEY,
  name TEXT NOT NULL,
  type TEXT DEFAULT 'outbound',  -- outbound, inbound, nurture
  status TEXT DEFAULT 'active',  -- active, paused, completed
  config TEXT,  -- JSON blob with campaign settings
  created_at INTEGER DEFAULT (strftime('%s', 'now')),
  updated_at INTEGER DEFAULT (strftime('%s', 'now'))
);
```

#### appointments
```sql
CREATE TABLE appointments (
  id TEXT PRIMARY KEY,
  lead_id TEXT NOT NULL,
  scheduled_at TEXT NOT NULL,  -- ISO 8601
  duration_minutes INTEGER DEFAULT 30,
  meeting_type TEXT,
  status TEXT DEFAULT 'scheduled',  -- scheduled, completed, cancelled, no_show
  calendar_url TEXT,
  notes TEXT,
  source TEXT DEFAULT 'voice_agent',
  created_at INTEGER DEFAULT (strftime('%s', 'now')),
  updated_at INTEGER DEFAULT (strftime('%s', 'now')),
  FOREIGN KEY (lead_id) REFERENCES leads(id)
);
```

#### events
```sql
CREATE TABLE events (
  id TEXT PRIMARY KEY,
  lead_id TEXT,
  campaign_id TEXT,
  type TEXT NOT NULL,  -- call_received, email_sent, appointment_booked, etc.
  data TEXT,  -- JSON blob
  timestamp INTEGER DEFAULT (strftime('%s', 'now')),
  FOREIGN KEY (lead_id) REFERENCES leads(id),
  FOREIGN KEY (campaign_id) REFERENCES campaigns(id)
);
```

### Indexes

```sql
CREATE INDEX idx_leads_phone ON leads(phone);
CREATE INDEX idx_leads_email ON leads(email);
CREATE INDEX idx_leads_campaign ON leads(campaign_id);
CREATE INDEX idx_leads_status ON leads(status);
CREATE INDEX idx_events_lead ON events(lead_id);
CREATE INDEX idx_events_campaign ON events(campaign_id);
CREATE INDEX idx_events_type ON events(type);
CREATE INDEX idx_appointments_lead ON appointments(lead_id);
CREATE INDEX idx_appointments_scheduled ON appointments(scheduled_at);
```

---

## Deployment Architecture

### Cloudflare Workers Deployment

**Configuration:** `wrangler.toml`

```toml
name = "jobhunt-ai"
main = "workers/mcp-server.js"
compatibility_date = "2025-01-01"

[env.dev]
name = "jobhunt-ai-dev"
vars = { ENVIRONMENT = "development" }

[[env.dev.d1_databases]]
binding = "DB"
database_name = "jobhunt-ai-dev"
database_id = "your-database-id"

[env.mcp-dev]
name = "jobhunt-ai-mcp-dev"
vars = { ENVIRONMENT = "development" }
routes = []
workers_dev = true

[[env.mcp-dev.d1_databases]]
binding = "DB"
database_name = "jobhunt-ai-dev"
database_id = "your-database-id"
```

**Deployment Commands:**

```bash
# Deploy main API
npx wrangler deploy --env dev

# Deploy MCP server
npx wrangler deploy --env mcp-dev

# Check status
npx wrangler deployments list

# View logs
npx wrangler tail --env dev --format pretty
```

### Frontend Deployment (Cloudflare Pages)

**Build Command:** `npm run build`
**Output Directory:** `dist`
**Deployment:** Automatic via git push

```bash
# Manual deployment
npx wrangler pages deploy dist --project-name=aijesusbro-brain
```

### Environment Variables

**Secrets (encrypted):**
```bash
# Retell API
wrangler secret put RETELL_API_KEY --env dev

# Cal.com API
wrangler secret put CALCOM_API_KEY --env dev

# Auth tokens
wrangler secret put API_TOKEN --env dev
```

**Public vars (in wrangler.toml):**
```toml
vars = {
  ENVIRONMENT = "development",
  MCP_SERVER_URL = "https://jobhunt-ai-mcp-dev.aijesusbro-brain.workers.dev"
}
```

---

## Security & Authentication

### API Authentication

**Method:** Bearer token authentication

**Headers Required:**
```http
Authorization: Bearer aijesusbro-dev-secret-2025
Content-Type: application/json
```

**Implementation:**
```javascript
async function authenticate(request) {
  const authHeader = request.headers.get('Authorization');
  if (!authHeader || !authHeader.startsWith('Bearer ')) {
    return new Response('Unauthorized', { status: 401 });
  }

  const token = authHeader.substring(7);
  if (token !== env.API_TOKEN) {
    return new Response('Forbidden', { status: 403 });
  }

  return null; // Authenticated
}
```

### Retell Webhook Signature Verification

**Purpose:** Verify webhooks are from Retell, not spoofed

**Implementation:**
```javascript
function verifyRetellSignature(body, signature, secret) {
  const hmac = crypto.createHmac('sha256', secret);
  const digest = hmac.update(body).digest('hex');
  return digest === signature;
}

// In webhook handler
const signature = request.headers.get('x-retell-signature');
const body = await request.text();
if (!verifyRetellSignature(body, signature, env.RETELL_WEBHOOK_SECRET)) {
  return new Response('Invalid signature', { status: 401 });
}
```

### Cal.com API Security

**Method:** API key in Authorization header

```javascript
const calcomResponse = await fetch('https://api.cal.com/v1/bookings', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${env.CALCOM_API_KEY}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify(bookingData)
});
```

### Data Privacy

- **PII Handling:** `opt_out_sensitive_data_storage: false` (we control data)
- **Call Recordings:** Stored in Retell with signed URLs
- **Database:** Edge-native (regional compliance)
- **GDPR:** Right to be forgotten via lead deletion API

---

## Monitoring & Observability

### Logs

**Cloudflare Workers Logs:**
```bash
# Real-time tail
npx wrangler tail --env dev --format pretty

# Filter by status
npx wrangler tail --env dev --status error

# Search in dashboard
https://dash.cloudflare.com → Workers → jobhunt-ai-dev → Logs
```

**Retell Call Logs:**
```bash
# List calls
curl "https://api.retellai.com/list-calls?agent_id=agent_589dbbbf5c860b1336bade6684" \
  -H "Authorization: Bearer $RETELL_API_KEY"

# Get call details
curl "https://api.retellai.com/get-call/{call_id}" \
  -H "Authorization: Bearer $RETELL_API_KEY"
```

### Metrics

**Key Metrics to Track:**

1. **Call Metrics:**
   - Total calls received
   - Average call duration
   - Qualification rate (qualified/total)
   - Booking rate (booked/qualified)
   - Tool call success rate

2. **Lead Metrics:**
   - New leads created per day
   - Lead status distribution
   - Time to qualification
   - Conversion rate

3. **Appointment Metrics:**
   - Appointments booked per day
   - Show rate vs no-show
   - Calendar integration success rate
   - Average time to booking

4. **System Health:**
   - API response times
   - Database query performance
   - MCP tool call latency
   - Error rates by endpoint

### Alerts

**Setup Cloudflare Alerts:**

1. **Error Rate Alert:**
   - Trigger: >5% error rate in 5 minutes
   - Action: Email notification

2. **Latency Alert:**
   - Trigger: P95 latency >1000ms
   - Action: Slack notification

3. **Database Alert:**
   - Trigger: D1 query errors
   - Action: Email + Slack

---

## Scaling Considerations

### Current Limits

- **D1 Database:** 500MB free tier, 25M row reads/day
- **Workers:** 100,000 requests/day (free tier)
- **Pages:** Unlimited bandwidth
- **Retell:** Pay-per-minute ($0.09/min for 11labs voice)

### Scaling Strategy

**Phase 1 (Current): Single Region**
- Cloudflare edge (global)
- D1 in single region
- Handles ~1000 calls/month

**Phase 2 (Next 6 Months): Multi-Campaign**
- Multiple concurrent campaigns
- Campaign-specific routing
- Durable Objects for state
- Upgrade to D1 paid tier

**Phase 3 (12+ Months): Multi-Tenant**
- Separate D1 per customer
- Customer-specific MCP servers
- White-label deployments
- Usage-based pricing

### Performance Optimizations

1. **Database:**
   - Add indexes on frequently queried columns
   - Denormalize for common queries
   - Use prepared statements
   - Consider D1 replicas for reads

2. **API:**
   - Cache static responses
   - Batch database operations
   - Use Cloudflare Cache API
   - Implement request coalescing

3. **Voice Agent:**
   - Reduce prompt size for faster processing
   - Cache common responses
   - Optimize tool schemas
   - Use streaming for long responses

---

## Conclusion

JobHunt AI demonstrates a production-ready architecture for AI-powered revenue operations:

✅ **MCP-Native Design:** Real tools, not function simulation
✅ **Edge Computing:** Global low-latency deployment
✅ **Multi-State Agents:** Proper conversation flows
✅ **Real Integrations:** Cal.com, database, webhooks
✅ **Scalable Foundation:** Built for multi-tenant growth

**Next Evolution:**
- Email agents (outbound sequences)
- Research agents (lead enrichment)
- Strategy agents (campaign optimization)
- Learning loop (feedback → prompt improvement)

The system proves that a single developer can build enterprise-grade AI infrastructure by leveraging modern platforms (Cloudflare) and protocols (MCP).

---

**Documentation:** `/Users/aijesusbro/AI Projects/jobhuntai/docs/`
**Repository:** Local development (git-tracked)
**Support:** Self-hosted, single operator
**Philosophy:** Build, prove, scale 🚀
