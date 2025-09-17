#!/usr/bin/env python3
"""
AGENT.FORGE Backend
Commercial multi-tenant AI agent deployment platform
"""

import os
import uuid
import hashlib
import secrets
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
import json

import jwt
from fastapi import FastAPI, HTTPException, Depends, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, EmailStr
import asyncpg
import asyncio
from contextlib import asynccontextmanager
from typing import Optional as TypingOptional

# Core imports
from onboarding_engine import OnboardingEngine, create_onboarding_engine, OnboardingStage

# Import Redis for caching
import redis.asyncio as redis

# LLM Integration
from llm_integration import llm, LLMProvider

# Usage tracking
from usage_endpoints import router as usage_router

# Configuration
JWT_SECRET = os.getenv("JWT_SECRET", secrets.token_hex(32))
JWT_ALGORITHM = "HS256"
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://localhost/agentforge")
GATEWAY_URL = os.getenv("GATEWAY_URL", "http://localhost:8002")
SERVICE_TOKEN = os.getenv("SERVICE_TOKEN", "")

# Bearer token authentication
security = HTTPBearer()

# Global instances
db_pool = None
onboarding_engine = None
redis_client = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifecycle management"""
    global db_pool, onboarding_engine, redis_client

    # Initialize database pool
    db_pool = await asyncpg.create_pool(
        DATABASE_URL,
        min_size=10,
        max_size=20,
        max_queries=50000,
        max_inactive_connection_lifetime=300
    )

    # Initialize Redis for caching
    redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
    redis_client = await redis.from_url(redis_url, decode_responses=True)

    # Initialize onboarding
    onboarding_engine = await create_onboarding_engine(db_pool)

    yield

    # Cleanup
    await redis_client.close()
    await db_pool.close()

# Initialize FastAPI app
app = FastAPI(
    title="Agent.Forge API",
    description="Commercial multi-tenant AI agent deployment for websites and teams",
    version="2.0.0",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure this properly in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include usage tracking routes
app.include_router(usage_router)

# ===============================
# PYDANTIC MODELS
# ===============================

class TeamCreate(BaseModel):
    name: str
    domain: str

class UserCreate(BaseModel):
    email: EmailStr
    password: str
    team_name: Optional[str] = None

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class ClientCreate(BaseModel):
    name: str
    domain: Optional[str] = None
    brand_color: Optional[str] = "#007bff"
    widget_position: Optional[str] = "bottom-right"
    welcome_message: Optional[str] = "Hi! How can I help you today?"

class KnowledgeEntry(BaseModel):
    intent: str
    title: str
    content: str
    priority: Optional[int] = 1

class ChatMessage(BaseModel):
    message: str
    session_id: Optional[str] = None
    visitor_id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

class DeploymentRequest(BaseModel):
    target: str = "railway"
    note: TypingOptional[str] = None

class DeploymentStatusUpdate(BaseModel):
    status: str
    message: TypingOptional[str] = None
    logs_append: TypingOptional[str] = None
    result: TypingOptional[Dict[str, Any]] = None

# ===============================
# UTILITY FUNCTIONS
# ===============================

def hash_password(password: str) -> str:
    """Hash password with salt"""
    salt = secrets.token_hex(16)
    password_hash = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt.encode('utf-8'), 100000)
    return f"{salt}${password_hash.hex()}"

def verify_password(password: str, password_hash: str) -> bool:
    """Verify password"""
    try:
        salt, hash_hex = password_hash.split('$')
        password_check = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt.encode('utf-8'), 100000)
        return password_check.hex() == hash_hex
    except:
        return False

def create_jwt_token(user_id: str, team_id: str) -> str:
    """Create JWT token"""
    payload = {
        "user_id": user_id,
        "team_id": team_id,
        "exp": datetime.utcnow() + timedelta(days=30)
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    """Extract current user from JWT"""
    token = credentials.credentials
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

def generate_widget_id() -> str:
    """Generate unique widget ID"""
    return f"wgt_{secrets.token_urlsafe(16)}"

def is_valid_service_token(token: str) -> bool:
    expected = SERVICE_TOKEN.strip()
    return bool(expected) and secrets.compare_digest(expected, token or "")

# ===============================
# AUTHENTICATION ENDPOINTS
# ===============================

@app.post("/auth/register")
async def register(user_data: UserCreate):
    """Register new user and team"""

    async with db_pool.acquire() as conn:
        # Check if email exists
        existing = await conn.fetchrow(
            "SELECT id FROM team_members WHERE email = $1",
            user_data.email
        )
        if existing:
            raise HTTPException(status_code=400, detail="Email already registered")

        # Create team if name provided
        if user_data.team_name:
            team_id = str(uuid.uuid4())
            await conn.execute(
                "INSERT INTO teams (id, name) VALUES ($1, $2)",
                team_id, user_data.team_name
            )
        else:
            # Get first team or create default
            team = await conn.fetchrow("SELECT id FROM teams LIMIT 1")
            team_id = team['id'] if team else str(uuid.uuid4())
            if not team:
                await conn.execute(
                    "INSERT INTO teams (id, name) VALUES ($1, 'Default Team')",
                    team_id
                )

        # Create user
        user_id = str(uuid.uuid4())
        password_hash = hash_password(user_data.password)

        await conn.execute(
            """
            INSERT INTO team_members (id, team_id, email, password_hash, role)
            VALUES ($1, $2, $3, $4, 'owner')
            """,
            user_id, team_id, user_data.email, password_hash
        )

        # Create JWT token
        token = create_jwt_token(user_id, team_id)

        return {
            "token": token,
            "user_id": user_id,
            "team_id": team_id
        }

@app.post("/auth/login")
async def login(user_data: UserLogin):
    """User login"""

    async with db_pool.acquire() as conn:
        user = await conn.fetchrow(
            "SELECT id, team_id, password_hash FROM team_members WHERE email = $1",
            user_data.email
        )

        if not user or not verify_password(user_data.password, user['password_hash']):
            raise HTTPException(status_code=401, detail="Invalid credentials")

        token = create_jwt_token(user['id'], user['team_id'])

        return {
            "token": token,
            "user_id": user['id'],
            "team_id": user['team_id']
        }

# ===============================
# CLIENT MANAGEMENT
# ===============================

@app.get("/clients")
async def get_clients(current_user: dict = Depends(get_current_user)):
    """Get all clients for team"""

    async with db_pool.acquire() as conn:
        clients = await conn.fetch(
            """
            SELECT id, name, domain, widget_id, created_at, active
            FROM clients
            WHERE team_id = $1
            ORDER BY created_at DESC
            """,
            current_user['team_id']
        )

        return [dict(c) for c in clients]

@app.post("/clients")
async def create_client(client_data: ClientCreate, current_user: dict = Depends(get_current_user)):
    """Create new client"""

    async with db_pool.acquire() as conn:
        client_id = str(uuid.uuid4())
        widget_id = generate_widget_id()

        await conn.execute(
            """
            INSERT INTO clients (id, team_id, name, domain, widget_id, brand_color, widget_position, welcome_message)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
            """,
            client_id, current_user['team_id'], client_data.name, client_data.domain,
            widget_id, client_data.brand_color, client_data.widget_position, client_data.welcome_message
        )

        # Create default agent
        agent_id = str(uuid.uuid4())
        await conn.execute(
            """
            INSERT INTO agents (id, client_id, name, system_prompt)
            VALUES ($1, $2, 'Default Agent', 'You are a helpful assistant.')
            """,
            agent_id, client_id
        )

        return {
            "client_id": client_id,
            "widget_id": widget_id,
            "agent_id": agent_id,
            "embed_code": f'<script src="{Request.url.scheme}://{Request.url.netloc}/widget.js?id={widget_id}"></script>'
        }

# ===============================
# DEPLOYMENTS
# ===============================

@app.post("/agents/{agent_id}/deploy")
async def deploy_agent(agent_id: str, req: DeploymentRequest, request: Request, current_user: dict = Depends(get_current_user)):
    """Create a deployment job and ask the Forge Gateway to execute it."""

    async with db_pool.acquire() as conn:
        # Join agent -> client -> team to validate ownership
        record = await conn.fetchrow(
            """
            SELECT a.id as agent_id, c.id as client_id, c.team_id as team_id
            FROM agents a
            JOIN clients c ON a.client_id = c.id
            WHERE a.id = $1 AND c.team_id = $2
            """,
            agent_id, current_user['team_id']
        )
        if not record:
            raise HTTPException(status_code=404, detail="Agent not found or not in your team")

        # Create deployment row
        deployment_id = str(uuid.uuid4())
        await conn.execute(
            """
            INSERT INTO deployments (id, team_id, client_id, agent_id, status, target, task_type, created_by)
            VALUES ($1, $2, $3, $4, 'pending', $5, 'deploy_agent', $6)
            """,
            deployment_id, record['team_id'], record['client_id'], record['agent_id'], req.target, current_user['user_id']
        )

    # Build callback URL
    callback_url = f"{request.url.scheme}://{request.url.netloc}/deployments/{deployment_id}/status"

    # Best-effort notify gateway (non-blocking)
    try:
        import httpx  # type: ignore
        payload = {
            "deployment_id": deployment_id,
            "team_id": record['team_id'],
            "client_id": record['client_id'],
            "agent_id": record['agent_id'],
            "target": req.target,
            "callback_url": callback_url
        }
        # Fire-and-forget
        async def notify_gateway():
            async with httpx.AsyncClient(timeout=10) as client:
                await client.post(f"{GATEWAY_URL}/deploy", json=payload, headers={"X-Service-Token": SERVICE_TOKEN})
        asyncio.create_task(notify_gateway())
    except Exception:
        # Dependency may be missing locally; deployment worker can be triggered manually
        pass

    return {"deployment_id": deployment_id, "status": "queued"}


@app.post("/deployments/{deployment_id}/status")
async def update_deployment_status(deployment_id: str, update: DeploymentStatusUpdate, request: Request):
    """Gateway callback to update deployment status/logs/result."""
    service_token = request.headers.get("X-Service-Token", "")
    if not is_valid_service_token(service_token):
        raise HTTPException(status_code=401, detail="Invalid service token")

    if update.status not in {"pending", "running", "success", "failed"}:
        raise HTTPException(status_code=400, detail="Invalid status")

    async with db_pool.acquire() as conn:
        # Append logs and update status/result
        await conn.execute(
            """
            UPDATE deployments
            SET status = $2,
                logs = COALESCE(logs, '') || COALESCE($3, ''),
                result = COALESCE($4, result),
                updated_at = NOW()
            WHERE id = $1
            """,
            deployment_id,
            update.status,
            (update.logs_append or "") + ("\n" if update.logs_append else ""),
            json.dumps(update.result) if update.result is not None else None
        )

    return {"deployment_id": deployment_id, "status": update.status}


@app.get("/deployments/{deployment_id}")
async def get_deployment(deployment_id: str, current_user: dict = Depends(get_current_user)):
    """Fetch a deployment's current status and logs for the requesting team."""
    async with db_pool.acquire() as conn:
        dep = await conn.fetchrow(
            """
            SELECT d.id, d.team_id, d.client_id, d.agent_id, d.status, d.logs, d.result, d.created_at, d.updated_at
            FROM deployments d
            WHERE d.id = $1
            """,
            deployment_id
        )
        if not dep:
            raise HTTPException(status_code=404, detail="Deployment not found")

        # Access control: ensure same team
        if dep['team_id'] != current_user['team_id']:
            raise HTTPException(status_code=403, detail="Forbidden")

        return {
            "id": str(dep['id']),
            "team_id": str(dep['team_id']),
            "client_id": str(dep['client_id']),
            "agent_id": str(dep['agent_id']),
            "status": dep['status'],
            "logs": dep['logs'] or "",
            "result": dep['result'] or {},
            "created_at": dep['created_at'].isoformat() if dep['created_at'] else None,
            "updated_at": dep['updated_at'].isoformat() if dep['updated_at'] else None
        }

