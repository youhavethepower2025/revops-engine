# VAPI MCP Server - Deployment Guide

## 🚀 Quick Deploy (5 minutes)

```bash
cd "/Users/aijesusbro/AI Projects/vapi-mcp-server"

# 1. Install dependencies
npm install

# 2. Create D1 database
npm run d1:create
# Copy the database_id from output and paste into wrangler.toml (line 8)

# 3. Run database migrations
npm run d1:execute

# 4. Set VAPI API key
npm run secret:vapi
# Paste your VAPI API key from https://vapi.ai/dashboard

# 5. Deploy to Cloudflare
npm run deploy

# 6. Test health endpoint
curl https://vapi-mcp-server.aijesusbro.workers.dev/health
```

---

## 📝 Step-by-Step Instructions

### Step 1: Install Dependencies

```bash
cd "/Users/aijesusbro/AI Projects/vapi-mcp-server"
npm install
```

This installs Wrangler and TypeScript.

---

### Step 2: Create D1 Database

```bash
npm run d1:create
```

**Output will look like:**
```
✅ Successfully created DB 'vapi-calls-db'

[[d1_databases]]
binding = "DB"
database_name = "vapi-calls-db"
database_id = "abc123-def456-ghi789"  # <-- COPY THIS
```

**Action:** Copy the `database_id` and replace `REPLACE_WITH_YOUR_D1_ID` in `wrangler.toml` (line 8)

---

### Step 3: Initialize Database Schema

```bash
npm run d1:execute
```

This creates all tables:
- `vapi_clients` - Client configurations
- `vapi_calls` - Call logs
- `vapi_transcripts` - Conversation history
- `vapi_tool_calls` - Tool execution logs

---

### Step 4: Set VAPI API Key

```bash
npm run secret:vapi
```

When prompted, paste your VAPI API key from: https://vapi.ai/dashboard

---

### Step 5: Deploy

```bash
npm run deploy
```

**Your MCP server will be live at:**
`https://vapi-mcp-server.aijesusbro.workers.dev`

---

## 🎯 Add Your First Client

```bash
curl -X POST https://vapi-mcp-server.aijesusbro.workers.dev/admin/clients \
  -H "Content-Type: application/json" \
  -d '{
    "client_id": "aijesusbro",
    "name": "AI Jesus Bro",
    "ghl_api_key": "YOUR_GHL_API_KEY_HERE",
    "ghl_location_id": "YOUR_GHL_LOCATION_ID_HERE",
    "settings": {
      "timezone": "America/Los_Angeles"
    }
  }'
```

**Expected Response:**
```json
{
  "success": true,
  "client_id": "aijesusbro",
  "mcp_url": "https://vapi-mcp-server.aijesusbro.workers.dev/mcp?client_id=aijesusbro"
}
```

**Save this MCP URL** - you'll use it to configure VAPI agents.

---

## 🤖 Create VAPI Agent (Manual Setup)

Go to https://vapi.ai/dashboard → Create Assistant

**Configuration:**

```json
{
  "name": "Test Agent",
  "model": {
    "provider": "openai",
    "model": "gpt-4o",
    "messages": [
      {
        "role": "system",
        "content": "You are a helpful customer service assistant. When a call starts, immediately use ghl_search_contact to identify the caller by their phone number."
      }
    ]
  },
  "voice": {
    "provider": "11labs",
    "voiceId": "21m00Tcm4TlvDq8ikWAM"
  },
  "tools": [
    {
      "type": "mcp",
      "serverUrl": "https://vapi-mcp-server.aijesusbro.workers.dev/mcp?client_id=aijesusbro",
      "protocol": "streamable-http"
    }
  ]
}
```

**Key Settings:**
- `type: "mcp"` - Tells VAPI this is an MCP server
- `serverUrl` - Your deployed MCP endpoint with client_id
- `protocol: "streamable-http"` - Use modern protocol

---

## 🧪 Test the Integration

### Option 1: VAPI Web Dialer

1. Go to VAPI dashboard
2. Find your assistant
3. Click "Test in Browser"
4. Say: "Hi, my phone number is 555-123-4567"
5. Watch logs: `npm run tail`

