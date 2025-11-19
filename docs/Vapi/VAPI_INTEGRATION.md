# Vapi Integration for Brain MCP

## Overview

Vapi is integrated into the brain MCP server alongside Retell, giving you the flexibility to use the voice AI platform you're most familiar with.

## Architecture

### Vapi vs Retell Key Differences

**Vapi**:
- Server URL approach for function calling
- Vapi calls YOUR server when assistant needs to execute a function
- Webhooks for events (call started, ended, function called, etc.)
- Simpler assistant model (single prompt + functions)
- Better for custom function logic on your server

**Retell**:
- MCP URL approach (they hit your MCP server)
- Multi-state conversation flows
- Built-in integrations (Cal.com, etc.)
- More complex state management

## Vapi Tools in Brain MCP

### Assistant Management
- `vapi_create_assistant` - Create new voice assistant
- `vapi_get_assistant` - Get assistant configuration
- `vapi_update_assistant` - Update assistant prompts/functions
- `vapi_list_assistants` - List all assistants
- `vapi_delete_assistant` - Delete an assistant

### Call Management
- `vapi_create_phone_call` - Make outbound call
- `vapi_get_call` - Get call details and transcript
- `vapi_list_calls` - List calls with filtering
- `vapi_end_call` - End an active call

### Phone Number Management
- `vapi_import_phone_number` - Import Twilio number to Vapi
- `vapi_list_phone_numbers` - List all phone numbers
- `vapi_delete_phone_number` - Remove phone number

## Function Calling Flow

```
1. Caller dials your Twilio number
2. Twilio forwards to Vapi (via webhook or SIP)
3. Vapi assistant answers with configured prompt
4. During conversation, assistant decides to call a function
5. Vapi POSTs to your server URL:
   POST https://revops-os-dev.aijesusbro-brain.workers.dev/api/vapi/function-call
   {
     "message": {
       "type": "function-call",
       "functionCall": {
         "name": "create_lead",
         "parameters": {
           "phone": "+14155551234",
           "name": "John Doe"
         }
       }
     }
   }
6. Your server executes the function and responds:
   {
     "result": {
       "lead_id": "abc123",
       "success": true
     }
   }
7. Vapi receives result and continues conversation
8. After call ends, Vapi sends webhook to:
   POST https://revops-os-dev.aijesusbro-brain.workers.dev/api/webhooks/vapi
```

## Configuration Steps

### 1. Get Vapi API Key
- Go to https://dashboard.vapi.ai
- Navigate to Settings → API Keys
- Copy your private key

### 2. Add to .env
```bash
VAPI_API_KEY=your_key_here
```

### 3. Create Assistant

Use brain MCP tool:
```python
vapi_create_assistant(
    name="RevOps OS Qualification Agent",
    model="gpt-4",
    voice="11labs-adriana",
    first_message="Hey there! Thanks for calling RevOps OS. What brought you to reach out today?",
    system_prompt="You are the qualification agent for RevOps OS...",
    functions=[
        {
            "name": "get_lead_by_phone",
            "description": "Look up caller by phone number",
            "parameters": {
                "type": "object",
                "properties": {
                    "phone": {"type": "string"}
                }
            }
        },
        {
            "name": "create_lead",
            "description": "Create new lead record",
            "parameters": {
                "type": "object",
                "properties": {
                    "phone": {"type": "string"},
                    "name": {"type": "string"},
                    "email": {"type": "string"},
                    "company": {"type": "string"}
                }
            }
        }
    ],
    server_url="https://revops-os-dev.aijesusbro-brain.workers.dev/api/vapi/function-call"
)
```

### 4. Set Up Server Endpoints

Create in `/workers/vapi/function-call.js`:
```javascript
export async function handleVapiFunctionCall(request, env) {
  const payload = await request.json();
  const { functionCall } = payload.message;

  switch (functionCall.name) {
    case 'get_lead_by_phone':
      return await getLeadByPhone(functionCall.parameters, env);
    case 'create_lead':
      return await createLead(functionCall.parameters, env);
    // ... more functions
  }
}
```

Create in `/workers/webhooks/vapi.js`:
```javascript
export async function handleVapiWebhook(request, env) {
  const payload = await request.json();

  switch (payload.message.type) {
    case 'call-started':
      await handleCallStarted(payload, env);
      break;
    case 'call-ended':
      await handleCallEnded(payload, env);
      break;
    case 'transcript':
      await handleTranscript(payload, env);
      break;
  }
}
```

### 5. Configure Twilio

**Option A: HTTP Webhook** (simpler)
1. Go to Twilio console → Phone Numbers
2. Select (323) 968-5736
3. Under Voice & Fax:
   - A CALL COMES IN: Webhook
   - URL: `https://api.vapi.ai/call/phone-number`
   - Method: POST
   - Add Query Parameter: `number=your_vapi_phone_number_id`

