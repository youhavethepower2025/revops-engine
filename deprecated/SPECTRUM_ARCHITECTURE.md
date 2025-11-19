# 🏗️ SPECTRUM ARCHITECTURE: WHERE PROMPTS AND CONTEXT LIVE

**The Critical Question:** Where does prompt and context live for Spectrum interface?

**The Answer:** This IS the model for everything you're building.

---

## THE CORE ARCHITECTURAL DECISION

You have 4 layers of "context" that need to live somewhere:

1. **Agent Definition** (Who is this agent? What's their role?)
2. **Agent Prompt** (System prompt defining behavior)
3. **Data Access** (Which APIs can this agent call?)
4. **Conversation Context** (History of this specific conversation)

**Where each lives:**

---

## LAYER 1: AGENT DEFINITIONS (Database)

**Store in PostgreSQL** (your MCP brain database)

```sql
CREATE TABLE spectrum_agents (
  id UUID PRIMARY KEY,
  name TEXT NOT NULL,                    -- "Sales Agent", "CFO Agent"
  role TEXT NOT NULL,                    -- "sales", "cfo", "cmo"
  description TEXT,                       -- "Helps prioritize leads and close deals"
  icon TEXT,                             -- "💼" or URL to icon
  system_prompt TEXT NOT NULL,           -- The actual LLM system prompt
  temperature FLOAT DEFAULT 0.7,         -- LLM temperature
  model TEXT DEFAULT 'gpt-4',            -- Which LLM to use

  -- Data access configuration
  data_sources JSONB,                    -- ["crm", "stripe", "analytics"]
  api_permissions JSONB,                 -- {"crm": ["read", "write"], "stripe": ["read"]}

  -- UI configuration
  color TEXT DEFAULT '#3b82f6',          -- Brand color for this agent
  position INTEGER,                       -- Order in sidebar
  enabled BOOLEAN DEFAULT true,

  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);
```

**Example Agent Definition:**

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "name": "Sales Agent",
  "role": "sales",
  "description": "Helps you prioritize leads and close deals",
  "icon": "💼",
  "system_prompt": "You are a Sales Agent for {company_name}. You have access to the CRM and can help with:\n- Lead prioritization\n- Contact lookup\n- Opportunity tracking\n- Appointment scheduling\n\nWhen asked about leads, always pull real data from the CRM. Prioritize by:\n1. Recent engagement (last contacted, email opens)\n2. Deal stage (closer to close = higher priority)\n3. Deal value\n\nBe concise and actionable. Always suggest next steps.",
  "temperature": 0.7,
  "model": "gpt-4",
  "data_sources": ["crm", "calendar"],
  "api_permissions": {
    "crm": ["read", "write"],
    "calendar": ["read", "write"]
  },
  "color": "#3b82f6",
  "position": 1,
  "enabled": true
}
```

**Why database, not code?**
- You can update prompts without deploying
- You can A/B test different prompts
- You can add new agents dynamically
- Clients can customize their agents (future: white-label)

---

## LAYER 2: SYSTEM PROMPTS (Dynamic Template)

**System prompts live in agent definition but get populated at runtime**

**Template with variables:**
```
You are a {role_name} for {company_name}.

Your responsibilities:
{responsibilities}

You have access to:
{available_data_sources}

Current business context:
- Company: {company_name}
- Industry: {company_industry}
- Stage: {company_stage}

When answering questions:
1. Always pull real data from available sources
2. {role_specific_instructions}
3. Be concise and actionable
4. Suggest next steps

Current date: {current_date}
User asking: {user_name} ({user_role})
```

**At conversation start, template gets populated:**

```javascript
// When user starts conversation with Sales Agent
const agent = await db.spectrum_agents.findOne({ role: 'sales' });
const company = await db.companies.findOne({ id: user.company_id });

const systemPrompt = populateTemplate(agent.system_prompt, {
  role_name: agent.name,
  company_name: company.name,
  company_industry: company.industry,
  company_stage: company.stage,
  responsibilities: agent.responsibilities,
  available_data_sources: agent.data_sources.join(', '),
  role_specific_instructions: agent.role_instructions,
  current_date: new Date().toLocaleDateString(),
  user_name: user.name,
  user_role: user.role
});

// Now send to LLM with populated context
```

---

## LAYER 3: DATA ACCESS (MCP Tools + RevOps OS)

**Agent definition specifies which data sources it can access**

**This maps to MCP tool permissions:**

```javascript
// Agent definition says: "data_sources": ["crm", "stripe", "calendar"]

