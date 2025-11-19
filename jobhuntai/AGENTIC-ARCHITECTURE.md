# JobHunt AI - Agentic Architecture

**Date**: November 13, 2025
**Author**: Built with Claude (AI Assistant)
**For**: John Kruze (@aijesusbro)

---

## Vision

Build a **truly agentic** job search system where:
- Users provide **intent** in natural language
- System **orchestrates itself** autonomously
- Agents **coordinate** through CloudFlare primitives
- Everything happens **at the edge** with zero manual steps

**Not**: Call 5 APIs in sequence
**Yes**: Say "Find jobs" and system does everything

---

## Core Principles

### 1. Agentic, Not Sequential
```
❌ Bad (Sequential):
You → API 1 → Wait → API 2 → Wait → API 3 → Wait → Done

✅ Good (Agentic):
You → Natural Language → System Orchestrates Everything → Done
                ↓
         Parallel Execution
         Self-Coordination
         Automatic Retries
```

### 2. CloudFlare Primitives as Building Blocks

**Not custom orchestration** - Use platform features:
- **Durable Objects**: Stateful coordination
- **Queues**: Work distribution
- **Workers AI**: Intelligence
- **D1**: Persistence
- **Browser Rendering**: JS pages

### 3. Event-Driven Architecture

Every operation emits events → Full observability

---

## Architecture Layers

### Layer 1: Natural Language Interface

**File**: `workers/nl-orchestrator.js`

**Purpose**: Parse human intent → System actions

**Flow**:
```javascript
User: "Find ML jobs at Anthropic"
  ↓
Workers AI (Llama 70B) parses intent:
{
  action: "find_jobs",
  companies: ["Anthropic"],
  filters: { role_types: ["ml"] }
}
  ↓
Router sends to orchestrateFindJobs()
  ↓
For each company:
  - Create/find organization in D1
  - Get Durable Object stub
  - Trigger orchestration
```

**Supported Actions**:
- `find_jobs`: Autonomous job search
- `check_status`: Get all job search statuses
- `review_applications`: List high-fit drafts
- `add_company`: Add org without searching yet
- `rescrape`: Force re-scrape with fresh data

**Intelligence**: Workers AI understands variations:
- "meta" or "facebook" → "Meta"
- "openai" or "chatgpt" → "OpenAI"
- "backend jobs" → filters: {role_types: ["backend"]}

---

### Layer 2: Per-Organization Coordinators

**File**: `workers/durable-objects/org-coordinator.js`

**Purpose**: Stateful brain for each company's job search

**Why Durable Objects?**:
- **Persistent state**: Survives across requests
- **Single-threaded**: No race conditions
- **Automatic consistency**: CloudFlare handles replication
- **Global**: Runs close to data

**State Managed**:
```javascript
{
  org_id: "...",
  org_name: "Anthropic",
  org_domain: "anthropic.com",
  phase: "discovering_url" | "scraping_jobs" | "processing_roles" | "complete",
  careersUrl: null | "https://...",
  jobsFound: 0,
  rolesAnalyzed: 0,
  highFitRoles: [{role_id, fit_score, role_title}],
  applicationsGenerated: 0,
  lastError: null,
  retryCount: 0
}
```

**Key Methods**:

**1. `orchestrateJobSearch()`**
- Entry point for starting autonomous workflow
- Checks current phase
- Sends tasks to appropriate queue
- Prevents duplicate runs

**2. `handleAgentComplete()`**
- Callback from agents via queue consumer
- Updates state based on agent results
- Automatically triggers next phase
- Handles errors and retries

**3. `notifyComplete()`**
- Called when all work done
- Logs completion event
- (Future) POST webhook to DevMCP

**Lifecycle Example**:
```
1. orchestrateJobSearch() called
   → phase: "discovering_url"
   → Sends to ORG_QUEUE: discover_careers_url

2. Agent completes → handleAgentComplete(agent: "discover_careers_url")
   → Updates state.careersUrl
   → phase: "url_discovered"
   → Automatically calls orchestrateJobSearch() again

3. orchestrateJobSearch() sees careersUrl exists
   → phase: "scraping_jobs"
   → Sends to ORG_QUEUE: scrape_jobs

4. Agent completes → handleAgentComplete(agent: "scrape_jobs")
   → Updates state.jobsFound = 10
   → phase: "jobs_scraped"
   → Sends 10 messages to ROLE_QUEUE (parallel!)

5. Each role analyzed → handleAgentComplete(agent: "role_analyzed")
   → Increments state.rolesAnalyzed
   → If fit_score >= 75: Send to ROLE_QUEUE: generate_application
   → When rolesAnalyzed === jobsFound: phase = "generating_applications"

6. Each app generated → handleAgentComplete(agent: "application_generated")
   → Increments state.applicationsGenerated
   → When applicationsGenerated === highFitRoles.length:
     → phase = "complete"
     → notifyComplete()
```

