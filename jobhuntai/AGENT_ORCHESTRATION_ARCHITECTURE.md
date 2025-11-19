# JobHunt AI - Agent Orchestration Architecture

**Design Goal:** Distributed multi-agent system on Cloudflare with ZERO complex primitives

**Demo Value:** Shows how to build production-grade agent orchestration using only D1 + Workers AI

---

## Architecture Principles

### What We USE
✅ **D1 Database** - Single source of truth (PostgreSQL-compatible SQLite at edge)
✅ **Workers AI** - Llama 70B for intelligence (no external API calls)
✅ **Browser API** - Cloudflare's headless Chrome (when needed)
✅ **Event Sourcing** - Full audit trail in `events` table

### What We DON'T USE
❌ **Durable Objects** - Too complex, hard to reason about
❌ **Queues** - Adds async complexity, not needed for job scraping
❌ **KV** - D1 is enough, no need for separate key-value store
❌ **Vectorize** - Not using embeddings (yet)
❌ **External APIs** - Everything runs on Cloudflare

**Result:** Pure serverless agent system with clean separation of concerns

---

## Agent Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      WORKER API LAYER                        │
│              (workers/api.js - Hono.js router)               │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                   AGENT ORCHESTRATION                        │
│              (Sequential, stateless, idempotent)             │
└─────────────────────────────────────────────────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        ▼                     ▼                     ▼
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│  Discovery   │────▶│   Scraping   │────▶│   Analysis   │
│    Agent     │     │    Agent     │     │    Agent     │
└──────────────┘     └──────────────┘     └──────────────┘
        │                     │                     │
        └─────────────────────┴─────────────────────┘
                              ▼
                    ┌──────────────────┐
                    │   D1 Database    │
                    │  (organizations, │
                    │   roles, events) │
                    └──────────────────┘
```

---

## Data Flow: Job Scraping

### Step 1: Check Cache
```
POST /api/organizations/:id/scrape-jobs
  ↓
SELECT careers_url FROM organizations WHERE id = :id
  ↓
IF careers_url EXISTS AND NOT stale (< 7 days old)
  → Skip to Step 3
ELSE
  → Continue to Step 2
```

### Step 2: Discover Careers URL
```
Call: discoverCareersUrl(org_id, domain, env)
  ↓
1. Try hardcoded patterns first (fast path)
   - https://www.{domain}/careers
   - https://{domain}/careers
   - https://jobs.{domain}
   etc.
  ↓
2. If all fail, use AI-powered search:
   - Query: "{company_name} careers page URL"
   - Use Workers AI to analyze results
   - Extract most likely URL
  ↓
3. Validate URL with HEAD request
  ↓
4. Save to database:
   UPDATE organizations
   SET careers_url = ?, careers_url_discovered_at = ?
   WHERE id = ?
  ↓
5. Emit discovery event:
   INSERT INTO events (event_type, entity_id, payload)
   VALUES ('careers_url_discovered', org_id, {url, method})
```

### Step 3: Scrape Jobs
```
Call: scrapeCompanyJobs(org_id, careers_url, env)
  ↓
1. Fetch careers page HTML (with Browser API if needed)
2. Use Workers AI to extract job listings
3. Extract REAL job URLs from HTML (not AI-generated)
4. For each job URL:
   - Fetch full job posting
   - Extract structured data (title, description, requirements)
   - Save to roles table
   - Emit role_scraped event
