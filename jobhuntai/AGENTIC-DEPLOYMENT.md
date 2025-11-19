# JobHunt AI - Agentic Deployment Guide

**Built for**: Autonomous job search orchestration with natural language interface
**Date**: November 13, 2025
**Status**: Ready to deploy

---

## What This Is

JobHunt AI is a **truly agentic** job search automation system built on CloudFlare's edge platform. It uses:

- **Durable Objects** for stateful per-organization orchestration
- **Queues** for async agent work distribution
- **Workers AI** (Llama 70B) for all intelligence
- **D1 Database** for persistence with event sourcing
- **Browser Rendering** for JavaScript-heavy career pages

**User Experience**: Natural language input → Autonomous multi-agent orchestration → Results

```
You: "Find ML jobs at Anthropic and Hugging Face"

System: *autonomous orchestration*
- Creates/finds organizations
- Discovers careers pages
- Scrapes all job listings (parallel)
- Researches each role (parallel × 50)
- Analyzes your fit
- Generates applications for high-fit roles (>75 score)

Result (2-3 minutes): "Found 15 jobs, 5 high-fit, 5 applications generated"
```

---

## Prerequisites

1. **CloudFlare Account** (free tier works)
2. **Wrangler CLI** installed
3. **Node.js** v18+ and npm

```bash
npm install -g wrangler
wrangler login
```

---

## Deployment Steps

### 1. Install Dependencies

```bash
cd "/Users/aijesusbro/AI Projects/jobhuntai"
npm install
```

### 2. Create CloudFlare Queues

```bash
# Create org-tasks queue (for URL discovery & scraping)
npx wrangler queues create org-tasks-dev

# Create role-tasks queue (for research, fit analysis, applications)
npx wrangler queues create role-tasks-dev

# Create dead letter queues (for failed messages)
npx wrangler queues create org-tasks-dlq
npx wrangler queues create role-tasks-dlq
```

### 3. Deploy Worker with Durable Objects

```bash
# Deploy to dev environment
npx wrangler deploy --env dev

# This creates:
# - Worker: jobhunt-ai-dev
# - Durable Object: OrgCoordinator
# - Queue consumers: org-tasks-dev, role-tasks-dev
```

**Note**: First deployment may take 2-3 minutes as CloudFlare provisions Durable Objects.

### 4. Verify Deployment

```bash
# Check health
curl https://jobhunt-ai-dev.aijesusbro-brain.workers.dev/health

# Expected: {"status":"ok","environment":"dev"}
```

### 5. Seed Your Profile

The system needs your resume/profile to analyze fit. Update the user_profile table:

```bash
npx wrangler d1 execute revops-os-db-dev --remote --command "
UPDATE user_profile SET
  full_name = 'Your Name',
  email = 'your@email.com',
  phone = '+1234567890',
  location = 'San Francisco, CA',
  linkedin_url = 'https://linkedin.com/in/yourprofile',
  github_url = 'https://github.com/yourhandle',
  skills = '[\"Python\", \"JavaScript\", \"AI/ML\", \"etc\"]',
  experience = 'Your work experience summary...',
  education = 'Your education...',
  key_projects = 'Your notable projects...'
WHERE account_id = 'account_john_kruze'
"
```

---

## Usage

### Natural Language API

**Endpoint**: `POST /api/orchestrate`

```bash
curl -X POST https://jobhunt-ai-dev.aijesusbro-brain.workers.dev/api/orchestrate \
  -H "Content-Type: application/json" \
  -d '{"query": "Find ML jobs at Anthropic"}'
```

**Response**:
```json
{
  "success": true,
  "message": "Started job search for 1 company",
  "companies": [{
    "company": "Anthropic",
    "org_id": "...",
    "status": "orchestrating",
    "phase": "discovering_url"
  }],
  "estimated_completion": "2-5 minutes",
  "next_steps": "System will autonomously discover, scrape, research, analyze, and generate applications..."
}
```

### Supported Queries