**Error Handling**:
- Track `retryCount`
- After 3 failures → phase = "error"
- Agents can retry via queue (automatic)

---

### Layer 3: Queue-Based Agent Distribution

**Files**:
- `wrangler.toml`: Queue definitions
- `workers/queue-consumer.js`: Message processor

**Why Queues?**:
- **Parallel processing**: 50 roles analyzed simultaneously
- **Durability**: Messages persisted until processed
- **Automatic retries**: Up to 3 attempts per message
- **Dead letter queues**: Failed messages captured for debugging
- **Batch processing**: Process multiple messages efficiently

**Queue Architecture**:

**org-tasks** (Sequential per org):
- `discover_careers_url`: Find careers page
- `scrape_jobs`: Extract job listings

**role-tasks** (Parallel, batch size 50):
- `research_and_analyze`: Extract requirements + analyze fit
- `generate_application`: Create cover letter

**Message Format**:
```javascript
{
  type: "research_and_analyze",
  role_id: "abc123...",
  org_id: "xyz789...",
  trace_id: "trace_abc...",
  timestamp: 1699999999999
}
```

**Consumer Logic** (`queue-consumer.js`):
```javascript
export default {
  async queue(batch, env) {
    for (const message of batch.messages) {
      const task = message.body;

      switch (task.type) {
        case 'discover_careers_url':
          await processDiscoverURL(task, env);
          break;
        // ... other cases
      }

      message.ack(); // Remove from queue
    }
  }
};
```

**After Processing**:
- Agent runs (e.g., research + fit analysis)
- Writes to D1 database
- **Calls Durable Object coordinator** to report completion
- Coordinator updates state and triggers next phase

**Retry Logic**:
- Message fails → Automatic retry (up to 3 times)
- After 3 failures → Sent to dead letter queue
- Coordinator tracks failures per org via `retryCount`

---

### Layer 4: The 5 Specialized Agents

Each agent is a focused function that does ONE thing well.

**Agent 1: Discover Careers URL**
**File**: `workers/agents/discover-careers-url.js`

**Strategy**:
1. Try 8 hardcoded patterns (fast path, ~500ms)
   - `https://domain/careers`
   - `https://domain/jobs`
   - `https://careers.domain`
   - etc.
2. If all fail → Use Workers AI to search homepage (slow path, ~3s)
3. Validate URL (fetch + check content-type)
4. Write to database + emit event

**Agent 2: Scrape Jobs**
**File**: `workers/agents/scrape-jobs.js`

**Strategy**:
1. Fetch careers page HTML
2. Use Workers AI to extract job listings (JSON array)
3. For each job:
   - Fetch individual posting
   - Extract description with AI
   - Validate URL
   - Create role record in database
4. Deduplicate (skip if job_url already exists)
5. Return array of created roles

**Agent 3: Research Role**
**File**: `workers/agents/research-job.js`

**Strategy**:
1. Fetch job posting
2. Use Workers AI to extract:
   - requirements (array)
   - nice_to_haves (array)
   - tech_stack (array)
   - responsibilities (array)
   - salary_range
   - location
   - work_arrangement
3. Update role record with JSON data
4. Emit event

**Agent 4: Fit Analysis**
**File**: `workers/agents/strategy-job.js`

**Strategy**:
1. Get role + organization + user profile from D1
2. Build context-rich prompt
3. Use Workers AI to analyze:
   - fitScore (0-100)
   - confidence (0-100)
   - positioningStrategy (string)
   - keyStrengths (array)
   - experiencesToHighlight (array)
   - potentialConcerns (array)
   - action (apply_now | wait_for_referral | skip)
   - reasoning (explanation)
4. Update role with fit data
5. Emit event