```

### Step 4: Return Results
```json
{
  "success": true,
  "org_id": "...",
  "careers_url": "https://www.anthropic.com/careers",
  "careers_url_source": "cached", // or "discovered"
  "jobs_found": 15,
  "roles_created": 10
}
```

---

## Database Schema Changes

### Organizations Table (Add Caching Columns)
```sql
ALTER TABLE organizations ADD COLUMN careers_url TEXT;
ALTER TABLE organizations ADD COLUMN careers_url_discovered_at INTEGER;
ALTER TABLE organizations ADD COLUMN careers_url_last_checked INTEGER;
ALTER TABLE organizations ADD COLUMN careers_url_discovery_method TEXT; -- 'hardcoded', 'ai_search', 'manual'
```

**Indexes:**
```sql
CREATE INDEX idx_orgs_careers_url ON organizations(careers_url);
CREATE INDEX idx_orgs_careers_url_discovered ON organizations(careers_url_discovered_at);
```

---

## Agent Files Structure

```
/workers/agents/
├── discover-careers-url.js    ← NEW: Career URL discovery
├── scrape-jobs.js             ← UPDATED: Use discovered URLs, extract real links
├── research-job.js            ← No changes needed
├── strategy-job.js            ← No changes needed
└── outreach-job.js            ← No changes needed

/workers/lib/
├── ai.js                      ← Helper for Workers AI calls
├── scraper.js                 ← Helper for web scraping
├── events.js                  ← Helper for event emission
└── [other utilities]          ← No changes needed
```

---

## Agent: discover-careers-url.js

**Purpose:** Find the real careers page URL for any company

**Input:**
- `org_id` - Organization ID
- `domain` - Company domain (e.g., "anthropic.com")
- `company_name` - Company name (e.g., "Anthropic")

**Process:**
1. Try 8 common URL patterns (fast path)
2. If all fail, use AI to search for careers page
3. Validate discovered URL
4. Cache in database

**Output:**
```json
{
  "success": true,
  "careers_url": "https://www.anthropic.com/careers",
  "discovery_method": "hardcoded",  // or "ai_search"
  "tried_urls": 1,
  "total_patterns": 8
}
```

**Database Side Effects:**
- Updates `organizations.careers_url`
- Updates `organizations.careers_url_discovered_at`
- Emits `careers_url_discovered` event

---

## Agent: scrape-jobs.js (Enhanced)

**Changes:**
1. Accept `careers_url` as parameter (from discovery or cache)
2. Extract REAL job URLs from page (not AI-generated)
3. Use Browser API if page is JavaScript-heavy
4. Better error handling with retry logic

**Key Improvement: Real URL Extraction**
```javascript
// OLD (CURRENT):
const jobUrl = `https://${org.domain}/careers/${slugify(job.title)}`;  // FAKE

// NEW (AFTER ENHANCEMENT):
const jobUrl = extractedLinks.find(link =>
  link.text.toLowerCase().includes(job.title.toLowerCase().slice(0, 20))
);  // REAL
```

---

## Orchestration Flow (workers/api.js)

**Route:** `POST /api/organizations/:id/scrape-jobs`

```javascript
async function handleScrapeJobs(c) {
  const org_id = c.req.param('id');
  const account_id = c.req.header('X-Account-Id');

  // 1. Get organization
  const org = await c.env.DB.prepare(`
    SELECT * FROM organizations WHERE id = ? AND account_id = ?
  `).bind(org_id, account_id).first();

  if (!org) {
    return c.json({ success: false, error: 'Organization not found' }, 404);
  }

  // 2. Check if we have a cached careers URL
  let careersUrl = org.careers_url;
  let urlSource = 'cached';

  const isCacheStale = !careersUrl ||
    (Date.now() - org.careers_url_discovered_at > 7 * 24 * 60 * 60 * 1000); // 7 days

  // 3. If no URL or stale, discover it
  if (isCacheStale) {
    const discovery = await discoverCareersUrl(org_id, org.domain, org.name, c.env);
    if (discovery.success) {
      careersUrl = discovery.careers_url;
      urlSource = 'discovered';
    } else {
      return c.json({
        success: false,
        error: 'Could not find careers page',
        tried_urls: discovery.tried_urls
      }, 404);
    }
  }

  // 4. Scrape jobs from discovered/cached URL
  const result = await scrapeCompanyJobs(org_id, account_id, careersUrl, c.env);

  // 5. Add metadata to response
  return c.json({
    ...result,
    careers_url_source: urlSource,
    careers_url: careersUrl
  });
}
```

---

## Event Sourcing

**All agent actions emit events to `events` table:**

```sql
-- Career URL discovered
INSERT INTO events (trace_id, account_id, event_type, entity_type, entity_id, payload)
VALUES (?, ?, 'careers_url_discovered', 'organization', ?,
  '{"url": "...", "method": "hardcoded", "tried_count": 1}');

