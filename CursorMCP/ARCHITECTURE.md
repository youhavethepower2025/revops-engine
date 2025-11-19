# CursorMCP Architecture

**A Beautiful, Modern MCP Server Designed for Cursor & Cloudflare**

---

## 🎯 Vision

CursorMCP is a purpose-built MCP server designed specifically for collaborative development with Cursor. It provides a clean, type-safe foundation for orchestrating Cloudflare Workers and building AI-powered development workflows.

### Design Principles

1. **Type Safety First** - Full type hints, Pydantic models, mypy compliance
2. **Modular & Extensible** - Plugin-based tool system, easy to add capabilities
3. **Async by Default** - Built on FastAPI, async/await throughout
4. **Developer Experience** - Clear structure, excellent logging, helpful errors
5. **Cloudflare Native** - Tools designed for Cloudflare Workers orchestration
6. **AI-Friendly** - Tools that make sense for AI assistants to use

---

## 🏗️ Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                        CURSOR (IDE)                             │
│              AI Assistant (Claude via MCP)                      │
└────────────────────────────┬────────────────────────────────────┘
                             │ MCP Protocol (stdio)
                             │ JSON-RPC 2.0
                             ↓
┌─────────────────────────────────────────────────────────────────┐
│                    CursorMCP Server                              │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  Core MCP Handler (mcp_server.py)                        │   │
│  │  - Handles MCP protocol                                  │   │
│  │  - Routes tool calls                                     │   │
│  │  - Manages resources                                     │   │
│  └──────────────────────────────────────────────────────────┘   │
│                          │                                       │
│  ┌───────────────────────┴───────────────────────┐              │
│  │                                                 │              │
│  │  Tool System (tools/)                          │              │
│  │  ┌──────────────┐  ┌──────────────┐          │              │
│  │  │ Cloudflare   │  │ Development  │          │              │
│  │  │ Tools        │  │ Tools        │          │              │
│  │  └──────────────┘  └──────────────┘          │              │
│  │  ┌──────────────┐  ┌──────────────┐          │              │
│  │  │ File System  │  │ Project      │          │              │
│  │  │ Tools        │  │ Management   │          │              │
│  │  └──────────────┘  └──────────────┘          │              │
│  └───────────────────────────────────────────────┘              │
│                          │                                       │
│  ┌───────────────────────┴───────────────────────┐              │
│  │                                                 │              │
│  │  Services Layer (services/)                     │              │
│  │  - Cloudflare API Client                        │              │
│  │  - Project State Manager                        │              │
│  │  - Configuration Manager                        │              │
│  └─────────────────────────────────────────────────┘              │
└────────────────────────────┬────────────────────────────────────┘
                             │ HTTP/API
                             ↓
┌─────────────────────────────────────────────────────────────────┐
│                  Cloudflare Workers                             │
│  - Workers API                                                  │
│  - Durable Objects                                              │
│  - D1 Database                                                  │
│  - KV Storage                                                   │
└─────────────────────────────────────────────────────────────────┘
```

---

## 📁 Project Structure

```
CursorMCP/
├── README.md                 # Project overview & quick start
├── ARCHITECTURE.md          # This file
├── pyproject.toml           # Modern Python project config
├── requirements.txt         # Dependencies
├── .env.example             # Environment template
│
├── src/
│   └── cursormcp/
│       ├── __init__.py
│       ├── main.py          # Entry point
│       ├── config.py         # Configuration management
│       │
│       ├── server/           # MCP Server Core
│       │   ├── __init__.py
│       │   ├── mcp_server.py # Main MCP protocol handler
│       │   ├── router.py     # Tool routing
│       │   └── types.py      # MCP type definitions
│       │
│       ├── tools/            # Tool Implementations
│       │   ├── __init__.py
│       │   ├── base.py       # Base tool class
│       │   ├── registry.py   # Tool registry
│       │   │
│       │   ├── cloudflare/   # Cloudflare tools
│       │   │   ├── __init__.py
│       │   │   ├── workers.py
│       │   │   ├── durable_objects.py
│       │   │   ├── d1.py
│       │   │   └── kv.py
│       │   │
│       │   ├── development/  # Development tools
│       │   │   ├── __init__.py
│       │   │   ├── files.py
│       │   │   ├── git.py
│       │   │   └── project.py
│       │   │
│       │   └── meta/         # Meta tools
│       │       ├── __init__.py
│       │       └── system.py
│       │
│       ├── services/         # Service Layer
│       │   ├── __init__.py
│       │   ├── cloudflare.py # Cloudflare API client
│       │   ├── state.py      # Project state management
│       │   └── logger.py     # Structured logging
│       │
│       └── models/           # Pydantic Models
│           ├── __init__.py
│           ├── tools.py      # Tool request/response models
│           └── cloudflare.py # Cloudflare API models
│
├── tests/                    # Test Suite
│   ├── __init__.py
│   ├── test_tools/
│   └── test_services/
│
└── examples/                 # Example configurations
    └── cloudflare_worker/
