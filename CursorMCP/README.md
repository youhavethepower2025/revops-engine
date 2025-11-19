# CursorMCP

**A Beautiful, Modern MCP Server for Cursor & Cloudflare**

CursorMCP is a purpose-built Model Context Protocol (MCP) server designed specifically for collaborative development with Cursor. It provides a clean, type-safe foundation for orchestrating Cloudflare Workers and building AI-powered development workflows.

## ✨ Features

- 🎯 **Type-Safe**: Full type hints, Pydantic models, mypy compliance
- 🧩 **Modular**: Plugin-based tool system, easy to extend
- ⚡ **Async**: Built on async/await throughout
- 🚀 **Cloudflare Native**: Tools designed for Cloudflare Workers orchestration
- 🤖 **AI-Friendly**: Tools that make sense for AI assistants to use
- 📝 **Well-Documented**: Clear architecture and comprehensive docs

## 🚀 Quick Start

### Installation

```bash
# Clone or navigate to the project
cd CursorMCP

# Install dependencies
pip install -r requirements.txt

# Or install in development mode
pip install -e .
```

### Configuration

1. Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```

2. Edit `.env` with your Cloudflare credentials:
```env
CLOUDFLARE_API_TOKEN=your_token_here
CLOUDFLARE_ACCOUNT_ID=your_account_id_here
WORKSPACE_ROOT=/path/to/your/workspace
```

### Running the Server

```bash
python -m cursormcp.main
```

The server runs via stdio and communicates using the MCP protocol (JSON-RPC 2.0).

## 🔧 Setting Up in Cursor

1. Add to your Cursor MCP configuration (usually `~/.cursor/mcp.json` or similar):

```json
{
  "mcpServers": {
    "cursormcp": {
      "command": "python",
      "args": ["-m", "cursormcp.main"],
      "env": {
        "CLOUDFLARE_API_TOKEN": "your_token",
        "CLOUDFLARE_ACCOUNT_ID": "your_account_id"
      }
    }
  }
}
```

2. Restart Cursor

3. The tools will be available in your Cursor AI assistant!

## 🛠️ Available Tools

### Cloudflare Tools
- `deploy_worker` - Deploy a Cloudflare Worker
- `list_workers` - List all Workers
- `get_worker_logs` - Get Worker logs
- `create_durable_object` - Create a Durable Object class
- `query_d1` - Query D1 database
- `get_kv_value` / `set_kv_value` - KV storage operations

### Development Tools
- `read_file` - Read file contents
- `write_file` - Write file contents
- `list_directory` - List directory contents
- `search_files` - Search for files
- `git_status` - Get git status
- `run_command` - Execute shell command (with safety)

### Meta Tools
- `list_tools` - List all available tools
- `get_tool_info` - Get tool documentation
- `get_server_status` - Server health check

## 📖 Architecture

See [ARCHITECTURE.md](./ARCHITECTURE.md) for detailed architecture documentation.

## 🧪 Development

```bash
# Run tests
pytest

# Type checking
mypy src/

# Format code
black src/

# Lint
ruff check src/
```

## 📝 License

MIT

## 🙏 Acknowledgments

Built with inspiration from:
- [Model Context Protocol](https://modelcontextprotocol.io)
- [DevMCP](https://github.com/yourusername/DevMCP) - Your existing MCP server
- [Cloudflare Workers](https://workers.cloudflare.com/)

---

**Built with ❤️ for Cursor & Cloudflare**