-- Job scraped
INSERT INTO events (trace_id, account_id, event_type, entity_type, entity_id, payload)
VALUES (?, ?, 'role_scraped', 'role', ?,
  '{"role_title": "...", "org_id": "...", "has_description": true}');

-- Fit analysis completed
INSERT INTO events (trace_id, account_id, event_type, entity_type, entity_id, payload)
VALUES (?, ?, 'fit_analyzed', 'role', ?,
  '{"fit_score": 82, "action": "apply_now"}');
```

**Benefits:**
- Full audit trail
- Debug agent behavior
- Analytics on agent performance
- Replay events if needed

---

## Why This is Cool for Developers

### 1. **Pure Serverless**
- No servers, no containers, no K8s
- Deploys in 3 seconds to 330+ edge locations
- Auto-scales to zero, scales to infinity

### 2. **Agent Orchestration Without Complexity**
- No message queues
- No complex state machines
- Just: agents → database → events
- Easy to reason about, easy to debug

### 3. **Smart Caching**
- Discovers URLs once, caches for 7 days
- Self-healing (re-discovers if stale)
- No manual configuration needed

### 4. **Event Sourcing**
- Every action logged
- Time-travel debugging
- Audit trail for compliance
- Performance analytics built-in

### 5. **Edge-Native AI**
- Workers AI (Llama 70B) runs at edge
- No external API calls (no latency, no rate limits)
- Browser API for JavaScript-rendered pages
- Everything in one platform

### 6. **Developer Experience**
- Single `wrangler deploy` command
- Logs via `wrangler tail`
- SQL debugging via `wrangler d1 execute`
- No infrastructure to manage

---

## Performance Characteristics

**Latency:**
- Cold start: ~10ms (Workers)
- Career URL discovery: 500-2000ms (includes AI)
- Job scraping: 2-5 seconds (includes AI extraction)
- Total end-to-end: 3-7 seconds for full pipeline

**Cost (Cloudflare Free Tier):**
- 100,000 requests/day
- 10,000 AI inferences/day
- 5M database reads/day
- **Total: $0/month**

**Scalability:**
- Handles 1000s of concurrent scraping requests
- Auto-scales globally
- No rate limiting (all internal)

---

## Migration Path

### Phase 1: Add Discovery Agent (This Session)
- Create `discover-careers-url.js`
- Add caching columns to organizations table
- Update scrape-jobs route to use discovery
- Test with 10 companies

### Phase 2: Enhance Scraper (Next Session)
- Re-enable Browser API with proper error handling
- Improve job URL extraction (real links, not AI-generated)
- Add retry logic for failed scrapes

### Phase 3: Production Hardening (This Week)
- Add rate limiting per organization
- Implement stale cache refresh in background
- Add monitoring and alerting
- Build admin dashboard for cache management

---

## File Changes Required

```
NEW FILES:
- workers/agents/discover-careers-url.js (200 lines)
- schema/migrations/008_add_careers_url_caching.sql (10 lines)

UPDATED FILES:
- workers/api.js (modify scrape-jobs route, +30 lines)
- workers/agents/scrape-jobs.js (enhance URL extraction, +50 lines)

TOTAL: +290 lines of code
```

---

**This architecture demonstrates:**
- ✅ Distributed agent orchestration (no complex primitives)
- ✅ Smart caching and self-healing
- ✅ Event sourcing for observability
- ✅ Edge-native AI execution
- ✅ Production-grade error handling
- ✅ Zero infrastructure management

**Perfect for a portfolio demo.**