**Agent 5: Generate Application**
**File**: `workers/agents/outreach-job.js`

**Strategy**:
1. Get role + fit analysis + user profile
2. Build context including positioning strategy
3. Use Workers AI to generate 3-4 paragraph cover letter
4. Create email subject + body
5. Save as draft application
6. Emit event

---

### Layer 5: Data Persistence & Event Sourcing

**Database**: CloudFlare D1 (SQLite at the edge)

**Key Tables**:
```sql
organizations   -- Target companies
roles           -- Job openings
applications    -- Draft and sent applications
user_profile    -- Your resume/skills
events          -- Full audit trail
```

**Event Sourcing**:
Every operation logged to `events` table:
```sql
INSERT INTO events (
  id, trace_id, account_id, event_type, entity_type, entity_id, payload, timestamp
)
```

**Event Types**:
- `operation_started`
- `operation_completed`
- `careers_url_discovered`
- `role_scraped`
- `role_researched`
- `fit_analyzed`
- `application_generated`
- `job_search_complete`

**Benefits**:
- Full audit trail
- Debugging (replay events)
- Analytics (query by event_type)
- Observability (see what system did)

---

## Complete Flow Diagram

```
User: "Find ML jobs at Anthropic"
  ↓
[NL Orchestrator] (nl-orchestrator.js)
  ├─ Workers AI parses intent
  └─ Creates org if not exists
  ↓
[Durable Object: Anthropic] (org-coordinator.js)
  ├─ State: { phase: "idle" }
  └─ orchestrateJobSearch() → ORG_QUEUE: discover_careers_url
  ↓
[Queue Consumer] (queue-consumer.js)
  └─ processDiscoverURL()
     ↓
  [Agent 1] (discover-careers-url.js)
     ├─ Tries 8 patterns
     ├─ Finds: anthropic.com/careers
     ├─ Writes to DB
     └─ Callback to Durable Object
  ↓
[Durable Object: Anthropic]
  ├─ handleAgentComplete() → Updates state.careersUrl
  ├─ phase: "url_discovered"
  └─ orchestrateJobSearch() again → ORG_QUEUE: scrape_jobs
  ↓
[Queue Consumer]
  └─ processScrapeJobs()
     ↓
  [Agent 2] (scrape-jobs.js)
     ├─ Fetches careers page
     ├─ Workers AI extracts 5 jobs
     ├─ Creates 5 role records
     └─ Callback to Durable Object
  ↓
[Durable Object: Anthropic]
  ├─ handleAgentComplete() → state.jobsFound = 5
  ├─ phase: "jobs_scraped"
  └─ Sends 5× to ROLE_QUEUE: research_and_analyze
  ↓
[Queue Consumer] (batch: 5 messages in parallel!)
  ├─ processResearchAndAnalyze() × 5
  │   ↓
  │ [Agent 3] Research × 5 (parallel)
  │   ↓
  │ [Agent 4] Fit Analysis × 5 (parallel)
  │   ├─ Role 1: fit_score = 88 (high fit!)
  │   ├─ Role 2: fit_score = 92 (high fit!)
  │   ├─ Role 3: fit_score = 45 (skip)
  │   ├─ Role 4: fit_score = 78 (high fit!)
  │   └─ Role 5: fit_score = 30 (skip)
  │   ↓
  └─ Callbacks to Durable Object × 5
  ↓
[Durable Object: Anthropic]
  ├─ handleAgentComplete() × 5
  ├─ rolesAnalyzed = 5
  ├─ highFitRoles = [Role1, Role2, Role4] (3 roles)
  ├─ phase: "generating_applications"
  └─ Sends 3× to ROLE_QUEUE: generate_application
  ↓
[Queue Consumer] (batch: 3 messages)
  └─ processGenerateApp() × 3
     ↓
  [Agent 5] (outreach-job.js) × 3
     ├─ Generates cover letter 1
     ├─ Generates cover letter 2
     ├─ Generates cover letter 3
     └─ Callbacks × 3
  ↓
[Durable Object: Anthropic]
  ├─ handleAgentComplete() × 3
  ├─ applicationsGenerated = 3
  ├─ phase: "complete"
  └─ notifyComplete()
     ↓
  [Event] job_search_complete
     ↓
  (Future) Webhook → DevMCP
```

