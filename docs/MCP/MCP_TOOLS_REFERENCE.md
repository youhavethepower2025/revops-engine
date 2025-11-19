# RevOps OS MCP Tools Reference

**MCP Server URL:** https://revops-os-mcp-dev.aijesusbro-brain.workers.dev

This document provides complete reference for all MCP tools available to Retell voice agents and other MCP clients.

---

## Tool Discovery

### List Available Tools
```bash
curl https://revops-os-mcp-dev.aijesusbro-brain.workers.dev/mcp/tools
```

Returns JSON schema for all 7 tools with descriptions and parameter definitions.

---

## Tool 1: get_lead_by_phone

**Purpose:** Look up lead by phone number (caller ID lookup)

**Use Case:** Start of every inbound call to identify returning customers

**Input Schema:**
```json
{
  "phone": "+14155551234",     // Required: E.164 format
  "account_id": "acc_xxx"      // Optional: defaults to auth context
}
```

**Example Request:**
```bash
curl -X POST https://revops-os-mcp-dev.aijesusbro-brain.workers.dev/mcp/execute \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -d '{
    "tool": "get_lead_by_phone",
    "arguments": {
      "phone": "+14155551234"
    }
  }'
```

**Response (Found):**
```json
{
  "success": true,
  "found": true,
  "lead": {
    "id": "lead_abc123",
    "name": "Jane Doe",
    "email": "jane@acme.com",
    "company": "Acme Corp",
    "status": "qualified",
    "created_at": 1704844800000
  },
  "campaign": {
    "id": "camp_xyz",
    "name": "Q1 Outbound",
    "status": "active"
  },
  "recent_events": [
    {
      "event_type": "email_sent",
      "timestamp": 1704844800000
    }
  ]
}
```

**Response (Not Found):**
```json
{
  "success": true,
  "found": false,
  "message": "No lead found with this phone number"
}
```

**Voice Agent Usage:**
```
Agent: "Let me check if you're already in our system..."
[Calls get_lead_by_phone]
→ Found: "Welcome back, Jane! I see you spoke with us last week."
→ Not Found: "Thanks for calling! Let me get some basic info."
```

---

## Tool 2: create_lead

**Purpose:** Create new lead record from phone call

**Use Case:** Every new caller should get a lead record created

**Input Schema:**
```json
{
  "phone": "+14155551234",           // Required: E.164 format
  "name": "Jane Doe",                // Required
  "email": "jane@acme.com",          // Optional
  "company": "Acme Corp",            // Optional
  "campaign_id": "camp_xyz",         // Optional
  "account_id": "acc_xxx",           // Optional
  "initial_context": {               // Optional: any JSON
    "referral_source": "LinkedIn",
    "pain_point": "scaling outbound"
  }
}
```

**Example Request:**
```bash
curl -X POST https://revops-os-mcp-dev.aijesusbro-brain.workers.dev/mcp/execute \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -d '{
    "tool": "create_lead",
    "arguments": {
      "phone": "+14155551234",
      "name": "Jane Doe",
      "email": "jane@acme.com",
      "company": "Acme Corp",
      "initial_context": {
        "call_source": "inbound",
        "interest_level": "high"
      }
    }
  }'
```

**Response:**
```json
{
  "success": true,
  "lead_id": "lead_abc123",
  "lead": {
    "id": "lead_abc123",
    "name": "Jane Doe",
    "email": "jane@acme.com",
    "phone": "+14155551234",
    "company": "Acme Corp",
    "status": "new",
    "created_at": 1704844800000
  },
  "message": "Lead created successfully"
}
```

**Voice Agent Usage:**
```
Agent: "Great! What company are you with?"
Caller: "Acme Corp"
Agent: "And what's the best email to reach you at?"
Caller: "jane@acme.com"
[Calls create_lead with collected info]
→ Lead record created in database
```

---

## Tool 3: update_lead_status

**Purpose:** Update lead qualification status after call

**Use Case:** End of call - mark as qualified/unqualified based on conversation

**Input Schema:**
```json
{
  "lead_id": "lead_abc123",          // Required
  "status": "qualified",             // Required: new/qualified/unqualified/meeting_booked/customer/lost
  "stage": "discovery",              // Optional: pipeline stage
  "notes": "Strong fit, budget confirmed" // Optional: call notes
}
```

**Valid Status Values:**
- `new` - Just created, no qualification yet
- `qualified` - Meets criteria, good fit
- `unqualified` - Not a fit (too small, wrong model, etc.)
- `meeting_booked` - Appointment scheduled
- `customer` - Closed/won
- `lost` - Closed/lost

