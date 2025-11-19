# Deployment Guide

## Live URLs

**Dev Environment:**
- API: https://jobhuntai-dev.aijesusbro-brain.workers.dev
- Event Viewer: https://jobhuntai-dev.aijesusbro-brain.workers.dev/

## Quick Deploy

```bash
cd "/Users/aijesusbro/AI Projects/jobhuntai"

# Deploy changes
npm run deploy:dev

# Watch logs
wrangler tail --env dev
```

## Database Management

```bash
# Query remote database
wrangler d1 execute jobhuntai-db-dev --env dev --remote --command "SELECT * FROM accounts LIMIT 10"

# Run schema updates
wrangler d1 execute jobhuntai-db-dev --env dev --remote --file=./path/to/migration.sql
```

## Testing

```bash
# Test deployed API
./test-deployed.sh
```

## Secrets Management

```bash
# Set JWT secret (already done)
wrangler secret put JWT_SECRET --env dev

# Set Anthropic API key (for Phase 1 agents)
wrangler secret put ANTHROPIC_API_KEY --env dev

# Set integration keys (as needed)
wrangler secret put SENDGRID_API_KEY --env dev
wrangler secret put TWILIO_API_KEY --env dev
wrangler secret put RETELL_API_KEY --env dev
```

## Monitoring

```bash
# Tail logs in real-time
wrangler tail --env dev

# Filter for errors
wrangler tail --env dev --format pretty | grep -i error

# View analytics in dashboard
open https://dash.cloudflare.com/bbd9ec5819a97651cc9f481c1c275c3d/workers/services/view/jobhuntai-dev
```

## Architecture Notes

**Current Setup (Free Tier):**
- Workers: Unlimited requests on Cloudflare network
- D1: SQLite at edge with read replicas
- Vectorize: Semantic search for patterns/conversations
- Durable Objects: Per-tenant coordination (using new_sqlite_classes)
- No Queues: Using Durable Objects for agent triggering

**Your $25 Plan:**
- Covers Cloudflare domains/CDN
- Workers are still on free tier
- To unlock Queues: Upgrade to Workers Paid ($5/mo)

## What's Deployed

✅ Complete database schema (event sourcing, observability, governance)
✅ Auth system (JWT, account creation, login)
✅ Event emission and tracking
✅ Multi-tenant architecture
✅ Event viewer UI

## Next: Phase 1

Add the agents:
- Research Agent (lead enrichment)
- Outreach Agent (message generation + sending)
- Response Agent (reply handling)

Requires:
- `ANTHROPIC_API_KEY` secret
- Integration keys (Sendgrid, etc.)
- Agent worker implementations
