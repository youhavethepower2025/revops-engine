# 🌈 SPECTRUM: CLOUDFLARE-NATIVE BUILD PLAN

**End Goal:** `aijesusbro.com/spectrum` - Your sales demo that IS the production infrastructure

**Architecture:** Same stack clients get = Cloudflare Workers + Pages + D1

---

## THE INFRASTRUCTURE STRATEGY

### What You Already Have

**1. CloudflareMCP** (`retell-brain-mcp`)
- **Purpose:** Multi-tenant MCP server (tool execution layer)
- **Location:** Deployed to Cloudflare Workers
- **Features:** Durable Objects, D1 database, MCP protocol
- **Tools:** remember, recall, search_memory, Retell tools, GHL tools
- **Multi-tenant:** Route by `?client_id=XXX`
- **Status:** ✅ Built, ready to use

**2. RevOps OS** (`revops-os-dev`)
- **Purpose:** Autonomous revenue operations (business logic layer)
- **Location:** `aijesusbro.com/revops/*`
- **Features:** Durable Objects, D1, Workers AI, Vectorize, Browser
- **Has:** MCP endpoint, event sourcing, voice agent
- **Status:** ✅ Live in production since Oct 10

### What You Need to Build

**3. Spectrum** (new)
- **Frontend:** Cloudflare Pages → `aijesusbro.com/spectrum`
- **Backend:** Cloudflare Worker → `spectrum-api`
- **Database:** D1 → `spectrum-db` (agent definitions, conversations)
- **Integrates with:** CloudflareMCP (tools) + RevOps OS (CRM)
- **Multi-tenant:** Same `?client_id=XXX` pattern
- **Status:** ❌ Not built yet

---

## THE COMPLETE STACK

```
┌─────────────────────────────────────────────────────────┐
│         SPECTRUM FRONTEND (Cloudflare Pages)            │
│         aijesusbro.com/spectrum                         │
│                                                          │
│  - Chat interface                                       │
│  - Agent sidebar                                        │
│  - Context panel                                        │
│  - Built with: HTML/JS or Svelte                        │
└────────────────────┬────────────────────────────────────┘
                     │ HTTPS
                     ↓
┌─────────────────────────────────────────────────────────┐
│         SPECTRUM API (Cloudflare Worker)                │
│         spectrum-api.aijesusbro-brain.workers.dev       │
│                                                          │
│  - POST /chat/send                                      │
│  - GET /agents                                          │
│  - GET /conversations                                   │
│  - Routes by client_id parameter                        │
└────────────────────┬────────────────────────────────────┘
                     │
        ┌────────────┴────────────┐
        ↓                         ↓
┌──────────────────┐    ┌─────────────────────────┐
│  D1 Database     │    │  Durable Objects        │
│  (spectrum-db)   │    │  (ConversationState)    │
│                  │    │                         │
│ - spectrum_agents│    │ - Active convos cached  │
│ - conversations  │    │ - Per-client isolation  │
│ - messages       │    │                         │
└──────────────────┘    └─────────────────────────┘
        │
        │ When LLM needs tools
        ↓
┌─────────────────────────────────────────────────────────┐
│         CLOUDFLAREMCP (existing deployment)             │
│         retell-brain-mcp.workers.dev                    │
│                                                          │
│  - MCP protocol endpoint                                │
│  - Tool execution: remember, recall, ghl_search, etc.   │
│  - Routes by client_id                                  │
└────────────────────┬────────────────────────────────────┘
                     │
        ┌────────────┴────────────┐
        ↓                         ↓
┌──────────────────┐    ┌─────────────────────────┐
│  REVOPS OS       │    │  External APIs          │
│  (CRM layer)     │    │                         │
│                  │    │  - GHL                  │
│ - MCP endpoint   │    │  - Stripe               │
│ - CRM abstraction│    │  - Calendar             │
│ - Event sourcing │    │  - Vapi (voice)         │
└──────────────────┘    └─────────────────────────┘
```

---

## WHY THIS ARCHITECTURE WINS

