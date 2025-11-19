# Spectrum Production - Multi-Agent AI System

## Status: ACTIVE & DEPLOYED

## Purpose
Multi-agent AI system where users interact with four specialized AI executives (Strategist, Builder, Closer, Operator) for business guidance.

## Core Innovation
Instead of one generic chatbot, users get a **department of AI executives** with domain-specific expertise.

## Infrastructure

### Deployment Stack
```
Frontend (CloudFlare Pages)
    ↓ HTTPS
CloudFlare Workers Proxy (api.spectrum.aijesusbro.com)
    ↓ HTTP
DigitalOcean Backend (64.23.221.37:8082)
    ├─ spectrum-api (FastAPI container)
    └─ spectrum-postgres (PostgreSQL 16)
```

### Access URLs
- **Frontend**: https://spectrum.aijesusbro.com
- **API**: https://spectrum.aijesusbro.com/api/* (proxied through CloudFlare)
- **Backend Direct**: http://64.23.221.37:8082 (internal)
- **Health Check**: https://spectrum.aijesusbro.com/api/health

### Technology Stack
| Component | Technology | Port |
|-----------|-----------|------|
| **Backend API** | Python + FastAPI | 8082 |
| **Database** | PostgreSQL 16 | 5432 |
| **AI Model** | Claude Haiku 4.5 | - |
| **Frontend** | Vanilla JS (no frameworks) | - |
| **CDN/Proxy** | CloudFlare Workers | - |
| **Containers** | Docker Compose | - |
| **Hosting** | DigitalOcean Droplet | - |

## The Four Agents

### 1. The Strategist (Blue)
- **Role**: `strategist`
- **Expertise**: Strategic planning, board decisions, market positioning
- **Personality**: Sharp, decisive, focused on leverage points
- **Tools**: 13-15 specialized tools

### 2. The Builder (Green)
- **Role**: `builder`
- **Expertise**: Product roadmap, technical architecture, engineering
- **Personality**: Pragmatic, execution-focused, ship fast
- **Tools**: 13-15 specialized tools

### 3. The Closer (Orange)
- **Role**: `closer`
- **Expertise**: Revenue ops, deal strategy, sales optimization
- **Personality**: Numbers-driven, momentum-obsessed
- **Tools**: 13-15 specialized tools

### 4. The Operator (Purple)
- **Role**: `operator`
- **Expertise**: Operational efficiency, process design, scaling
- **Personality**: Systems thinker, efficiency-obsessed
- **Tools**: 13-15 specialized tools

## Key Components

### 1. Main API (`spectrum_api.py` - 85KB)
- FastAPI server with 4 agent configurations
- Each agent has unique system prompt + tools
- Real-time streaming responses
- Conversation history management
- Knowledge retrieval integration

### 2. Knowledge System
- **Schema**: `knowledge_schema.sql`
- **Tools**: `knowledge_tools.py`
- Hierarchical knowledge nodes
- Full-text search
- Context retrieval for agents

### 3. Tool Implementations (`tool_implementations.py`)
- Shared tools across all agents
- GHL integration, VAPI integration
- Calendar, contacts, pipeline management

### 4. Database Schema (PostgreSQL)
Tables:
- `agents` - Agent configurations (4 rows)
- `conversations` - Chat sessions
- `messages` - Individual messages
- `knowledge_nodes` - Hierarchical knowledge
- `knowledge_tags` - Tag system
- `tool_usage` - Analytics

## Docker Containers

### spectrum-api
- Image: Custom build from Dockerfile
- Port: 8082 (mapped from internal 8080)
- Environment:
  - `DATABASE_URL`: PostgreSQL connection
  - `ANTHROPIC_API_KEY`: Claude API
  - `PORT`: 8080
- Restart: unless-stopped

### spectrum-postgres
- Image: postgres:16-alpine
- Port: 5432
- Database: `spectrum`
- User: `spectrum`
- Volume: `postgres_data` (persistent)
- Restart: unless-stopped

## Deployment Process

### Deploy Command
```bash
cd "/Users/aijesusbro/AI Projects/spectrum-production"
./deploy_to_do.sh
```

### What `deploy_to_do.sh` Does
1. Creates tarball of code
2. SCPs to DigitalOcean droplet (64.23.221.37)
3. Extracts on server
4. Builds Docker image
5. Restarts containers
6. Total time: ~90 seconds

### Manual Operations
```bash
# SSH into droplet
ssh root@64.23.221.37

# Check containers
docker ps -a

# View logs
docker logs spectrum-api --tail 50

# Restart services
docker-compose restart

# Full rebuild
docker-compose down && docker-compose up -d --build
```

## Database Access