# ===============================
# KNOWLEDGE MANAGEMENT
# ===============================

@app.get("/clients/{client_id}/knowledge")
async def get_knowledge(client_id: str, current_user: dict = Depends(get_current_user)):
    """Get client knowledge base"""

    async with db_pool.acquire() as conn:
        # Verify client belongs to team
        client = await conn.fetchrow(
            "SELECT id FROM clients WHERE id = $1 AND team_id = $2",
            client_id, current_user['team_id']
        )
        if not client:
            raise HTTPException(status_code=404, detail="Client not found")

        entries = await conn.fetch(
            """
            SELECT id, intent, title, content, priority, active
            FROM knowledge_entries
            WHERE client_id = $1
            ORDER BY priority DESC, created_at DESC
            """,
            client_id
        )

        return [dict(e) for e in entries]

@app.post("/clients/{client_id}/knowledge")
async def add_knowledge(client_id: str, entry: KnowledgeEntry, current_user: dict = Depends(get_current_user)):
    """Add knowledge entry"""

    async with db_pool.acquire() as conn:
        # Verify client belongs to team
        client = await conn.fetchrow(
            "SELECT id FROM clients WHERE id = $1 AND team_id = $2",
            client_id, current_user['team_id']
        )
        if not client:
            raise HTTPException(status_code=404, detail="Client not found")

        entry_id = str(uuid.uuid4())
        await conn.execute(
            """
            INSERT INTO knowledge_entries (id, client_id, intent, title, content, priority, content_type)
            VALUES ($1, $2, $3, $4, $5, $6, 'faq')
            """,
            entry_id, client_id, entry.intent, entry.title, entry.content, entry.priority
        )

        return {"id": entry_id, "status": "created"}

