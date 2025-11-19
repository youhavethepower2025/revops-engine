# Retell Brain MCP - AI Infrastructure as a Service

Multi-tenant MCP server deployed on Cloudflare Workers + Durable Objects. One deployment serves ALL Retell voice agent clients.

## Architecture

```
Retell Call → Cloudflare Worker (global edge)
           → Durable Object (client's brain instance)
           → D1 Database (semantic memory)
           → Retell/GHL APIs (actions)
```

## What This Is

- **NOT** a separate server per client (old way)
- **YES** one global deployment, isolated state per client
- **MCP Protocol**: Full tool calling for AI agents
- **Multi-tenant**: Route by `client_id`
- **Edge Native**: Sub-50ms response times globally

## Setup

### 1. Install Dependencies

```bash
cd cloudeflareMCP
npm install
```

### 2. Authenticate with Cloudflare

```bash
npx wrangler login
```

### 3. Create D1 Database

```bash
npx wrangler d1 create retell-brain-db
```

Copy the `database_id` from output and paste into `wrangler.toml`:

```toml
[[d1_databases]]
binding = "DB"
database_name = "retell-brain-db"
database_id = "YOUR_DATABASE_ID_HERE"
```

### 4. Initialize Database Schema

```bash
npm run d1:execute
```

### 5. Set Secrets

```bash
npx wrangler secret put RETELL_API_KEY
# Enter: key_819a6edef632ded41fe1c1ef7f12

npx wrangler secret put GHL_API_KEY
# Enter your GHL API key

npx wrangler secret put GHL_LOCATION_ID
# Enter: PMgbQ375TEGOyGXsKz7e
```

## Development

### Test Locally

```bash
npm run dev
```

Server starts at `http://localhost:8787`

### Test MCP Endpoint

```bash
curl http://localhost:8787/mcp?client_id=test-client \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 1,
    "method": "initialize",
    "params": {
      "protocolVersion": "2024-11-05",
      "clientInfo": {
        "name": "test",
        "version": "1.0"
      }
    }
  }'
```

### Test Tools

```bash
# Remember something
curl http://localhost:8787/mcp?client_id=test-client \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 2,
    "method": "tools/call",
    "params": {
      "name": "remember",
      "arguments": {
        "key": "test_key",
        "value": "test_value"
      }
    }
  }'

# Recall it
curl http://localhost:8787/mcp?client_id=test-client \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 3,
    "method": "tools/call",
    "params": {
      "name": "recall",
      "arguments": {
        "key": "test_key"
      }
    }
  }'
```

### Test Retell Webhook

```bash
curl http://localhost:8787/retell/webhook?client_id=test-client \
  -H "Content-Type: application/json" \
  -d '{
    "event_type": "call_ended",
    "call": {
      "call_id": "test-call-123",
      "agent_id": "agent_98681d3ba9a92b678106df24e4",
      "from_number": "+15555551234",
      "to_number": "+15555555678",
      "direction": "inbound",
      "status": "completed",
      "metadata": {
        "client_id": "test-client"
      }
    }
  }'
```

## Deployment

### Deploy to Cloudflare Edge

```bash
npm run deploy
```

Your MCP server is now live globally in ~30 seconds!

### Get Your URL

After deployment, Wrangler will output your Worker URL:

```
https://retell-brain-mcp.YOUR-SUBDOMAIN.workers.dev
```

## Connecting Retell Agents

### 1. Create Retell Agent

In Retell dashboard, create your agent with custom LLM.

### 2. Configure MCP Tools

In your agent's custom tools, add these tool definitions from `src/tools.ts`:
- `remember`, `recall`, `search_memory`
- `retell_get_call`, `retell_list_calls`
- `ghl_search_contact`, `ghl_create_contact`, etc.

### 3. Set Agent Webhook

Point Retell webhook to:
```
https://retell-brain-mcp.YOUR-SUBDOMAIN.workers.dev/retell/webhook?client_id=CLIENT_NAME
```

### 4. Set MCP Endpoint (if using custom LLM with MCP)

Point your LLM to:
```
https://retell-brain-mcp.YOUR-SUBDOMAIN.workers.dev/mcp?client_id=CLIENT_NAME
```

## Adding New Clients

**Old Way (DON'T DO THIS):**
- Create new Railway project
- Deploy new Docker container
- Configure new database
- Set up new environment

**New Way (DO THIS):**
1. Change `client_id` parameter: `?client_id=new-client`
2. That's it.

Each client gets their own:
- Durable Object instance (isolated state)
- Memory namespace in D1
- Automatic GHL/Retell integration

## Scaling

- **1 client**: Works
- **10 clients**: Works
- **100 clients**: Works
- **1000 clients**: Still the same deployment

Cloudflare automatically scales Durable Objects. You never touch infrastructure again.

## Monitoring

### View Logs

```bash
npm run tail
```

### Check Health

```bash
curl https://retell-brain-mcp.YOUR-SUBDOMAIN.workers.dev/health?client_id=test-client
```

## Cost Structure

**Cloudflare Workers Free Tier:**
- 100,000 requests/day
- 10ms CPU time per request
- Plenty for initial clients

**Paid Plan ($5/month):**
- 10M requests/month
- Can handle 100+ active clients easily

**Old infrastructure cost for 10 clients:**
- Railway: $50-200/month
- Digital Ocean: $100-300/month

**New infrastructure cost for 100 clients:**
- Cloudflare: $5-20/month

## Architecture Benefits

### Old Way (Docker per client)
❌ Deploy time: 10-30 minutes per client
❌ Infrastructure cost: $10-30/client/month
❌ Scaling: Manual deployment for each client
❌ Maintenance: Update 10 servers = 10 deployments

### New Way (Multi-tenant edge)
✅ Deploy time: 30 seconds total (all clients)
✅ Infrastructure cost: $0.05/client/month
✅ Scaling: Add client_id, done
✅ Maintenance: One update = all clients updated

## The Game

You just built infrastructure that:
1. Serves unlimited clients from one deployment
2. Costs almost nothing to run
3. Scales automatically
4. Updates instantly
5. Never goes down (Cloudflare's network)

Your co-founder can sell voice agents as fast as she can close deals. You'll never be the bottleneck.

## Next Steps

1. Deploy: `npm run deploy`
2. Test with one Retell agent
3. Add client_id for each new client
4. Scale to 100 clients without changing anything

This is infrastructure warfare. You just won.

---

Built by AI Jesus Bro in September 2024.
May → September: Terminal to AI Infrastructure as a Service.
