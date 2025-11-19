# MCP-Native Systems Deployment Guide

**Complete guide to deploying RevOps Engine and Content Intelligence**

---

## 🎯 What Was Built

### CursorMCP Enhancements
- ✅ 18 new tools added (R2, Vectorize, MCP apps, scaffolding)
- ✅ Total: 47 tools available

### RevOps Engine
- ✅ 6 specialized workers
- ✅ 3 workflows
- ✅ MCP server with 5 tools
- ✅ D1 database schema

### Content Intelligence
- ✅ 6 specialized workers
- ✅ 3 workflows
- ✅ MCP server with 5 tools
- ✅ D1 database schema

---

## 🚀 Deployment Steps

### Step 1: Create D1 Databases

```bash
# RevOps Engine
cd "/Users/aijesusbro/AI Projects/revops-engine"
wrangler d1 create revops-engine-dev

# Copy the database_id from output
# Update wrangler.toml with database_id

# Content Intelligence
cd "/Users/aijesusbro/AI Projects/content-intelligence"
wrangler d1 create content-intelligence-dev

# Copy the database_id from output
# Update wrangler.toml with database_id
```

### Step 2: Apply Database Schemas

**Using CursorMCP (via Cursor):**

```
"Create the RevOps Engine database schema"
→ system_create_d1_schema({
    database_id: "your-revops-db-id",
    schema_sql: [read from revops-engine/schema/init.sql]
  })

"Create the Content Intelligence database schema"
→ system_create_d1_schema({
    database_id: "your-content-db-id",
    schema_sql: [read from content-intelligence/schema/init.sql]
  })
```

**Or manually:**
```bash
wrangler d1 execute revops-engine-dev --env dev --remote --file=./schema/init.sql
wrangler d1 execute content-intelligence-dev --env dev --remote --file=./schema/init.sql
```

### Step 3: Deploy Workers

**RevOps Workers:**
```bash
cd "/Users/aijesusbro/AI Projects/revops-engine"

# Deploy each worker
wrangler deploy --name revops-search --compatibility-date 2024-01-01 workers/search.js
wrangler deploy --name revops-scraper --compatibility-date 2024-01-01 workers/scraper.js
wrangler deploy --name revops-enrichment --compatibility-date 2024-01-01 workers/enrichment.js
wrangler deploy --name revops-researcher --compatibility-date 2024-01-01 workers/researcher.js
wrangler deploy --name revops-writer --compatibility-date 2024-01-01 workers/writer.js
wrangler deploy --name revops-tracker --compatibility-date 2024-01-01 workers/tracker.js
wrangler deploy --name revops-api --compatibility-date 2024-01-01 workers/api.js
wrangler deploy --name revops-mcp-server --compatibility-date 2024-01-01 workers/mcp-server.js
```

**Content Workers:**
```bash
cd "/Users/aijesusbro/AI Projects/content-intelligence"

# Deploy each worker
wrangler deploy --name content-search --compatibility-date 2024-01-01 workers/search.js
wrangler deploy --name content-fetcher --compatibility-date 2024-01-01 workers/fetcher.js
wrangler deploy --name content-analyzer --compatibility-date 2024-01-01 workers/analyzer.js
wrangler deploy --name content-grapher --compatibility-date 2024-01-01 workers/grapher.js
wrangler deploy --name content-synthesizer --compatibility-date 2024-01-01 workers/synthesizer.js
wrangler deploy --name content-monitor --compatibility-date 2024-01-01 workers/monitor.js
wrangler deploy --name content-api --compatibility-date 2024-01-01 workers/api.js
wrangler deploy --name content-mcp-server --compatibility-date 2024-01-01 workers/mcp-server.js
```

**Or use CursorMCP:**
```
"Deploy all RevOps workers as a cluster"
→ system_deploy_worker_cluster({
    workers: [read all worker files],
    shared_bindings: [D1, AI, BROWSER]
  })
```

### Step 4: Configure Worker Bindings

After deploying, configure bindings via Cloudflare Dashboard or wrangler.toml:

**For each worker that needs D1:**
```bash
wrangler d1 bindings add revops-search --database revops-engine-dev --binding DB
```

**For Workers AI:**
- Automatically available via `env.AI` binding
- No configuration needed

**For Browser API:**
- Automatically available via `env.BROWSER` binding
- No configuration needed

### Step 5: Connect Systems to CursorMCP

