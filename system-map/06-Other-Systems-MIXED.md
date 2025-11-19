# Other Systems - Mixed Status

## Status: MIXED (Some Active, Some Deprecated)

---

## 1. aijesusbro-brain (LIKELY DEPRECATED)

### Status: SUPERSEDED BY DEVMCP

### What This Was
An earlier version of your local brain MCP server (September 2024), before DevMCP was created.

### Key Differences from DevMCP
- **Port**: 8081 (vs DevMCP on 8080)
- **Database**: `aijesusbro-postgres` on port 5434 (vs DevMCP on 5433)
- **Redis**: Port 6381 (vs DevMCP on 6380)
- **Containers**: `aijesusbro-brain`, `aijesusbro-postgres`, `aijesusbro-redis`

### Infrastructure (When It Existed)
```
aijesusbro-brain (port 8081)      - MCP server with 46+ tools
aijesusbro-postgres (port 5434)    - PostgreSQL database
aijesusbro-redis (port 6381)       - Redis cache
```

### What It Did
- GHL integration (same account as DevMCP)
- Retell integration (before VAPI migration)
- Webhook endpoints: `/webhooks/retell`, `/webhooks/ghl`, `/webhooks/twilio`
- Memory system with PostgreSQL

### Why It Was Replaced
Based on dates:
- **September 2024**: aijesusbro-brain created
- **October 2024**: DevMCP created with more tools (70+ vs 46+)
- **Result**: DevMCP became the primary local MCP server

### Files
- `brain_server.py` (44KB) - Main MCP server
- `brain_production.py` - Production variant
- `enhanced_tools.py` - Tool implementations
- `docker-compose.yml` - Container orchestration
- Various deployment scripts for DigitalOcean

### Recommendation
**STATUS CHECK NEEDED**: Are these containers still running?
```bash
docker ps -a | grep aijesusbro
```

If not running, this folder can be archived to `/legacy/aijesusbro-brain/`.

---

## 2. cloudeflareMCP (UNCLEAR STATUS)

### Status: UNKNOWN - NEEDS VERIFICATION

### What This Is
A CloudFlare MCP server for CloudFlare API operations. Originally called "retell-brain-mcp" but repurposed.

### Infrastructure
- **Platform**: CloudFlare Workers
- **Name**: `retell-brain-mcp` (confusing name!)
- **Database**: D1 - `retell-brain-db` (ID: 89199ac6-f0a7-4de3-9a8d-ea004beb0583)
- **Durable Objects**: `ClientBrain` for stateful operations
- **Workers AI**: Edge LLM inference capability

### Configuration (wrangler.toml)
```toml
name = "retell-brain-mcp"
main = "src/index.ts"
workers_dev = true

[[d1_databases]]
binding = "DB"
database_name = "retell-brain-db"
database_id = "89199ac6-f0a7-4de3-9a8d-ea004beb0583"

[[durable_objects.bindings]]
name = "BRAIN"
class_name = "ClientBrain"
```

### Purpose (According to README)
MCP server that provides CloudFlare API tools:
- Domain management
- DNS record operations
- Worker deployments
- D1 database operations
- Pages deployments
- Possibly: Subdomain configuration (see `set_subdomain.sh`)

### Deployment Status
- **Last Modified**: October 2025
- **Deployed**: Unclear - need to check CloudFlare dashboard
- **URL Pattern**: Likely `https://retell-brain-mcp.aijesusbro-brain.workers.dev`

### Files
```
/cloudeflareMCP/
├── src/
│   └── index.ts           # Main MCP server
├── schema.sql             # D1 database schema
├── wrangler.toml          # CloudFlare config
├── set_subdomain.sh       # Subdomain configuration script
├── .secrets.sh            # API token setup
└── [deployment docs]
```

### Questions to Resolve
1. Is this actually deployed? Check: `wrangler deployments list`
2. What's it actually used for? CloudFlare API automation?
3. Why is it named "retell-brain-mcp" if it's for CloudFlare ops?
4. Does anything depend on it?

---

## 3. vapi-mcp-server (LIKELY ACTIVE)

### Status: PROBABLY ACTIVE

### What This Is
CloudFlare MCP server for VAPI.ai voice integration. Provides tools for managing voice calls, transcripts, and client configurations.

### Infrastructure
- **Platform**: CloudFlare Workers
- **Name**: `vapi-mcp-server`
- **Database**: D1 - `vapi-calls-db` (ID: ed6526ff-6bb7-40e4-a0ba-d3e1535054e7)
- **Durable Objects**: `VapiBrain` for per-client instances
- **URL**: Likely `https://vapi-mcp-server.aijesusbro-brain.workers.dev`

### Configuration (wrangler.toml)
```toml
name = "vapi-mcp-server"
main = "src/index.ts"

[[d1_databases]]
binding = "DB"
database_name = "vapi-calls-db"
database_id = "ed6526ff-6bb7-40e4-a0ba-d3e1535054e7"

[[durable_objects.bindings]]
name = "VAPI_BRAIN"
class_name = "VapiBrain"
```

### Purpose
MCP server that provides VAPI tools:
- List calls
- Get call transcripts
- Manage voice agents
- Store call metadata in D1
- Per-client brain instances via Durable Objects

### Evidence of Active Use
1. **Referenced by spectrum-cloudflare**:
   ```toml
   [[services]]
   binding = "MCP"
   service = "vapi-mcp-server"
   ```

2. **DevMCP has VAPI tools**: `vapi_tools.py` in DevMCP
   - But DevMCP may call VAPI API directly, not this MCP server

3. **Recent docs**: October 2024 deployment docs

### Files
```
/vapi-mcp-server/
├── src/
│   └── index.ts               # Main MCP server
├── schema.sql                 # D1 database schema
├── add_memory_table.sql       # Memory table addition
├── wrangler.toml              # CloudFlare config
├── VAPI_INTEGRATION_URLS.md   # Integration docs
└── [deployment status docs]
```

### Questions to Resolve
1. Is this deployed and active? Check CloudFlare dashboard
2. Does DevMCP use this, or does it call VAPI API directly?
3. Is the D1 database (`vapi-calls-db`) actively being written to?
4. What's the actual URL and how is it accessed?

---

## Summary Table

| System | Status | Platform | Purpose | Recommendation |
|--------|--------|----------|---------|----------------|
| **aijesusbro-brain** | DEPRECATED | Local Docker | Old MCP server | Archive to `/legacy/` |
| **cloudeflareMCP** | UNKNOWN | CF Workers | CF API operations | Verify deployment status |
| **vapi-mcp-server** | LIKELY ACTIVE | CF Workers | VAPI voice integration | Verify & document usage |

---

## Next Steps to Clarify

### 1. Check Running Containers
```bash
docker ps -a | grep aijesusbro
# If nothing, aijesusbro-brain is not running → archive it
```

### 2. Check CloudFlare Deployments
Need to check CloudFlare dashboard for active workers:
- `retell-brain-mcp` (cloudeflareMCP)
- `vapi-mcp-server`

Or use CLI:
```bash
cd "/Users/aijesusbro/AI Projects/cloudeflareMCP"
wrangler deployments list

cd "/Users/aijesusbro/AI Projects/vapi-mcp-server"
wrangler deployments list
```

### 3. Check D1 Databases
```bash
# Check if databases are actually being used
wrangler d1 execute retell-brain-db --command "SELECT COUNT(*) FROM sqlite_master"
wrangler d1 execute vapi-calls-db --command "SELECT COUNT(*) FROM calls"
```

---

## Last Updated
November 13, 2025
