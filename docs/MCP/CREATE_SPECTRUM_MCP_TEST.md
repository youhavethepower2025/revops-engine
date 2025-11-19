# 🚧 SPECTRUM MCP TEST CREATION - ISSUE DISCOVERED

**Date:** October 21, 2025
**Status:** ⚠️ VAPI API Validation Issue

---

## PROBLEM DISCOVERED

When attempting to create "Spectrum MCP Test" agent with MCP tools format:

```json
{
  "model": {
    "tools": [{
      "type": "mcp",
      "serverUrl": "https://vapi-mcp-server.aijesusbro-brain.workers.dev/mcp?client_id=aijesusbro",
      "protocol": "streamable-http"
    }]
  }
}
```

**VAPI API Response:**
```
{
  "message": ["model.each value in tools.property serverUrl should not exist"],
  "error": "Bad Request",
  "statusCode": 400
}
```

---

## ROOT CAUSE ANALYSIS

**VAPI's MCP Support Might Work Differently:**

Option 1: **Server-Side Tool Execution**
VAPI might use `serverUrl` at the ROOT level (not inside tools array) for function/tool calling webhooks.

Option 2: **Different MCP Format**
VAPI's MCP implementation might use a different schema than documented.

Option 3: **Not Yet Released**
MCP support might not be fully available in the API yet (dashboard-only feature).

---

## INVESTIGATION NEEDED

Let me check VAPI's actual MCP implementation format by:

1. ✅ Searching VAPI community/docs for working MCP examples
2. ✅ Checking if `serverUrl` goes at root level vs inside tools
3. ✅ Testing with `serverUrl` + `serverMessages` configuration

---

## ALTERNATIVE APPROACH (WORKING NOW)

Instead of MCP tools in model config, use:

**1. Server URL for Webhooks** (already supported):
```json
{
  "serverUrl": "https://vapi-mcp-server.aijesusbro-brain.workers.dev/webhooks/vapi",
  "serverMessages": ["end-of-call-report", "status-update", "function-call"]
}
```

**2. Traditional Functions Array** (OpenAI format):
```json
{
  "model": {
    "functions": [
      {
        "name": "ghl_search_contact",
        "description": "Search for contact by phone number",
        "parameters": {
          "type": "object",
          "properties": {
            "phone": {"type": "string"}
          }
        }
      }
    ]
  }
}
```

**3. Bridge to MCP Server**:
When VAPI calls function, webhook forwards to vapi-mcp-server which executes MCP tool.

---

## RECOMMENDED NEXT STEP

Create **Spectrum MCP Test v1** using:
- `serverUrl` for webhook-based tool calling
- Enhanced A9 prompt with caller ID instructions
- Dynamic variables ({{customer.number}}, {{now}})
- Webhook handler bridges to MCP server

This achieves the same result (MCP tool execution) via webhook bridge instead of direct MCP protocol.

**Proceed with this approach?**