**Option B: SIP Trunk** (better audio)
1. In Vapi dashboard, get SIP credentials
2. In Twilio, create SIP trunk pointing to Vapi
3. Route phone number to SIP trunk

## Webhook Events

Vapi sends these events to your webhook URL:

### call-started
```json
{
  "message": {
    "type": "call-started",
    "call": {
      "id": "call_abc123",
      "type": "inboundPhoneCall",
      "status": "in-progress",
      "phoneNumber": {
        "number": "+13239685736"
      },
      "customer": {
        "number": "+14155551234"
      }
    }
  }
}
```

### function-call (to your server URL, not webhook)
```json
{
  "message": {
    "type": "function-call",
    "functionCall": {
      "name": "create_lead",
      "parameters": {
        "phone": "+14155551234",
        "name": "John Doe"
      }
    },
    "call": {
      "id": "call_abc123"
    }
  }
}
```

Your response:
```json
{
  "result": {
    "lead_id": "abc123",
    "success": true,
    "message": "Lead created successfully"
  }
}
```

### call-ended
```json
{
  "message": {
    "type": "call-ended",
    "call": {
      "id": "call_abc123",
      "status": "ended",
      "endedReason": "customer-ended-call",
      "duration": 120.5,
      "transcript": "Full conversation...",
      "messages": [ /* array of all messages */ ]
    }
  }
}
```

### transcript
```json
{
  "message": {
    "type": "transcript",
    "role": "user",
    "transcript": "I want to book a demo",
    "call": {
      "id": "call_abc123"
    }
  }
}
```

## Example: Full Migration from Retell

### 1. Create Vapi Assistant

```bash
# Using brain MCP via Claude Code
vapi_create_assistant({
  "name": "RevOps OS Agent",
  "model": "gpt-4",
  "voice": "11labs-adriana",
  "first_message": "Hey there! Thanks for calling RevOps OS.",
  "system_prompt": "You are the inbound qualification agent...",
  "functions": [
    // Same functions as Retell MCP tools
  ],
  "server_url": "https://revops-os-dev.aijesusbro-brain.workers.dev/api/vapi/function-call"
})
```

### 2. Deploy Function Handler

```bash
cd "/Users/aijesusbro/AI Projects/revopsOS"
# Function call handler will be added to api.js
npm run deploy:dev
```

### 3. Update Twilio

```bash
# Change from Retell SIP trunk to Vapi webhook
# Twilio console → (323) 968-5736 → Voice Configuration
# Set webhook to: https://api.vapi.ai/call/phone-number?number={vapi_phone_id}
```

### 4. Test

Call (323) 968-5736 and verify:
- Vapi assistant answers
- Functions are called (check logs: `npx wrangler tail --env dev`)
- Lead created in database
- Transcript saved after call

## Benefits of Vapi

1. **Simpler Architecture** - No multi-state complexity, just functions
2. **More Control** - Function logic on your server, not in prompts
3. **Better Debugging** - See exactly what functions are called and when
4. **Flexible** - Easy to add new functions without reconfiguring assistant
5. **Familiar** - You already have experience with it

## API Reference

### Create Assistant
```python
vapi_create_assistant(
    name: str,
    model: str = "gpt-4",
    voice: str = "11labs-adriana",
    first_message: str = "",
    system_prompt: str = "",
    functions: list = [],
    server_url: str = "",
    webhook_url: str = "",
    provider: str = "openai"
)
```

### Create Phone Call
```python
vapi_create_phone_call(
    assistant_id: str,
    customer_number: str,
    phone_number_id: str,  # Your Vapi phone number
    name: str = ""
)
```

### Import Phone Number
```python
vapi_import_phone_number(
    provider: str = "twilio",
    number: str = "+13239685736",
    twilio_account_sid: str = "",
    twilio_auth_token: str = ""
)
```

## Troubleshooting

### Function calls not working
- Check `server_url` is set on assistant
- Verify endpoint is public (no auth required for Vapi)
- Check logs: `npx wrangler tail --env dev`
- Test endpoint manually: `curl -X POST {your_server_url} -d '{...}'`

### Webhook not firing
- Check `webhook_url` is set on assistant or phone number
- Verify endpoint is reachable
- Check Vapi dashboard for webhook delivery status

### Poor call quality
- Switch from HTTP webhook to SIP trunk
- Use Vapi's SIP credentials in Twilio
- Better audio, lower latency

## Next Steps

1. Get Vapi API key from dashboard
2. Add to `.env` and rebuild Docker container
3. Create assistant using brain MCP
4. Deploy function handler to RevOps OS
5. Update Twilio to point to Vapi
6. Test call flow
7. Celebrate being back on familiar ground! 🎉
