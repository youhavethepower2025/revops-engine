# 🎙️ VAPI MCP Server

**Multi-tenant MCP server for VAPI voice agents with GoHighLevel integration**

## What This Does

This is a production-ready MCP (Model Context Protocol) server that gives VAPI voice agents the ability to:

- 🔍 **Search contacts** in GoHighLevel CRM by phone number (caller ID lookup)
- 📅 **Book appointments** during voice calls
- 📝 **Add notes** to contact records
- 💬 **Send follow-up SMS** messages (placeholder for Twilio/GHL integration)

**Multi-tenant:** One deployment serves unlimited clients via `client_id` routing.

---

## Architecture

```
VAPI Voice Call
  ↓
VAPI AI detects need for tool (e.g., "identify caller")
  ↓
POST /mcp?client_id=X { method: "tools/call", name: "ghl_search_contact" }
  ↓
Durable Object for client X (isolated state)
  ↓
Uses client X's GHL credentials
  ↓
Searches GHL API
  ↓
Returns contact data to VAPI
  ↓
VAPI AI: "Hi John! How can I help you today?"
```

---

## Tech Stack

- **Cloudflare Workers** - Edge compute (global deployment)
- **Durable Objects** - Per-client stateful instances
- **D1 Database** - SQLite for call logs, transcripts, client configs
- **MCP Protocol** - JSON-RPC 2.0 over Streamable HTTP
- **VAPI** - Voice AI platform
- **GoHighLevel** - CRM integration

---

## Quick Start

See [DEPLOYMENT.md](./DEPLOYMENT.md) for complete instructions.

```bash
npm install
npm run d1:create          # Create database
npm run d1:execute         # Run migrations
npm run secret:vapi        # Set API key
npm run deploy             # Deploy to Cloudflare
```

---

## Project Structure

```
vapi-mcp-server/
├── src/
│   ├── index.ts       # Main Worker (routing, webhooks, admin)
│   └── brain.ts       # Durable Object (MCP protocol, tools)
├── schema.sql         # D1 database schema
├── wrangler.toml      # Cloudflare Workers config
├── DEPLOYMENT.md      # Step-by-step deployment guide
└── package.json       # Dependencies and scripts
```

---

## Tools Available

The MCP server exposes these tools to VAPI agents:

### `ghl_search_contact`
Search GHL CRM by phone number (caller ID lookup)

**Input:** `{ phone: "5551234567" }`

**Output:** `{ found: true, id: "...", name: "John Doe", ... }`

### `ghl_create_appointment`
Book an appointment for a contact

**Input:** `{ contactId: "...", startTime: "2025-01-15T10:00:00-08:00", title: "..." }`

**Output:** `{ success: true, appointmentId: "..." }`

### `ghl_add_note`
Add a note to a contact record

**Input:** `{ contactId: "...", note: "Discussed roof repair options" }`

**Output:** `{ success: true }`

### `send_followup_sms`
Send follow-up SMS (placeholder - implement with Twilio/GHL)

**Input:** `{ phone: "5551234567", message: "Thanks for calling!" }`

**Output:** `{ success: true, message: "SMS queued" }`

---

## Multi-Tenant Usage

### Add a Client

```bash
curl -X POST https://vapi-mcp-server.aijesusbro.workers.dev/admin/clients \
  -H "Content-Type: application/json" \
  -d '{
    "client_id": "bison",
    "name": "Bison Roofing",
    "ghl_api_key": "...",
    "ghl_location_id": "..."
  }'
```

### Configure VAPI Agent

```json
{
  "tools": [{
    "type": "mcp",
    "serverUrl": "https://vapi-mcp-server.aijesusbro.workers.dev/mcp?client_id=bison",
    "protocol": "streamable-http"
  }]
}
```

**Each client gets:**
- Isolated Durable Object instance
- Separate GHL credentials
- Own call logs and transcripts
- Complete data isolation

---

## Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/health` | GET | Health check |
| `/mcp` | POST/GET | MCP protocol endpoint (tools/list, tools/call) |
| `/webhooks/vapi` | POST | VAPI webhooks (end-of-call reports) |
| `/admin/clients` | GET/POST | List/create clients |
| `/admin/calls` | GET | List call logs |

---

## Monitoring

```bash
# Live tail logs
npm run tail

# Query database
npm run d1:query "SELECT * FROM vapi_calls LIMIT 5"

# List clients
curl https://vapi-mcp-server.aijesusbro.workers.dev/admin/clients

# List calls
curl "https://vapi-mcp-server.aijesusbro.workers.dev/admin/calls?client_id=bison&limit=10"
```

---

## Development

```bash
# Local dev server
npm run dev

# Deploy to production
npm run deploy

# Update database schema
# 1. Edit schema.sql
# 2. npm run d1:execute
```

---

## Production Checklist

- [ ] D1 database created
- [ ] VAPI_API_KEY secret set
- [ ] At least one client configured
- [ ] VAPI agent created with MCP tools
- [ ] Webhooks configured
- [ ] Test call successful
- [ ] Logs appearing in database

---

## Why This Architecture?

**Multi-tenant from day one:**
- Add clients without redeploying
- Each client isolated via Durable Objects
- Same codebase serves everyone

**Edge-native:**
- <50ms latency globally
- Auto-scaling
- No servers to manage

**MCP protocol:**
- Standardized tool calling
- Dynamic tool discovery
- Works with any MCP-compatible AI

**Complete visibility:**
- All calls logged
- Full transcripts stored
- Tool execution tracked
- Analytics-ready data

---

## License

MIT

## Author

AI Jesus Bro - Built October 2025
