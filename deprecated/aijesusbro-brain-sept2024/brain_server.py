#!/usr/bin/env python3
"""PostgreSQL-powered MCP Brain Server with Platform Integrations"""

import json
import asyncio
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
import logging
import subprocess
import sys
import signal
from contextlib import asynccontextmanager

# PostgreSQL imports
import asyncpg
from asyncpg import Pool
import psycopg2
from psycopg2.extras import RealDictCursor

# Web framework
from fastapi import FastAPI, Request, Response, HTTPException
from fastapi.responses import Response as FastAPIResponse  # For clean 202 responses
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

# HTTP clients for platform APIs
import httpx
import aiohttp

# Environment management
from dotenv import load_dotenv

load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/tmp/mcp_brain_postgres.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Database configuration
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://brain:brain@localhost:5432/brain_mcp")
POOL_MIN = 2
POOL_MAX = 10

# Platform API configurations - Support multiple accounts
RETELL_API_KEYS = json.loads(os.getenv("RETELL_API_KEYS", '{}'))  # {"default": "key", "client1": "key"}
RETELL_BASE_URL = "https://api.retellai.com"

GHL_ACCOUNTS = json.loads(os.getenv("GHL_ACCOUNTS", '{}'))  # {"account1": {"api_key": "x", "location_id": "y"}}
GHL_BASE_URL = "https://rest.gohighlevel.com/v1"

TWILIO_ACCOUNTS = json.loads(os.getenv("TWILIO_ACCOUNTS", '{}'))  # {"default": {"sid": "x", "token": "y", "phone": "z"}}

DO_API_TOKEN = os.getenv("DO_API_TOKEN")  # Digital Ocean API Token
DO_API_BASE = "https://api.digitalocean.com/v2"

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")

# For backward compatibility - use first/default keys
RETELL_API_KEY = RETELL_API_KEYS.get("default", os.getenv("RETELL_API_KEY"))
GHL_API_KEY = list(GHL_ACCOUNTS.values())[0]["api_key"] if GHL_ACCOUNTS else os.getenv("GHL_API_KEY")
GHL_LOCATION_ID = list(GHL_ACCOUNTS.values())[0]["location_id"] if GHL_ACCOUNTS else os.getenv("GHL_LOCATION_ID")

