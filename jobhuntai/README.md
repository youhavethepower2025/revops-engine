# JobHunt AI

**AI-powered job search automation**

Automatically scrapes jobs from target companies, analyzes fit based on your profile, and helps you apply smarter.

**Live API:** https://jobhunt-ai-dev.aijesusbro-brain.workers.dev

---

## What This Is

JobHunt AI is a personal job search automation system built on Cloudflare Workers that:

- **Scrapes jobs** from target company careers pages
- **Analyzes fit** based on your experience and target roles
- **Generates applications** with personalized cover letters
- **Tracks everything** in a database with full audit trail

**This is not a job board.** It's your personal AI assistant that finds and evaluates jobs at companies YOU choose.

---

## Tech Stack

**Infrastructure:**
- Edge Runtime: Cloudflare Workers
- Database: D1 (SQLite at edge)
- AI: Workers AI (Llama 70B, Qwen 14B) + Claude API
- Browser: Cloudflare Browser API (for JavaScript-heavy pages)

**Core Technologies:**
- Backend: Hono.js (fast edge-native web framework)
- Language: JavaScript/ES6
- Deployment: Single command via Wrangler CLI

---

## Core Features

### Job Scraping Agent
- Scrapes careers pages from target companies (Anthropic, OpenAI, etc.)
- Extracts job titles, descriptions, requirements, URLs
- Uses Browser API to handle JavaScript-rendered pages
- AI extraction for structured data from HTML

### Fit Analysis Agent
- Compares job requirements against your profile
- Scores opportunities (0-100 fit score)
- Explains reasoning for each role
- Highlights which experiences to emphasize

### Application Agent
- Generates personalized cover letters
- Customizes based on fit analysis
- Uses your base template + positioning strategy
- Maintains your voice and style

### Research Agent
- Enriches company information
- Tracks tech stack, culture, funding stage
- Identifies hiring managers and recruiters
- Monitors job posting patterns

---

## Database Schema

**Core Tables:**
- `organizations` - Target companies (95 real companies seeded)
- `roles` - Job openings at organizations
- `people` - Hiring managers, recruiters, team leads
- `applications` - Draft and sent applications
- `interviews` - Interview scheduling and notes
- `user_profile` - Your resume, skills, target roles

**Event Sourcing:**
- `events` - Full audit trail of all actions
- `decision_logs` - AI agent reasoning and decisions

---

## Quick Start

### 1. Deploy to Cloudflare

```bash
# Clone and install
cd "/Users/aijesusbro/AI Projects/jobhuntai"
npm install

# Create D1 database
wrangler d1 create jobhunt-ai-db-dev

# Update wrangler.toml with database ID

# Deploy
npm run deploy:dev

# Initialize database
npm run db:init:dev
```

### 2. Test Job Scraper

```bash
# Test with Anthropic
curl "https://jobhunt-ai-dev.aijesusbro-brain.workers.dev/api/organizations" \
  -X POST \
  -H "Content-Type: application/json" \
  -H "X-Account-Id: account_john_kruze" \
  -d '{"name": "Anthropic", "domain": "anthropic.com", "priority": 5}'

# Get org ID from response, then trigger scraper
curl "https://jobhunt-ai-dev.aijesusbro-brain.workers.dev/api/organizations/$ORG_ID/scrape-jobs" \
  -X POST \
  -H "X-Account-Id: account_john_kruze"

# View scraped jobs
curl "https://jobhunt-ai-dev.aijesusbro-brain.workers.dev/api/roles" \
  -H "X-Account-Id: account_john_kruze"
```

### 3. Check Fit Analysis

```bash
# Analyze fit for a specific role
curl "https://jobhunt-ai-dev.aijesusbro-brain.workers.dev/api/roles/$ROLE_ID/analyze" \
  -X POST \
  -H "X-Account-Id: account_john_kruze"

# View top fits
curl "https://jobhunt-ai-dev.aijesusbro-brain.workers.dev/api/roles?sort=fit_score&limit=10" \
  -H "X-Account-Id: account_john_kruze"
```

---

## Project Structure

