# Cursor Setup Guide

**Connect CursorMCP to Cursor IDE**

---

## 🐳 Option 1: Docker (Recommended)

### Step 1: Build Docker Image

```bash
cd "/Users/aijesusbro/AI Projects/CursorMCP"
docker-compose build
```

### Step 2: Create Cursor MCP Config

Create or edit `~/.cursor/mcp.json` (or wherever Cursor stores MCP config):

```json
{
  "mcpServers": {
    "cursormcp": {
      "command": "docker",
      "args": [
        "run",
        "-i",
        "--rm",
        "-e", "CLOUDFLARE_API_TOKEN=gWbANxar1WFWh-GTi2IhtcdUBmmw2Cb47KIz9Q1n",
        "-e", "CLOUDFLARE_ACCOUNT_ID=bbd9ec5819a97651cc9f481c1c275c3d",
        "-e", "WORKSPACE_ROOT=/Users/aijesusbro/AI Projects",
        "-v", "/Users/aijesusbro/AI Projects:/workspace:ro",
        "cursormcp_cursormcp:latest"
      ]
    }
  }
}
```

**Or use docker-compose:**

```json
{
  "mcpServers": {
    "cursormcp": {
      "command": "docker-compose",
      "args": [
        "-f", "/Users/aijesusbro/AI Projects/CursorMCP/docker-compose.yml",
        "run",
        "--rm",
        "cursormcp"
      ],
      "env": {
        "CLOUDFLARE_API_TOKEN": "gWbANxar1WFWh-GTi2IhtcdUBmmw2Cb47KIz9Q1n",
        "CLOUDFLARE_ACCOUNT_ID": "bbd9ec5819a97651cc9f481c1c275c3d",
        "WORKSPACE_ROOT": "/Users/aijesusbro/AI Projects"
      }
    }
  }
}
```

---

## 🐍 Option 2: Direct Python (No Docker)

### Step 1: Install Dependencies

```bash
cd "/Users/aijesusbro/AI Projects/CursorMCP"
pip3 install -r requirements.txt
```

### Step 2: Create Cursor MCP Config

```json
{
  "mcpServers": {
    "cursormcp": {
      "command": "python3",
      "args": ["-m", "cursormcp.main"],
      "cwd": "/Users/aijesusbro/AI Projects/CursorMCP",
      "env": {
        "CLOUDFLARE_API_TOKEN": "gWbANxar1WFWh-GTi2IhtcdUBmmw2Cb47KIz9Q1n",
        "CLOUDFLARE_ACCOUNT_ID": "bbd9ec5819a97651cc9f481c1c275c3d",
        "WORKSPACE_ROOT": "/Users/aijesusbro/AI Projects",
        "PYTHONPATH": "/Users/aijesusbro/AI Projects/CursorMCP/src"
      }
    }
  }
}
```

---

## ✅ Verify Connection

1. **Restart Cursor** (required after config changes)

2. **Open a chat** with the AI assistant

3. **Test with:**
   - "List all available tools"
   - "Get server status"
   - "List my Cloudflare workers"

4. **You should see:**
   - 30 tools available
   - Server status showing healthy
   - Your Cloudflare workers listed

---

## 🔧 Troubleshooting

### Tools not appearing
- Check Cursor logs for errors
- Verify environment variables are set
- Ensure Python/Docker is accessible

### Docker issues
- Make sure Docker is running
- Check `docker-compose build` completed successfully
- Verify image exists: `docker images | grep cursormcp`

### API errors
- Verify Cloudflare API token is valid
- Check account ID is correct
- Test API directly: `curl -H "Authorization: Bearer $TOKEN" https://api.cloudflare.com/client/v4/accounts/$ACCOUNT_ID/workers/scripts`

---

## 🎯 Next Steps

Once connected:
1. Try listing your workers: "List my Cloudflare workers"
2. Query a D1 database: "List my D1 databases"
3. Check KV namespaces: "List my KV namespaces"
4. Start building app MCP servers!

---

**Ready to orchestrate Cloudflare!** 🚀