```javascript
// Job search
"Find ML jobs at Anthropic and OpenAI"
"Search for backend roles at YC companies"
"Find remote engineering positions"

// Status
"Check status"
"What's happening?"

// Review
"Show me applications ready to send"
"Get high-fit roles"
"Review applications"

// Management
"Add Google DeepMind"
"Rescrape Hugging Face"
```

### Check Status

```bash
curl -X POST https://jobhunt-ai-dev.aijesusbro-brain.workers.dev/api/orchestrate \
  -H "Content-Type: application/json" \
  -d '{"query": "Check status"}'
```

### Get High-Fit Applications

```bash
curl -X POST https://jobhunt-ai-dev.aijesusbro-brain.workers.dev/api/orchestrate \
  -H "Content-Type: application/json" \
  -d '{"query": "Show high-fit applications"}'
```

### Direct Coordinator Access (Advanced)

```bash
# Check specific organization status
curl https://jobhunt-ai-dev.aijesusbro-brain.workers.dev/api/coordinator/{ORG_ID}/status

# Manually trigger orchestration for org
curl -X POST https://jobhunt-ai-dev.aijesusbro-brain.workers.dev/api/coordinator/{ORG_ID}/orchestrate
```

---

## How It Works (Architecture)

### 1. Natural Language Parser

**Workers AI** (Llama 70B) parses your query:

```
"Find ML jobs at Anthropic"
→ {action: "find_jobs", companies: ["Anthropic"], filters: {role_types: ["ml"]}}
```

### 2. Per-Organization Coordination

**Durable Object** created for each organization:
- Manages all state (phase, jobs found, fit scores, etc.)
- Orchestrates the 5-agent workflow
- Handles retries and errors

### 3. Agent Workflow (Autonomous)

```
Coordinator → ORG_QUEUE: discover_careers_url
  ↓
Agent 1 → Discovers URL → Callback to Coordinator
  ↓
Coordinator → ORG_QUEUE: scrape_jobs
  ↓
Agent 2 → Scrapes 10 jobs → Callback to Coordinator
  ↓
Coordinator → ROLE_QUEUE × 10: research_and_analyze (PARALLEL!)
  ↓
Agent 3 + 4 (×10 in parallel) → Research + Fit Analysis → Callbacks
  ↓
Coordinator → ROLE_QUEUE × 3: generate_application (for high-fit only)
  ↓
Agent 5 (×3) → Generate cover letters → Callbacks
  ↓
Coordinator → COMPLETE → Webhook to DevMCP (optional)
```

### 4. Queue-Based Processing

**org-tasks queue**: URL discovery, job scraping (sequential per org)
**role-tasks queue**: Research, fit analysis, app generation (parallel, batch size 50)

**Why queues?**:
- Parallel processing (50 roles analyzed simultaneously)
- Automatic retries (up to 3 attempts)
- Dead letter queues for failed tasks
- Durability (messages persisted)

### 5. Event Sourcing

Every operation logged to `events` table:
- `careers_url_discovered`
- `role_scraped`
- `role_researched`
- `fit_analyzed`
- `application_generated`
- `job_search_complete`

Full audit trail of everything the system does.

---

## Performance

### Typical Job Search (1 company, 10 jobs)

| Phase | Time | Parallel? |
|-------|------|-----------|
| URL Discovery | 1-2s | No |
| Job Scraping | 30-60s | No (sequential fetches) |
| Research (×10) | 10-20s | **Yes** (batch processed) |
| Fit Analysis (×10) | 5-10s | **Yes** (included with research) |
| Applications (×3) | 10-15s | **Yes** (for high-fit roles) |
| **Total** | **60-100s** | - |

### Scale

- **1 company**: ~1-2 minutes
- **10 companies (parallel)**: ~2-3 minutes (Durable Objects run in parallel)
- **100 companies (parallel)**: ~3-5 minutes
- **1000 roles analyzed**: ~30 seconds (queue batch processing)

---

## Monitoring & Debugging

### CloudFlare Dashboard

1. **Workers & Pages** → `jobhunt-ai-dev`
   - View logs
   - Monitor requests
   - Check errors

