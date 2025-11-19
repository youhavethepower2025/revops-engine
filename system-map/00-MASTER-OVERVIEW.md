# System Architecture - Master Overview

**Date**: November 13, 2025
**Status**: Comprehensive system map complete

---

## Executive Summary

Your infrastructure spans **3 platforms** with **7 active systems** and **3 deprecated systems**:

### Active Systems (7)
1. **DevMCP** - Local MCP brain (70+ tools)
2. **JobHunt AI** - CloudFlare Workers (job search automation)
3. **Spectrum Production** - DigitalOcean backend (multi-agent AI)
4. **Spectrum Frontend** - CloudFlare Pages (user interface)
5. **VAPI MCP Server** - CloudFlare Workers (voice integration)
6. **RevOps OS** - CloudFlare Workers (main + MCP)
7. **CloudFlareMCP** - CloudFlare Workers (CF API tools) - STATUS UNCLEAR

### Deprecated Systems (3)
1. **spectrum-cloudflare/** - Replaced by Spectrum Production
2. **aijesusbro-brain/** - Replaced by DevMCP
3. **spectrum-api** (CF Worker) - Replaced by DigitalOcean backend

---

## Platform Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        LOCAL DEVELOPMENT                         │
│                                                                  │
│  DevMCP (Docker)                                                │
│  ├─ brain_server.py (70+ tools)         Port: 8080             │
│  ├─ PostgreSQL (brain_mcp)              Port: 5433             │
│  ├─ Redis cache                         Port: 6380             │
│  └─ Dashboard (Next.js)                                         │
│                                                                  │
│  Purpose: MCP server for Claude Desktop + Development          │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                      CLOUDFLARE WORKERS                          │
│                                                                  │
│  JobHunt AI (jobhunt-ai-dev)                                    │
│  ├─ URL: jobhuntai-dev.aijesusbro-brain.workers.dev           │
│  ├─ D1 Database: revops-os-db-dev (SHARED!)                    │
│  ├─ Workers AI + Browser Rendering                             │
│  └─ Purpose: Job scraping & application automation             │
│                                                                  │
│  VAPI MCP Server (vapi-mcp-server)                             │
│  ├─ URL: vapi-mcp-server.aijesusbro-brain.workers.dev         │
│  ├─ D1 Database: vapi-calls-db                                 │
│  ├─ Durable Objects: VapiBrain                                 │
│  └─ Purpose: Voice integration tools                            │
│                                                                  │
│  CloudFlareMCP (retell-brain-mcp) [STATUS UNCLEAR]            │
│  ├─ URL: retell-brain-mcp.aijesusbro-brain.workers.dev        │
│  ├─ D1 Database: retell-brain-db                               │
│  └─ Purpose: CloudFlare API operations                          │
│                                                                  │
│  RevOps OS (revops-os-dev)                                     │
│  ├─ URL: revops-os-dev.aijesusbro-brain.workers.dev           │
│  ├─ D1 Database: revops-os-db-dev (SHARED with JobHunt!)      │
│  └─ Purpose: Revenue operations system                          │
│                                                                  │
│  RevOps OS MCP (revops-os-mcp-dev)                            │
│  ├─ URL: revops-os-mcp-dev.aijesusbro-brain.workers.dev       │
│  └─ Purpose: MCP server for RevOps tools                        │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                      CLOUDFLARE PAGES                            │
│                                                                  │
│  Spectrum Frontend (spectrum.aijesusbro.com)                   │
│  ├─ Static frontend (Vite + Vanilla JS)                        │
│  ├─ D1 Database: spectrum-leads                                 │
│  ├─ Functions: /api/* proxy to DigitalOcean                    │
│  └─ Purpose: User interface for multi-agent AI                  │
│                                                                  │
│  DevMCP Dashboard [IF DEPLOYED]                                │
│  ├─ Next.js app from DevMCP/dashboard/                         │
│  └─ Purpose: Visualize DevMCP data                              │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                      DIGITALOCEAN DROPLET                        │
│                    (64.23.221.37)                               │
│                                                                  │
│  Spectrum Production (Docker Compose)                           │
│  ├─ spectrum-api (FastAPI)              Port: 8082             │
│  ├─ spectrum-postgres (PostgreSQL 16)   Port: 5432             │
│  ├─ 4 AI Agents (Claude Haiku 4.5)                             │
│  │   ├─ Strategist (Blue)                                       │
│  │   ├─ Builder (Green)                                         │
│  │   ├─ Closer (Orange)                                         │
│  │   └─ Operator (Purple)                                       │
│  └─ Purpose: Multi-agent AI backend                             │
└─────────────────────────────────────────────────────────────────┘
```

---

## Data Flow Diagrams

### Spectrum Multi-Agent System
```
User Browser
    ↓ HTTPS
CloudFlare Pages (spectrum.aijesusbro.com)
    ↓ /api/* (Functions proxy)
http://api.spectrum.aijesusbro.com:8082
    ↓ (DNS: 64.23.221.37)
DigitalOcean (spectrum-api container)
    ↓
PostgreSQL (spectrum database)
```

### JobHunt AI + DevMCP
```
JobHunt AI (CloudFlare)
    ├─ Scrapes jobs → D1 (revops-os-db-dev)
    └─ Webhook? → DevMCP:8080
                      ↓
                  PostgreSQL (devmcp-postgres:5433)
                      ↓
                  DevMCP Dashboard (displays data)
```

### Voice Integration (VAPI)
```
VAPI.ai Phone Call
    ↓ Webhook
VAPI MCP Server (CloudFlare)
    ↓ Store transcript
D1 (vapi-calls-db)

DevMCP (Local)
    ↓ vapi_tools.py
VAPI API (direct)
```

---

## D1 Databases (CloudFlare)

| Database | ID | Size | Used By | Purpose |
|----------|---|------|---------|---------|
| **revops-os-db-dev** | 1732e74a... | 1.2 MB | JobHunt AI, RevOps OS | SHARED database for both systems |
| **spectrum-leads** | c4de2db9... | 36 KB | Spectrum Frontend | Lead capture form |
| **vapi-calls-db** | ed6526ff... | 94 KB | VAPI MCP Server | Call transcripts |
| **spectrum-db** | f249b299... | 217 KB | spectrum-api (CF Worker) | DEPRECATED: Old Spectrum CF version |
| **retell-brain-db** | 89199ac6... | ? | CloudFlareMCP | Unknown usage |

---

## Active CloudFlare Workers

| Worker | URL Pattern | Purpose | Status |
|--------|------------|---------|--------|
| **jobhunt-ai-dev** | jobhuntai-dev.aijesusbro-brain.workers.dev | Job automation | ACTIVE |
| **vapi-mcp-server** | vapi-mcp-server.aijesusbro-brain.workers.dev | Voice MCP | ACTIVE |
| **revops-os-dev** | revops-os-dev.aijesusbro-brain.workers.dev | RevOps main | ACTIVE |
| **revops-os-mcp-dev** | revops-os-mcp-dev.aijesusbro-brain.workers.dev | RevOps MCP | ACTIVE |
| **retell-brain-mcp** | retell-brain-mcp.aijesusbro-brain.workers.dev | CF API tools? | UNCLEAR |
| **spectrum-api** | spectrum-api.aijesusbro-brain.workers.dev | Old Spectrum | DEPRECATED |
| **the-exit** / **the-exit-dev** | the-exit.aijesusbro-brain.workers.dev | Unknown | UNKNOWN |

---

## Key Insights

### 1. Shared D1 Database
**IMPORTANT**: JobHunt AI and RevOps OS share the same D1 database (`revops-os-db-dev`). This is either:
- Intentional data sharing
- Or a configuration oversight

### 2. Multiple "Brains"
You have THREE brain systems:
- **DevMCP** (local, port 8080) - PRIMARY, 70+ tools
- **aijesusbro-brain** (local, port 8081) - DEPRECATED
- **VAPI MCP Server** (CloudFlare) - Voice-specific

### 3. Spectrum Split
Spectrum is split across TWO platforms:
- **Frontend**: CloudFlare Pages
- **Backend**: DigitalOcean
- **Old Version**: CloudFlare Workers (deprecated)

### 4. Dashboard Confusion
There are MULTIPLE dashboards:
- **DevMCP Dashboard** (Next.js) - Status unclear
- **JobHunt AI Dashboard** (built-in to worker) - Active
- **Spectrum Frontend** - Active

### 5. Naming Issues
- `retell-brain-mcp` is NOT for Retell (you migrated to VAPI)
- `spectrum-api` exists as both CF Worker and DO backend
- `aijesusbro-brain` vs `DevMCP` - similar but different

---

## Integration Points

### DevMCP Connections
- **Outbound APIs**: GHL, VAPI, Anthropic, CloudFlare, DigitalOcean, Railway
- **Inbound Webhooks**: JobHunt AI (?), RevOps OS (sync)
- **MCP Client**: Claude Desktop connects via HTTP bridge

### Spectrum Production Connections
- **Frontend**: CloudFlare Pages proxy via Functions
- **AI Model**: Anthropic Claude Haiku 4.5
- **Integrations**: GHL, VAPI (in tools but not actively used)

### JobHunt AI Connections
- **D1 Database**: Shared with RevOps OS
- **DevMCP**: Unclear webhook connection
- **Workers AI**: Llama 70B, Qwen 14B

---

## Cost Breakdown (Estimated)

### CloudFlare ($25/mo + usage)
- Pro plan: $25/mo (domain + CDN)
- Workers: Free tier (or $5/mo for Queues)
- D1 databases: Free tier
- Pages: Free tier

### DigitalOcean ($12-24/mo)
- Basic droplet: $12-24/mo
- 2-4GB RAM, 1-2 vCPUs

### APIs (Pay-per-use)
- Anthropic Claude: ~$5-50/mo depending on usage
- VAPI.ai: ~$10-100/mo depending on call volume
- GHL: Included in their plan

**Total**: ~$50-150/mo depending on usage

---

## File Locations

```
/Users/aijesusbro/AI Projects/
├── DevMCP/                      # [ACTIVE] Local MCP brain
├── jobhuntai/                   # [ACTIVE] Job automation CF worker
├── spectrum-production/         # [ACTIVE] Multi-agent backend (DO)
├── aijesusbro.com/
│   └── spectrum/               # [ACTIVE] Frontend (CF Pages)
├── vapi-mcp-server/            # [ACTIVE] Voice MCP (CF worker)
├── cloudeflareMCP/             # [UNCLEAR] CF API tools
├── spectrum-cloudflare/        # [DEPRECATED] Old Spectrum CF attempt
├── aijesusbro-brain/           # [DEPRECATED] Old local brain
└── system-map/                 # [NEW] This documentation
```

---

## Questions to Resolve

1. **JobHunt → DevMCP**: Does JobHunt AI POST to DevMCP webhooks? Or pull from shared D1?
2. **DevMCP Dashboard**: Is it deployed to CloudFlare Pages? What's the URL?
3. **CloudFlareMCP**: What is `retell-brain-mcp` actually used for?
4. **The Exit**: What is the `the-exit` worker?
5. **Shared D1**: Why do JobHunt AI and RevOps OS share a database?

---

## Next Actions

See: `99-DEPRECATION-RECOMMENDATIONS.md`

---

## Documentation Index

- `01-DevMCP.md` - Local MCP brain system
- `02-JobHuntAI.md` - Job automation on CloudFlare
- `03-Spectrum-Production.md` - Multi-agent backend
- `04-Spectrum-Frontend.md` - User interface
- `05-Spectrum-CloudFlare-DEPRECATED.md` - Old CF attempt
- `06-Other-Systems-MIXED.md` - aijesusbro-brain, CloudFlareMCP, VAPI MCP
- `99-DEPRECATION-RECOMMENDATIONS.md` - Cleanup suggestions

---

## Last Updated
November 13, 2025