**For Your Demo (aijesusbro.com/spectrum):**
- ✅ Send one link, people see it instantly
- ✅ Talks to YOUR real business data (GHL, Stripe, etc.)
- ✅ Fast (Cloudflare edge, <50ms globally)
- ✅ Always up (Cloudflare's network)
- ✅ Professional (not localhost:8000)

**For Client Deployments:**
- ✅ Exact same infrastructure
- ✅ Just change `client_id` parameter
- ✅ Their branded URL: `client.com/spectrum`
- ✅ Their data (isolated Durable Object + D1 namespace)
- ✅ Deploy in 30 seconds

**For Scaling:**
- ✅ 1 client = works
- ✅ 100 clients = same deployment
- ✅ 1000 clients = still same deployment
- ✅ Cost: $5-20/month total (not per client!)

**This is the model you sell:**
"You get the exact infrastructure I'm using right now. Same speed, same reliability, same features. Just with your branding and your data."

---

## PHASE-BY-PHASE BUILD (1-Hour Blocks)

### PHASE 0: Setup Spectrum Infrastructure (1.5 hours)

**Goal:** Create Cloudflare project structure

#### Phase 0.1: Create Spectrum Project (30 min)

```bash
# Create project directory
cd /Users/aijesusbro/AI\ Projects/
mkdir spectrum
cd spectrum

# Initialize npm project
npm init -y

# Install dependencies
npm install wrangler --save-dev
npm install @anthropic-ai/sdk

# Create wrangler.toml
cat > wrangler.toml << 'EOF'
name = "spectrum-api"
main = "src/index.ts"
compatibility_date = "2024-10-18"
node_compat = true

# D1 Database for agent definitions
[[d1_databases]]
binding = "DB"
database_name = "spectrum-db"
database_id = ""  # Will populate after creation

# Durable Objects for conversation state
[[durable_objects.bindings]]
name = "CONVERSATION"
class_name = "ConversationState"
script_name = "spectrum-api"

[[migrations]]
tag = "v1"
new_sqlite_classes = ["ConversationState"]

# Environment variables
[vars]
ENVIRONMENT = "production"
CLOUDFLAREMCP_URL = "https://retell-brain-mcp.aijesusbro-brain.workers.dev"
REVOPS_OS_URL = "https://aijesusbro-brain.workers.dev/revops"

# Secrets (set via: wrangler secret put <KEY>)
# ANTHROPIC_API_KEY
EOF

# Create source directory
mkdir src
```

**Test:** `npm list` shows wrangler installed

---

#### Phase 0.2: Create D1 Database (15 min)

```bash
# Login to Cloudflare
npx wrangler login

# Create D1 database
npx wrangler d1 create spectrum-db
```

**Copy the `database_id` from output and paste into `wrangler.toml`**

**Create schema file:**
```bash
cat > schema.sql << 'EOF'
-- Agent Definitions
CREATE TABLE spectrum_agents (
  id TEXT PRIMARY KEY,
  client_id TEXT NOT NULL,
  name TEXT NOT NULL,
  role TEXT NOT NULL,
  description TEXT,
  system_prompt TEXT NOT NULL,
  temperature REAL DEFAULT 0.7,
  model TEXT DEFAULT 'claude-sonnet-3-5-20241022',
  data_sources TEXT DEFAULT '[]',  -- JSON array as text
  color TEXT DEFAULT '#3b82f6',
  position INTEGER,
  enabled INTEGER DEFAULT 1,
  created_at INTEGER DEFAULT (unixepoch()),
  updated_at INTEGER DEFAULT (unixepoch())
);

CREATE INDEX idx_agents_client ON spectrum_agents(client_id, enabled);
CREATE UNIQUE INDEX idx_agents_role ON spectrum_agents(client_id, role);

-- Conversations
CREATE TABLE spectrum_conversations (
  id TEXT PRIMARY KEY,
  client_id TEXT NOT NULL,
  user_id TEXT,
  agent_id TEXT NOT NULL,
  started_at INTEGER DEFAULT (unixepoch()),
  last_message_at INTEGER DEFAULT (unixepoch()),
  message_count INTEGER DEFAULT 0,
  metadata TEXT DEFAULT '{}'  -- JSON object as text
);

CREATE INDEX idx_conversations_client ON spectrum_conversations(client_id, last_message_at DESC);

-- Messages
CREATE TABLE spectrum_messages (
  id TEXT PRIMARY KEY,
  conversation_id TEXT NOT NULL,
  role TEXT NOT NULL,
  content TEXT NOT NULL,
  tool_calls TEXT,  -- JSON array as text
  tool_results TEXT,  -- JSON array as text
  tokens_used INTEGER,
  created_at INTEGER DEFAULT (unixepoch())
);

CREATE INDEX idx_messages_conversation ON spectrum_messages(conversation_id, created_at);
EOF
```

**Execute schema:**
```bash
npx wrangler d1 execute spectrum-db --file=schema.sql
```

**Test:**
```bash
npx wrangler d1 execute spectrum-db --command="SELECT name FROM sqlite_master WHERE type='table';"
```

Should show: `spectrum_agents`, `spectrum_conversations`, `spectrum_messages`

---

#### Phase 0.3: Seed Reality Agent (30 min)

```bash
cat > seed.sql << 'EOF'
-- Insert Reality Agent for aijesusbro client
INSERT INTO spectrum_agents (
  id,
  client_id,
  name,
  role,
  description,
  system_prompt,
  data_sources,
  position
) VALUES (
  'agent_aijesusbro_reality',
  'aijesusbro',
  'Reality Agent',
  'reality',
  'Orchestrates AI Jesus Bro business operations',
  'You are the Reality Agent for AI Jesus Bro.

Your purpose: Orchestrate business operations through API integrations.

You have access to:
- CRM (GoHighLevel): Contacts, leads, opportunities, pipeline
- Calendar: Appointments, availability
- Voice: Call logs, transcripts from Vapi
- Revenue: Stripe data (when connected)

When asked questions:
1. ALWAYS pull real data from available tools (never make up data)
2. Be specific: names, numbers, dates
3. Prioritize actions that move revenue forward
4. Suggest concrete next steps
5. Show reasoning behind recommendations

Context:
- Running on Cloudflare edge infrastructure
- Multi-client architecture
- Event sourcing captures every interaction
- Learning from usage patterns

Style: Direct, strategic, actionable. No corporate fluff.

Current date: {current_date}
Client: AI Jesus Bro',
  '["crm","calendar","voice"]',
  1
);
EOF

npx wrangler d1 execute spectrum-db --file=seed.sql
```

**Test:**
```bash
npx wrangler d1 execute spectrum-db --command="SELECT name, role, client_id FROM spectrum_agents;"
```

Should show: Reality Agent for aijesusbro client

---

### PHASE 1: Build Spectrum API Worker (2.5 hours)

#### Phase 1.1: Basic Worker + Chat Endpoint (1 hour)

**Create:** `src/index.ts`

```typescript
import Anthropic from '@anthropic-ai/sdk';

interface Env {
  DB: D1Database;
  CONVERSATION: DurableObjectNamespace;
  ANTHROPIC_API_KEY: string;
  CLOUDFLAREMCP_URL: string;
  REVOPS_OS_URL: string;
}

interface ChatRequest {
  agent_role: string;
  message: string;
  conversation_id?: string;
}

export default {
  async fetch(request: Request, env: Env): Promise<Response> {
    const url = new URL(request.url);
    const client_id = url.searchParams.get('client_id') || 'aijesusbro';

    // CORS headers
    const corsHeaders = {
      'Access-Control-Allow-Origin': '*',
      'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
      'Access-Control-Allow-Headers': 'Content-Type',
    };

    if (request.method === 'OPTIONS') {
      return new Response(null, { headers: corsHeaders });
    }

    // Health check
    if (url.pathname === '/health') {
      return Response.json({ status: 'ok', client_id }, { headers: corsHeaders });
    }

    // List agents
    if (url.pathname === '/agents' && request.method === 'GET') {
      const agents = await env.DB.prepare(
        'SELECT id, name, role, description, color, position FROM spectrum_agents WHERE client_id = ? AND enabled = 1 ORDER BY position'
      ).bind(client_id).all();

      return Response.json({ agents: agents.results }, { headers: corsHeaders });
    }

    // Chat endpoint
    if (url.pathname === '/chat/send' && request.method === 'POST') {
      const body = await request.json() as ChatRequest;

      // Load agent
      const agent = await env.DB.prepare(
        'SELECT * FROM spectrum_agents WHERE client_id = ? AND role = ? AND enabled = 1'
      ).bind(client_id, body.agent_role).first();

      if (!agent) {
        return Response.json({ error: 'Agent not found' }, { status: 404, headers: corsHeaders });
      }

      // Initialize Anthropic
      const anthropic = new Anthropic({
        apiKey: env.ANTHROPIC_API_KEY,
      });

      // For now: Simple message (no conversation history - Phase 1.2)
      const system_prompt = (agent.system_prompt as string).replace(
        '{current_date}',
        new Date().toLocaleDateString()
      );

      const response = await anthropic.messages.create({
        model: agent.model as string,
        max_tokens: 1024,
        system: system_prompt,
        messages: [
          { role: 'user', content: body.message }
        ]
      });

      const reply = response.content[0].type === 'text' ? response.content[0].text : '';

      return Response.json({
        agent: agent.name,
        message: reply,
        conversation_id: null  // Add in Phase 1.2
      }, { headers: corsHeaders });
    }

    return Response.json({ error: 'Not found' }, { status: 404, headers: corsHeaders });
  }
};

// Durable Object for conversation state (Phase 1.2)
export class ConversationState implements DurableObject {
  constructor(private state: DurableObjectState, private env: Env) {}

  async fetch(request: Request): Promise<Response> {
    // Will implement in Phase 1.2
    return new Response('Conversation state');
  }
}
```

**Deploy:**
```bash
# Set API key
npx wrangler secret put ANTHROPIC_API_KEY
# Paste your Anthropic key

# Deploy
npx wrangler deploy
```

**Test:**
```bash
# Get worker URL from output, then:
WORKER_URL="https://spectrum-api.YOUR-SUBDOMAIN.workers.dev"

# Test health
curl "$WORKER_URL/health?client_id=aijesusbro"

# Test agents list
curl "$WORKER_URL/agents?client_id=aijesusbro"

# Test chat
curl -X POST "$WORKER_URL/chat/send?client_id=aijesusbro" \
  -H "Content-Type: application/json" \
  -d '{
    "agent_role": "reality",
    "message": "Hello, what can you help me with?"
  }'
```

**Expected:** JSON response with agent reply

---

#### Phase 1.2: Add Conversation History (1 hour)

**Update `src/index.ts` to use D1 for message history:**

```typescript
// In /chat/send endpoint, after loading agent:

// Load or create conversation
let conversation_id = body.conversation_id;
let messages: any[] = [];

if (conversation_id) {
  // Load existing conversation
  const convo = await env.DB.prepare(
    'SELECT * FROM spectrum_conversations WHERE id = ? AND client_id = ?'
  ).bind(conversation_id, client_id).first();

  if (convo) {
    // Load last 10 messages
    const msg_results = await env.DB.prepare(
      'SELECT role, content FROM spectrum_messages WHERE conversation_id = ? ORDER BY created_at ASC LIMIT 10'
    ).bind(conversation_id).all();

    messages = msg_results.results.map(m => ({
      role: m.role,
      content: m.content
    }));
  }
} else {
  // Create new conversation
  conversation_id = crypto.randomUUID();
  await env.DB.prepare(
    'INSERT INTO spectrum_conversations (id, client_id, agent_id) VALUES (?, ?, ?)'
  ).bind(conversation_id, client_id, agent.id).run();
}

// Add current message
messages.push({ role: 'user', content: body.message });

// Call Anthropic with history
const response = await anthropic.messages.create({
  model: agent.model as string,
  max_tokens: 1024,
  system: system_prompt,
  messages: messages
});

const reply = response.content[0].type === 'text' ? response.content[0].text : '';

// Store messages
await env.DB.prepare(
  'INSERT INTO spectrum_messages (id, conversation_id, role, content) VALUES (?, ?, ?, ?)'
).bind(crypto.randomUUID(), conversation_id, 'user', body.message).run();

await env.DB.prepare(
  'INSERT INTO spectrum_messages (id, conversation_id, role, content, tokens_used) VALUES (?, ?, ?, ?, ?)'
).bind(crypto.randomUUID(), conversation_id, 'assistant', reply, response.usage.output_tokens).run();

// Update conversation
await env.DB.prepare(
  'UPDATE spectrum_conversations SET last_message_at = unixepoch(), message_count = message_count + 2 WHERE id = ?'
).bind(conversation_id).run();

return Response.json({
  agent: agent.name,
  message: reply,
  conversation_id: conversation_id
}, { headers: corsHeaders });
```

**Deploy:**
```bash
npx wrangler deploy
```

**Test:**
```bash
# First message
RESULT=$(curl -s -X POST "$WORKER_URL/chat/send?client_id=aijesusbro" \
  -H "Content-Type: application/json" \
  -d '{"agent_role": "reality", "message": "My name is Sarah"}')

echo $RESULT

# Extract conversation_id (or copy manually from output)
CONVO_ID=$(echo $RESULT | jq -r '.conversation_id')

# Second message (should remember name)
curl -X POST "$WORKER_URL/chat/send?client_id=aijesusbro" \
  -H "Content-Type: application/json" \
  -d "{\"agent_role\": \"reality\", \"message\": \"What is my name?\", \"conversation_id\": \"$CONVO_ID\"}"
```

**Expected:** Agent remembers your name from first message

---

#### Phase 1.3: Add Conversations List Endpoint (30 min)

```typescript
// Add to fetch() handler:

if (url.pathname === '/conversations' && request.method === 'GET') {
  const convos = await env.DB.prepare(`
    SELECT
      c.id,
      c.started_at,
      c.message_count,
      a.name as agent_name,
      (SELECT content FROM spectrum_messages WHERE conversation_id = c.id ORDER BY created_at DESC LIMIT 1) as last_message
    FROM spectrum_conversations c
    JOIN spectrum_agents a ON c.agent_id = a.id
    WHERE c.client_id = ?
    ORDER BY c.last_message_at DESC
    LIMIT 20
  `).bind(client_id).all();

  return Response.json({ conversations: convos.results }, { headers: corsHeaders });
}
```

**Deploy & Test:**
```bash
npx wrangler deploy

curl "$WORKER_URL/conversations?client_id=aijesusbro"
```

---

### PHASE 2: Build Spectrum Frontend (1.5 hours)

#### Phase 2.1: Create Cloudflare Pages Site (1.5 hours)

**Create:** `frontend/index.html`

```html
<!DOCTYPE html>
<html>
<head>
  <title>Spectrum - AI Jesus Bro</title>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <style>
    * { margin: 0; padding: 0; box-sizing: border-box; }
    body {
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
      display: flex;
      height: 100vh;
      background: #0f172a;
      color: #f1f5f9;
    }

    #sidebar {
      width: 260px;
      background: #1e293b;
      padding: 24px;
      border-right: 1px solid #334155;
    }

    .logo {
      font-size: 24px;
      font-weight: 700;
      margin-bottom: 32px;
      background: linear-gradient(135deg, #3b82f6 0%, #8b5cf6 100%);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
    }

    .agent-btn {
      width: 100%;
      padding: 12px 16px;
      margin: 8px 0;
      background: #334155;
      color: #f1f5f9;
      border: none;
      border-radius: 8px;
      cursor: pointer;
      text-align: left;
      font-size: 14px;
      transition: all 0.2s;
    }

    .agent-btn:hover {
      background: #475569;
    }

    .agent-btn.active {
      background: #3b82f6;
      box-shadow: 0 4px 12px rgba(59, 130, 246, 0.4);
    }

    #chat {
      flex: 1;
      display: flex;
      flex-direction: column;
    }

    #header {
      padding: 20px 24px;
      border-bottom: 1px solid #334155;
      background: #1e293b;
    }

    #agent-name {
      font-size: 18px;
      font-weight: 600;
    }

    #messages {
      flex: 1;
      overflow-y: auto;
      padding: 24px;
    }

    .message {
      margin: 16px 0;
      padding: 16px;
      border-radius: 12px;
      max-width: 80%;
      line-height: 1.6;
    }

    .user {
      background: #3b82f6;
      margin-left: auto;
    }

    .assistant {
      background: #334155;
    }

    #input-area {
      padding: 24px;
      border-top: 1px solid #334155;
      background: #1e293b;
      display: flex;
      gap: 12px;
    }

    #message-input {
      flex: 1;
      padding: 14px 18px;
      background: #334155;
      border: 1px solid #475569;
      border-radius: 8px;
      color: #f1f5f9;
      font-size: 14px;
    }

    #message-input:focus {
      outline: none;
      border-color: #3b82f6;
    }

    #send-btn {
      padding: 14px 28px;
      background: #3b82f6;
      color: white;
      border: none;
      border-radius: 8px;
      cursor: pointer;
      font-weight: 600;
      font-size: 14px;
      transition: all 0.2s;
    }

    #send-btn:hover {
      background: #2563eb;
    }

    #send-btn:disabled {
      background: #475569;
      cursor: not-allowed;
    }

    .typing {
      opacity: 0.7;
      font-style: italic;
    }
  </style>
</head>
<body>
  <div id="sidebar">
    <div class="logo">Spectrum</div>
    <div id="agents"></div>
  </div>

  <div id="chat">
    <div id="header">
      <div id="agent-name">Select an agent</div>
    </div>

    <div id="messages"></div>

    <div id="input-area">
      <input
        id="message-input"
        placeholder="Ask a question..."
        autocomplete="off"
      />
      <button id="send-btn">Send</button>
    </div>
  </div>

  <script>
    const API_URL = 'YOUR_WORKER_URL_HERE';  // Replace after worker deployed
    const CLIENT_ID = 'aijesusbro';

    let currentAgent = 'reality';
    let currentAgentName = 'Reality Agent';
    let conversationId = null;

    // Load agents on start
    async function loadAgents() {
      const res = await fetch(`${API_URL}/agents?client_id=${CLIENT_ID}`);
      const data = await res.json();

      const agentsDiv = document.getElementById('agents');
      data.agents.forEach(agent => {
        const btn = document.createElement('button');
        btn.className = 'agent-btn' + (agent.role === currentAgent ? ' active' : '');
        btn.textContent = agent.name;
        btn.onclick = () => switchAgent(agent.role, agent.name);
        agentsDiv.appendChild(btn);
      });
    }

    function switchAgent(role, name) {
      currentAgent = role;
      currentAgentName = name;
      conversationId = null;
      document.getElementById('messages').innerHTML = '';
      document.getElementById('agent-name').textContent = name;

      document.querySelectorAll('.agent-btn').forEach(btn => {
        btn.classList.remove('active');
      });
      event.target.classList.add('active');
    }

    async function sendMessage() {
      const input = document.getElementById('message-input');
      const sendBtn = document.getElementById('send-btn');
      const message = input.value.trim();

      if (!message) return;

      // Disable input
      input.value = '';
      sendBtn.disabled = true;

      // Add user message
      addMessage('user', message);

      // Show typing indicator
      const typingId = addMessage('assistant', 'Thinking...', true);

      try {
        // Send to API
        const res = await fetch(`${API_URL}/chat/send?client_id=${CLIENT_ID}`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            agent_role: currentAgent,
            message: message,
            conversation_id: conversationId
          })
        });

        const data = await res.json();
        conversationId = data.conversation_id;

        // Remove typing indicator
        document.getElementById(typingId).remove();

        // Add real response
        addMessage('assistant', data.message);
      } catch (error) {
        document.getElementById(typingId).remove();
        addMessage('assistant', 'Error: Could not reach API');
      }

      // Re-enable input
      sendBtn.disabled = false;
      input.focus();
    }

    function addMessage(role, content, typing = false) {
      const messagesDiv = document.getElementById('messages');
      const msgDiv = document.createElement('div');
      const id = 'msg-' + Date.now();
      msgDiv.id = id;
      msgDiv.className = `message ${role}` + (typing ? ' typing' : '');
      msgDiv.textContent = content;
      messagesDiv.appendChild(msgDiv);
      messagesDiv.scrollTop = messagesDiv.scrollHeight;
      return id;
    }

    // Enter to send
    document.getElementById('message-input').addEventListener('keypress', (e) => {
      if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        sendMessage();
      }
    });

    document.getElementById('send-btn').addEventListener('click', sendMessage);

    // Initialize
    loadAgents();
    document.getElementById('agent-name').textContent = currentAgentName;
  </script>
</body>
</html>
```

**Update `API_URL` in the HTML after you deploy the worker.**

**Deploy to Cloudflare Pages:**
```bash
cd frontend

# Deploy
npx wrangler pages deploy . --project-name=spectrum

# Output will give you URL like:
# https://spectrum.pages.dev
```

**Test:** Visit the URL, should see Spectrum interface

---

### PHASE 3: Connect to CloudflareMCP (1.5 hours)

#### Phase 3.1: Add Tool Calling to Worker (1.5 hours)

**Update `src/index.ts` to call CloudflareMCP for tools:**

```typescript
// Add tool definitions
const TOOL_DEFINITIONS = {
  crm: [
    {
      name: 'search_contacts',
      description: 'Search contacts in CRM by name, phone, email, or status',
      input_schema: {
        type: 'object',
        properties: {
          query: { type: 'string', description: 'Search query (name, phone, email)' },
          status: { type: 'string', description: 'Filter by status (lead, customer, etc.)' }
        }
      }
    }
  ],
  calendar: [
    {
      name: 'get_availability',
      description: 'Get available appointment slots',
      input_schema: {
        type: 'object',
        properties: {
          date: { type: 'string', description: 'Date (YYYY-MM-DD)' }
        }
      }
    }
  ]
};

// Map to CloudflareMCP tool names
const MCP_TOOL_MAP: Record<string, string> = {
  'search_contacts': 'ghl_search_contact',
  'get_availability': 'ghl_get_calendar_slots'
};

async function callMCPTool(env: Env, client_id: string, tool_name: string, tool_input: any) {
  const mcp_tool = MCP_TOOL_MAP[tool_name] || tool_name;

  const response = await fetch(`${env.CLOUDFLAREMCP_URL}/mcp?client_id=${client_id}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      jsonrpc: '2.0',
      id: Date.now(),
      method: 'tools/call',
      params: {
        name: mcp_tool,
        arguments: tool_input
      }
    })
  });

  const data = await response.json();
  return data.result;
}