2. **Queues**
   - `org-tasks-dev`: Messages waiting
   - `role-tasks-dev`: Messages waiting
   - Dead letter queues: Failed messages

3. **Durable Objects**
   - Active coordinators
   - Storage usage

### Query Logs

```bash
# Tail worker logs
npx wrangler tail jobhunt-ai-dev --env dev

# Tail queue consumer logs
npx wrangler tail jobhunt-ai-dev --env dev --format pretty
```

### Database Queries

```bash
# Count active job searches
npx wrangler d1 execute revops-os-db-dev --remote --command "
SELECT phase, COUNT(*) FROM (
  SELECT DISTINCT entity_id, MAX(timestamp) as last_ts
  FROM events
  WHERE event_type LIKE '%complete%'
  GROUP BY entity_id
)
"

# View recent events
npx wrangler d1 execute revops-os-db-dev --remote --command "
SELECT event_type, entity_type, timestamp
FROM events
ORDER BY timestamp DESC
LIMIT 20
"
```

---

## Troubleshooting

### Queue Not Processing

```bash
# Check queue depth
npx wrangler queues list

# Manually trigger queue processing (if stuck)
# Messages auto-retry, but you can redeploy to force
npx wrangler deploy --env dev
```

### Durable Object Stuck

```bash
# Reset specific coordinator
curl -X POST https://jobhunt-ai-dev.aijesusbro-brain.workers.dev/api/coordinator/{ORG_ID}/reset
```

### Workers AI Timeout

Workers AI calls have 60s timeout. If job pages are huge:
- URLs will be truncated to first 4000 characters
- System will retry up to 3 times
- Check dead letter queue for failed attempts

---

## Roadmap

### Phase 1: Core Agentic System ✅
- [x] Durable Object coordinators
- [x] Queue-based agent distribution
- [x] Natural language interface
- [x] Full autonomous workflow

### Phase 2: Enhancements 🔄
- [ ] Browser Rendering for JS pages (Anthropic, etc.)
- [ ] Cron Triggers for daily auto-scraping
- [ ] DevMCP webhook integration
- [ ] Multi-user support

### Phase 3: Intelligence 📅
- [ ] Learning from application outcomes
- [ ] Referral network detection (LinkedIn)
- [ ] Automatic follow-ups
- [ ] Interview scheduling

---

## MCP Integration (DevMCP)

Once deployed, add to DevMCP as a tool:

```python
# tools/job_hunt_tools.py

@mcp.tool()
async def job_hunt(query: str) -> dict:
    """
    Natural language job search orchestration.

    Examples:
    - "Find ML jobs at Anthropic"
    - "Check status"
    - "Show applications ready to send"

    Returns: Status and results
    """
    response = await fetch(
        'https://jobhunt-ai-dev.aijesusbro-brain.workers.dev/api/orchestrate',
        method='POST',
        json={'query': query}
    )
    return response.json()
```

**Usage in Claude Desktop**:
```
You: "Find ML jobs"
Claude: *uses job_hunt tool*
Claude: "Started job search for 5 companies. Found 47 jobs, 12 high-fit, generating applications..."
```

---

## Cost Estimate

CloudFlare free tier includes:
- **Workers**: 100,000 requests/day
- **Durable Objects**: 1M requests/day
- **Queues**: 1M messages/day
- **Workers AI**: 10,000 neurons/day (enough for ~500 job analyses)
- **D1**: 5GB storage, 5M reads/day

**Expected usage**:
- 10 companies/day = ~500 Workers AI calls
- Well within free tier

**Paid tier** ($5/month):
- 10M Workers requests
- 10M Durable Object requests
- 10M queue messages
- 100,000 Workers AI neurons (~5,000 analyses/day)

---

## Support

**Issues**: File in GitHub (when open-sourced)
**Questions**: Check `AGENTIC-ARCHITECTURE.md` for deep dive

---

*Built with CloudFlare Workers, Durable Objects, Queues, Workers AI*
*Part of the AI-First Developer Environment by @aijesusbro*