**Example Request:**
```bash
curl -X POST https://revops-os-mcp-dev.aijesusbro-brain.workers.dev/mcp/execute \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -d '{
    "tool": "update_lead_status",
    "arguments": {
      "lead_id": "lead_abc123",
      "status": "qualified",
      "notes": "B2B SaaS, $5M ARR, looking to replace BDR team"
    }
  }'
```

**Response:**
```json
{
  "success": true,
  "lead": {
    "id": "lead_abc123",
    "status": "qualified",
    "updated_at": 1704844800000
  },
  "message": "Lead status updated to qualified"
}
```

**Voice Agent Usage:**
```
[End of qualification call]
IF qualified:
  [Calls update_lead_status with status="qualified" + notes]
ELSE:
  [Calls update_lead_status with status="unqualified" + reason]
```

---

## Tool 4: book_appointment

**Purpose:** Schedule discovery call/meeting for qualified lead

**Use Case:** Qualified prospect wants to book - check calendar and confirm time

**Input Schema:**
```json
{
  "lead_id": "lead_abc123",          // Required
  "scheduled_at": "2025-01-15T14:00:00Z", // Required: ISO 8601 format
  "duration_minutes": 30,            // Optional: default 30
  "meeting_type": "Discovery Call",  // Optional: default "Discovery Call"
  "notes": "Interested in voice agent features" // Optional
}
```

**Meeting Type Examples:**
- `Discovery Call`
- `Demo`
- `Consultation`
- `Follow-Up`
- `Onboarding`

**Example Request:**
```bash
curl -X POST https://revops-os-mcp-dev.aijesusbro-brain.workers.dev/mcp/execute \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -d '{
    "tool": "book_appointment",
    "arguments": {
      "lead_id": "lead_abc123",
      "scheduled_at": "2025-01-15T14:00:00Z",
      "duration_minutes": 30,
      "meeting_type": "Discovery Call",
      "notes": "Prefers video call, has 3 decision makers"
    }
  }'
```

**Response:**
```json
{
  "success": true,
  "appointment": {
    "id": "appt_xyz789",
    "lead_id": "lead_abc123",
    "scheduled_at": 1705327200000,
    "duration_minutes": 30,
    "meeting_type": "Discovery Call",
    "status": "scheduled"
  },
  "message": "Appointment booked for Tue, Jan 15, 2025 2:00 PM",
  "calendar_url": null
}
```

**Side Effects:**
- Creates appointment record
- Updates lead status to `meeting_booked`
- Emits `appointment_booked` event
- (Future) Sends calendar invite via Calendly/Cal.com integration

**Voice Agent Usage:**
```
Agent: "What does your calendar look like this week?"
Caller: "I'm free Tuesday at 2pm"
Agent: "Perfect! Let me get you scheduled."
[Calls book_appointment]
Agent: "You're all set for Tuesday, January 15th at 2 PM. You'll get a calendar invite at jane@acme.com."
```

---

## Tool 5: get_campaign_context

**Purpose:** Retrieve active campaign information for a lead

**Use Case:** Understand what campaign lead is part of, see messaging strategy

**Input Schema:**
```json
{
  "campaign_id": "camp_xyz",         // Optional: direct lookup
  "lead_id": "lead_abc123"           // Optional: find via lead
}
```

**Note:** Must provide either `campaign_id` OR `lead_id`

**Example Request:**
```bash
curl -X POST https://revops-os-mcp-dev.aijesusbro-brain.workers.dev/mcp/execute \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -d '{
    "tool": "get_campaign_context",
    "arguments": {
      "lead_id": "lead_abc123"
    }
  }'
```

**Response:**
```json
{
  "success": true,
  "campaign": {
    "id": "camp_xyz",
    "name": "Q1 B2B SaaS Outbound",
    "status": "active",
    "config": {
      "target_audience": "B2B SaaS founders, $1-10M ARR",
      "value_proposition": "Replace BDR team with autonomous AI agents"
    }
  },
  "stats": {
    "total_leads": 250,
    "contacted": 180,
    "replied": 45,
    "qualified": 23,
    "reply_rate": 0.25
  }
}
```

**Voice Agent Usage:**
```
[Caller mentions they got an email]
[Calls get_campaign_context to see which campaign they're in]
→ Understand messaging angle they've already seen
→ Avoid repeating same pitch
→ Personalize based on campaign strategy
```

---

## Tool 6: create_campaign

**Purpose:** Create new outreach campaign

**Use Case:** Admin/setup - not typically used by voice agents

