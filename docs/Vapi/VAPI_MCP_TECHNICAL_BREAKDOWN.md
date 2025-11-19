# 🔧 VAPI MCP TECHNICAL BREAKDOWN

**Date:** October 22, 2025
**Status:** ✅ DEPLOYED & OPERATIONAL

---

## 📍 WHERE IS IT DEPLOYED?

### Platform: Cloudflare Workers

**URL:** `https://vapi-mcp-server.aijesusbro-brain.workers.dev`

**Architecture:**
- **Cloudflare Worker** - Edge compute (main entry point)
- **Durable Objects** - Stateful per-client brain instances
- **D1 Database** - SQLite at the edge for storage

**Project Location:** `/Users/aijesusbro/AI Projects/vapi-mcp-server/`

---

## 🔗 URLS YOU NEED

### 1. MCP Endpoint (For VAPI Assistants)
```
https://vapi-mcp-server.aijesusbro-brain.workers.dev/mcp?client_id=aijesusbro
```

**What it does:** VAPI agents connect here to access MCP tools
**Protocol:** Streamable HTTP (MCP 2.0)
**Used in:** Agent configuration `model.tools` array

### 2. Webhook Endpoint (For Call Logging)
```
https://vapi-mcp-server.aijesusbro-brain.workers.dev/webhooks/vapi
```

**What it does:** Receives end-of-call reports from VAPI
**Stores:** Transcripts, tool calls, call metadata
**Configure in:** VAPI Dashboard → Settings → Webhooks

### 3. Admin Endpoints

**List Clients:**
```
https://vapi-mcp-server.aijesusbro-brain.workers.dev/admin/clients
```

**List Calls:**
```
https://vapi-mcp-server.aijesusbro-brain.workers.dev/admin/calls?client_id=aijesusbro&limit=10
```

**Health Check:**
```
https://vapi-mcp-server.aijesusbro-brain.workers.dev/health
```

---

## 🛠️ TOOLS CURRENTLY IMPLEMENTED

### 1. ghl_search_contact
**Purpose:** Search GHL CRM by phone number (caller ID lookup)

**Input:**
```json
{
  "phone": "5551234567"
}
```

**Output:**
```json
{
  "found": true,
  "contact": {
    "id": "abc123",
    "firstName": "John",
    "lastName": "Doe",
    "email": "john@example.com",
    "phone": "5551234567"
  }
}
```

**When to use:** IMMEDIATELY at call start with {{customer.number}}

---

### 2. ghl_get_calendar_slots
**Purpose:** Check available appointment slots

**Input:**
```json
{
  "calendar_id": "cal_abc123",
  "start_date": "2025-10-25",
  "end_date": "2025-10-27"
}
```

**Output:**
```json
{
  "slots": [
    {
      "start": "2025-10-25T10:00:00Z",
      "end": "2025-10-25T11:00:00Z",
      "available": true
    }
  ]
}
```

---

### 3. ghl_create_appointment
**Purpose:** Book an appointment in GHL calendar

**Input:**
```json
{
  "contact_id": "abc123",
  "calendar_id": "cal_abc123",
  "start_time": "2025-10-25T10:00:00Z",
  "end_time": "2025-10-25T11:00:00Z",
  "title": "Discovery Call - John Doe",
  "notes": "Interested in voice AI agents"
}
```

**Output:**
```json
{
  "success": true,
  "appointment_id": "appt_xyz789",
  "confirmation": "Appointment booked for 2025-10-25 at 10:00 AM"
}
```

---

### 4. ghl_add_note
**Purpose:** Add note to contact record in GHL

**Input:**
```json
{
  "contact_id": "abc123",
  "note": "Called on 10/22 at 2:30pm. Qualified as high intent. Booking discovery call."
}
```

**Output:**
```json
{
  "success": true,
  "note_id": "note_123"
}
```

---

### 5. send_followup_sms
**Purpose:** Send SMS follow-up (currently placeholder)

**Input:**
```json
{
  "phone": "5551234567",
  "message": "Thanks for your call! Here's the info we discussed..."
}
```

**Output:**
```json
{
  "success": true,
  "message": "SMS sending not yet implemented - placeholder response"
}
```

**Note:** This is a placeholder. Needs Twilio/GHL SMS integration.

---

## 👥 CLIENTS CONFIGURED

### 1. aijesusbro
- **Name:** AI Jesus Bro Sandbox
- **GHL Location:** PMgbQ375TEGOyGXsKz7e
- **Status:** ✅ Active
- **MCP URL:** `...mcp?client_id=aijesusbro`

### 2. advisory9
- **Name:** Advisory9 Sandbox
- **GHL Location:** PMgbQ375TEGOyGXsKz7e (same sandbox)
- **Status:** ✅ Active
- **MCP URL:** `...mcp?client_id=advisory9`

---

## 🏗️ ARCHITECTURE BREAKDOWN

### How It Works:

```
VAPI Agent (during call)
    ↓
Needs to use tool (e.g., ghl_search_contact)
    ↓
Connects to MCP server via Streamable HTTP
GET/POST https://vapi-mcp-server.aijesusbro-brain.workers.dev/mcp?client_id=aijesusbro
    ↓
Cloudflare Worker (index.ts)
Routes to Durable Object based on client_id
    ↓
Durable Object (brain.ts) - VapiBrain class
    ↓
1. Loads client config from D1 (GHL API keys)
2. Parses MCP request (JSON-RPC 2.0)
3. Executes tool (e.g., calls GHL API)
4. Returns result in MCP format
    ↓
VAPI Agent receives result
Continues conversation with data
```

### After Call Ends:

```
VAPI
    ↓
Sends webhook: POST /webhooks/vapi
    ↓
Cloudflare Worker (index.ts)
    ↓
Stores in D1 database:
- vapi_calls table (call metadata)
- vapi_transcripts table (full conversation)
- vapi_tool_calls table (tool execution logs)
```