```

---

## 🔧 Core Components

### 1. MCP Server (`server/mcp_server.py`)

Handles the MCP protocol (JSON-RPC 2.0 over stdio):

- **Protocol Handler**: Parses MCP requests, routes to appropriate handlers
- **Tool Execution**: Calls tools with proper error handling
- **Resource Management**: Manages MCP resources (files, etc.)
- **Prompt Templates**: Provides prompt templates for AI assistants

**Key Features:**
- Type-safe request/response handling
- Comprehensive error handling with helpful messages
- Async execution for all operations
- Structured logging

### 2. Tool System (`tools/`)

Modular tool architecture:

**Base Tool Class** (`tools/base.py`):
```python
class BaseTool:
    name: str
    description: str
    input_schema: dict
    
    async def execute(self, args: dict) -> dict:
        """Execute tool logic"""
        pass
```

**Tool Registry** (`tools/registry.py`):
- Auto-discovers tools
- Validates tool schemas
- Provides tool listing for MCP

**Tool Categories:**

1. **Cloudflare Tools** (`tools/cloudflare/`)
   - `deploy_worker` - Deploy a Worker
   - `create_durable_object` - Create DO class
   - `query_d1` - Query D1 database
   - `get_kv_value` - Read from KV
   - `set_kv_value` - Write to KV
   - `list_workers` - List all Workers
   - `get_worker_logs` - Get Worker logs

2. **Development Tools** (`tools/development/`)
   - `read_file` - Read file contents
   - `write_file` - Write file contents
   - `list_directory` - List directory
   - `search_files` - Search for files
   - `git_status` - Get git status
   - `git_commit` - Create commit
   - `run_command` - Execute shell command (with safety)

3. **Meta Tools** (`tools/meta/`)
   - `list_tools` - List all available tools
   - `get_tool_info` - Get tool documentation
   - `get_server_status` - Server health check

### 3. Services Layer (`services/`)

Business logic and external API clients:

**Cloudflare Service** (`services/cloudflare.py`):
- Wraps Cloudflare API
- Handles authentication
- Provides typed methods for all operations
- Error handling and retries

**State Manager** (`services/state.py`):
- Tracks project state
- Manages deployment history
- Stores configuration

### 4. Configuration (`config.py`)

Centralized configuration management:

- Environment variable loading
- Type-safe config access
- Validation
- Default values

---

## 🚀 Tool Examples

### Example: Deploy Cloudflare Worker

```python
# tools/cloudflare/workers.py
from ..base import BaseTool
from ...services.cloudflare import CloudflareService

class DeployWorkerTool(BaseTool):
    name = "deploy_worker"
    description = "Deploy a Cloudflare Worker script"
    
    input_schema = {
        "type": "object",
        "properties": {
            "script": {"type": "string", "description": "Worker script code"},
            "name": {"type": "string", "description": "Worker name"},
            "account_id": {"type": "string", "description": "Cloudflare account ID"}
        },
        "required": ["script", "name", "account_id"]
    }
    
    async def execute(self, args: dict) -> dict:
        service = CloudflareService()
        result = await service.deploy_worker(
            script=args["script"],
            name=args["name"],
            account_id=args["account_id"]
        )
        return {"deployment_id": result.id, "url": result.url}