**In Cursor, use MCP tools:**
```
"Connect to RevOps MCP server"
→ mcp_connect_app({
    app_name: "revops",
    worker_url: "revops-mcp-server.aijesusbro-brain.workers.dev"
  })

"Connect to Content Intelligence MCP server"
→ mcp_connect_app({
    app_name: "content",
    worker_url: "content-mcp-server.aijesusbro-brain.workers.dev"
  })
```

### Step 6: Test Systems

**Test RevOps:**
```
"Start a campaign to research 5 AI companies"
→ mcp_call_app_tool("revops", "start_campaign", {
    campaign_name: "AI Companies Test",
    criteria: { industry: "AI", roles: ["CTO"], count: 5 },
    user_id: "test_user"
  })
```

**Test Content:**
```
"Research MCP adoption trends"
→ mcp_call_app_tool("content", "research_topic", {
    topic: "MCP adoption trends",
    user_id: "test_user",
    max_sources: 20
  })
```

---

## 📊 System Architecture

### RevOps Engine Flow

```
User → CursorMCP → revops-mcp-server
  → start_campaign tool
    → Triggers Workflow: company-research-pipeline
      → revops-search (find companies)
      → revops-scraper (extract contacts)
      → revops-enrichment (enhance data)
      → revops-researcher (AI research)
      → revops-writer (generate emails)
    → Stores in D1: campaigns, prospects, messages
  → Returns: "20 prospects researched, drafts ready"
```

### Content Intelligence Flow

```
User → CursorMCP → content-mcp-server
  → research_topic tool
    → Triggers Workflow: deep-research
      → content-search (find sources)
      → content-fetcher (extract content)
      → content-analyzer (AI insights)
      → content-grapher (build graph)
      → content-synthesizer (generate report)
    → Stores in D1: research_topics, sources, insights, knowledge_graph, reports
  → Returns: "40+ sources analyzed, report generated"
```

---

## 🔧 Configuration Files

### RevOps Engine
- `revops-engine/wrangler.toml` - Cloudflare config
- `revops-engine/package.json` - Dependencies
- `revops-engine/schema/init.sql` - Database schema

### Content Intelligence
- `content-intelligence/wrangler.toml` - Cloudflare config
- `content-intelligence/package.json` - Dependencies
- `content-intelligence/schema/init.sql` - Database schema

---

## 🎯 Monday Demo Scripts

### Demo 1: RevOps Engine

**Command in Cursor:**
```
"Research 20 AI infrastructure companies and draft outreach to their CTOs"
```

**Expected Flow:**
1. `mcp_call_app_tool("revops", "start_campaign", {...})`
2. RevOps executes full pipeline
3. Returns: "20 companies researched, 20+ CTOs found, personalized emails drafted"

**Show:**
- D1 database queries showing prospects
- Generated email drafts
- Research notes

### Demo 2: Content Intelligence

**Command in Cursor:**
```
"Research MCP adoption trends and create a technical brief"
```

**Expected Flow:**
1. `mcp_call_app_tool("content", "research_topic", {...})`
2. Content executes research pipeline
3. Returns: "40+ sources analyzed, key trends extracted, 5-page report generated"

**Show:**
- Sources table
- Insights extracted
- Generated report
- Knowledge graph

### Demo 3: Cross-System Orchestration

**Command in Cursor:**
```
"Research AI infrastructure companies, then create outreach campaign"
```

**Expected Flow:**
1. Content system researches topic
2. RevOps system uses research to find companies
3. RevOps generates outreach
4. Single unified response

---

## ✅ Verification Checklist

- [ ] D1 databases created
- [ ] Schemas applied
- [ ] All workers deployed
- [ ] Worker bindings configured
- [ ] MCP servers deployed
- [ ] Systems connected to CursorMCP
- [ ] Test campaigns/research working
- [ ] Cross-system orchestration working

---

## 🚨 Troubleshooting

### Workers not deploying
- Check wrangler.toml configuration
- Verify Cloudflare API token
- Check worker names are unique

### Database errors
- Verify database_id in wrangler.toml
- Check schema SQL syntax
- Ensure bindings are configured

### MCP connection fails
- Verify worker URLs are correct
- Check MCP endpoint is `/mcp`
- Test worker health: `https://worker-url/health`

### AI not working
- Verify Workers AI binding
- Check model name: `@cf/qwen/qwen-2.5-7b-instruct`
- Ensure account has Workers AI access

---

## 📚 Next Steps

1. Deploy systems to Cloudflare
2. Connect via CursorMCP
3. Test end-to-end flows
4. Prepare Monday demos
5. Build next 3 systems (CRM, Documents, Automation)

---

**All systems built and ready for deployment!** 🚀