// In chat endpoint, before calling Anthropic:
const data_sources = JSON.parse(agent.data_sources as string);
const tools: any[] = [];
data_sources.forEach((source: string) => {
  if (TOOL_DEFINITIONS[source]) {
    tools.push(...TOOL_DEFINITIONS[source]);
  }
});

// Call Anthropic with tools
const response = await anthropic.messages.create({
  model: agent.model as string,
  max_tokens: 1024,
  system: system_prompt,
  messages: messages,
  tools: tools.length > 0 ? tools : undefined
});

// Handle tool calls
let final_content = '';
if (response.stop_reason === 'tool_use') {
  const tool_results = [];

  for (const block of response.content) {
    if (block.type === 'tool_use') {
      const result = await callMCPTool(env, client_id, block.name, block.input);
      tool_results.push({
        type: 'tool_result',
        tool_use_id: block.id,
        content: JSON.stringify(result)
      });
    }
  }

  // Send tool results back to LLM
  messages.push({
    role: 'assistant',
    content: response.content
  });
  messages.push({
    role: 'user',
    content: tool_results
  });

  const final_response = await anthropic.messages.create({
    model: agent.model as string,
    max_tokens: 1024,
    system: system_prompt,
    messages: messages
  });

  final_content = final_response.content[0].type === 'text' ? final_response.content[0].text : '';
} else {
  final_content = response.content[0].type === 'text' ? response.content[0].text : '';
}