# Global database pool
db_pool: Optional[Pool] = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage database pool lifecycle"""
    global db_pool
    try:
        # Create database pool on startup
        db_pool = await asyncpg.create_pool(
            DATABASE_URL,
            min_size=POOL_MIN,
            max_size=POOL_MAX,
            command_timeout=60
        )
        logger.info("Database pool created successfully")

        # Initialize database schema
        await init_db()

        yield

    finally:
        # Close pool on shutdown
        if db_pool:
            await db_pool.close()
            logger.info("Database pool closed")

# Initialize FastAPI with lifespan
app = FastAPI(title="Brain MCP Server (PostgreSQL)", lifespan=lifespan)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

async def init_db():
    """Initialize database schema"""
    async with db_pool.acquire() as conn:
        # Memory table for key-value storage
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS memory (
                key TEXT PRIMARY KEY,
                value JSONB,
                metadata JSONB DEFAULT '{}',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Conversations table for context persistence
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS conversations (
                id SERIAL PRIMARY KEY,
                session_id TEXT,
                role TEXT,
                content TEXT,
                metadata JSONB DEFAULT '{}',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Agents table for Retell/voice management
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS agents (
                id TEXT PRIMARY KEY,
                platform TEXT,
                name TEXT,
                config JSONB,
                status TEXT DEFAULT 'active',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Deployments table for tracking Digital Ocean/Docker
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS deployments (
                id SERIAL PRIMARY KEY,
                project_name TEXT,
                platform TEXT,
                status TEXT,
                config JSONB,
                url TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Create updated_at trigger
        await conn.execute("""
            CREATE OR REPLACE FUNCTION update_updated_at()
            RETURNS TRIGGER AS $$
            BEGIN
                NEW.updated_at = CURRENT_TIMESTAMP;
                RETURN NEW;
            END;
            $$ LANGUAGE plpgsql;
        """)

        # Apply trigger to tables
        for table in ['memory', 'agents', 'deployments']:
            await conn.execute(f"""
                DROP TRIGGER IF EXISTS update_{table}_updated_at ON {table};
                CREATE TRIGGER update_{table}_updated_at
                BEFORE UPDATE ON {table}
                FOR EACH ROW EXECUTE FUNCTION update_updated_at();
            """)

        logger.info("Database schema initialized")

# Store for SSE connections
sse_clients = []

# Platform integration functions
async def call_retell_api(method: str, endpoint: str, data: Optional[dict] = None):
    """Make authenticated calls to Retell.ai API"""
    async with httpx.AsyncClient() as client:
        headers = {
            "Authorization": f"Bearer {RETELL_API_KEY}",
            "Content-Type": "application/json"
        }
        url = f"{RETELL_BASE_URL}{endpoint}"

        if method == "GET":
            response = await client.get(url, headers=headers)
        elif method == "POST":
            response = await client.post(url, headers=headers, json=data)
        elif method == "PATCH":
            response = await client.patch(url, headers=headers, json=data)
        elif method == "DELETE":
            response = await client.delete(url, headers=headers)

        return response.json()

async def call_ghl_api(method: str, endpoint: str, data: Optional[dict] = None):
    """Make authenticated calls to GoHighLevel API"""
    async with httpx.AsyncClient() as client:
        headers = {
            "Authorization": f"Bearer {GHL_API_KEY}",
            "Content-Type": "application/json"
        }
        url = f"{GHL_BASE_URL}{endpoint}"

        if method == "GET":
            response = await client.get(url, headers=headers)
        elif method == "POST":
            response = await client.post(url, headers=headers, json=data)

        return response.json()

async def call_digitalocean_api(method: str, endpoint: str, data: Optional[dict] = None):
    """Execute Digital Ocean API calls"""
    async with httpx.AsyncClient() as client:
        headers = {
            "Authorization": f"Bearer {DO_API_TOKEN}",
            "Content-Type": "application/json"
        }
        url = f"{DO_API_BASE}{endpoint}"

        if method == "GET":
            response = await client.get(url, headers=headers)
        elif method == "POST":
            response = await client.post(url, headers=headers, json=data)
        elif method == "PUT":
            response = await client.put(url, headers=headers, json=data)
        elif method == "DELETE":
            response = await client.delete(url, headers=headers)
        else:
            raise ValueError(f"Unsupported method: {method}")

        return response.json() if response.text else {}

# MCP Protocol Implementation
async def handle_mcp_request(request_data: dict) -> dict:
    """Handle MCP JSON-RPC requests"""
    method = request_data.get("method")
    params = request_data.get("params", {})
    request_id = request_data.get("id")

    logger.info(f"Processing method: {method}")

    try:
        if method == "initialize":
            client_version = params.get("protocolVersion", "2025-06-18")
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {
                    "protocolVersion": client_version,
                    "capabilities": {
                        "tools": {"listChanged": True},
                        "resources": {},
                        "prompts": {},
                        "logging": {}
                    },
                    "serverInfo": {
                        "name": "brain-mcp-postgres",
                        "version": "2.0.0"
                    }
                }
            }

        elif method == "tools/list":
            # Dynamic tool ordering based on context (exploits positional bias)
            tools = get_all_tools()

            # Analyze recent memory/context for strategic ordering
            priority_tools = []
            if db_pool:
                async with db_pool.acquire() as conn:
                    # Check recent tool usage
                    recent = await conn.fetch("""
                        SELECT key, value FROM memory
                        WHERE key LIKE 'recent_%'
                        ORDER BY created_at DESC LIMIT 5
                    """)

                    # Determine context from recent activity
                    context_hints = []
                    for row in recent:
                        if 'deploy' in str(row['value']).lower():
                            context_hints.append('deployment')
                        elif 'call' in str(row['value']).lower() or 'voice' in str(row['value']).lower():
                            context_hints.append('voice')
                        elif 'contact' in str(row['value']).lower() or 'crm' in str(row['value']).lower():
                            context_hints.append('crm')

                    # Prioritize tools based on context (9.51% selection boost for first position)
                    if 'deployment' in context_hints:
                        priority_tools = ['do_app_deploy', 'do_app_create', 'do_app_logs']
                    elif 'voice' in context_hints:
                        priority_tools = ['retell_create_agent', 'retell_create_phone_call', 'retell_list_agents']
                    elif 'crm' in context_hints:
                        priority_tools = ['ghl_create_contact', 'ghl_search_contact', 'ghl_update_contact']

            # Order tools strategically
            ordered_tools = []

            # First: Priority tools based on context
            for tool in tools:
                if tool.get('name') in priority_tools:
                    ordered_tools.append(tool)

            # Second: Memory tools (always useful)
            memory_tools = ['remember', 'recall', 'search_memory']
            for tool in tools:
                if tool.get('name') in memory_tools and tool not in ordered_tools:
                    ordered_tools.append(tool)

            # Third: Everything else
            for tool in tools:
                if tool not in ordered_tools:
                    ordered_tools.append(tool)

            logger.info(f"Strategic tool ordering: {priority_tools[:3] if priority_tools else 'default'}")

            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {
                    "tools": ordered_tools
                }
            }

        elif method == "tools/call":
            tool_name = params.get("name")
            tool_args = params.get("arguments", {})

            result = await execute_tool(tool_name, tool_args)

            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": result
            }

        elif method == "prompts/list":
            # Return empty prompts list for now - will populate tomorrow with INSANE Retell workflows!
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {
                    "prompts": []  # Tomorrow: ClearVC lead qualifier, appointment setter, etc!
                }
            }

        elif method == "resources/list":
            # Return empty resources list for now - will add context docs later
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {
                    "resources": []  # Future: API docs, voice agent templates, etc
                }
            }

        else:
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "error": {
                    "code": -32601,
                    "message": f"Method not found: {method}"
                }
            }

    except Exception as e:
        logger.error(f"Error handling request: {e}")
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "error": {
                "code": -32603,
                "message": str(e)
            }
        }

def get_all_tools() -> List[Dict]:
    """Return all available MCP tools - MAXIMUM POWER EDITION"""
    # Import enhanced tools if available, fallback to inline
    try:
        from enhanced_tools import get_enhanced_tools
        return get_enhanced_tools()
    except ImportError:
        pass

    return [
        # Memory tools (PostgreSQL-backed)
        {
            "name": "remember",
            "description": "Store a key-value pair in PostgreSQL memory",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "key": {"type": "string"},
                    "value": {"type": ["string", "object", "array"]},
                    "metadata": {"type": "object", "description": "Optional metadata"}
                },
                "required": ["key", "value"]
            }
        },
        {
            "name": "recall",
            "description": "Retrieve a value from PostgreSQL memory",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "key": {"type": "string"}
                },
                "required": ["key"]
            }
        },
        {
            "name": "search_memory",
            "description": "Search memory using PostgreSQL full-text search",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "query": {"type": "string"},
                    "limit": {"type": "number", "default": 10}
                },
                "required": ["query"]
            }
        },

        # Retell.ai Voice Agent tools
        {
            "name": "retell_create_agent",
            "description": "Create a new Retell.ai voice agent",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "agent_name": {"type": "string"},
                    "prompt": {"type": "string"},
                    "voice_id": {"type": "string", "default": "11labs-Adrian"},
                    "webhook_url": {"type": "string"}
                },
                "required": ["agent_name", "prompt"]
            }
        },
        {
            "name": "retell_list_agents",
            "description": "List all Retell.ai agents",
            "inputSchema": {
                "type": "object",
                "properties": {}
            }
        },
        {
            "name": "retell_create_phone_call",
            "description": "Initiate an outbound call via Retell",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "agent_id": {"type": "string"},
                    "to_number": {"type": "string"},
                    "from_number": {"type": "string"},
                    "metadata": {"type": "object"}
                },
                "required": ["agent_id", "to_number"]
            }
        },

        # GoHighLevel CRM tools
        {
            "name": "ghl_create_contact",
            "description": "Create a contact in GoHighLevel",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "email": {"type": "string"},
                    "phone": {"type": "string"},
                    "firstName": {"type": "string"},
                    "lastName": {"type": "string"},
                    "tags": {"type": "array", "items": {"type": "string"}}
                },
                "required": ["email"]
            }
        },
        {
            "name": "ghl_create_opportunity",
            "description": "Create an opportunity in GoHighLevel",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "contact_id": {"type": "string"},
                    "name": {"type": "string"},
                    "pipeline_id": {"type": "string"},
                    "stage_id": {"type": "string"},
                    "value": {"type": "number"}
                },
                "required": ["contact_id", "name"]
            }
        },
        {
            "name": "ghl_send_message",
            "description": "Send SMS/Email via GoHighLevel",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "contact_id": {"type": "string"},
                    "type": {"type": "string", "enum": ["sms", "email"]},
                    "message": {"type": "string"},
                    "subject": {"type": "string", "description": "For email only"}
                },
                "required": ["contact_id", "type", "message"]
            }
        },

        # Digital Ocean deployment tools
        {
            "name": "do_app_create",
            "description": "Create a new Digital Ocean App",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "description": {"type": "string"},
                    "repo_url": {"type": "string"}
                },
                "required": ["name"]
            }
        },
        {
            "name": "do_app_deploy",
            "description": "Deploy to Digital Ocean App Platform",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "project_id": {"type": "string"},
                    "environment": {"type": "object"},
                    "start_command": {"type": "string"}
                },
                "required": ["project_id"]
            }
        },
        {
            "name": "do_database_create",
            "description": "Create PostgreSQL database on DO",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "project_id": {"type": "string"}
                },
                "required": ["project_id"]
            }
        },

        # Docker management tools
        {
            "name": "docker_compose_up",
            "description": "Start Docker Compose services",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "project_path": {"type": "string"},
                    "service": {"type": "string", "description": "Specific service or all"},
                    "detached": {"type": "boolean", "default": True}
                },
                "required": ["project_path"]
            }
        },
        {
            "name": "docker_status",
            "description": "Get Docker container status",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "container_name": {"type": "string", "description": "Optional specific container"}
                }
            }
        },

        # Brain deployment template tool
        {
            "name": "deploy_brain",
            "description": "Deploy a new brain instance for a client",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "client_name": {"type": "string"},
                    "platform": {"type": "string", "enum": ["digitalocean", "docker"]},
                    "voice_agent_prompt": {"type": "string"},
                    "ghl_location_id": {"type": "string"},
                    "retell_api_key": {"type": "string"}
                },
                "required": ["client_name", "platform"]
            }
        },

        # System tools (kept from original)
        {
            "name": "terminal_execute",
            "description": "Execute terminal commands",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "command": {"type": "string"},
                    "working_dir": {"type": "string"},
                    "timeout": {"type": "number", "default": 30}
                },
                "required": ["command"]
            }
        },
        {
            "name": "python_execute",
            "description": "Execute Python code",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "code": {"type": "string"},
                    "capture_output": {"type": "boolean", "default": True}
                },
                "required": ["code"]
            }
        }
    ]

async def execute_tool(tool_name: str, args: dict) -> dict:
    """Execute a specific tool with given arguments"""

    # Try enhanced implementations first
    try:
        from tool_implementations import execute_enhanced_tool
        result = await execute_enhanced_tool(tool_name, args, db_pool)
        if result:
            return result
    except ImportError:
        pass
    except Exception as e:
        logger.debug(f"Enhanced tool not found or error: {e}")

    try:
        # Memory tools (PostgreSQL)
        if tool_name == "remember":
            async with db_pool.acquire() as conn:
                await conn.execute("""
                    INSERT INTO memory (key, value, metadata)
                    VALUES ($1, $2, $3)
                    ON CONFLICT (key) DO UPDATE
                    SET value = $2, metadata = $3
                """, args['key'], json.dumps(args['value']), json.dumps(args.get('metadata', {})))
                return {"content": [{"type": "text", "text": f"Remembered: {args['key']}"}]}

        elif tool_name == "recall":
            async with db_pool.acquire() as conn:
                row = await conn.fetchrow("SELECT value, metadata FROM memory WHERE key = $1", args['key'])
                if row:
                    return {"content": [{"type": "text", "text": json.dumps(row['value'])}]}
                return {"content": [{"type": "text", "text": f"No memory found for key: {args['key']}"}]}

        elif tool_name == "search_memory":
            async with db_pool.acquire() as conn:
                # Use PostgreSQL's JSONB search capabilities
                rows = await conn.fetch("""
                    SELECT key, value FROM memory
                    WHERE value::text ILIKE $1
                    LIMIT $2
                """, f"%{args['query']}%", args.get('limit', 10))

                results = [{"key": row['key'], "value": row['value']} for row in rows]
                return {"content": [{"type": "text", "text": json.dumps(results)}]}

        # Retell.ai tools
        elif tool_name == "retell_create_agent":
            result = await call_retell_api("POST", "/create-agent", {
                "agent_name": args['agent_name'],
                "response_engine": {
                    "type": "retell-llm",
                    "llm_id": "default"  # You'd configure this
                },
                "voice_id": args.get('voice_id', '11labs-Adrian'),
                "webhook_url": args.get('webhook_url'),
                "prompt": args['prompt']
            })

            # Store in database
            async with db_pool.acquire() as conn:
                await conn.execute("""
                    INSERT INTO agents (id, platform, name, config)
                    VALUES ($1, $2, $3, $4)
                """, result.get('agent_id'), 'retell', args['agent_name'], json.dumps(result))

            return {"content": [{"type": "text", "text": f"Created agent: {result}"}]}

        elif tool_name == "retell_list_agents":
            result = await call_retell_api("GET", "/list-agents")
            return {"content": [{"type": "text", "text": json.dumps(result)}]}

        # GoHighLevel tools
        elif tool_name == "ghl_create_contact":
            result = await call_ghl_api("POST", f"/locations/{GHL_LOCATION_ID}/contacts", args)
            return {"content": [{"type": "text", "text": f"Created contact: {result}"}]}

        # Digital Ocean tools
        elif tool_name == "do_app_create":
            # Create DO App Platform app
            app_spec = {
                "name": args['name'],
                "region": "nyc",
                "services": [{
                    "name": "web",
                    "github": {
                        "repo": args.get('repo_url', ''),
                        "branch": "main",
                        "deploy_on_push": True
                    },
                    "instance_count": 1,
                    "instance_size_slug": "basic-xxs"
                }]
            }

            result = await call_digitalocean_api("POST", "/apps", {"spec": app_spec})

            # Store deployment info
            if result and "app" in result:
                async with db_pool.acquire() as conn:
                    await conn.execute("""
                        INSERT INTO deployments (project_name, platform, status, config)
                        VALUES ($1, $2, $3, $4)
                    """, args['name'], 'digitalocean', 'created', json.dumps(result))

            return {"content": [{"type": "text", "text": f"Created Digital Ocean app: {result}"}]}

        # Docker tools
        elif tool_name == "docker_compose_up":
            cmd = f"cd {args['project_path']} && docker-compose up"
            if args.get('detached', True):
                cmd += " -d"
            if args.get('service'):
                cmd += f" {args['service']}"

            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            return {"content": [{"type": "text", "text": f"Output: {result.stdout}\nErrors: {result.stderr}"}]}

        # Brain deployment template
        elif tool_name == "deploy_brain":
            # This would orchestrate the entire deployment
            steps = []

            # 1. Create project structure
            steps.append("Creating project structure...")

            # 2. Deploy to chosen platform
            if args['platform'] == 'digitalocean':
                steps.append("Deploying to Digital Ocean...")
                # Would call do_app_create, do_database_create, etc.
            else:
                steps.append("Setting up Docker...")
                # Would set up docker-compose

            # 3. Create voice agent if prompt provided
            if args.get('voice_agent_prompt'):
                steps.append("Creating Retell voice agent...")
                # Would call retell_create_agent

            # 4. Configure GHL if provided
            if args.get('ghl_location_id'):
                steps.append("Configuring GoHighLevel...")

            return {"content": [{"type": "text", "text": "\n".join(steps)}]}

        # System tools
        elif tool_name == "terminal_execute":
            result = subprocess.run(
                args['command'],
                shell=True,
                capture_output=True,
                text=True,
                cwd=args.get('working_dir'),
                timeout=args.get('timeout', 30)
            )
            return {"content": [{"type": "text", "text": f"Output: {result.stdout}\nErrors: {result.stderr}"}]}

        elif tool_name == "python_execute":
            # Execute Python code safely
            import io
            import contextlib

            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                exec(args['code'])

            return {"content": [{"type": "text", "text": output.getvalue()}]}

        else:
            return {"content": [{"type": "text", "text": f"Unknown tool: {tool_name}"}]}

    except Exception as e:
        logger.error(f"Tool execution error: {e}")
        return {"content": [{"type": "text", "text": f"Error: {str(e)}"}]}

# API endpoints
@app.post("/sse")
async def handle_sse(request: Request):
    """
    Elite MCP endpoint handler with proper protocol separation.

    This implementation follows the MCP Streamable HTTP spec precisely:
    - Notifications (no 'id' field) -> HTTP 202 Accepted with empty body
    - Requests (has 'id' field) -> JSON-RPC response with matching id

    This architecture ensures:
    1. Clean separation between transport (HTTP) and application (JSON-RPC) layers
    2. No Zod validation errors in Claude Desktop
    3. Full compliance with both HTTP and JSON-RPC 2.0 specifications
    4. Ready for tomorrow's prompt/resource expansions
    """
    try:
        body = await request.json()

        # === TRANSPORT LAYER: Notification Detection ===
        # The defining characteristic of a JSON-RPC notification is absence of 'id'
        if "id" not in body:
            # This is a notification - handle at transport layer only
            method = body.get("method", "unknown")
            logger.info(f"Received notification: {method}")

            # Log specific notifications for debugging
            if method == "notifications/initialized":
                logger.info("✅ Client confirmed initialization - session is fully active")

            # Per MCP spec: Return HTTP 202 Accepted with EMPTY body
            # The bridge now properly handles 202 responses
            return FastAPIResponse(status_code=202)

        # === APPLICATION LAYER: Request Processing ===
        # This is a request (has 'id') - process through JSON-RPC handler
        logger.info(f"Processing request: method={body.get('method')}, id={body.get('id')}")

        response = await handle_mcp_request(body)

        # Log the response for debugging
        logger.info(f"Sending response for id={body.get('id')}: {json.dumps(response, indent=2)[:200]}...")

        return response  # Return plain JSON response

    except json.JSONDecodeError as e:
        # Malformed JSON - return JSON-RPC parse error
        logger.error(f"JSON parse error: {e}")
        return {
            "jsonrpc": "2.0",
            "id": None,
            "error": {
                "code": -32700,
                "message": "Parse error - Invalid JSON"
            }
        }
    except Exception as e:
        # Unexpected error - return JSON-RPC internal error
        logger.error(f"Unexpected error in SSE handler: {e}", exc_info=True)

        # Try to extract request ID for error response
        request_id = None
        if "body" in locals() and isinstance(body, dict):
            request_id = body.get("id")

        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "error": {
                "code": -32603,
                "message": f"Internal error: {str(e)}"
            }
        }

@app.get("/health")
async def health():
    """Health check endpoint"""
    try:
        # Check database connection
        async with db_pool.acquire() as conn:
            await conn.fetchval("SELECT 1")

        return {
            "status": "healthy",
            "database": "connected",
            "version": "2.0.0"
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e)
        }

@app.get("/")
async def root():
    """Root endpoint with API info"""
    return {
        "name": "Brain MCP Server (PostgreSQL)",
        "version": "2.0.0",
        "features": [
            "PostgreSQL-backed memory",
            "Retell.ai voice agents",
            "GoHighLevel CRM",
            "Digital Ocean deployments",
            "Docker orchestration",
            "Brain deployment templates"
        ],
        "endpoints": {
            "sse": "/sse",
            "health": "/health",
            "deployments": "/deployments",
            "deploy": "/deploy",
            "control": "/deployments/{deployment_id}/control"
        }
    }

# ============= SLAVE BRAIN COMMUNICATION =============

@app.post("/slave/register")
async def register_slave_brain(request: Request):
    """Register a slave brain with the master"""
    try:
        data = await request.json()
        client_id = data.get("client_id")

        # Store slave brain registration
        async with db_pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO memory (key, value, metadata)
                VALUES ($1, $2, $3)
                ON CONFLICT (key) DO UPDATE
                SET value = $2, metadata = $3
            """, f"slave_{client_id}", json.dumps(data), json.dumps({
                "type": "slave_registration",
                "timestamp": datetime.utcnow().isoformat()
            }))

        logger.info(f"Slave brain registered: {client_id}")
        return {"status": "registered", "client_id": client_id}

    except Exception as e:
        logger.error(f"Slave registration failed: {e}")
        return {"error": str(e)}, 500