**Input Schema:**
```json
{
  "name": "Q1 B2B SaaS Outbound",    // Required
  "target_audience": "B2B SaaS founders, $1-10M ARR", // Required
  "value_proposition": "Replace BDR team with AI", // Required
  "account_id": "acc_xxx"            // Optional: defaults to auth context
}
```

**Example Request:**
```bash
curl -X POST https://revops-os-mcp-dev.aijesusbro-brain.workers.dev/mcp/execute \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -d '{
    "tool": "create_campaign",
    "arguments": {
      "name": "Q1 Enterprise Outbound",
      "target_audience": "Enterprise B2B companies, 500+ employees",
      "value_proposition": "Autonomous revenue operations at scale"
    }
  }'
```

**Response:**
```json
{
  "success": true,
  "campaign_id": "camp_xyz",
  "campaign": {
    "id": "camp_xyz",
    "name": "Q1 Enterprise Outbound",
    "status": "draft",
    "created_at": 1704844800000
  },
  "message": "Campaign created successfully"
}
```

---

## Tool 7: add_leads

**Purpose:** Bulk import leads into a campaign

**Use Case:** Admin/setup - import prospect lists

**Input Schema:**
```json
{
  "campaign_id": "camp_xyz",         // Required
  "leads": [                         // Required: array of lead objects
    {
      "name": "Jane Doe",            // Required
      "email": "jane@acme.com",      // Required
      "phone": "+14155551234",       // Optional
      "company": "Acme Corp",        // Optional
      "website": "https://acme.com"  // Optional
    }
  ]
}
```

**Example Request:**
```bash
curl -X POST https://revops-os-mcp-dev.aijesusbro-brain.workers.dev/mcp/execute \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -d '{
    "tool": "add_leads",
    "arguments": {
      "campaign_id": "camp_xyz",
      "leads": [
        {
          "name": "Jane Doe",
          "email": "jane@acme.com",
          "company": "Acme Corp"
        },
        {
          "name": "John Smith",
          "email": "john@example.com",
          "company": "Example Inc"
        }
      ]
    }
  }'
```

**Response:**
```json
{
  "success": true,
  "created_count": 2,
  "leads": [
    { "id": "lead_abc123", "name": "Jane Doe" },
    { "id": "lead_def456", "name": "John Smith" }
  ],
  "message": "2 leads added to campaign"
}
```

---

## Common Patterns

### Pattern 1: Inbound Call Flow
```
1. get_lead_by_phone(caller_phone)
   → Check if returning customer

2. IF not found:
     create_lead(phone, name, company, email)
     → Create new record

3. [Qualification conversation]

4. IF qualified:
     book_appointment(lead_id, scheduled_at)
     → Schedule discovery call

5. update_lead_status(lead_id, "qualified")
   → Mark final status
```

### Pattern 2: Error Handling
All tools return `success: true/false`

**On Error:**
```json
{
  "success": false,
  "error": "Lead not found"
}
```

**Voice Agent Response:**
"I'm having a bit of trouble with that. Let me try again..." or handle gracefully

### Pattern 3: Authentication
MCP server expects JWT token in Authorization header:
```
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

Token should contain:
- `user_id`
- `account_id`
- Valid signature

---

## Testing Tools

### Manual Testing (curl)
```bash
# Health check
curl https://revops-os-mcp-dev.aijesusbro-brain.workers.dev/health

# List tools
curl https://revops-os-mcp-dev.aijesusbro-brain.workers.dev/mcp/tools

# Execute tool (requires valid JWT)
curl -X POST https://revops-os-mcp-dev.aijesusbro-brain.workers.dev/mcp/execute \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "tool": "get_lead_by_phone",
    "arguments": { "phone": "+14155551234" }
  }'
```

### Retell Voice Agent Testing
1. Create agent in Retell dashboard
2. Set MCP URL: `https://revops-os-mcp-dev.aijesusbro-brain.workers.dev`
3. Agent prompt should reference available tools
4. Make test call to trigger tool usage
5. Check logs:
   ```bash
   npx wrangler tail --env dev --format pretty
   ```

---

## Performance Expectations

- **Response Time:** <500ms average (edge-optimized)
- **Rate Limits:** None currently (will add per-account limits in production)
- **Concurrency:** Unlimited (Cloudflare Workers auto-scale)
- **Availability:** 99.9% (Cloudflare SLA)

---

## Changelog

**2025-01-09:** Initial MCP server deployment
- 7 tools available
- Integrated with RevOps OS API
- Deployed to Cloudflare Workers edge network
- Ready for Retell voice agent integration
