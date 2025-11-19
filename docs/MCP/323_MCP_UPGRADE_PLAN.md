# 🎯 323 NUMBER MCP UPGRADE - ACTION PLAN

**Objective:** Make (323) 968-5736 fire with MCP tools for GHL integration

---

## 📊 CURRENT STATE

### Phone Number:
- **Number:** +13239685736
- **Name:** LA Spectrum OS
- **Assigned To:** "Spectrum" agent (ID: ade4b8c5-8d35-465b-a8f2-1db21557d5a2)

### Current "Spectrum" Agent:
- **Model:** Claude Haiku 4.5
- **Voice:** Elliot (Vapi)
- **First Message:** "Hi, this is Julian, what's the name of your agency?"
- **Role:** AI sales assistant for John Kruze's business
- **❌ NO MCP TOOLS**
- **❌ NO WEBHOOKS**
- **❌ NO CALLER ID LOOKUP**

### What Already Works:
- ✅ Phone number active
- ✅ Agent answers calls
- ✅ Dynamic variables in prompt ({{customer.number}}, {{now}})
- ✅ Recording enabled
- ✅ Good system prompt (8643 chars)

---

## 🔥 WHAT NEEDS TO BE ADDED

### 1. MCP Tools Configuration
Add to agent's `model.tools` array:

```json
{
  "type": "mcp",
  "function": {
    "name": "mcpTools"
  },
  "server": {
    "url": "https://vapi-mcp-server.aijesusbro-brain.workers.dev/mcp?client_id=aijesusbro"
  }
}
```

**This gives the agent:**
- ghl_search_contact (caller ID lookup)
- ghl_create_appointment
- ghl_add_note
- send_followup_sms

### 2. Webhook Configuration
Add to root level of agent config:

```json
{
  "serverMessages": [
    "end-of-call-report",
    "status-update",
    "function-call"
  ]
}
```

**This enables:**
- Post-call transcript storage in D1
- Tool execution logging
- Real-time call monitoring

### 3. System Prompt Enhancement
**Add THIS section to the beginning of system prompt:**

```
**🔧 MCP TOOLS - REAL-TIME CRM INTEGRATION:**

At the START of EVERY call, you MUST execute ghl_search_contact with the caller's phone number ({{customer.number}}) to identify them BEFORE engaging deeply. This gives you their contact info from GoHighLevel CRM.

Available tools:
1. ghl_search_contact(phone) - Look up caller in CRM (USE FIRST!)
2. ghl_create_appointment(...) - Book discovery calls directly in calendar
3. ghl_add_note(contact_id, note) - Document call outcomes in CRM
4. send_followup_sms(...) - Send SMS follow-ups

**Example execution sequence:**
1. Answer: "Hey there! You've reached [Your Name]'s AI assistant..."
2. IMMEDIATELY execute: ghl_search_contact(phone="{{customer.number}}")
3. If found: Reference their info naturally: "Hi [FirstName]!"
4. Continue conversation with personalized context
5. After qualifying: Use ghl_add_note to document
6. When booking: Use ghl_create_appointment
```

---

## 🚀 EXECUTION PLAN

### Step 1: Update Agent via API ✅
```bash
PATCH https://api.vapi.ai/assistant/ade4b8c5-8d35-465b-a8f2-1db21557d5a2
```

**Changes:**
- Add MCP tools to model.tools
- Add serverMessages for webhooks
- Prepend MCP instructions to system prompt

### Step 2: Configure VAPI Webhooks (Manual) ⚠️
Go to https://dashboard.vapi.ai/settings
Add webhook URL: `https://vapi-mcp-server.aijesusbro-brain.workers.dev/webhooks/vapi`
Enable: "End of Call Report"

### Step 3: Test Call ✅
Call (323) 968-5736
Verify:
- Agent answers
- Agent uses ghl_search_contact automatically
- Webhook fires after call
- Data shows in vapi-mcp-server logs

---

## 📝 UPDATED SYSTEM PROMPT (FULL)

```
**🔧 MCP TOOLS - REAL-TIME CRM INTEGRATION:**

At the START of EVERY call, you MUST execute ghl_search_contact with the caller's phone number ({{customer.number}}) to identify them BEFORE engaging deeply. This gives you their contact info from GoHighLevel CRM.

Available tools:
1. ghl_search_contact(phone) - Look up caller in CRM (USE FIRST!)
2. ghl_create_appointment(...) - Book discovery calls directly in calendar
3. ghl_add_note(contact_id, note) - Document call outcomes in CRM
4. send_followup_sms(...) - Send SMS follow-ups

**Example execution:**
1. Answer: "Hey there! You've reached [Your Name]'s AI assistant..."
2. Execute: ghl_search_contact(phone="{{customer.number}}")
3. If found: "Hi [FirstName]! Great to hear from you."
4. Continue conversation
5. Document: ghl_add_note(contact_id, "Called {{now}}. Qualified as [status]. Next: [action]")
6. Book: ghl_create_appointment(...) when ready

---

# IDENTITY & ROLE
You are the AI assistant for John Kruze's business. You handle inbound inquiries about AI automation services and voice agents.

[... rest of original 8643 char prompt ...]
```

---

## ✅ SUCCESS CRITERIA

**After upgrade, calling 323 should:**
1. ✅ Agent answers with greeting
2. ✅ Agent executes ghl_search_contact({{customer.number}}) automatically
3. ✅ If caller in GHL: Agent says "Hi [Name]!"
4. ✅ Agent can book appointments with ghl_create_appointment
5. ✅ Agent documents calls with ghl_add_note
6. ✅ Webhook fires after call
7. ✅ Transcript + tool logs saved to D1
8. ✅ Viewable in vapi-mcp-server admin endpoints

---

## 🎯 WHY THIS WORKS

**Before:**
- Agent talks to prospects
- No CRM integration
- Manual follow-up needed
- No call data stored

**After:**
- Agent identifies callers automatically via GHL lookup
- Books appointments directly in calendar
- Documents every interaction in CRM
- Full call history stored and queryable
- Complete audit trail of tool usage

---

## 🔗 MONITORING

**During test call:**
```bash
cd "/Users/aijesusbro/AI Projects/vapi-mcp-server"
npm run tail
```

**After call:**
```bash
curl "https://vapi-mcp-server.aijesusbro-brain.workers.dev/admin/calls?client_id=aijesusbro&limit=5"
```

**Check D1:**
```bash
wrangler d1 execute vapi-calls-db --remote --command="
SELECT * FROM vapi_calls ORDER BY started_at DESC LIMIT 5
"
```

---

## 🚨 CRITICAL WEBHOOK URL

**Add to VAPI Dashboard → Settings → Webhooks:**
```
https://vapi-mcp-server.aijesusbro-brain.workers.dev/webhooks/vapi
```

**Enable:** End of Call Report

---

**Ready to execute?** Say "do it" and I'll upgrade the Spectrum agent on 323 right now. 🚀