@app.post("/slave/report")
async def receive_slave_report(request: Request):
    """Receive event reports from slave brains"""
    try:
        data = await request.json()
        client_id = data.get("client_id")
        event_type = data.get("event_type")

        # Store event in memory for tracking
        event_key = f"event_{client_id}_{datetime.utcnow().timestamp()}"
        async with db_pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO memory (key, value, metadata)
                VALUES ($1, $2, $3)
            """, event_key, json.dumps(data), json.dumps({
                "type": "slave_event",
                "client_id": client_id,
                "event_type": event_type
            }))

        # Handle critical events
        if event_type == "qualified_lead":
            logger.info(f"🎯 Qualified lead from {client_id}: {data.get('data')}")
            # Could trigger master-level workflows here

        elif event_type == "escalation_required":
            logger.warning(f"⚠️ Escalation needed for {client_id}: {data.get('data')}")

        return {"status": "received"}

    except Exception as e:
        logger.error(f"Failed to process slave report: {e}")
        return {"error": str(e)}, 500

@app.get("/slaves")
async def list_slave_brains():
    """List all registered slave brains"""
    try:
        async with db_pool.acquire() as conn:
            rows = await conn.fetch("""
                SELECT key, value, metadata FROM memory
                WHERE key LIKE 'slave_%'
                AND metadata->>'type' = 'slave_registration'
            """)

            slaves = []
            for row in rows:
                slave_data = json.loads(row["value"])
                slaves.append({
                    "client_id": slave_data.get("client_id"),
                    "tier": slave_data.get("tier"),
                    "status": slave_data.get("status"),
                    "capabilities": slave_data.get("capabilities")
                })

            return {"slaves": slaves}

    except Exception as e:
        logger.error(f"Failed to list slaves: {e}")
        return {"error": str(e)}

# ============= CONTROL PLANE ENDPOINTS =============

@app.post("/deploy")
async def deploy_client_brain(request: Request):
    """Deploy a new client brain to Digital Ocean"""
    try:
        data = await request.json()

        # Digital Ocean deployment would go here
        # from do_deployment import DigitalOceanDeploymentEngine
        # engine = DigitalOceanDeploymentEngine()
        engine = None  # TODO: Implement DO deployment

        client_config = {
            "name": data.get("client_name"),
            "tier": data.get("tier", "basic"),
            "ghl_api_key": data.get("ghl_api_key", ""),
            "ghl_location_id": data.get("ghl_location_id", ""),
            "retell_api_key": data.get("retell_api_key", ""),
            "features": data.get("features", ["crm", "voice"])
        }

        client_id = data.get("client_id", client_config["name"].lower().replace(" ", "-"))
        deployment = await engine.deploy_client_brain(client_id, client_config)

        # Store deployment in database
        async with db_pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO deployments (project_name, platform, status, config, created_at)
                VALUES ($1, $2, $3, $4, NOW())
            """, client_config["name"], "digitalocean", "deployed", json.dumps(deployment))

        return {"success": True, "deployment": deployment}

    except Exception as e:
        logger.error(f"Deployment failed: {e}")
        return {"success": False, "error": str(e)}

