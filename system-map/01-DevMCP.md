# DevMCP - Local Development Brain

## Status: ACTIVE & RUNNING

## Purpose
Your local MCP (Model Context Protocol) server that provides 70+ tools to Claude Desktop for development work.

## Infrastructure

### Deployment
- **Location**: Local Docker on macOS
- **Stack**: PostgreSQL + Redis + FastAPI/Python
- **Port**: 8080 (exposed to localhost)

### Running Containers
```
devmcp-brain (port 8080)      - Main MCP server
devmcp-postgres (port 5433)   - PostgreSQL database: brain_mcp
devmcp-redis (port 6380)      - Redis cache
```

### Start Command
```bash
cd "/Users/aijesusbro/AI Projects/DevMCP"
docker-compose -f docker-compose.postgres.yml up -d
```

## Key Components

### 1. Brain Server (`brain_server.py` - 120KB)
- Main MCP server with 70+ tools
- Provides: VAPI tools, GHL tools, Gmail tools, Job Hunt tools, RevOps tools
- Database operations, memory storage, webhook processing

### 2. Job Hunt Tools (`job_hunt_tools.py`)
- **CRITICAL CONNECTION**: These tools write data to local PostgreSQL
- Schema: `job_hunt_schema.sql`
- Tables: jobs, applications, contacts, companies, activities
- This is where JobHunt AI CloudFlare worker POSTS data to

### 3. RevOps Tools (`revops_tools.py`)
- Connection to: `https://revops-os-dev.aijesusbro-brain.workers.dev`
- Account: `account_john_kruze`
- Sync service: Auto-sync between RevOps CloudFlare and local DB

### 4. Dashboard (Next.js)
- **Location**: `/DevMCP/dashboard/`
- **Framework**: Next.js + React
- **Purpose**: Visualize data from DevMCP PostgreSQL database
- **Deploys to**: Likely CloudFlare Pages (has wrangler config)
- **API Connection**: Talks to localhost:8080 (DevMCP brain server)

## External Connections

### Outbound APIs (from .env)
- **GHL**: GoHighLevel API (Location: PMgbQ375TEGOyGXsKz7e)
- **VAPI**: Voice API (bb0d907c-0834-420e-932c-f3f25f8221ad)
- **Railway**: API token for Railway deployments
- **Anthropic**: Claude API key
- **Cloudflare**: Account ID + AI wrapper (https://ai-wrapper.aijesusbro.workers.dev)
- **DigitalOcean**: API token for droplet management
- **RevOps**: Dev worker (https://revops-os-dev.aijesusbro-brain.workers.dev)

### Inbound Webhooks
- **JobHunt AI**: POST job/application data from CloudFlare worker
- **RevOps**: Sync data from CloudFlare worker to local DB

## Database Schema

### PostgreSQL Tables
- `memory` - Key-value storage with metadata
- `job_hunt_*` - Jobs, applications, contacts, companies, activities
- `revops_*` - RevOps synced data (accounts, contacts, deals, etc.)
- `gmail_*` - Gmail intelligence (emails, contacts, threads)
- `chat_*` - Chat history storage

## Dashboard Access
- **Development**: http://localhost:3000 (when running `npm run dev`)
- **Production**: Likely deployed to CloudFlare Pages (need to verify URL)

## Key Files
- `brain_server.py` (120KB) - Main MCP server
- `job_hunt_tools.py` (20KB) - Job hunt operations
- `revops_tools.py` (18KB) - RevOps integration
- `gmail_tools_v2.py` (17KB) - Gmail operations
- `vapi_tools.py` (16KB) - Voice API operations
- `docker-compose.postgres.yml` - Container orchestration

## Data Flow

```
JobHunt AI (CloudFlare)
    → POST to DevMCP:8080/webhooks/jobhunt
    → Stored in PostgreSQL (devmcp-postgres:5433)
    → Displayed in Dashboard (Next.js)

RevOps OS (CloudFlare)
    → Syncs to DevMCP:8080/webhooks/revops
    → Stored in PostgreSQL
    → Queryable via RevOps tools

Claude Desktop
    → Connects via MCP HTTP bridge
    → Uses 70+ tools from brain_server.py
    → Reads/writes PostgreSQL data
```

## Health Check
- URL: http://localhost:8080/health
- Containers: All 3 should be "Up" and "healthy"

## Last Updated
November 13, 2025