### Option 2: Real Phone Call

1. Assign VAPI assistant to a phone number
2. Call that number
3. Have a conversation
4. Check call logs

---

## 📊 Monitor & Debug

### Live Tail Logs

```bash
npm run tail
```

Watch real-time:
- MCP requests
- Tool executions
- GHL API calls
- Errors

### Check Database

```bash
# List recent calls
wrangler d1 execute vapi-calls-db --command="SELECT * FROM vapi_calls ORDER BY started_at DESC LIMIT 5"

# Check clients
wrangler d1 execute vapi-calls-db --command="SELECT * FROM vapi_clients"

# Tool execution stats
wrangler d1 execute vapi-calls-db --command="SELECT tool_name, COUNT(*) as count, AVG(execution_time_ms) as avg_time FROM vapi_tool_calls GROUP BY tool_name"
```

### Admin Endpoints

```bash
# List clients
curl https://vapi-mcp-server.aijesusbro.workers.dev/admin/clients

# List calls for a client
curl "https://vapi-mcp-server.aijesusbro.workers.dev/admin/calls?client_id=aijesusbro&limit=10"
```

---

## 🔧 Configure VAPI Webhooks

Go to VAPI dashboard → Settings → Webhooks

**Add Webhook URL:**
```
https://vapi-mcp-server.aijesusbro.workers.dev/webhooks/vapi
```

**Enable Events:**
- ✅ End of Call Report
- ✅ Status Update (optional)

**Why:** This stores call transcripts and tool execution logs in your D1 database.

---

## ✅ Production Checklist

- [ ] D1 database created and migrated
- [ ] VAPI_API_KEY secret set
- [ ] Worker deployed successfully
- [ ] At least one client configured
- [ ] VAPI assistant created with MCP tools
- [ ] Test call made and logged
- [ ] Webhooks configured
- [ ] Call logs appearing in database

---

## 🚨 Troubleshooting

### "Client not configured" error

**Cause:** Client doesn't exist in database or is inactive

**Fix:**
```bash
# Check if client exists
wrangler d1 execute vapi-calls-db --command="SELECT * FROM vapi_clients WHERE client_id='aijesusbro'"

# If not, add via curl (see "Add Your First Client" above)
```

### GHL API errors

**Cause:** Invalid GHL credentials or permissions

**Fix:**
1. Verify GHL API key has correct scopes (contacts, appointments, notes)
2. Check GHL location ID is correct
3. Test GHL API directly:
   ```bash
   curl https://rest.gohighlevel.com/v1/contacts/ \
     -H "Authorization: Bearer YOUR_GHL_API_KEY" \
     -H "Version: 2021-07-28"
   ```

### Tools not being called

**Cause:** VAPI assistant not configured correctly

**Fix:**
1. Check assistant has MCP tool with correct serverUrl
2. Verify protocol is "streamable-http"
3. Update system prompt to explicitly mention using tools
4. Test with VAPI web dialer first

### Call logs not appearing

**Cause:** Webhook not configured or failing

**Fix:**
1. Go to VAPI dashboard → Settings → Webhooks
2. Add: `https://vapi-mcp-server.aijesusbro.workers.dev/webhooks/vapi`
3. Enable "End of Call Report"
4. Make test call
5. Check `npm run tail` for webhook errors

---

## 📈 Next Steps

Once working:

1. **Add more clients:** Use `/admin/clients` endpoint
2. **Create more VAPI agents:** Each can use same MCP server with different client_id
3. **Add more tools:** Edit `src/brain.ts` → `listTools()` method
4. **Implement SMS:** Add Twilio/GHL integration in `sendSMS()` method
5. **Build analytics:** Query D1 database for insights

---

## 🔗 Useful Links

- VAPI Dashboard: https://vapi.ai/dashboard
- VAPI Docs: https://docs.vapi.ai
- Cloudflare Dashboard: https://dash.cloudflare.com
- Wrangler Docs: https://developers.cloudflare.com/workers/wrangler/

---

**Need help?** Check logs with `npm run tail` or inspect database with `wrangler d1 execute`
