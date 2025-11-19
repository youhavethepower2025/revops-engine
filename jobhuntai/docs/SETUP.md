# Setup Guide

## Prerequisites

- Node.js 18+
- Cloudflare account
- Wrangler CLI installed globally: `npm install -g wrangler`

## Initial Setup

### 1. Install Dependencies

```bash
cd jobhuntai
npm install
```

### 2. Authenticate Wrangler

```bash
wrangler login
```

### 3. Create D1 Databases

```bash
# Development
wrangler d1 create jobhuntai-db-dev

# Staging
wrangler d1 create jobhuntai-db-staging

# Production
wrangler d1 create jobhuntai-db-production
```

Copy the database IDs from the output and update `wrangler.toml`:

```toml
[[d1_databases]]
binding = "DB"
database_name = "jobhuntai-db"
database_id = "YOUR_DEV_DB_ID_HERE"
```

### 4. Initialize Database Schema

```bash
# Development
npm run db:init:dev

# Staging (later)
wrangler d1 execute jobhuntai-db-staging --env staging --file=./schema/schema.sql

# Production (later)
wrangler d1 execute jobhuntai-db-production --env production --file=./schema/schema.sql
```

### 5. Create Vectorize Index

```bash
wrangler vectorize create jobhuntai-vectors --dimensions=1536 --metric=cosine
```

### 6. Create Queue

```bash
wrangler queues create agent-queue
```

## Development

### Run Locally

```bash
npm run dev
```

Visit http://localhost:8787/health to verify it's running.

### Deploy to Dev

```bash
npm run deploy:dev
```

### Query Database

```bash
# Interactive
npm run db:query:dev "SELECT * FROM accounts LIMIT 10"

# Or use wrangler directly
wrangler d1 execute jobhuntai-db-dev --env dev --command "SELECT * FROM accounts"
```

## Testing API

```bash
# Health check
curl http://localhost:8787/health

# Create account (will return 501 until implemented)
curl -X POST http://localhost:8787/api/accounts \
  -H "Content-Type: application/json" \
  -d '{"name": "Test Account"}'
```

## Next Steps

See `docs/PHASE_0.md` for implementation checklist.
