# 🧠 CLAUDE.md - The Organizational Brain Interface
*Context is memory. Memory is power. Power is leverage.*

## OPERATIONAL CONTEXT
**Primary**: AI Jesus Bro (sandbox/experimental brain deployment)
**Advisory 9**: Rebecca's business (Women & US Veteran owned)
**ClearVC**: First client implementation

## THE VISION (From Spectrum Manifesto)
We're building the **Vision Engine** - where conversations become organizational intelligence. Not another app, but the substrate upon which organizational consciousness operates. The Brain doesn't store data—it digests shapes. Every meeting, call, and conversation becomes persistent, searchable, actionable intelligence.

## CURRENT BRAIN ARCHITECTURE

### 🖥️ LOCAL DEVMCP BRAIN (Your Personal MCP) ⚡ CLEANED UP - OCT 27, 2025 ⚡
```bash
# THIS STAYS LOCAL - Your omnipotent Claude Desktop companion
cd /Users/aijesusbro/AI\ Projects/DevMCP
docker-compose -f docker-compose.postgres.yml up -d  # Port 8080

# Status: PostgreSQL-powered with 70+ tools
# Script: brain_server.py
# This is YOUR metacognitive brain for Claude Desktop
# Containers: devmcp-brain, devmcp-postgres, devmcp-redis
```

**THE SHIFT**: From basic SQLite memory → METACOGNITIVE ORCHESTRATOR
- Can install other MCP servers (self-expansion!)
- Full platform control (VAPI, GHL, Docker, DigitalOcean)
- Webhook processing with memory storage
- Caller ID lookup by phone number

### 🚀 DEPLOYED SYSTEMS