```

### Example: Read File

```python
# tools/development/files.py
from ..base import BaseTool
from pathlib import Path

class ReadFileTool(BaseTool):
    name = "read_file"
    description = "Read contents of a file"
    
    input_schema = {
        "type": "object",
        "properties": {
            "path": {"type": "string", "description": "File path"}
        },
        "required": ["path"]
    }
    
    async def execute(self, args: dict) -> dict:
        path = Path(args["path"])
        if not path.exists():
            raise FileNotFoundError(f"File not found: {path}")
        
        content = path.read_text()
        return {"content": content, "path": str(path)}
```

---

## 🔐 Security & Safety

1. **File System Safety**
   - Restrict file operations to workspace directory
   - Validate paths to prevent directory traversal
   - Read-only operations by default

2. **Command Execution**
   - Whitelist of allowed commands
   - Timeout on all commands
   - Sandboxed execution where possible

3. **API Keys**
   - Environment variables only
   - Never logged or exposed
   - Rotatable credentials

4. **Error Handling**
   - Never expose internal details
   - User-friendly error messages
   - Comprehensive logging (without secrets)

---

## 📊 Data Flow

### Tool Call Flow

```
1. Cursor → MCP Request (JSON-RPC)
   {
     "jsonrpc": "2.0",
     "id": 1,
     "method": "tools/call",
     "params": {
       "name": "deploy_worker",
       "arguments": {...}
     }
   }

2. MCP Server → Router
   - Validates request
   - Finds tool in registry
   - Validates arguments against schema

3. Router → Tool.execute()
   - Calls tool implementation
   - Handles errors
   - Returns result

4. Tool → Service Layer
   - Calls Cloudflare API
   - Handles authentication
   - Processes response

5. Service → Tool → Router → MCP Server
   - Formats response
   - Returns to Cursor

6. Cursor ← MCP Response
   {
     "jsonrpc": "2.0",
     "id": 1,
     "result": {
       "content": [{"type": "text", "text": "..."}]
     }
   }
```

---

## 🧪 Testing Strategy

1. **Unit Tests**: Test individual tools in isolation
2. **Integration Tests**: Test tool + service interactions
3. **E2E Tests**: Test full MCP protocol flow
4. **Mock Services**: Mock Cloudflare API for testing

---

## 🚦 Development Workflow

### Local Development

```bash
# Install dependencies
pip install -e .

# Run server
python -m cursormcp.main

# Run tests
pytest

# Type checking
mypy src/
```

### Adding a New Tool

1. Create tool class in appropriate category
2. Inherit from `BaseTool`
3. Implement `execute()` method
4. Register in `tools/__init__.py`
5. Add tests

---

## 🎨 Design Decisions

### Why Type Safety?

- Catches errors early
- Better IDE support
- Self-documenting code
- Easier refactoring

### Why Async?

- Non-blocking I/O for API calls
- Better performance
- Modern Python standard

### Why Modular?

- Easy to add new tools
- Clear separation of concerns
- Testable components
- Reusable services

### Why Pydantic?

- Runtime validation
- Type coercion
- Excellent error messages
- JSON schema generation

---

## 🔮 Future Enhancements

1. **Resource Providers**: Expose files, databases as MCP resources
2. **Prompt Templates**: Pre-built prompts for common tasks
3. **Workflow Orchestration**: Chain multiple tools together
4. **State Persistence**: Save project state across sessions
5. **Plugin System**: Allow external tool plugins
6. **Web Dashboard**: Visual tool explorer and usage stats

---

## 📚 References

- [MCP Specification](https://modelcontextprotocol.io)
- [Cloudflare Workers API](https://developers.cloudflare.com/api/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Pydantic Documentation](https://docs.pydantic.dev/)

---

**Built with ❤️ for Cursor & Cloudflare**

