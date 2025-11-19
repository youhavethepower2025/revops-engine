# JobHunt AI - CloudFlare Workers

## Status: ACTIVE & DEPLOYED

## Purpose
Personal job search automation system that scrapes jobs from target companies, analyzes fit, and generates applications.

## Infrastructure

### Deployment
- **Platform**: CloudFlare Workers (Edge Runtime)
- **URL (Dev)**: https://jobhuntai-dev.aijesusbro-brain.workers.dev
- **Alternative URL**: https://jobhunt-ai-dev.aijesusbro-brain.workers.dev
- **Database**: D1 (SQLite at edge) - `revops-os-db-dev` (database_id: 1732e74a-4f4f-48ae-95a8-fb0fb73416df)

### Stack
- **Framework**: Hono.js (edge-native web framework)
- **AI**: Workers AI (Llama 70B, Qwen 14B) + Claude API
- **Browser**: CloudFlare Browser API (for JS-heavy pages)
- **Language**: JavaScript/ES6

## Key Components

### 1. API Worker (`workers/api.js`)
- Main CloudFlare worker serving both API and frontend
- Routes:
  - `/` - Index/landing page
  - `/dashboard` - Main dashboard UI
  - `/dashboard-v2` - V2 dashboard UI
  - `/crm` - CRM subdomain routes
  - `/test/ai` - Test Workers AI
  - `/test/scrape` - Test browser scraping
  - `/test/research` - Test research agent

### 2. Agents
- **Job Scraping Agent**: Scrapes careers pages from target companies
- **Fit Analysis Agent**: Scores opportunities (0-100) against your profile
- **Application Agent**: Generates personalized cover letters
- **Research Agent**: Enriches company info and tracks hiring patterns

### 3. Frontend (Built-in)
- HTML served directly from the worker (no separate deployment)
- Dashboard V1: Basic job tracking
- Dashboard V2: Enhanced UI with more features
- Event viewer for debugging

## Database Schema

### D1 Tables
- `organizations` - Target companies (95 companies seeded)
- `roles` - Job openings at organizations
- `people` - Hiring managers, recruiters
- `applications` - Draft and sent applications
- `interviews` - Interview scheduling and notes
- `user_profile` - Your resume, skills, target roles
- `events` - Full audit trail of all actions
- `decision_logs` - AI agent reasoning and decisions
- `accounts` - Multi-tenant support

**NOTE**: Uses the SAME D1 database as RevOps OS (`revops-os-db-dev`)

## Connection to DevMCP

### Data Flow Pattern
```
JobHunt AI (CloudFlare)
    → Scrapes jobs & creates applications
    → Stores in D1 database (edge)
    → ALSO sends data to DevMCP?
    → DevMCP stores in PostgreSQL (local)
    → DevMCP Dashboard displays combined data
```

**IMPORTANT**: Need to verify webhook connection between JobHunt AI and DevMCP. DevMCP has `job_hunt_tools.py` and `job_hunt_schema.sql` which suggests it receives data from JobHunt AI, but the webhook endpoint needs to be confirmed.

## External Connections

### APIs (from .env)
- **CloudFlare**: Account ID: bbd9ec5819a97651cc9f481c1c275c3d
- **GHL**: GoHighLevel API (same location as DevMCP)
- **Retell**: API key (legacy voice integration)
- **Anthropic**: Claude API for advanced agent reasoning

### Workers AI Models
- `@cf/meta/llama-3.1-70b-instruct` - General reasoning
- `@cf/qwen/qwen1.5-14b-chat-awq` - Entity extraction

## Deployment Commands

```bash
cd "/Users/aijesusbro/AI Projects/jobhuntai"

# Deploy to dev
npm run deploy:dev

# Watch logs
wrangler tail --env dev

# Query D1 database
wrangler d1 execute jobhuntai-db-dev --env dev --remote --command "SELECT * FROM accounts LIMIT 10"
```

## Access URLs

- **Main App**: https://jobhuntai-dev.aijesusbro-brain.workers.dev/
- **Dashboard**: https://jobhuntai-dev.aijesusbro-brain.workers.dev/dashboard
- **Dashboard V2**: https://jobhuntai-dev.aijesusbro-brain.workers.dev/dashboard-v2
- **CRM**: https://jobhuntai-dev.aijesusbro-brain.workers.dev/crm
- **Health Check**: https://jobhuntai-dev.aijesusbro-brain.workers.dev/health

## Dashboard Location

JobHunt AI has TWO dashboards:
1. **Built-in Dashboard**: Served from the worker itself (workers/lib/app-html.js, dashboard-v2-html.js)
2. **DevMCP Dashboard**: Separate Next.js app that queries DevMCP PostgreSQL

This means the JobHunt AI dashboard at the CloudFlare URL queries D1 directly, while DevMCP dashboard queries DevMCP PostgreSQL.

## Integration Points

### With DevMCP
- DevMCP has `job_hunt_tools.py` with functions to:
  - Create jobs, applications, contacts, companies
  - Track activities and interactions
  - Query job hunt data from PostgreSQL
- Unclear if JobHunt AI actively syncs to DevMCP or if this is manual

### With RevOps OS
- **Shares the same D1 database**: `revops-os-db-dev`
- This creates a unified data store at the edge
- Both systems can query each other's tables

## Secrets (Wrangler)
- `JWT_SECRET` - For auth tokens
- `ANTHROPIC_API_KEY` - For Claude API
- `SENDGRID_API_KEY` - For email sending
- `TWILIO_API_KEY` - For SMS
- `RETELL_API_KEY` - For voice (legacy)

## Questions to Resolve
1. Does JobHunt AI actively POST to DevMCP webhooks?
2. Or does DevMCP pull from the shared D1 database?
3. Which dashboard are you primarily using?
4. Is the separate DevMCP dashboard deployed to CloudFlare Pages?

## Last Updated
November 13, 2025
