# MedTainer Cloudflare Tunnel Setup

## ✅ Completed Steps

### 1. SSH Key Setup
- Generated SSH key for passwordless access
- Copied to MedTainer server (24.199.118.227)
- Status: **WORKING** ✅

### 2. Cloudflared Installation
- Installed cloudflared version 2025.11.1
- Location: `/usr/bin/cloudflared`
- Status: **INSTALLED** ✅

### 3. Tunnel Creation
- **Tunnel Name**: medtainer
- **Tunnel ID**: `edbfc982-d5e1-47ee-bf8f-7ffa65cec842`
- **Status**: HEALTHY ✅
- **Connections**: Active to Cloudflare edge (sjc05)

### 4. Systemd Service
- Installed as system service
- Auto-starts on reboot
- Config: `/etc/cloudflared/config.yml`
- Credentials: `/etc/cloudflared/edbfc982-d5e1-47ee-bf8f-7ffa65cec842.json`
- Status: **RUNNING** ✅

### 5. Tunnel Configuration
```yaml
tunnel: edbfc982-d5e1-47ee-bf8f-7ffa65cec842
credentials-file: /root/.cloudflared/edbfc982-d5e1-47ee-bf8f-7ffa65cec842.json

ingress:
  - hostname: medtainer.aijesusbro.com
    service: http://localhost:8000
  - service: http_status:404
```

---

## 🔴 Final Step: Add DNS CNAME Record

The tunnel is **LIVE and HEALTHY**, but needs a DNS record to route traffic.

### Option 1: Cloudflare Dashboard (Easiest)
1. Go to [Cloudflare Dashboard](https://dash.cloudflare.com/)
2. Select domain: `aijesusbro.com`
3. Go to **DNS** → **Records**
4. Click **Add record**
5. Configure:
   - **Type**: CNAME
   - **Name**: medtainer
   - **Target**: `edbfc982-d5e1-47ee-bf8f-7ffa65cec842.cfargotunnel.com`
   - **Proxy status**: ✅ Proxied (orange cloud)
   - **TTL**: Auto
6. Click **Save**

### Option 2: Cloudflare API
```bash
curl -X POST "https://api.cloudflare.com/client/v4/zones/c42aeeb4c6da8a14d33808f4f321f321/dns_records" \
  -H "X-Auth-Email: YOUR_CLOUDFLARE_EMAIL" \
  -H "X-Auth-Key: YOUR_GLOBAL_API_KEY" \
  -H "Content-Type: application/json" \
  --data '{
    "type":"CNAME",
    "name":"medtainer",
    "content":"edbfc982-d5e1-47ee-bf8f-7ffa65cec842.cfargotunnel.com",
    "ttl":1,
    "proxied":true
  }'
```

---

## 🧪 Testing After DNS Setup

Once DNS is configured (wait 1-5 minutes for propagation):

```bash
# Test health endpoint
curl https://medtainer.aijesusbro.com/health

# Expected response:
# {"app":"MedTainer MCP Server","environment":"production","status":"ok"}

# List available tools
curl https://medtainer.aijesusbro.com/mcp/tools

# Expected: 26 tools (GHL: 13, GoDaddy: 8, DigitalOcean: 5)
```

---

## 🔧 Management Commands

### Check Tunnel Status
```bash
ssh root@24.199.118.227 "systemctl status cloudflared"
```

### View Logs
```bash
ssh root@24.199.118.227 "journalctl -u cloudflared -f"
```

### Restart Tunnel
```bash
ssh root@24.199.118.227 "systemctl restart cloudflared"
```

### Check Tunnel Health via API
```bash
curl -s https://api.cloudflare.com/client/v4/accounts/bbd9ec5819a97651cc9f481c1c275c3d/cfd_tunnel/edbfc982-d5e1-47ee-bf8f-7ffa65cec842 \
  -H "Authorization: Bearer gWbANxar1WFWh-GTi2IhtcdUBmmw2Cb47KIz9Q1n" | jq '.result.status'
```

---

## 🎯 Next Steps: Add to Claude Desktop

Once DNS is working, add to Claude Desktop config:

### If MedTainer has SSE endpoint:
```json
{
  "mcpServers": {
    "medtainer": {
      "command": "node",
      "args": ["/Users/aijesusbro/AI Projects/mcp-http-bridge.js", "https://medtainer.aijesusbro.com/sse"]
    }
  }
}
```

### If using REST API only:
You'll need to create a bridge or use a different MCP client that supports HTTP/REST.

---

## 📊 Current Status

| Component | Status | Details |
|-----------|--------|---------|
| Server | ✅ Running | 24.199.118.227 |
| Docker Containers | ✅ Healthy | medtainer-mcp, medtainer-postgres |
| Cloudflared | ✅ Installed | v2025.11.1 |
| Tunnel | ✅ Healthy | edbfc982-d5e1-47ee-bf8f-7ffa65cec842 |
| Systemd Service | ✅ Running | Auto-start enabled |
| DNS Record | ⏳ Pending | Need to add CNAME |
| HTTPS URL | ⏳ Pending DNS | https://medtainer.aijesusbro.com |

---

## 🔒 Security Notes

- Port 8000 is currently **OPEN** on the DO droplet
- **Recommended**: Close port 8000 after DNS is working
- Only allow tunnel traffic:

```bash
ssh root@24.199.118.227 "ufw allow 22/tcp && ufw allow 80/tcp && ufw allow 443/tcp && ufw deny 8000/tcp && ufw --force enable"
```

This ensures MedTainer is **ONLY** accessible via the Cloudflare tunnel (encrypted, DDoS protected, hidden origin).

---

**Deployment Date**: 2025-11-14
**Tunnel ID**: edbfc982-d5e1-47ee-bf8f-7ffa65cec842
**Domain**: medtainer.aijesusbro.com
**Owner**: medtaynor (John)
