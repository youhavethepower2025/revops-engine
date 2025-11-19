# JobHunt AI Investigation Report

**Date**: November 13, 2025
**Purpose**: Identify what's real vs fake, what works, what needs building

---

## The Discovery: Fake Test Data

You discovered 95 organizations and 300+ jobs that were **hardcoded test data**, not real scraping results.

## Current State Analysis

### Database: `revops-os-db-dev` (1.2MB)

**Tables Found** (33 total):
```
Job Hunt Tables:
- organizations (95 rows - NEED TO VERIFY IF REAL OR FAKE)
- roles (job openings)
- people (hiring managers)
- applications
- interviews
- user_profile

RevOps Legacy Tables (still in DB):
- accounts
- leads
- campaigns
- conversations
- events
- decision_logs
- analytics
- patterns
- experiments
- agent_memory
- agent_versions
- call_records
- flow_traces
- compliance_checks
- approval_workflows
- circuit_breaker_state
- dead_letter_queue
- opt_outs
- actions
- users
```

**Problem**: This database has BOTH JobHunt AI and old RevOps tables!

###Worker Structure

**Main API** (`workers/api.js` - 50KB):
- Framework: Hono.js
- Routes:
  - `/health` - Health check ✅
  - `/` - Index HTML (built-in dashboard)
  - `/dashboard` - Dashboard UI
  - `/dashboard-v2` - Enhanced dashboard
  - `/test/ai` - Test Workers AI ⚠️ (creates test data)
  - `/test/scrape` - Test scraping ⚠️ (creates test data)
  - `/test/research` - Test research agent ⚠️ (creates test accounts/leads)
  - `/test/outreach` - Test outreach agent ⚠️ (creates test campaigns)

**Agents** (`workers/agents/`):
- Research agent
- Outreach agent
- (Need to verify what else exists)

**Lib** (`workers/lib/`):
- auth.js
- events.js
- index-html.js (dashboard HTML)
- app-html.js
- dashboard-v2-html.js
- scraper.js (company website scraping)
- (Need to verify complete list)

---

## Critical Issues Found

### 1. Test URL is WRONG
`test-job-scraper.sh` calls:
```bash
API_BASE="https://revops-os-dev.aijesusbro-brain.workers.dev/api"
```

**Problem**: We just deleted `revops-os-dev` worker!
**Fix needed**: Change to `https://jobhunt-ai-dev.aijesusbro-brain.workers.dev/api`

### 2. Test Endpoints Create Fake Data
All `/test/*` endpoints create fake accounts, leads, and campaigns:
```javascript
// From api.js:77-107
app.get('/test/research', async (c) => {
  const account_id = generateId();
  const lead_id = generateId();

  // Creates FAKE test account
  await c.env.DB.prepare(`INSERT INTO accounts...`).run();

  // Creates FAKE test lead
  await c.env.DB.prepare(`INSERT INTO leads...`).run();
})
```

**These test endpoints are dangerous** - they pollute production DB with fake data!

### 3. Mixed Database Schema
The D1 database has:
- JobHunt AI tables (organizations, roles, applications)
- Old RevOps tables (leads, campaigns, conversations)

**Decision needed**: Clean up old RevOps tables or keep for compatibility?

### 4. No Real Scraping Yet?
Need to verify:
- Does `/organizations/:id/scrape-jobs` actually work?
- Are the 95 organizations real or seeded test data?
- Have any real jobs been scraped?

---

## What Actually Works

### ✅ Confirmed Working:
1. **Database connection** - D1 is connected and accessible
2. **Health endpoint** - `/health` returns OK
3. **Workers AI** - Test endpoint shows Llama 70B and Qwen working
4. **Browser rendering** - CloudFlare Browser API available
5. **Basic structure** - Hono app, CORS, routing all functional

### ⚠️ Needs Verification:
1. **Job scraping** - Does it actually scrape or just create test data?
2. **Research agent** - Real company enrichment or fake?
3. **Outreach agent** - Actually generates or templates only?
4. **Dashboard** - Shows real data or test data?

### ❌ Known Broken:
1. **Test script** - Calls deleted worker URL
2. **Test endpoints** - Create fake data in production DB

---

## Architecture Gaps

### Missing Components for Full Functionality:

#### 1. URL Discovery Worker
You mentioned needing a worker that "gets URL information differently"
- **Current**: Scraper assumes careers URL known
- **Needed**: Discover careers page URL automatically
- **Approach**: Crawl homepage, look for "careers", "jobs", "join us" links

#### 2. Durable Objects (Your Idea)
- **Current**: Everything in D1 (edge database)
- **Potential**: Durable Objects for:
  - Per-organization scraping state
  - Rate limiting per domain
  - Scraping queue management
  - Deduplication logic

