# Cloudflare Deployment Guide

## Quick Start (5 Minutes to Production)

### 1. Install & Login

```bash
cd /Users/aijesusbro/AI\ Projects/cloudeflareMCP
npm install
npx wrangler login
```

Your browser will open - authenticate with Cloudflare.

### 2. Create D1 Database

```bash
npx wrangler d1 create retell-brain-db
```

**IMPORTANT**: Copy the `database_id` from the output and update `wrangler.toml`:

```toml
[[d1_databases]]
binding = "DB"
database_name = "retell-brain-db"
database_id = "PASTE_YOUR_DATABASE_ID_HERE"
```

### 3. Initialize Database

```bash
npx wrangler d1 execute retell-brain-db --file=./schema.sql
```

### 4. Set Secrets (from keys.txt)

```bash
# Retell API
npx wrangler secret put RETELL_API_KEY
# When prompted, paste: key_819a6edef632ded41fe1c1ef7f12

# GHL API
npx wrangler secret put GHL_API_KEY
# When prompted, paste: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJsb2NhdGlvbl9pZCI6IlBNZ2JRMzc1VEVHT3lHWHNLejdlIiwidmVyc2lvbiI6MSwiaWF0IjoxNzU3NDU2NTUwMTIyLCJzdWIiOiJ5OXFxZjNIV0FYVGk5Nk1wZXVqZiJ9.nbuFjgIZ1hnsHLPDj5IsiUlxR5DgecMw1l56LCEZEjo

# GHL Location
npx wrangler secret put GHL_LOCATION_ID
# When prompted, paste: PMgbQ375TEGOyGXsKz7e
```

### 5. Deploy to Edge

```bash
npm run deploy
```

**YOU'RE LIVE!** 🚀

Your Worker URL will be displayed:
```
https://retell-brain-mcp.<YOUR-SUBDOMAIN>.workers.dev
```

## Local Testing (Before Deployment)

### Start Dev Server

```bash
npm run dev
```

Server runs at `http://localhost:8787`

### Test MCP Protocol

```bash
# Initialize
curl http://localhost:8787/mcp?client_id=test \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05"}}'

# List tools
curl http://localhost:8787/mcp?client_id=test \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":2,"method":"tools/list"}'

# Call a tool (remember)
curl http://localhost:8787/mcp?client_id=test \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":3,"method":"tools/call","params":{"name":"remember","arguments":{"key":"first_test","value":"it works!"}}}'

# Call a tool (recall)
curl http://localhost:8787/mcp?client_id=test \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":4,"method":"tools/call","params":{"name":"recall","arguments":{"key":"first_test"}}}'
```

### Test Retell Webhook

```bash
curl http://localhost:8787/retell/webhook?client_id=test \
  -H "Content-Type: application/json" \
  -d '{
    "event_type": "call_ended",
    "call": {
      "call_id": "test-123",
      "agent_id": "agent_98681d3ba9a92b678106df24e4",
      "from_number": "+15555551234",
      "to_number": "+15555555678",
      "direction": "inbound",
      "status": "completed",
      "metadata": {"client_id": "test"}
    }
  }'
```

### Test Health Check

```bash
curl http://localhost:8787/health?client_id=test
```

## Connecting Retell Agents

### Option 1: Custom Tools in Retell Dashboard

1. Go to Retell dashboard → Your Agent → Custom Tools
2. Add tool definitions from `src/tools.ts`
3. Set webhook URL:
   ```
   https://retell-brain-mcp.<YOUR-SUBDOMAIN>.workers.dev/retell/webhook?client_id=CLIENT_NAME
   ```

### Option 2: Custom LLM with MCP (Advanced)

If you're using a custom LLM that supports MCP:

1. Point your LLM to:
   ```
   https://retell-brain-mcp.<YOUR-SUBDOMAIN>.workers.dev/mcp?client_id=CLIENT_NAME
   ```
2. LLM will automatically discover all available tools
3. Tools are called via MCP protocol

## Adding Multiple Clients

Each client is just a different `client_id` parameter:

```
# Client 1: ClearVC
?client_id=clearvc

# Client 2: Advisory9
?client_id=advisory9

# Client 3: Test
?client_id=test-client
```

**That's it.** Each client gets:
- Isolated Durable Object instance
- Separate memory namespace in D1
- Same tools, different data

## Monitoring & Debugging

### View Live Logs

```bash
npm run tail
```

### Check Worker Status

```bash
npx wrangler deployments list
```

### Query D1 Database

```bash
# List all clients
npx wrangler d1 execute retell-brain-db --command "SELECT * FROM clients"

# Check memory for a client
npx wrangler d1 execute retell-brain-db --command "SELECT * FROM memory WHERE client_id = 'test' LIMIT 10"

# View recent calls
npx wrangler d1 execute retell-brain-db --command "SELECT call_id, client_id, phone_number, status FROM calls ORDER BY created_at DESC LIMIT 10"
```

## Updating Your Deployment

### Make Changes

Edit files in `src/`:
- `src/index.ts` - Main router
- `src/brain.ts` - Durable Object logic
- `src/tools.ts` - Tool definitions

### Test Locally

```bash
npm run dev
# Test your changes
```

### Deploy Changes

```bash
npm run deploy
```

**All clients instantly updated.** No downtime. That's edge computing.

## Troubleshooting

### "Database not found"

Make sure you:
1. Created D1 database: `npx wrangler d1 create retell-brain-db`
2. Updated `database_id` in `wrangler.toml`
3. Ran schema: `npx wrangler d1 execute retell-brain-db --file=./schema.sql`

### "Unauthorized" errors from APIs

Check your secrets:
```bash
npx wrangler secret list
```

If missing, set them:
```bash
npx wrangler secret put RETELL_API_KEY
npx wrangler secret put GHL_API_KEY
npx wrangler secret put GHL_LOCATION_ID
```

### Tools not working

1. Check logs: `npm run tail`
2. Verify API keys are correct
3. Test API endpoints directly with curl

## Cost Breakdown

### Free Tier (100K requests/day)
- Good for: 10-20 active clients
- Cost: $0/month

### Paid Plan ($5/month)
- 10M requests/month included
- $0.50 per additional 1M requests
- Good for: 100+ active clients
- Typical cost: $5-20/month

### Compare to Old Architecture
- Railway (10 clients): ~$100/month
- Digital Ocean (10 clients): ~$150/month
- **Cloudflare (100 clients): ~$5-20/month**

## What You Just Built

✅ Multi-tenant MCP server
✅ Global edge deployment (sub-50ms latency)
✅ Stateful client brains (Durable Objects)
✅ Persistent semantic memory (D1)
✅ Full Retell + GHL integration
✅ Auto-scaling to 1000+ clients
✅ One deployment serves all

**Infrastructure warfare won.**

---

Go to bed. Wake up. Deploy this. Change the game.