const reply = final_content;
```

**Deploy:**
```bash
npx wrangler deploy
```

**Test:**
```bash
curl -X POST "$WORKER_URL/chat/send?client_id=aijesusbro" \
  -H "Content-Type: application/json" \
  -d '{"agent_role": "reality", "message": "Search for contacts with name John"}'
```

**Expected:** Agent calls CloudflareMCP → GHL API → Returns real contacts

---

### PHASE 4: Deploy to aijesusbro.com/spectrum (30 min)

#### Phase 4.1: Configure Custom Domain

**In Cloudflare dashboard:**
1. Go to Pages project "spectrum"
2. Custom domains → Add custom domain
3. Enter: `aijesusbro.com`
4. Subdomain: `spectrum`
5. Cloudflare creates DNS records automatically

**Or via CLI:**
```bash
npx wrangler pages deployment list --project-name=spectrum

# Get latest deployment ID, then:
npx wrangler pages domains add spectrum aijesusbro.com
```

**Update frontend `API_URL`:**
Edit `frontend/index.html`:
```javascript
const API_URL = 'https://spectrum-api.aijesusbro-brain.workers.dev';
```

Redeploy:
```bash
npx wrangler pages deploy frontend --project-name=spectrum
```

**Test:** Visit `https://aijesusbro.com/spectrum` (may take 5 min for DNS)