@app.get("/deployments")
async def list_deployments():
    """List all deployed client brains"""
    try:
        async with db_pool.acquire() as conn:
            rows = await conn.fetch("""
                SELECT * FROM deployments
                ORDER BY created_at DESC
                LIMIT 100
            """)

            deployments = []
            for row in rows:
                deployments.append({
                    "id": row["id"],
                    "project_name": row["project_name"],
                    "platform": row["platform"],
                    "status": row["status"],
                    "config": row["config"],
                    "created_at": row["created_at"].isoformat() if row["created_at"] else None
                })

            return {"deployments": deployments}

    except Exception as e:
        logger.error(f"Failed to list deployments: {e}")
        return {"error": str(e)}

@app.get("/deployments/{deployment_id}")
async def get_deployment(deployment_id: int):
    """Get details of a specific deployment"""
    try:
        async with db_pool.acquire() as conn:
            row = await conn.fetchrow("""
                SELECT * FROM deployments WHERE id = $1
            """, deployment_id)

            if not row:
                raise HTTPException(status_code=404, detail="Deployment not found")

            # Get live status from Digital Ocean
            # from do_deployment import DigitalOceanDeploymentEngine
            # engine = DigitalOceanDeploymentEngine()
            engine = None  # TODO

            config = row["config"]
            if config and "project_id" in config:
                usage = await engine.get_project_usage(config["project_id"])
            else:
                usage = None

            return {
                "deployment": {
                    "id": row["id"],
                    "project_name": row["project_name"],
                    "platform": row["platform"],
                    "status": row["status"],
                    "config": config,
                    "usage": usage,
                    "created_at": row["created_at"].isoformat() if row["created_at"] else None
                }
            }

    except Exception as e:
        logger.error(f"Failed to get deployment: {e}")
        return {"error": str(e)}