```
/jobhuntai/
├── README.md
├── DEPLOYMENT.md
├── wrangler.toml
├── package.json
│
├── workers/
│   ├── api.js (main API server)
│   ├── agents/
│   │   ├── scrape-jobs.js (job scraping)
│   │   ├── research-job.js (job research)
│   │   ├── strategy-job.js (fit analysis)
│   │   └── outreach-job.js (application generation)
│   └── lib/
│       ├── ai.js (AI utilities)
│       ├── auth.js (JWT authentication)
│       ├── scraper.js (web scraping)
│       └── [other utilities]
│
├── schema/
│   ├── schema.sql (main schema)
│   └── migrations/
│       ├── 006_job_hunt.sql (job hunt tables)
│       └── 007_add_org_unique_constraints.sql
│
├── docs/
│   ├── ARCHITECTURE.md
│   ├── FREE_TIER_NOTES.md
│   └── SETUP.md
│
└── test-job-scraper.sh
```

---

## API Endpoints

**Organizations:**
```
GET    /api/organizations           # List target companies
POST   /api/organizations           # Add company
GET    /api/organizations/:id       # Get company details
POST   /api/organizations/:id/scrape-jobs  # Scrape jobs
```

**Roles (Jobs):**
```
GET    /api/roles                   # List all jobs
GET    /api/roles/:id               # Get job details
POST   /api/roles/:id/analyze       # Run fit analysis
PUT    /api/roles/:id               # Update role
```

**Applications:**
```
GET    /api/applications            # List applications
POST   /api/applications            # Create application
GET    /api/applications/:id        # Get application
PUT    /api/applications/:id        # Update application
```

**User Profile:**
```
GET    /api/profile                 # Get your profile
PUT    /api/profile                 # Update profile
```

Full API docs: [docs/API.md](docs/API.md)

---

## Current Status

### ✅ What Works
- Core infrastructure (Cloudflare Workers + D1)
- Event sourcing system (full audit trail)
- Authentication (JWT-based)
- Database schema (organizations, roles, applications, etc.)
- Research Agent (company website scraping)
- Strategy Agent (fit analysis logic)
- Application Agent (cover letter generation)

### ⚠️ Needs Testing
- **Job Scraper** - Code exists but needs validation with real careers pages
  - URL pattern matching
  - Browser API integration
  - AI extraction from HTML
  - Structured data validation

### 📋 Roadmap
1. Test and fix job scraper with 5-10 real companies
2. Add monitoring and error alerts
3. Build dashboard UI for job tracking
4. Add email integration for application sending
5. Implement interview scheduling
6. Add Chrome extension for one-click applications

---

## Development

```bash
# Run locally
npm run dev

# Deploy to dev
npm run deploy:dev

# Query database
npm run db:query:dev

# Watch logs
wrangler tail --env dev
```

---

## Database Management

```bash
# Query remote database
wrangler d1 execute jobhunt-ai-db-dev --env dev --remote \
  --command "SELECT * FROM roles LIMIT 10"

# Run migrations
wrangler d1 execute jobhunt-ai-db-dev --env dev --remote \
  --file=./schema/migrations/006_job_hunt.sql
```

---

## Monitoring

```bash
# Tail logs
wrangler tail --env dev --format pretty

# View in dashboard
open https://dash.cloudflare.com/<account-id>/workers/services/view/jobhunt-ai-dev
```

---

## Testing

```bash
# Test job scraper
./test-job-scraper.sh

# Test API health
curl https://jobhunt-ai-dev.aijesusbro-brain.workers.dev/health
```

---

## Cost

**Free Tier (Current):**
- Workers: 100,000 requests/day
- D1: 5M reads, 100K writes/day
- Workers AI: 10,000 neurons/day
- **Total: $0/month**

**Paid Tier ($5/month if needed):**
- Workers: 10M requests/month
- D1: 25B reads, 50M writes/month
- Queues: 1M operations/month

For personal job hunting, free tier is more than sufficient.

---

## Configuration

**Environment Variables (via wrangler secret):**
- `JWT_SECRET` - For authentication tokens
- `ANTHROPIC_API_KEY` - For Claude API (fit analysis)

**Database Bindings:**
- `DB` - D1 database binding
- `AI` - Workers AI binding
- `BROWSER` - Browser API binding (for scraping JavaScript pages)

---

## Built By

Solo developer learning AI systems architecture through real-world application.

**Tech Journey:**
- Opened terminal: May 2024
- First production deployment: November 2024
- Total experience: 18 months of intensive building

**Philosophy:**
- Build in public
- Ship fast, iterate faster
- Use AI to build AI tools
- Context is everything

---

## License

Personal project. Not open source (yet).

---

**This is not a CRM. This is not a job board. This is your personal AI job search assistant.**
