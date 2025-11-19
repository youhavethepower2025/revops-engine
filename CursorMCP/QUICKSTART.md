# CursorMCP Quick Start Guide

Get up and running with CursorMCP in 5 minutes!

## 🚀 Installation

```bash
# Navigate to project
cd CursorMCP

# Install dependencies
pip install -r requirements.txt

# Or install in editable mode
pip install -e .
```

## ⚙️ Configuration

1. **Create `.env` file** (copy from `.env.example`):
```bash
cp .env.example .env
```

2. **Edit `.env`** with your settings:
```env
# Required for Cloudflare tools (optional for now)
CLOUDFLARE_API_TOKEN=your_token_here
CLOUDFLARE_ACCOUNT_ID=your_account_id_here

# Workspace root (defaults to current directory)
WORKSPACE_ROOT=/Users/aijesusbro/AI Projects

# Optional: Logging level
LOG_LEVEL=INFO
```

## 🧪 Test the Server

### Manual Test

```bash
# Run the server
python -m cursormcp.main
```

The server runs via stdio. You can test it by sending JSON-RPC requests:

```bash
# In another terminal, test with echo
echo '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{}}' | python -m cursormcp.main
```

### Expected Response

```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    "protocolVersion": "2024-11-05",
    "capabilities": {
      "tools": {}
    },
    "serverInfo": {
      "name": "cursormcp",
      "version": "0.1.0"
    }
  }
}
```

## 🔌 Connect to Cursor

### Option 1: Cursor Settings (Recommended)

1. Open Cursor Settings
2. Navigate to MCP / Extensions
3. Add server configuration:

```json
{
  "mcpServers": {
    "cursormcp": {
      "command": "python",
      "args": ["-m", "cursormcp.main"],
      "env": {
        "CLOUDFLARE_API_TOKEN": "your_token",
        "CLOUDFLARE_ACCOUNT_ID": "your_account_id",
        "WORKSPACE_ROOT": "/Users/aijesusbro/AI Projects"
      }
    }
  }
}
```

### Option 2: Configuration File

Create or edit `~/.cursor/mcp.json`:

```json
{
  "mcpServers": {
    "cursormcp": {
      "command": "python",
      "args": ["-m", "cursormcp.main"],
      "cwd": "/Users/aijesusbro/AI Projects/CursorMCP",
      "env": {
        "CLOUDFLARE_API_TOKEN": "your_token",
        "CLOUDFLARE_ACCOUNT_ID": "your_account_id"
      }
    }
  }
}
```

## ✅ Verify Connection

1. Restart Cursor
2. Open a chat with the AI assistant
3. Try asking:
   - "List all available tools"
   - "Get server status"
   - "Read the file README.md"

If tools are available, you're all set! 🎉

## 🛠️ Available Tools

### Meta Tools
- `list_tools` - List all available tools
- `get_tool_info` - Get tool documentation
- `get_server_status` - Server health check

### Development Tools
- `read_file` - Read file contents
- `write_file` - Write file contents
- `list_directory` - List directory
- `search_files` - Search for files

### Cloudflare Tools
- Coming soon! (Foundation is ready)

## 🐛 Troubleshooting

### Server won't start
- Check Python version: `python --version` (needs 3.10+)
- Verify dependencies: `pip list | grep pydantic`
- Check `.env` file exists and has valid paths

### Tools not appearing in Cursor
- Verify MCP configuration is correct
- Check Cursor logs for errors
- Ensure server starts without errors
- Try restarting Cursor

### File operations fail
- Check `WORKSPACE_ROOT` is set correctly
- Verify paths are within workspace
- Check file permissions

## 📚 Next Steps

1. Read [ARCHITECTURE.md](./ARCHITECTURE.md) for design details
2. Check [README.md](./README.md) for full documentation
3. Start building Cloudflare tools!

---

**Need help?** Check the logs or open an issue!