---

## 🗄️ DATABASE SCHEMA

### Table: vapi_clients
```sql
CREATE TABLE vapi_clients (
  client_id TEXT PRIMARY KEY,
  name TEXT NOT NULL,
  ghl_api_key TEXT NOT NULL,
  ghl_location_id TEXT NOT NULL,
  settings TEXT,
  active INTEGER DEFAULT 1,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

### Table: vapi_calls
```sql
CREATE TABLE vapi_calls (
  id TEXT PRIMARY KEY,
  client_id TEXT NOT NULL,
  assistant_id TEXT,
  phone_number TEXT,
  caller_name TEXT,
  direction TEXT,
  started_at DATETIME,
  ended_at DATETIME,
  duration_seconds INTEGER,
  status TEXT,
  cost_cents INTEGER,
  recording_url TEXT,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

### Table: vapi_transcripts
```sql
CREATE TABLE vapi_transcripts (
  id TEXT PRIMARY KEY,
  call_id TEXT NOT NULL,
  role TEXT,
  content TEXT,
  timestamp DATETIME,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

### Table: vapi_tool_calls
```sql
CREATE TABLE vapi_tool_calls (
  id TEXT PRIMARY KEY,
  call_id TEXT NOT NULL,
  client_id TEXT NOT NULL,
  tool_name TEXT,
  arguments TEXT,
  result TEXT,
  success INTEGER,
  error TEXT,
  execution_time_ms INTEGER,
  timestamp DATETIME,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

---

## ⚠️ WHAT'S NOT SET UP YET

### 1. Webhook Configuration in VAPI Dashboard
**Status:** ❌ NOT CONFIGURED YET

**You need to:**
1. Go to https://dashboard.vapi.ai/settings
2. Find "Webhooks" section
3. Add: `https://vapi-mcp-server.aijesusbro-brain.workers.dev/webhooks/vapi`
4. Enable: "End of Call Report"

**Why:** Without this, calls won't be logged to D1

---

### 2. MCP Tools in 323 Agent
**Status:** ❌ NOT CONFIGURED YET

**Current state:**
- Agent "Spectrum" on 323 has NO tools
- Agent "Spectrum MCP Test" has tools BUT not connected to 323

**You need to either:**
- **Option A:** Update "Spectrum" agent to add MCP tools
- **Option B:** Reassign 323 to "Spectrum MCP Test" agent

---

### 3. SMS Sending Implementation
**Status:** ⚠️ PLACEHOLDER ONLY

The `send_followup_sms` tool exists but doesn't actually send SMS yet.

**To implement:**
- Add Twilio integration to brain.ts
- OR use GHL SMS API

---

## 🧪 HOW TO TEST MCP TOOLS

### Test 1: List Tools (What agent sees)
```bash
curl -X POST https://vapi-mcp-server.aijesusbro-brain.workers.dev/mcp?client_id=aijesusbro \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 1,
    "method": "tools/list"
  }'
```

**Expected:** List of 5 tools (ghl_search_contact, ghl_get_calendar_slots, ghl_create_appointment, ghl_add_note, send_followup_sms)

---

### Test 2: Execute Tool
```bash
curl -X POST https://vapi-mcp-server.aijesusbro-brain.workers.dev/mcp?client_id=aijesusbro \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 2,
    "method": "tools/call",
    "params": {
      "name": "ghl_search_contact",
      "arguments": {
        "phone": "5551234567"
      }
    }
  }'
```

**Expected:** Search result from GHL (or error if contact not found)

---

## 📊 MONITORING COMMANDS

### Check if server is up:
```bash
curl https://vapi-mcp-server.aijesusbro-brain.workers.dev/health
```

### List configured clients:
```bash
curl https://vapi-mcp-server.aijesusbro-brain.workers.dev/admin/clients
```

### Check recent calls:
```bash
curl "https://vapi-mcp-server.aijesusbro-brain.workers.dev/admin/calls?client_id=aijesusbro&limit=5"
```

### Live logs:
```bash
cd "/Users/aijesusbro/AI Projects/vapi-mcp-server"
npm run tail
```

### Query D1 database:
```bash
cd "/Users/aijesusbro/AI Projects/vapi-mcp-server"
wrangler d1 execute vapi-calls-db --remote --command="SELECT * FROM vapi_calls ORDER BY started_at DESC LIMIT 5"
```

---

## 🎯 SUMMARY

**What's Working:**
- ✅ MCP server deployed on Cloudflare Workers
- ✅ 5 GHL tools implemented
- ✅ 2 clients configured (aijesusbro, advisory9)
- ✅ D1 database ready
- ✅ Durable Objects handling per-client state

**What's Missing:**
- ❌ Webhook not configured in VAPI dashboard
- ❌ 323 agent doesn't have MCP tools yet
- ❌ SMS sending not implemented (placeholder only)

**Next Steps:**
1. Add MCP tools to 323 agent
2. Configure webhook in VAPI dashboard
3. Test call on 323
4. Verify tool execution and logging

---

**URLs Summary:**

| Purpose | URL |
|---------|-----|
| MCP Endpoint | `https://vapi-mcp-server.aijesusbro-brain.workers.dev/mcp?client_id=aijesusbro` |
| Webhooks | `https://vapi-mcp-server.aijesusbro-brain.workers.dev/webhooks/vapi` |
| Health | `https://vapi-mcp-server.aijesusbro-brain.workers.dev/health` |
| Admin Clients | `https://vapi-mcp-server.aijesusbro-brain.workers.dev/admin/clients` |
| Admin Calls | `https://vapi-mcp-server.aijesusbro-brain.workers.dev/admin/calls` |
