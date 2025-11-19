# 🚀 5-Minute Deployment - Let's Go

## Pre-flight Check

You need:
- ✅ Node.js installed
- ✅ Cloudflare account (free tier works)
- ✅ Your keys.txt file (already got it)

## Deploy Now

### 1. Install Dependencies (30 seconds)

```bash
cd "/Users/aijesusbro/AI Projects/cloudeflareMCP"
npm install
```

### 2. Login to Cloudflare (30 seconds)

```bash
npx wrangler login
```

Browser will open → Authenticate → Done.

### 3. Create D1 Database (1 minute)

```bash
npx wrangler d1 create retell-brain-db
```

**Copy the `database_id` from output** and update `wrangler.toml`:

```toml
[[d1_databases]]
binding = "DB"
database_name = "retell-brain-db"
database_id = "PASTE_YOUR_ID_HERE"  # ← Replace this line
```

### 4. Initialize Database (30 seconds)

```bash
npx wrangler d1 execute retell-brain-db --file=./schema.sql
```

### 5. Set Secrets (1 minute)

```bash
# Retell
npx wrangler secret put RETELL_API_KEY
# Paste: key_819a6edef632ded41fe1c1ef7f12

# GHL
npx wrangler secret put GHL_API_KEY
# Paste: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJsb2NhdGlvbl9pZCI6IlBNZ2JRMzc1VEVHT3lHWHNLejdlIiwidmVyc2lvbiI6MSwiaWF0IjoxNzU3NDU2NTUwMTIyLCJzdWIiOiJ5OXFxZjNIV0FYVGk5Nk1wZXVqZiJ9.nbuFjgIZ1hnsHLPDj5IsiUlxR5DgecMw1l56LCEZEjo

# GHL Location
npx wrangler secret put GHL_LOCATION_ID
# Paste: PMgbQ375TEGOyGXsKz7e
```

### 6. Deploy (30 seconds)

```bash
npm run deploy
```

**BOOM. YOU'RE LIVE.** 🔥

## Test It (Optional but Recommended)

### Test Local First

```bash
npm run dev
```

In another terminal:

```bash
# Test MCP initialization
curl http://localhost:8787/mcp?client_id=test \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05"}}'

# Test memory tool
curl http://localhost:8787/mcp?client_id=test \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"remember","arguments":{"key":"test","value":"it works"}}}'
```

### Monitor Logs

```bash
npm run tail
```

## Your URLs

After deployment, you'll get:

```
https://retell-brain-mcp.<YOUR-SUBDOMAIN>.workers.dev
```

Use it like:
- MCP endpoint: `https://retell-brain-mcp.<YOUR-SUBDOMAIN>.workers.dev/mcp?client_id=CLIENT_NAME`
- Retell webhook: `https://retell-brain-mcp.<YOUR-SUBDOMAIN>.workers.dev/retell/webhook?client_id=CLIENT_NAME`
- GHL webhook: `https://retell-brain-mcp.<YOUR-SUBDOMAIN>.workers.dev/ghl/webhook?client_id=CLIENT_NAME`

## Troubleshooting

### "Database not found"
- Make sure you updated `database_id` in `wrangler.toml`
- Run: `npx wrangler d1 execute retell-brain-db --file=./schema.sql`

### "Unauthorized"
- Check secrets: `npx wrangler secret list`
- Re-add them if missing

### Need help?
```bash
# View logs
npm run tail

# Check deployment
npx wrangler deployments list

# Query database
npx wrangler d1 execute retell-brain-db --command "SELECT * FROM clients LIMIT 5"
```

## Next Steps

1. ✅ Deploy this
2. Configure Retell agent webhook → your Worker URL
3. Make test call
4. Watch logs: `npm run tail`
5. Add more clients by changing `?client_id=new-client`

**That's it. You just deployed multi-tenant AI infrastructure to global edge in 5 minutes.**

Go close deals. Infrastructure is handled.