### Via Local psql
```bash
# Connect to production database
ssh -L 5432:localhost:5432 root@64.23.221.37
psql -h localhost -U spectrum -d spectrum
```

### Seeding Data
```bash
# Seed agents (if needed)
ssh root@64.23.221.37 "cd /root/spectrum-production && docker exec -i spectrum-postgres psql -U spectrum -d spectrum < seed_agents.sql"

# Seed knowledge base
ssh root@64.23.221.37 "cd /root/spectrum-production && docker exec spectrum-api python seed_mvp_knowledge.py"
```

## Frontend Integration

### Frontend Location
- **Source**: `/Users/aijesusbro/AI Projects/aijesusbro.com/spectrum/`
- **Deployed**: CloudFlare Pages (spectrum.aijesusbro.com)
- **Files**: `src/app.js`, `index.html`

### API Communication
```javascript
// Frontend calls (in src/app.js)
fetch('https://spectrum.aijesusbro.com/api/chat', {
    method: 'POST',
    body: JSON.stringify({ agent_id, message })
})
```

### CloudFlare Workers Proxy
- Handles CORS
- Proxies `/api/*` to DigitalOcean backend
- HTTPS → HTTP bridge
- Location: Not in local filesystem (deployed via Wrangler)

## External Integrations

### Anthropic Claude
- Model: `claude-haiku-4.5-20250917`
- Max tokens: 4096
- Temperature: 0.7
- Streaming: Yes

### VAPI (Voice)
- Integration: `vapi_tools.py`
- Purpose: Voice agent management
- Status: Integrated but not actively used by agents

### GoHighLevel (CRM)
- Integration: In tool implementations
- Purpose: Contact/calendar/pipeline management
- Status: Available to all agents

## Knowledge System

### Architecture
- **Hierarchical nodes**: Frameworks → Concepts → Tactics
- **Tags**: Cross-cutting topics (pricing, hiring, etc.)
- **Full-text search**: PostgreSQL `tsvector`
- **Context retrieval**: Agents query knowledge before responding

### Content
Seeded with MVP knowledge:
- Sales frameworks (MEDDPICC, Sandler, etc.)
- Product frameworks (Jobs-to-be-Done, etc.)
- Operations frameworks (OKRs, etc.)
- Strategic frameworks (Porter's 5 Forces, etc.)

## Monitoring & Health

### Health Endpoint
```bash
curl https://spectrum.aijesusbro.com/api/health
# Returns: {"status": "ok", "agents": 4, "timestamp": "..."}
```

### Logs
```bash
# Real-time logs
ssh root@64.23.221.37 "docker logs -f spectrum-api"

# Last 100 lines
ssh root@64.23.221.37 "docker logs spectrum-api --tail 100"
```

### Container Status
```bash
# Check if containers are running
ssh root@64.23.221.37 "docker ps -a | grep spectrum"
```

## Legacy & Migration Notes

### Railway → DigitalOcean
- **Migration Date**: October 2025
- **Old files**: `/spectrum-production/railway-old/`
- **Status**: Fully migrated, Railway files archived
- **Reason**: Better control, lower costs

### Retell → VAPI
- **Migration Date**: October 2025
- **Old integration**: Removed (see `FINAL_RETELL_PURGE.md`)
- **New integration**: VAPI.ai for voice agents

## File Structure

```
/spectrum-production/
├── spectrum_api.py          # Main FastAPI server (85KB)
├── knowledge_tools.py       # Knowledge retrieval engine
├── tool_implementations.py  # Shared tools for agents
├── docker-compose.yml       # Container orchestration
├── Dockerfile               # API container build
├── deploy_to_do.sh          # DigitalOcean deployment
├── knowledge_schema.sql     # Knowledge database schema
├── seed_agents.sql          # 4 agent configurations
├── seed_mvp_knowledge.py    # Seed knowledge base
└── SPECTRUM_INFRASTRUCTURE.md  # This doc (more details)
```

## Questions to Resolve

1. **CloudFlare Workers Proxy**: Where is the proxy code? Is it deployed separately?
2. **Frontend Deployment**: How is aijesusbro.com/spectrum deployed to CloudFlare Pages?
3. **SSH Access**: Need to verify SSH key for DigitalOcean droplet access
4. **Tool Count**: Each agent is supposed to have 13-15 tools - need to audit actual count

## Cost Breakdown

- **DigitalOcean Droplet**: ~$12-24/mo (Basic droplet)
- **CloudFlare**: $25/mo (Pro plan for domain + CDN)
- **Anthropic API**: Pay-per-use (Haiku is cheap)
- **Total**: ~$40-50/mo

## Last Updated
November 13, 2025