#### 3. MCP Server Integration
- **Current**: Standalone worker
- **Needed**: MCP protocol server so DevMCP can control it
- **Would enable**:
  - Trigger scrapes from DevMCP
  - Query jobs from DevMCP
  - Manage organizations from DevMCP

#### 4. Real Production APIs
Need to verify which are implemented:
- `POST /organizations` - Create org
- `GET /organizations` - List orgs
- `POST /organizations/:id/scrape-jobs` - Trigger scrape
- `GET /roles` - List jobs
- `POST /applications` - Create application
- `GET /applications` - List applications

---

## Recommended Investigation Steps

### Phase 1: Validate Current State (Do This First)

```bash
# 1. Check if the 95 orgs are real or test data
cd "/Users/aijesusbro/AI Projects/jobhuntai"
npx wrangler d1 execute revops-os-db-dev --remote --command \
  "SELECT name, domain, created_at FROM organizations LIMIT 10"

# 2. Check if any real jobs exist
npx wrangler d1 execute revops-os-db-dev --remote --command \
  "SELECT role_title, job_url, org_id FROM roles LIMIT 10"

# 3. Test the actual worker (not test endpoints!)
curl https://jobhunt-ai-dev.aijesusbro-brain.workers.dev/health

# 4. Try to list organizations via API
curl https://jobhunt-ai-dev.aijesusbro-brain.workers.dev/api/organizations \
  -H "X-Account-Id: account_john_kruze"
```

### Phase 2: Read All Worker Code

Check what's in:
```bash
ls -la workers/agents/
ls -la workers/lib/
```

Read each file to understand actual functionality.

### Phase 3: Test Real Scraping

Try scraping ONE company manually:
```bash
# Create a test org
curl -X POST https://jobhunt-ai-dev.aijesusbro-brain.workers.dev/api/organizations \
  -H "Content-Type: application/json" \
  -H "X-Account-Id: account_john_kruze" \
  -d '{
    "name": "Anthropic",
    "domain": "anthropic.com",
    "industry": "AI",
    "priority": 1
  }'

# Then trigger scrape
curl -X POST https://jobhunt-ai-dev.aijesusbro-brain.workers.dev/api/organizations/[ORG_ID]/scrape-jobs \
  -H "X-Account-Id: account_john_kruze"
```

---

## Optimization Opportunities

### 1. URL Discovery Worker (NEW)
```
Input: Company domain
Output: Careers page URL

Process:
1. Fetch homepage
2. Parse for common career links
3. Use Workers AI to analyze page
4. Return careers URL + confidence score
```

### 2. Scraping Worker (ENHANCE)
```
Current: Basic scraping
Enhanced:
- Rate limiting per domain
- Retry logic with exponential backoff
- Deduplication (don't re-scrape same job)
- Structured data extraction with AI
- Screenshots for visual confirmation
```

### 3. Durable Objects State Machine
```
Per-organization scraping state:
- last_scraped_at
- scrape_interval
- consecutive_failures
- discovered_urls
- rate_limit_state
```

### 4. MCP Server Wrapper
```
Create: workers/mcp-server.js

Exposes tools:
- trigger_org_scrape(org_id)
- list_organizations()
- create_organization(name, domain)
- list_recent_jobs(limit)
- get_job_details(role_id)
- analyze_job_fit(role_id)
```

---

## Database Cleanup Needed

### Option A: Keep Job Hunt Tables Only
```sql
-- Drop all RevOps tables
DROP TABLE IF EXISTS leads;
DROP TABLE IF EXISTS campaigns;
DROP TABLE IF EXISTS conversations;
-- etc...
```

### Option B: Migrate to Separate DB
Create `jobhunt-ai-db` and migrate only Job Hunt tables.

---

## Next Actions

1. **Run investigation queries** (see Phase 1 above)
2. **Audit all worker files** - understand what actually exists
3. **Fix test script** - update URL from revops-os-dev to jobhunt-ai-dev
4. **Test real scraping** - verify it works with ONE company
5. **Clean database** - remove fake data or separate JobHunt from RevOps
6. **Build URL discovery** - new worker for finding careers pages
7. **Add Durable Objects** - state management for scraping
8. **Create MCP server** - so DevMCP can control JobHunt AI

---

## Questions to Answer

1. Are the 95 organizations real companies or test data?
2. Are there any real jobs in the database or all fake?
3. What agent files exist in `workers/agents/`?
4. What lib files exist in `workers/lib/`?
5. Does the actual scraping endpoint work?
6. Should we clean up old RevOps tables?
7. Do you want URL discovery as a separate worker or built-in?
8. Should we use Durable Objects for scraping state?

---

**Ready to deep dive?** Let me know what you want to investigate first!