**Total Time**: ~2-3 minutes
**Parallel Processing**: Research + fit analysis for 5 roles happens simultaneously
**Automatic**: User does nothing after initial query

---

## Why This Is Truly Agentic

### 1. Self-Coordination
Agents don't know about each other. Coordinator orchestrates.

### 2. Autonomous Execution
No manual steps. Coordinator triggers next phase automatically.

### 3. Parallel Intelligence
50 roles analyzed simultaneously via queue batching.

### 4. Self-Healing
Automatic retries, dead letter queues, error tracking.

### 5. Stateful
Durable Objects maintain context across all operations.

### 6. Event-Driven
Everything emits events → Full observability.

### 7. Natural Language
Users provide intent, not instructions.

---

## Scaling Characteristics

### Sequential Bottlenecks
- URL discovery: 1 per org (can't parallelize, need to wait)
- Job scraping: 1 per org (need careers URL first)

### Parallel Execution
- **Multiple orgs**: N Durable Objects run independently
- **Role processing**: Batch size 50 in queue
- **Application generation**: All high-fit roles at once

### Performance Math

**1 company, 10 jobs**:
- URL: 2s
- Scrape: 60s (10 fetches)
- Research+Fit (×10 parallel): 20s
- Apps (×3 parallel): 15s
- **Total: ~100s**

**10 companies (parallel Durable Objects)**:
- Each runs independently
- Longest company = total time
- **Total: ~100-120s** (not 10× longer!)

**100 roles (single company)**:
- Research+Fit batched in groups of 50
- 2 batches × 20s = 40s
- **Not 100 × 20s!**

---

## Development vs Production

### Development (`--env dev`)
- Worker: `jobhunt-ai-dev`
- Queues: `org-tasks-dev`, `role-tasks-dev`
- D1: `revops-os-db-dev`

### Production (`--env production`)
- Worker: `jobhunt-ai`
- Queues: `org-tasks`, `role-tasks`
- D1: `jobhunt-ai-db-production` (to create)

---

## Future Enhancements

### Phase 2: Advanced Agentic Features

**Browser Rendering Agent**:
- Use CloudFlare Browser API
- Handle JavaScript-heavy pages (Anthropic, etc.)
- Screenshot for verification

**Cron Orchestrator**:
- Daily auto-scrape priority companies
- Trigger at 8am: "Check for new jobs"
- Email digest of high-fit roles

**Learning Agent**:
- Track application outcomes
- Learn which positioning strategies work
- Improve fit scoring over time

**Referral Agent**:
- LinkedIn integration
- Detect connections at target company
- Auto-request referrals

### Phase 3: Multi-User

**Account Isolation**:
- Each user gets own Durable Object namespace
- Separate queues per account
- Multi-tenant D1 with account_id

**Team Features**:
- Share job searches
- Collaborative application review
- Team fit analysis (who fits best?)

---

## Monitoring & Observability

### CloudFlare Analytics
- Request rates
- Error rates
- Durable Object invocations
- Queue depths

### Custom Events
Query `events` table for insights:
```sql
-- Job searches completed today
SELECT COUNT(DISTINCT entity_id)
FROM events
WHERE event_type = 'job_search_complete'
  AND timestamp > ?

-- Average fit scores
SELECT AVG(CAST(json_extract(payload, '$.fit_score') AS INTEGER))
FROM events
WHERE event_type = 'fit_analyzed'

-- Most common errors
SELECT payload, COUNT(*)
FROM events
WHERE event_type LIKE '%error%'
GROUP BY payload
ORDER BY COUNT(*) DESC
```

---

## Summary

JobHunt AI is a **genuinely agentic system** that:

✅ Uses CloudFlare primitives properly (DO, Queues, Workers AI)
✅ Orchestrates itself autonomously
✅ Processes work in parallel (not sequential)
✅ Maintains state across operations
✅ Heals itself (retries, DLQ)
✅ Provides natural language interface
✅ Emits full event trail
✅ Scales efficiently (Durable Objects + Queues)

**User Experience**: Say what you want → System does everything → Get results

**Not**: Call APIs manually
**Yes**: Autonomous multi-agent orchestration

---

*Built on CloudFlare Workers, Durable Objects, Queues, Workers AI, D1*
*Architecture by Claude (AI Assistant) for @aijesusbro*
*November 13, 2025*