// This gets translated to allowed MCP tools:
const TOOL_MAPPING = {
  'crm': [
    'revops_get_contact',
    'revops_search_contacts',
    'revops_create_contact',
    'revops_update_contact',
    'revops_search_opportunities',
    'revops_create_opportunity'
  ],
  'stripe': [
    'stripe_get_customer',
    'stripe_list_subscriptions',
    'stripe_get_revenue',
    'stripe_get_mrr'
  ],
  'calendar': [
    'calendar_get_availability',
    'calendar_book_appointment',
    'calendar_list_appointments'
  ],
  'analytics': [
    'ga4_get_traffic',
    'ga4_get_conversions',
    'ga4_get_sources'
  ]
};

// When Sales Agent asks a question:
// 1. User: "Who should I call today?"
// 2. System loads allowed tools for Sales Agent
// 3. LLM can only call tools in allowed list
// 4. LLM calls: revops_search_contacts({ status: 'lead', sort: 'priority' })
// 5. MCP server executes via RevOps OS
// 6. Results returned to LLM
// 7. LLM formats answer for user
```

**Where tool definitions live:** Your existing MCP server (`mcp-code/brain_server.py`)

**Where RevOps OS lives:** `/Users/aijesusbro/AI Projects/revopsOS/` (becomes the CRM abstraction layer)

**Flow:**
```
User asks Sales Agent question
    ↓
Frontend sends to backend
    ↓
Backend loads Sales Agent definition
    ↓
Backend calls LLM with system prompt + allowed tools
    ↓
LLM decides it needs CRM data
    ↓
LLM calls: revops_search_contacts(...)
    ↓
MCP server routes to RevOps OS
    ↓
RevOps OS routes to GHL (or HubSpot, Salesforce)
    ↓
Data returns to LLM
    ↓
LLM formats answer
    ↓
Answer shown to user in chat
```

---

## LAYER 4: CONVERSATION CONTEXT (Database + Redis)

**Conversation history stored in PostgreSQL:**

```sql
CREATE TABLE spectrum_conversations (
  id UUID PRIMARY KEY,
  user_id UUID NOT NULL,
  agent_id UUID NOT NULL,                -- Which agent (Sales, CFO, etc.)
  company_id UUID NOT NULL,              -- Which company
  started_at TIMESTAMP DEFAULT NOW(),
  last_message_at TIMESTAMP DEFAULT NOW(),
  message_count INTEGER DEFAULT 0,
  metadata JSONB                         -- Custom fields
);