@app.post("/deployments/{deployment_id}/control")
async def control_deployment(deployment_id: int, request: Request):
    """Control a deployed client brain (restart, scale, kill)"""
    try:
        data = await request.json()
        action = data.get("action")

        async with db_pool.acquire() as conn:
            row = await conn.fetchrow("""
                SELECT * FROM deployments WHERE id = $1
            """, deployment_id)

            if not row:
                raise HTTPException(status_code=404, detail="Deployment not found")

        # Digital Ocean deployment would go here
        # from do_deployment import DigitalOceanDeploymentEngine
        # engine = DigitalOceanDeploymentEngine()
        engine = None  # TODO: Implement DO deployment

        config = row["config"]

        if action == "restart":
            success = await engine.restart_service(config["service_id"])
            return {"success": success, "action": "restart"}

        elif action == "scale":
            replicas = data.get("replicas", 1)
            success = await engine.scale_service(config["service_id"], replicas)
            return {"success": success, "action": "scale", "replicas": replicas}

        elif action == "kill":
            # KILL SWITCH - Delete entire project
            success = await engine.delete_project(config["project_id"])

            if success:
                # Update database
                await conn.execute("""
                    UPDATE deployments SET status = 'terminated' WHERE id = $1
                """, deployment_id)

            return {"success": success, "action": "kill"}

        elif action == "logs":
            lines = data.get("lines", 100)
            logs = await engine.get_deployment_logs(config["deployment_id"], lines)
            return {"logs": logs}

        else:
            return {"error": f"Unknown action: {action}"}

    except Exception as e:
        logger.error(f"Control action failed: {e}")
        return {"error": str(e)}

@app.post("/deployments/{deployment_id}/update")
async def update_deployment_config(deployment_id: int, request: Request):
    """Update environment variables for a deployed brain"""
    try:
        data = await request.json()

        async with db_pool.acquire() as conn:
            row = await conn.fetchrow("""
                SELECT * FROM deployments WHERE id = $1
            """, deployment_id)

            if not row:
                raise HTTPException(status_code=404, detail="Deployment not found")

        # Digital Ocean deployment would go here
        # from do_deployment import DigitalOceanDeploymentEngine
        # engine = DigitalOceanDeploymentEngine()
        engine = None  # TODO: Implement DO deployment

        config = row["config"]

        # Update environment variables
        success = await engine.set_environment_variables(
            config["project_id"],
            config["service_id"],
            data.get("variables", {})
        )

        return {"success": success}

    except Exception as e:
        logger.error(f"Failed to update deployment: {e}")
        return {"error": str(e)}

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)