---

### PHASE 5: Multi-Tenant Test (30 min)

**Add second client (test client):**

```bash
npx wrangler d1 execute spectrum-db --command="
INSERT INTO spectrum_agents (
  id, client_id, name, role, description, system_prompt, data_sources, position
) VALUES (
  'agent_testclient_sales',
  'testclient',
  'Sales Agent',
  'sales',
  'Helps prioritize leads and close deals',
  'You are a Sales Agent. Help prioritize leads using the CRM.',
  '[\"crm\"]',
  1
);"
```

**Test both clients:**
```bash
# AI Jesus Bro client
curl "$WORKER_URL/agents?client_id=aijesusbro"
# Should show: Reality Agent

# Test client
curl "$WORKER_URL/agents?client_id=testclient"
# Should show: Sales Agent

# Verify isolation (testclient can't see aijesusbro's agents)
```

**Expected:** Each client sees only their agents

---

## DEPLOYMENT CHECKLIST

### Before Going Live

- [ ] Worker deployed: `spectrum-api.aijesusbro-brain.workers.dev`
- [ ] D1 database created and schema applied
- [ ] Reality Agent seeded in database
- [ ] Frontend deployed to Pages
- [ ] Custom domain configured: `aijesusbro.com/spectrum`
- [ ] ANTHROPIC_API_KEY secret set
- [ ] Tested chat with real CloudflareMCP integration
- [ ] Verified multi-tenant isolation works

