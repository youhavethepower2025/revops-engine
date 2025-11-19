# Vapi Integration URLs - Real Data Connection

## ✅ Fake Data Deleted

All demo data has been removed from the database. System is now clean and ready for real Vapi calls.

---

## 🔗 URLs for Your Vapi Agent Configuration

### **1. MCP Server URL** (for Vapi agent tools)
```
https://vapi-mcp-server.aijesusbro-brain.workers.dev/mcp?client_id=aijesusbro
```

**What this does**: Gives your Vapi agent access to all 8 tools (CRM, memory, call logs, etc.)

**How to use**: In your Vapi agent configuration, add this as your MCP server URL

---

### **2. Webhook URL** (for storing call data)
```
https://vapi-mcp-server.aijesusbro-brain.workers.dev/webhooks/vapi
```

**What this does**:
- Receives end-of-call reports from Vapi
- Stores call records in `vapi_calls` table
- Stores transcripts in `vapi_transcripts` table
- Stores tool execution logs in `vapi_tool_calls` table

**How to use**: In Vapi dashboard → Agent settings → Webhook URL

---

## 📋 What Gets Stored Automatically

When a call ends, Vapi sends a webhook that stores:

### Call Record (`vapi_calls` table):
- Call ID
- Phone number
- Caller name
- Start/end time
- Duration
- Status (completed, failed, no-answer)
- Cost (in cents)
- Recording URL
- Summary
- Ended reason

### Transcript (`vapi_transcripts` table):
- Every message in the conversation
- Role (user/assistant/system)
- Content (what was said)
- Timestamp

### Tool Calls (`vapi_tool_calls` table):
- Which tools were used during the call
- Arguments passed to tools
- Results returned
- Success/failure status
- Execution time

---

## 🧪 Testing Real Data Flow

### Step 1: Make a Test Call
Call your Vapi agent's phone number

### Step 2: Check if Data Arrived
```bash
# Check for calls
wrangler d1 execute vapi-calls-db --remote --command \
  "SELECT id, phone_number, status, started_at FROM vapi_calls ORDER BY started_at DESC LIMIT 5"

# Check for transcripts
wrangler d1 execute vapi-calls-db --remote --command \
  "SELECT call_id, role, content FROM vapi_transcripts ORDER BY timestamp DESC LIMIT 10"

# Check for tool executions
wrangler d1 execute vapi-calls-db --remote --command \
  "SELECT tool_name, success, timestamp FROM vapi_tool_calls ORDER BY timestamp DESC LIMIT 10"
```

### Step 3: Test Spectrum Retrieval
```bash
curl -s -X POST 'https://spectrum-api.aijesusbro-brain.workers.dev/chat/send' \
  -H 'Content-Type: application/json' \
  -d '{"agent_role":"reality","message":"Show me recent calls","client_id":"aijesusbro"}' \
  | jq -r '.message'
```

---

## 🔧 If Calls Aren't Showing Up

### Debug Webhook Delivery:

**1. Check webhook is configured in Vapi:**
- Log into Vapi dashboard
- Go to your agent settings
- Verify webhook URL is: `https://vapi-mcp-server.aijesusbro-brain.workers.dev/webhooks/vapi`

**2. Check worker logs:**
```bash
wrangler tail vapi-mcp-server --format=pretty
```

You should see:
```
[Webhook] VAPI event: end-of-call-report
[Webhook] Processing call xxx-xxx-xxx for client aijesusbro
[Webhook] Stored call xxx-xxx-xxx with transcript and tool calls
```

**3. Test webhook manually:**
```bash
curl -X POST 'https://vapi-mcp-server.aijesusbro-brain.workers.dev/webhooks/vapi' \
  -H 'Content-Type: application/json' \
  -d '{
    "message": {
      "type": "status-update",
      "status": "in-progress"
    }
  }'
```

Should return: `{"received":true}`

---

## 📊 Expected Data Format from Vapi

When Vapi sends an `end-of-call-report`, it includes:

```json
{
  "message": {
    "type": "end-of-call-report",
    "call": {
      "id": "call_abc123",
      "assistantId": "assistant_xyz",
      "customer": {
        "number": "+15551234567",
        "name": "John Doe"
      },
      "type": "inbound",
      "startedAt": "2025-10-22T18:30:00Z",
      "endedAt": "2025-10-22T18:33:00Z",
      "duration": 180,
      "status": "completed",
      "cost": 0.45,
      "recordingUrl": "https://...",
      "transcript": [
        {"role": "user", "message": "Hello", "time": "2025-10-22T18:30:05Z"},
        {"role": "assistant", "message": "Hi! How can I help?", "time": "2025-10-22T18:30:06Z"}
      ],
      "messages": [
        {
          "role": "assistant",
          "toolCalls": [
            {
              "function": {
                "name": "ghl_search_contact",
                "arguments": {"phone": "+15551234567"}
              },
              "result": {"found": true, "name": "John Doe"}
            }
          ],
          "time": "2025-10-22T18:30:10Z"
        }
      ]
    }
  }
}
```

Our webhook parses all of this and stores it in the database.

---

## 🚀 Quick Setup Checklist

- [ ] Add MCP server URL to Vapi agent configuration
- [ ] Add webhook URL to Vapi agent settings
- [ ] Make a test call to your Vapi number
- [ ] Check database for call record
- [ ] Test Spectrum retrieval with "Show me recent calls"
- [ ] Verify formatting looks good
- [ ] Ready for demo with REAL data

---

## 🔑 Client ID Note

The webhook extracts `client_id` from the MCP server URL in your agent's tool configuration.

**Your URL includes**: `?client_id=aijesusbro`

This ensures calls are properly associated with your account in the multi-tenant system.

---

## 📝 Summary

**MCP Server URL**:
```
https://vapi-mcp-server.aijesusbro-brain.workers.dev/mcp?client_id=aijesusbro
```

**Webhook URL**:
```
https://vapi-mcp-server.aijesusbro-brain.workers.dev/webhooks/vapi
```

Both are live and ready. Once you configure these in Vapi, calls will automatically flow into the database and Spectrum will be able to retrieve them with proper formatting.

No fake data. Just real infrastructure doing real work.