CREATE TABLE spectrum_messages (
  id UUID PRIMARY KEY,
  conversation_id UUID NOT NULL,
  role TEXT NOT NULL,                    -- 'user', 'assistant', 'system'
  content TEXT NOT NULL,
  tool_calls JSONB,                      -- If LLM called MCP tools
  tool_results JSONB,                    -- Results from tool calls
  tokens_used INTEGER,
  created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_conversation_messages
  ON spectrum_messages(conversation_id, created_at);
```

**Recent context cached in Redis:**

```javascript
// Key: spectrum:conversation:{conversation_id}:context
// Value: Last 10 messages + agent definition
// TTL: 1 hour

const conversationContext = {
  agent: { /* agent definition */ },
  messages: [
    { role: 'user', content: 'Who should I call today?' },
    { role: 'assistant', content: 'Based on your CRM...' },
    // ... last 10 messages
  ],
  metadata: {
    company_id: 'xxx',
    user_id: 'yyy',
    last_tool_calls: [...]
  }
};

// On each new message:
// 1. Load from Redis (fast)
// 2. If not in Redis, load from PostgreSQL
// 3. Add new message
// 4. Send to LLM
// 5. Store result
// 6. Update Redis cache
```

**Why both PostgreSQL and Redis?**
- PostgreSQL = permanent storage, full history, analytics
- Redis = fast access for active conversations, expires after 1 hour of inactivity

---

## THE COMPLETE DATA FLOW

### Scenario: User asks Sales Agent "Who should I call today?"

**Step 1: Load Agent Context**
```javascript
// Frontend sends message
POST /api/chat/send {
  agent_role: 'sales',
  message: 'Who should I call today?',
  conversation_id: 'abc-123' // or null for new conversation
}

// Backend handler
async function handleChatMessage(req) {
  const { agent_role, message, conversation_id } = req.body;
  const user = req.user; // From auth token

  // 1. Load agent definition from database
  const agent = await db.spectrum_agents.findOne({
    role: agent_role,
    company_id: user.company_id,
    enabled: true
  });

  if (!agent) throw new Error('Agent not found');
```

**Step 2: Load Conversation History**
```javascript
  // 2. Load or create conversation
  let conversation;
  if (conversation_id) {
    // Load existing conversation from Redis (fast)
    conversation = await redis.get(`spectrum:conversation:${conversation_id}`);

    if (!conversation) {
      // Not in cache, load from PostgreSQL
      conversation = await db.spectrum_conversations.findOne({ id: conversation_id });
      const messages = await db.spectrum_messages.find({
        conversation_id,
        order: 'created_at DESC',
        limit: 10
      });
      conversation.messages = messages.reverse();
    }
  } else {
    // New conversation
    conversation = await db.spectrum_conversations.create({
      user_id: user.id,
      agent_id: agent.id,
      company_id: user.company_id
    });
    conversation.messages = [];
  }
```

**Step 3: Build Context for LLM**
```javascript
  // 3. Build system prompt with company context
  const company = await db.companies.findOne({ id: user.company_id });

  const systemPrompt = populateTemplate(agent.system_prompt, {
    company_name: company.name,
    company_industry: company.industry,
    user_name: user.name,
    current_date: new Date().toLocaleDateString(),
    // ... other variables
  });

  // 4. Build message history for LLM
  const messages = [
    { role: 'system', content: systemPrompt },
    ...conversation.messages.map(m => ({
      role: m.role,
      content: m.content
    })),
    { role: 'user', content: message }
  ];
```

**Step 4: Get Allowed Tools**
```javascript
  // 5. Get allowed tools for this agent
  const allowedTools = getToolsForAgent(agent.data_sources);

  // data_sources: ['crm', 'calendar']
  // becomes tools: ['revops_get_contact', 'revops_search_contacts',
  //                 'calendar_get_availability', ...]
```

**Step 5: Call LLM with MCP Tools**
```javascript
  // 6. Call LLM (OpenAI, Anthropic, etc.)
  const response = await callLLMWithTools({
    model: agent.model,
    temperature: agent.temperature,
    messages: messages,
    tools: allowedTools,
    mcpServer: mcpServerUrl // http://localhost:8080 or CloudflareMCP URL
  });

  // LLM might call tools:
  // Tool call: revops_search_contacts({ status: 'lead', limit: 5 })
  // MCP server executes via RevOps OS
  // RevOps OS queries GHL
  // Results: [{ name: 'John Doe', company: 'TechCorp', ... }, ...]
  // LLM receives results and formats answer
```

**Step 6: Store Results**
```javascript
  // 7. Store user message
  await db.spectrum_messages.create({
    conversation_id: conversation.id,
    role: 'user',
    content: message
  });

  // 8. Store assistant response
  await db.spectrum_messages.create({
    conversation_id: conversation.id,
    role: 'assistant',
    content: response.content,
    tool_calls: response.tool_calls,
    tool_results: response.tool_results,
    tokens_used: response.usage.total_tokens
  });

  // 9. Update conversation
  await db.spectrum_conversations.update(conversation.id, {
    last_message_at: new Date(),
    message_count: conversation.message_count + 2
  });

  // 10. Update Redis cache
  conversation.messages.push(
    { role: 'user', content: message },
    { role: 'assistant', content: response.content }
  );
  await redis.setex(
    `spectrum:conversation:${conversation.id}`,
    3600, // 1 hour TTL
    JSON.stringify(conversation)
  );

  // 11. Return response to frontend
  return {
    conversation_id: conversation.id,
    message: response.content,
    tool_calls: response.tool_calls // For debugging/transparency
  };
}
```

---

## WHERE EVERYTHING LIVES (SUMMARY)

| Component | Storage | Why |
|-----------|---------|-----|
| **Agent Definitions** | PostgreSQL (`spectrum_agents` table) | Permanent, queryable, can update without deploy |
| **System Prompts** | In agent definition, populated at runtime | Templates with variables, flexible |
| **Available Tools** | MCP Server (`mcp-code/brain_server.py`) | Already exists, 70+ tools ready |
| **Tool Permissions** | Agent definition (`data_sources` field) | Maps to allowed MCP tools |
| **Conversation History** | PostgreSQL (`spectrum_messages` table) | Permanent storage, analytics |
| **Active Conversation Cache** | Redis (`spectrum:conversation:{id}`) | Fast access, expires after 1 hour |
| **Company Context** | PostgreSQL (`companies` table) | Business metadata |
| **User Context** | PostgreSQL (`users` table) | Who is asking questions |

---

## THE ACTUAL IMPLEMENTATION STACK

```
┌─────────────────────────────────────────────────────┐
│           FRONTEND (Cloudflare Pages)               │
│                                                      │
│  - Chat interface (Next.js or Svelte)               │
│  - Agent sidebar (loads from API)                   │
│  - Message display                                  │
│  - Context panel (shows tool calls)                 │
└──────────────────┬──────────────────────────────────┘
                   │
                   │ HTTP/WebSocket
                   ↓
┌─────────────────────────────────────────────────────┐
│      BACKEND API (Cloudflare Workers or Railway)    │
│                                                      │
│  - Chat handler (/api/chat/send)                    │
│  - Agent loader (from PostgreSQL)                   │
│  - LLM orchestrator (OpenAI/Anthropic)              │
│  - Conversation manager (PostgreSQL + Redis)        │
└──────────────────┬──────────────────────────────────┘
                   │
        ┌──────────┴─────────────┐
        ↓                        ↓
┌──────────────────┐    ┌───────────────────┐
│   PostgreSQL     │    │   Redis Cache     │
│                  │    │                   │
│ - spectrum_agents│    │ - Active convos   │
│ - conversations  │    │ - TTL: 1 hour     │
│ - messages       │    │                   │
│ - companies      │    └───────────────────┘
│ - users          │
└──────────────────┘
        │
        │ When LLM needs data
        ↓
┌─────────────────────────────────────────────────────┐
│         MCP SERVER (localhost:8080 or Cloud)        │
│                                                      │
│  - Existing brain_server.py (70+ tools)             │
│  - Tool execution                                   │
│  - Routes to RevOps OS                              │
└──────────────────┬──────────────────────────────────┘
                   │
                   ↓
┌─────────────────────────────────────────────────────┐
│              REVOPS OS (CRM Abstraction)            │
│                                                      │
│  - Unified CRM interface                            │
│  - GHL adapter, HubSpot adapter, etc.               │
│  - Database: contacts, opportunities, etc.          │
└──────────────────┬──────────────────────────────────┘
                   │
        ┌──────────┴──────────┬──────────┐
        ↓                     ↓          ↓
   ┌────────┐         ┌──────────┐  ┌────────┐
   │  GHL   │         │ HubSpot  │  │ Stripe │
   │  API   │         │   API    │  │  API   │
   └────────┘         └──────────┘  └────────┘
```

---

## EXAMPLE: ACTUAL AGENT DEFINITIONS YOU WOULD CREATE

### Sales Agent
```json
{
  "name": "Sales Agent",
  "role": "sales",
  "system_prompt": "You are a Sales Agent for {company_name}. Help prioritize leads and close deals.\n\nYou can:\n- Search contacts in CRM\n- View opportunity pipeline\n- Book appointments\n\nWhen asked about leads, pull real CRM data and prioritize by:\n1. Recent engagement\n2. Deal stage\n3. Deal value\n\nBe concise and suggest next actions.",
  "data_sources": ["crm", "calendar"],
  "model": "gpt-4"
}
```

### Operations Agent (what you actually need first)
```json
{
  "name": "Operations Agent",
  "role": "operations",
  "system_prompt": "You are an Operations Agent for {company_name}. Help manage daily business operations.\n\nYou can:\n- Look up contacts and leads in CRM\n- Check appointment schedules\n- View pipeline and opportunities\n- Track tasks and follow-ups\n\nWhen asked questions, always pull real data. Be specific and actionable.",
  "data_sources": ["crm", "calendar", "tasks"],
  "model": "gpt-4"
}
```

### Revenue Agent (for Rebecca/Advisory9)
```json
{
  "name": "Revenue Agent",
  "role": "revenue",
  "system_prompt": "You are a Revenue Agent for {company_name}, a strategic advisory firm.\n\nYou help with:\n- Lead qualification and prioritization\n- Revenue tracking and forecasting\n- Client engagement analysis\n- Pipeline management\n\nYou have access to:\n- CRM (contacts, opportunities)\n- Calendar (appointments, availability)\n- Revenue data (if Stripe connected)\n\nWhen asked about revenue or clients, pull real data and provide strategic insights.",
  "data_sources": ["crm", "calendar", "stripe"],
  "model": "gpt-4"
}
```

---

## THE MODEL FOR EVERYTHING YOU'RE BUILDING

**This architecture IS the model:**

1. **Agent definitions in database** → Can update without deploying
2. **System prompts as templates** → Flexible, context-aware
3. **Data access via MCP tools** → Already built, just need to wire up
4. **RevOps OS as abstraction** → CRM-agnostic, future-proof
5. **Conversation in PostgreSQL + Redis** → Fast and permanent
6. **Everything queryable** → Analytics, learning loops, A/B testing

**This same pattern works for:**
- Voice agents (Vapi) → Same agent definitions, same data access, just different interface
- Slack bots → Same backend, different frontend
- Email automation → Same agent logic, triggered differently
- Scheduled reports → Same data access, automated execution

**The agent definition IS the source of truth.**

Everything else (chat interface, voice, Slack, email) is just a different way to interact with the same agents.

---

## NEXT: LET'S BUILD THIS IN PHASES

Now that we know WHERE everything lives, I'll create a phase-by-phase implementation plan where each phase is ~1 hour of work + testing.

Would you like me to create the detailed phase breakdown now?
