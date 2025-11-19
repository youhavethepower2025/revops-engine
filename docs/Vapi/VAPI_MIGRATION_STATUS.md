# Vapi Migration - STATUS ✅

**Date**: October 16, 2025
**Status**: Brain MCP Ready → Now Deploying to Vapi

---

## ✅ What's Complete

### 1. Brain MCP with Vapi Integration
- ✅ Vapi API key configured: `bb0d907c-0834-420e-932c-f3f25f8221ad`
- ✅ Vapi tools module created (`vapi_tools.py`)
- ✅ 13 Vapi tools available in brain MCP:
  - Assistant management (create, update, delete, list)
  - Call management (create, get, list, end)
  - Phone number management (import, update, delete, list)
- ✅ Docker container rebuilt and running
- ✅ Database: PostgreSQL with agents table ready

### 2. Architecture Comparison

**Retell** (what we just migrated from):
- Multi-state conversation flows
- MCP URL approach
- Built-in integrations
- More complex

**Vapi** (what you know):
- Server URL for function calling
- Simpler assistant model
- More control over function logic
- You already have experience!

---

## 🚀 Next Steps (Testing Phase)

### Priority 1: Create Simple Vapi Assistant

Use your brain MCP (now running at port 8080):

```bash
# Test that Vapi tools are available
curl http://localhost:8080/sse \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 1,
    "method": "tools/list"
  }' | jq '.result.tools[] | select(.name | startswith("vapi"))'
```

You should see all Vapi tools listed!

### Priority 2: Import Phone Number to Vapi

Your Twilio number: **(323) 968-5736**
Twilio Account SID: `ACd7564cf277675642888a72f63d1655a3`
Twilio Auth Token: `e65397c32f16f83469ee9d859308eb6a`

Via brain MCP (you'll use this through Claude Code):

```python
# Import Twilio number to Vapi
vapi_import_phone_number(
    provider="twilio",
    number="+13239685736",
    name="RevOps OS Main Line",
    twilio_account_sid="ACd7564cf277675642888a72f63d1655a3",
    twilio_auth_token="e65397c32f16f83469ee9d859308eb6a"
)

# This returns a phone_number_id - save it!
```

### Priority 3: Create Test Assistant

Simple assistant just for testing calls:

```python
vapi_create_assistant(
    name="RevOps OS Test Agent",
    model="gpt-4",
    voice="11labs-adriana",  # Or your preferred voice
    first_message="Hey there! Thanks for calling. This is a test of the Vapi system. What's your name?",
    system_prompt="""You are a friendly test assistant for RevOps OS.

Your only job is to:
1. Greet the caller
2. Ask their name
3. Confirm you can hear them clearly
4. Thank them for testing
5. End the call politely

Be natural and conversational."""
)

# Returns assistant_id - save it!
```

### Priority 4: Configure Vapi Phone Number

Connect your imported number to the assistant:

```python
# After getting phone_number_id and assistant_id from above
vapi_update_phone_number(
    phone_number_id="[from step 2]",
    assistant_id="[from step 3]"
)
```

### Priority 5: Update Twilio Webhook

**Option A: Web Interface** (fastest):
1. Go to: https://console.twilio.com/us1/develop/phone-numbers/manage/active
2. Click on (323) 968-5736
3. Under "Voice & Fax":
   - A CALL COMES IN: Webhook
   - URL: `https://api.vapi.ai/call/phone-number`
   - Method: POST
4. Save

**Option B: Via API**:
```bash
curl -X POST "https://api.twilio.com/2010-04-01/Accounts/ACd7564cf277675642888a72f63d1655a3/IncomingPhoneNumbers/[PHONE_SID].json" \
  -u "ACd7564cf277675642888a72f63d1655a3:e65397c32f16f83469ee9d859308eb6a" \
  -d "VoiceUrl=https://api.vapi.ai/call/phone-number" \
  -d "VoiceMethod=POST"
```

### Priority 6: TEST THE CALL!

**Call**: (323) 968-5736

**What should happen**:
1. Vapi answers with your test assistant
2. Assistant greets you
3. You can have a simple conversation
4. Call works end-to-end

**If it works**: 🎉 You're back on Vapi!

**If it doesn't**: Check Vapi dashboard logs at https://dashboard.vapi.ai

---

## 📋 Later: RevOps OS Integration

Once the call works, we'll add:
1. Function calling endpoint in RevOps OS
2. Webhook handler for call events
3. Database integration
4. Full qualification flow

But first - let's just get that call working!

---

## 🔧 Vapi Tools Available (via Brain MCP)

### Assistant Management
- `vapi_create_assistant` - Create voice assistant
- `vapi_get_assistant` - Get assistant config
- `vapi_update_assistant` - Update prompts/functions
- `vapi_list_assistants` - List all assistants
- `vapi_delete_assistant` - Delete assistant

### Call Management
- `vapi_create_phone_call` - Make outbound call
- `vapi_get_call` - Get call details/transcript
- `vapi_list_calls` - List calls with filtering
- `vapi_end_call` - End active call

### Phone Numbers
- `vapi_import_phone_number` - Import Twilio number ⭐ USE THIS FIRST
- `vapi_list_phone_numbers` - List all numbers
- `vapi_get_phone_number` - Get number details
- `vapi_update_phone_number` - Update config
- `vapi_delete_phone_number` - Remove number

---

## 🎯 Your Immediate Action Items

1. **Test brain MCP** - Make sure Vapi tools show up
2. **Import phone number** - Use `vapi_import_phone_number`
3. **Create test assistant** - Simple greeting assistant
4. **Link them together** - Update phone number with assistant ID
5. **Switch Twilio** - Point to Vapi webhook
6. **CALL IT** - (323) 968-5736 and test!

Then we'll add all the fancy RevOps OS integration.

---

## 📝 Credentials Reference

**Vapi**:
- API Key: `bb0d907c-0834-420e-932c-f3f25f8221ad`
- Dashboard: https://dashboard.vapi.ai

**Twilio** (AI Jesus Bro):
- Account SID: `ACd7564cf277675642888a72f63d1655a3`
- Auth Token: `e65397c32f16f83469ee9d859308eb6a`
- Phone: (323) 968-5736 (`+13239685736`)

**Brain MCP**:
- URL: http://localhost:8080
- Status: Running ✅
- Tools: 70+ (including 13 Vapi tools)

---

## 🚨 Important Notes

- **Don't worry about RevOps OS integration yet** - let's just get the call working first
- **Use brain MCP through Claude Code** - all the tools are available via MCP
- **Vapi dashboard** - check it for logs and debugging
- **Simple first** - test with basic assistant, add complexity later

---

**Ready to test?** Let's import that phone number and make a call! 📞