# ===============================
# WIDGET API
# ===============================

@app.get("/widget/{widget_id}")
async def serve_widget(widget_id: str):
    """Serve widget interface"""

    widget_html = f'''<!DOCTYPE html>
<html>
<head>
    <title>Chat Widget</title>
    <style>
        /* Widget styles here */
        body {{ margin: 0; font-family: -apple-system, sans-serif; }}
        #chat-container {{ height: 100vh; display: flex; flex-direction: column; }}
        #messages {{ flex: 1; overflow-y: auto; padding: 1rem; }}
        .message {{ margin: 0.5rem 0; }}
        .user {{ text-align: right; }}
        .assistant {{ text-align: left; }}
        #input-area {{ padding: 1rem; border-top: 1px solid #eee; }}
        #message-input {{ width: calc(100% - 80px); padding: 0.5rem; }}
        #send-button {{ width: 60px; padding: 0.5rem; }}
    </style>
</head>
<body>
    <div id="chat-container">
        <div id="messages"></div>
        <div id="input-area">
            <input type="text" id="message-input" placeholder="Type your message...">
            <button id="send-button">Send</button>
        </div>
    </div>
    <script>
        const widgetId = '{widget_id}';
        const messages = document.getElementById('messages');
        const input = document.getElementById('message-input');
        const button = document.getElementById('send-button');

        let sessionId = localStorage.getItem('session_id') || null;

        function addMessage(text, role) {{
            const div = document.createElement('div');
            div.className = `message ${{role}}`;
            div.textContent = text;
            messages.appendChild(div);
            messages.scrollTop = messages.scrollHeight;
        }}

        async function sendMessage() {{
            const message = input.value.trim();
            if (!message) return;

            addMessage(message, 'user');
            input.value = '';

            try {{
                const response = await fetch(`/widget/${{widgetId}}/chat`, {{
                    method: 'POST',
                    headers: {{ 'Content-Type': 'application/json' }},
                    body: JSON.stringify({{
                        message: message,
                        session_id: sessionId
                    }})
                }});

                const data = await response.json();
                sessionId = data.session_id;
                localStorage.setItem('session_id', sessionId);

                addMessage(data.response || 'Sorry, something went wrong.', 'assistant');
            }} catch (error) {{
                addMessage('Connection error. Please try again.', 'assistant');
            }}
        }}

        button.addEventListener('click', sendMessage);
        input.addEventListener('keypress', (e) => {{
            if (e.key === 'Enter') sendMessage();
        }});
    </script>
</body>
</html>'''

    return HTMLResponse(content=widget_html)

@app.post("/widget/{widget_id}/chat")
async def chat_with_widget(widget_id: str, message_data: ChatMessage):
    """Handle widget chat - Simple, fast, revenue-focused"""

    from simple_chat import handle_chat

    session_id = message_data.session_id or f"session_{secrets.token_urlsafe(8)}"

    # Use simplified chat handler
    result = await handle_chat(
        widget_id=widget_id,
        message=message_data.message,
        session_id=session_id,
        db_pool=db_pool,
        redis_client=redis_client
    )

    return result

# ===============================
# HEALTH CHECK
# ===============================

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "message": "Agent.Forge is operational",
        "version": "2.0.0"
    }

# ===============================
# ROOT ENDPOINT
# ===============================

@app.get("/")
async def root():
    """API root endpoint"""
    return {
        "name": "Agent.Forge API",
        "version": "2.0.0",
        "description": "Commercial AI agent deployment platform",
        "documentation": "/docs",
        "health": "/health"
    }