### Post-Launch

- [ ] Share link with 3 people, get feedback
- [ ] Monitor Cloudflare analytics (requests, errors)
- [ ] Add second agent (Sales Agent or Operations Agent)
- [ ] Connect RevOps OS as CRM abstraction (Phase 6)

---

## THE SALES PITCH

**When you send someone `aijesusbro.com/spectrum`:**

> "This is Spectrum - AI teammates with full business context.
>
> What you're seeing is MY Reality Agent talking to MY actual business data (CRM, calendar, etc.).
>
> You get the exact same infrastructure. Same speed, same reliability, same capabilities.
>
> Just with your branding, your data, your agents.
>
> Deployment time: 30 seconds. Just change the client_id parameter.
>
> Want to see it with YOUR data? Let's set it up right now."

**They can't say no.** You just showed them the product working in real-time.

---

## TOTAL TIME ESTIMATE

| Phase | Time | What You Get |
|-------|------|--------------|
| 0 | 1.5h | D1 database + Reality Agent seeded |
| 1 | 2.5h | Working API with conversation history |
| 2 | 1.5h | Frontend deployed to Pages |
| 3 | 1.5h | CloudflareMCP integration (real data!) |
| 4 | 30m | Live at aijesusbro.com/spectrum |
| 5 | 30m | Multi-tenant verified |

**Total:** ~8 hours spread across a few days

**Result:** Production-ready Spectrum that IS the product you sell

---

Ready to start with Phase 0? Let's create the Cloudflare project structure.