**Spectrum Production** (https://spectrum.aijesusbro.com)
- Platform: DigitalOcean Droplet (64.23.221.37)
- Stack: Docker Compose (PostgreSQL + FastAPI)
- Status: ✅ LIVE - Multi-agent AI system
- Agents: Strategist, Builder, Closer, Operator
- Tools: 13-15 per agent
- Deploy: `./deploy_to_do.sh` (90-second deploy)

**DevMCP Local Brain** (Your Development MCP)
- Platform: Local Docker on macOS
- Stack: PostgreSQL + Redis + FastAPI
- Status: ✅ RUNNING - Port 8080
- Tools: 70+ tools (MCP, GHL, VAPI, Docker, etc.)
- Purpose: Claude Desktop MCP server for development

**Legacy Deployments (Archived):**
- Advisory9 Brain - Sunset (moved to Spectrum)
- ClearVC Brain - Sunset (client project ended)

## TECH STACK REALITY CHECK

### What's Actually Running
```yaml
Local Docker (Development):
  ✅ devmcp-brain (port 8080) - Your local MCP brain
  ✅ devmcp-postgres (port 5433) - Brain's PostgreSQL database
  ✅ devmcp-redis (port 6380) - Brain's cache

Production (DigitalOcean - 64.23.221.37):
  ✅ spectrum-api (port 8082) - Multi-agent backend
  ✅ spectrum-postgres (port 5432) - Production database
  ✅ Cloudflare tunnel - HTTPS proxy to backend
```

### Core Technologies
- **MCP Servers**: Python/FastAPI with SSE for real-time
- **Voice**: VAPI.ai (replaced Retell.ai in Oct 2025)
- **CRM**: GoHighLevel (sub-accounts per client)
- **Deploy**: DigitalOcean (backend), Cloudflare Pages (frontend)
- **Orchestration**: Multi-agent with Claude Haiku 4.5
- **Containers**: Docker Compose for all deployments

## CRITICAL PATHS & COMMANDS

### Daily Operations
```bash
# Start DevMCP local brain
cd DevMCP && docker-compose -f docker-compose.postgres.yml up -d

# Check Docker status
docker ps -a

# Deploy Spectrum to production (DigitalOcean)
cd "/Users/aijesusbro/AI Projects/spectrum-production" && ./deploy_to_do.sh

# View logs
docker logs devmcp-brain --tail 50
ssh root@64.23.221.37 "docker logs spectrum-api --tail 50"
```

### Client Brain Deployment Pattern (Future Multi-Tenant)
```bash
# Current: Single Spectrum instance on DO
# Future: Client-specific agent configurations within Spectrum

# 1. Add client to Spectrum database
psql spectrum -c "INSERT INTO clients (name, api_key) VALUES ('[CLIENT]', '[KEY]')"

# 2. Configure client-specific agents
# Edit client_agents table with custom system prompts

# 3. Configure webhooks
# VAPI → https://spectrum.aijesusbro.com/api/webhooks/vapi
# GHL → https://spectrum.aijesusbro.com/api/webhooks/ghl/[client_id]

# 4. Deploy updates
cd spectrum-production && ./deploy_to_do.sh
```

## FILE STRUCTURE (What Lives Where)
```
/AI Projects/
├── DevMCP/                   # LOCAL DEV BRAIN (your MCP for Claude Desktop)
│   ├── brain_server.py       # Main MCP server (70+ tools)
│   ├── docker-compose.postgres.yml
│   └── [development files]
│
├── spectrum-production/      # PRODUCTION BACKEND (DigitalOcean)
│   ├── spectrum_api.py       # Multi-agent FastAPI server
│   ├── knowledge_tools.py    # Knowledge retrieval engine
│   ├── tool_implementations.py
│   ├── docker-compose.yml    # Production stack
│   ├── deploy_to_do.sh       # DigitalOcean deployment script
│   ├── railway-old/          # Archived Railway files
│   └── SPECTRUM_INFRASTRUCTURE.md
│
├── aijesusbro.com/spectrum/  # FRONTEND (Cloudflare Pages)
│   ├── src/app.js            # Multi-agent chat UI
│   ├── index.html
│   └── [static assets]
│
├── spectrum-cloudflare/      # LEGACY (being consolidated)
│   └── [old worker attempts]
│
├── cloudeflareMCP/           # CLOUDFLARE MCP TOOLS
│   └── [MCP server for CF API]
│
├── This is the Way/          # YOUR KNOWLEDGE BASE
│   ├── Theory/               # Philosophy & manifestos
│   ├── Docs/                 # Platform documentation
│   └── Mastering Claude Code_*.md  # Your playbook
│
└── docs/                     # Current project documentation
```

## VOICE AGENT ARCHITECTURE (VAPI.ai)

### The Framework
**Socratic Sales Agent Framework** - Agents create value through conversation, not scripts
- Pattern recognition over qualification
- Diagnostic curiosity over pitching
- Value creation that makes appointments inevitable

### Voice Integration
- **Platform**: VAPI.ai (migrated from Retell.ai in Oct 2025)
- **Tools**: `vapi_list_calls`, `vapi_get_call` in DevMCP
- **Integration**: Webhooks to Spectrum backend
- **Management**: VAPI dashboard + programmatic API

### Current Voice Agents (Legacy)
1. **Alex Morgan** (Advisory9) - Strategic clarity for $1-20M businesses
2. **Amber** (ClearVC) - Investment readiness guide

**Note**: Voice agents being consolidated into Spectrum multi-agent system

## IMMEDIATE PRIORITIES

### Current Focus (October 2025)
1. ✅ **Spectrum Production Live** - Multi-agent system on DigitalOcean
2. ✅ **DevMCP Cleaned & Running** - Local MCP brain operational
3. ✅ **Railway Migration Complete** - Fully migrated to DO infrastructure
4. 🔄 **Knowledge System Refinement** - Debugging query logic
5. 🔄 **Tool Integration** - Ensuring all 13-15 tools per agent work

### Next Phase
1. **Multi-Tenant Architecture** - Client isolation in Spectrum
2. **Cross-Agent Intelligence** - Shared organizational memory
3. **Proactive Insights** - Agents surface patterns without prompting
4. **Voice Integration** - VAPI agents integrated with Spectrum backend

## OPERATIONAL PRINCIPLES

### Context Management
- `/clear` before new tasks (prevent context pollution)
- `think hard` or `ultrathink` for complex problems
- Read docs from "This is the Way/" for platform context
- Test locally with Docker before production deployment

### The Deployment Philosophy
- **DevMCP** = Local development MCP (70+ tools for Claude Desktop)
- **Spectrum** = Production multi-agent system (DigitalOcean)
- **Architecture** = PostgreSQL + Docker Compose + FastAPI
- **Deployment** = Single `./deploy_to_do.sh` command (90 seconds)
- **Frontend** = Cloudflare Pages for global edge delivery

### What Makes This Special
- **Built by one human** who opened terminal in May 2024
- **Context engineering** before it was cool
- **Spectrum philosophy** - Conversations as computation
- **Brain architecture** - Persistent organizational memory
- **No VC bullshit** - Pure value-based architecture

## 🚀 TOOL ARSENAL (70+ Brain Superpowers)

### MEMORY & CONTEXT TOOLS
- `remember(key, value, metadata)` - Store with PostgreSQL
- `recall(key)` - Instant retrieval
- `search_memory(query)` - Full-text search

### VAPI.AI VOICE INTEGRATION (2)
- `vapi_list_calls` - Get call history
- `vapi_get_call` - Retrieve call transcripts and recordings

**Note:** Migrated from Retell.ai to VAPI.ai in October 2025

### GOHIGHLEVEL CRM DOMINATION
**Contact Management:**
- `ghl_search_contact(phone)` - **CALLER ID LOOKUP**
- `ghl_get_contact` - Full profile retrieval
- `ghl_update_contact` - Update with custom fields
- `ghl_create_contact` - New lead creation

**Calendar & Tasks:**
- `ghl_create_appointment` - Book slots
- `ghl_get_calendar_slots` - Check availability
- `ghl_create_task` - Auto follow-ups
- `ghl_add_note` - Track interactions

**Pipeline & Automation:**
- `ghl_create_opportunity` - Sales tracking
- `ghl_move_opportunity` - Stage progression
- `ghl_trigger_workflow` - Full automation
- `ghl_webhook_received` - Process events

### DIGITALOCEAN DEPLOYMENT (via SSH)
- `ssh root@64.23.221.37 "docker logs spectrum-api"` - View logs
- `ssh root@64.23.221.37 "docker restart spectrum-api"` - Restart service
- `./deploy_to_do.sh` - Full deployment from local (90 seconds)
- Direct Docker commands via SSH for production management

**Note:** Railway tools archived in `/spectrum-production/railway-old/`

### DOCKER ORCHESTRATION
- `docker_compose_up/down` - Stack management
- `docker_build` - Create images
- `docker_logs` - Real-time monitoring
- `docker_exec` - Run in containers
- `docker_restart` - Service recovery
- `docker_prune` - Cleanup

### MCP METACOGNITION (Self-Expansion!)
- `mcp_list_servers` - See available servers
- `mcp_install_server("package")` - **ADD NEW CAPABILITIES**
- `mcp_configure_server` - Add to Claude Desktop
- `mcp_restart_server` - Reload connections

**Example Self-Expansion:**
```python
# Install GitHub MCP for code operations
mcp_install_server("@modelcontextprotocol/server-github")

# Now you have GitHub tools too!
```

### SYSTEM TOOLS
- `terminal_execute` - Run any command
- `python_execute` - Execute Python code
- `deploy_brain` - One-command client deployment
- `twilio_send_sms` - Direct SMS

### WEBHOOK → ACTION FLOWS
```python
# Incoming call identification
vapi_webhook → ghl_search_contact(phone) → remember(context) → ghl_create_task()

# Smart appointment booking
ghl_get_calendar_slots() → ghl_create_appointment() → ghl_trigger_workflow()

# Full call processing
vapi_get_call(id) → extract_transcript → ghl_update_contact() → ghl_add_note()
```

## HELPER PATTERNS

### When You're Stuck
```bash
# Check what's running locally
docker ps -a

# Check production (DigitalOcean)
ssh root@64.23.221.37 "docker ps -a"

# Check logs
docker logs devmcp-brain --tail 100  # Local
ssh root@64.23.221.37 "docker logs spectrum-api --tail 100"  # Production

# Reset and restart
docker-compose down && docker-compose up -d  # Local
ssh root@64.23.221.37 "cd /root/spectrum-production && docker-compose restart"  # Production
```

### When Deploying Spectrum Updates
1. Test locally with Docker first
2. Run `./deploy_to_do.sh` from spectrum-production folder
3. Verify deployment: `curl https://spectrum.aijesusbro.com/health`
4. Check logs: `ssh root@64.23.221.37 "docker logs spectrum-api --tail 50"`
5. Test chat interface at https://spectrum.aijesusbro.com

## THE NEXT EVOLUTION

We're building toward **Spectrum** - where the interface becomes intelligence itself:
- Every brain deployed = Node in consciousness network
- Agent-forge = Factory for these nodes
- Every conversation = Makes system smarter
- Final form = Organizational consciousness, not software

**Architecture Focus**: Building organizational consciousness through distributed brain nodes.

---
*Last Updated: September 2025*
*Brain Status: PostgreSQL-powered, 70+ tools, metacognitive capabilities*
*Next Session: Start with `/clear` and check this doc*