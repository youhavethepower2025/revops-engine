#!/usr/bin/env python3
"""
AGENT.FORGE - The Backend of Valinor
FastAPI application for multi-tenant agent deployment

Built from Medellín with love and game theory
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

# The Onboarding Engine of Gondor
from onboarding_engine import OnboardingEngine, create_onboarding_engine, OnboardingStage

# The Secret of the West
JWT_SECRET = os.getenv("JWT_SECRET", secrets.token_hex(32))
JWT_ALGORITHM = "HS256"
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://localhost/agentforge")

# Bearer token authentication
security = HTTPBearer()

# Database connection pool (The Mirror of Galadriel)
db_pool = None
onboarding_engine = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """The lifecycle of Middle-earth"""
    global db_pool, onboarding_engine
    db_pool = await asyncpg.create_pool(DATABASE_URL)
    onboarding_engine = await create_onboarding_engine(db_pool)
    yield
    await db_pool.close()

# Initialize the One Ring
app = FastAPI(
    title="Agent.Forge API",
    description="Multi-tenant agent deployment platform - The Backend of Valinor",
    version="1.0.0",
    lifespan=lifespan
)

# CORS - Because even the Undying Lands need to talk to mortals
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your domains
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ===============================
# MODELS (The Silmarillion)
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

class AgentCreate(BaseModel):
    name: str
    system_prompt: Optional[str] = "You are a helpful and friendly assistant."
    model: Optional[str] = "gpt-3.5-turbo"
    temperature: Optional[float] = 0.7
    max_tokens: Optional[int] = 500

class KnowledgeEntry(BaseModel):
    intent: str
    content_type: str  # 'core_fact', 'current_info', 'faq'
    title: str
    content: str
    keywords: Optional[List[str]] = []
    priority: Optional[int] = 1

class ChatMessage(BaseModel):
    message: str
    session_id: Optional[str] = None
    visitor_id: Optional[str] = None

# ===============================
# UTILITY FUNCTIONS (The Powers)
# ===============================

def hash_password(password: str) -> tuple[str, str]:
    """Hash password with salt (The security of Númenor)"""
    salt = secrets.token_hex(16)
    password_hash = hashlib.sha256((password + salt).encode()).hexdigest()
    return password_hash, salt

def verify_password(password: str, hash: str, salt: str) -> bool:
    """Verify password (The test of truth)"""
    return hashlib.sha256((password + salt).encode()).hexdigest() == hash

def create_jwt_token(user_id: str, team_id: str) -> str:
    """Create JWT token (The gift of the Elven-rings)"""
    payload = {
        "user_id": user_id,
        "team_id": team_id,
        "exp": datetime.utcnow() + timedelta(days=7)
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Extract current user from JWT (The wisdom of Elrond)"""
    try:
        payload = jwt.decode(credentials.credentials, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        user_id = payload.get("user_id")
        team_id = payload.get("team_id")
        
        if not user_id or not team_id:
            raise HTTPException(status_code=401, detail="Invalid token")
        
        async with db_pool.acquire() as conn:
            user = await conn.fetchrow(
                "SELECT id, email, team_id, role FROM team_members WHERE id = $1 AND team_id = $2",
                user_id, team_id
            )
            
            if not user:
                raise HTTPException(status_code=401, detail="User not found")
                
            return dict(user)
            
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

def generate_widget_id() -> str:
    """Generate unique widget ID (The names of power)"""
    return f"wg_{secrets.token_urlsafe(16)}"

async def verify_client_access(current_user: dict, client_id: str, conn: asyncpg.Connection) -> bool:
    """Verify that the current user's team has access to the client."""
    owner_team_id = await conn.fetchval(
        "SELECT team_id FROM clients WHERE id = $1", client_id
    )
    if not owner_team_id or str(owner_team_id) != current_user['team_id']:
        return False
    return True

# ===============================
# DATABASE HELPERS (The Servants)
# ===============================

async def create_team(name: str, domain: str) -> str:
    """Create a new team (Establish a new realm)"""
    team_id = str(uuid.uuid4())
    
    async with db_pool.acquire() as conn:
        await conn.execute(
            """
            INSERT INTO teams (id, name, domain, created_at, active)
            VALUES ($1, $2, $3, $4, $5)
            """,
            team_id, name, domain, datetime.utcnow(), True
        )
    
    return team_id

async def create_team_member(team_id: str, email: str, password: str, role: str = "admin") -> str:
    """Create team member (Welcome a new ranger)"""
    user_id = str(uuid.uuid4())
    password_hash, salt = hash_password(password)
    
    async with db_pool.acquire() as conn:
        await conn.execute(
            """
            INSERT INTO team_members (id, team_id, email, password_hash, salt, role, created_at)
            VALUES ($1, $2, $3, $4, $5, $6, $7)
            """,
            user_id, team_id, email, password_hash, salt, role, datetime.utcnow()
        )
    
    return user_id

# ===============================
# AUTHENTICATION (The Gates)
# ===============================

@app.post("/auth/register")
async def register(user_data: UserCreate):
    """Register new user and team (Enter Middle-earth)"""
    
    # Check if user already exists
    async with db_pool.acquire() as conn:
        existing_user = await conn.fetchrow(
            "SELECT id FROM team_members WHERE email = $1", user_data.email
        )
        
        if existing_user:
            raise HTTPException(status_code=400, detail="User already exists")
        
        # Create team if provided
        if user_data.team_name:
            team_domain = user_data.email.split('@')[1]  # Use email domain as team domain
            team_id = await create_team(user_data.team_name, team_domain)
        else:
            # For now, create a default team
            team_domain = user_data.email.split('@')[1]
            team_id = await create_team(f"{user_data.email.split('@')[0]}'s Team", team_domain)
        
        # Create user
        user_id = await create_team_member(team_id, user_data.email, user_data.password)
        
        # Create JWT token
        token = create_jwt_token(user_id, team_id)
        
        return {
            "token": token,
            "user": {
                "id": user_id,
                "email": user_data.email,
                "team_id": team_id
            }
        }

@app.post("/auth/login")
async def login(login_data: UserLogin):
    """User login (Return to Rivendell)"""
    
    async with db_pool.acquire() as conn:
        user = await conn.fetchrow(
            """
            SELECT id, email, password_hash, salt, team_id, role 
            FROM team_members 
            WHERE email = $1
            """,
            login_data.email
        )
        
        if not user or not verify_password(login_data.password, user['password_hash'], user['salt']):
            raise HTTPException(status_code=401, detail="Invalid credentials")
        
        # Update last login
        await conn.execute(
            "UPDATE team_members SET last_login = $1 WHERE id = $2",
            datetime.utcnow(), user['id']
        )
        
        # Create token
        token = create_jwt_token(user['id'], user['team_id'])
        
        return {
            "token": token,
            "user": {
                "id": user['id'],
                "email": user['email'],
                "team_id": user['team_id'],
                "role": user['role']
            }
        }

@app.get("/auth/me")
async def get_me(current_user: dict = Depends(get_current_user)):
    """Get current user info (Know thyself)"""
    return current_user

# ===============================
# TEAM MANAGEMENT (The White Council)
# ===============================

@app.get("/teams/current")
async def get_current_team(current_user: dict = Depends(get_current_user)):
    """Get current team info (Your realm's status)"""
    
    async with db_pool.acquire() as conn:
        team = await conn.fetchrow(
            "SELECT * FROM teams WHERE id = $1",
            current_user['team_id']
        )
        
        if not team:
            raise HTTPException(status_code=404, detail="Team not found")
            
        # Get team members
        members = await conn.fetch(
            """
            SELECT id, email, role, last_login, created_at 
            FROM team_members 
            WHERE team_id = $1
            """,
            current_user['team_id']
        )
        
        # Get client count
        client_count = await conn.fetchval(
            "SELECT COUNT(*) FROM clients WHERE team_id = $1",
            current_user['team_id']
        )
        
        return {
            **dict(team),
            "members": [dict(member) for member in members],
            "client_count": client_count
        }

# ===============================
# CLIENT MANAGEMENT (The Stewards)
# ===============================

@app.get("/clients")
async def get_clients(current_user: dict = Depends(get_current_user)):
    """Get all clients for team (Your protected realms)"""
    
    async with db_pool.acquire() as conn:
        clients = await conn.fetch(
            """
            SELECT c.*, 
                   COUNT(a.id) as agent_count,
                   COUNT(DISTINCT conv.id) as conversation_count
            FROM clients c
            LEFT JOIN agents a ON c.id = a.client_id AND a.active = true
            LEFT JOIN conversations conv ON c.id = conv.client_id
            WHERE c.team_id = $1 AND c.active = true
            GROUP BY c.id
            ORDER BY c.created_at DESC
            """,
            current_user['team_id']
        )
        
        return [dict(client) for client in clients]

@app.post("/clients")
async def create_client(client_data: ClientCreate, current_user: dict = Depends(get_current_user)):
    """Create new client (Establish new realm)"""
    
    client_id = str(uuid.uuid4())
    widget_id = generate_widget_id()
    
    async with db_pool.acquire() as conn:
        await conn.execute(
            """
            INSERT INTO clients (id, team_id, name, domain, widget_id, brand_color, 
                               widget_position, welcome_message, created_at, active)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
            """,
            client_id, current_user['team_id'], client_data.name, client_data.domain,
            widget_id, client_data.brand_color, client_data.widget_position,
            client_data.welcome_message, datetime.utcnow(), True
        )
        
        # Create default agent
        default_agent_id = str(uuid.uuid4())
        default_system_prompt = f"You are a helpful and friendly assistant for {client_data.name}. Your goal is to answer user questions based on the information provided. Be polite and professional."
        await conn.execute(
            """
            INSERT INTO agents (id, client_id, name, system_prompt,
                              model, temperature, max_tokens, created_at, active)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
            """,
            default_agent_id, client_id, f"{client_data.name} Assistant",
            default_system_prompt,
            "gpt-3.5-turbo", 0.7, 500, datetime.utcnow(), True
        )
        
        return {
            "id": client_id,
            "widget_id": widget_id,
            "name": client_data.name,
            "domain": client_data.domain,
            "default_agent_id": default_agent_id
        }

@app.get("/clients/{client_id}")
async def get_client(client_id: str, current_user: dict = Depends(get_current_user)):
    """Get specific client (Realm details)"""
    
    async with db_pool.acquire() as conn:
        client = await conn.fetchrow(
            "SELECT * FROM clients WHERE id = $1 AND team_id = $2",
            client_id, current_user['team_id']
        )
        
        if not client:
            raise HTTPException(status_code=404, detail="Client not found")
        
        # Get agents
        agents = await conn.fetch(
            "SELECT * FROM agents WHERE client_id = $1 AND active = true",
            client_id
        )
        
        # Get knowledge entries count
        knowledge_count = await conn.fetchval(
            "SELECT COUNT(*) FROM knowledge_entries WHERE client_id = $1 AND active = true",
            client_id
        )
        
        return {
            **dict(client),
            "agents": [dict(agent) for agent in agents],
            "knowledge_count": knowledge_count
        }

@app.get("/clients/{client_id}/widget")
async def get_widget_code(client_id: str, current_user: dict = Depends(get_current_user)):
    """Get widget embed code (The beacon code)"""
    
    async with db_pool.acquire() as conn:
        client = await conn.fetchrow(
            "SELECT widget_id, name FROM clients WHERE id = $1 AND team_id = $2",
            client_id, current_user['team_id']
        )
        
        if not client:
            raise HTTPException(status_code=404, detail="Client not found")
        
        widget_code = f'''<!-- {client['name']} Agent Widget -->
<script>
  (function() {{
    var script = document.createElement('script');
    script.src = 'https://agent.forge/widget.js?id={client['widget_id']}';
    script.async = true;
    document.head.appendChild(script);
  }})();
</script>'''
        
        return {
            "widget_id": client['widget_id'],
            "embed_code": widget_code,
            "test_url": f"https://agent.forge/widget/{client['widget_id']}"
        }

# ===============================
# KNOWLEDGE MANAGEMENT (The Libraries)
# ===============================

@app.get("/clients/{client_id}/knowledge")
async def get_knowledge(client_id: str, current_user: dict = Depends(get_current_user)):
    """Get client knowledge base (The realm's library)"""
    
    async with db_pool.acquire() as conn:
        # Verify client ownership
        client = await conn.fetchrow(
            "SELECT id FROM clients WHERE id = $1 AND team_id = $2",
            client_id, current_user['team_id']
        )
        
        if not client:
            raise HTTPException(status_code=404, detail="Client not found")
        
        knowledge = await conn.fetch(
            """
            SELECT * FROM knowledge_entries 
            WHERE client_id = $1 AND active = true
            ORDER BY content_type, priority DESC, created_at DESC
            """,
            client_id
        )
        
        return [dict(entry) for entry in knowledge]

@app.post("/clients/{client_id}/knowledge")
async def add_knowledge(
    client_id: str, 
    knowledge_data: KnowledgeEntry, 
    current_user: dict = Depends(get_current_user)
):
    """Add knowledge entry (Add new lore)"""
    
    async with db_pool.acquire() as conn:
        # Verify client ownership
        client = await conn.fetchrow(
            "SELECT id FROM clients WHERE id = $1 AND team_id = $2",
            client_id, current_user['team_id']
        )
        
        if not client:
            raise HTTPException(status_code=404, detail="Client not found")
        
        entry_id = str(uuid.uuid4())
        await conn.execute(
            """
            INSERT INTO knowledge_entries (id, client_id, intent, content_type, title, 
                                         content, keywords, priority, created_at, active)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
            """,
            entry_id, client_id, knowledge_data.intent, knowledge_data.content_type,
            knowledge_data.title, knowledge_data.content, knowledge_data.keywords,
            knowledge_data.priority, datetime.utcnow(), True
        )
        
        return {"id": entry_id, "message": "Knowledge added successfully"}

# ===============================
# WIDGET API (The Palantír Network)
# ===============================

@app.get("/widget/{widget_id}")
async def get_widget(widget_id: str):
    """Serve widget interface (The seeing stone)"""
    
    async with db_pool.acquire() as conn:
        client = await conn.fetchrow(
            """
            SELECT c.*, t.name as team_name
            FROM clients c
            JOIN teams t ON c.team_id = t.id
            WHERE c.widget_id = $1 AND c.active = true
            """,
            widget_id
        )
        
        if not client:
            raise HTTPException(status_code=404, detail="Widget not found")
        
        # Widget HTML interface
        widget_html = f'''
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{client['name']} Assistant</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            margin: 0;
            padding: 20px;
            background: linear-gradient(135deg, {client['brand_color']}22 0%, {client['brand_color']}11 100%);
            min-height: 100vh;
            display: flex;
            flex-direction: column;
        }}
        
        .chat-container {{
            max-width: 800px;
            margin: 0 auto;
            background: white;
            border-radius: 12px;
            box-shadow: 0 4px 20px rgba(0,0,0,0.1);
            display: flex;
            flex-direction: column;
            height: 600px;
        }}
        
        .chat-header {{
            background: {client['brand_color']};
            color: white;
            padding: 20px;
            border-radius: 12px 12px 0 0;
            text-align: center;
        }}
        
        .chat-messages {{
            flex: 1;
            overflow-y: auto;
            padding: 20px;
            display: flex;
            flex-direction: column;
            gap: 15px;
        }}
        
        .message {{
            max-width: 80%;
            padding: 12px 16px;
            border-radius: 18px;
            word-wrap: break-word;
        }}
        
        .message.user {{
            background: {client['brand_color']};
            color: white;
            align-self: flex-end;
            margin-left: auto;
        }}
        
        .message.assistant {{
            background: #f1f3f5;
            color: #333;
            align-self: flex-start;
        }}
        
        .chat-input {{
            display: flex;
            padding: 20px;
            border-top: 1px solid #eee;
            gap: 12px;
        }}
        
        #messageInput {{
            flex: 1;
            padding: 12px;
            border: 2px solid #eee;
            border-radius: 24px;
            outline: none;
            font-size: 14px;
        }}
        
        #messageInput:focus {{
            border-color: {client['brand_color']};
        }}
        
        #sendButton {{
            background: {client['brand_color']};
            color: white;
            border: none;
            padding: 12px 20px;
            border-radius: 24px;
            cursor: pointer;
            font-weight: 500;
        }}
        
        #sendButton:hover {{
            opacity: 0.9;
        }}
        
        .typing {{
            background: #f1f3f5;
            color: #666;
            align-self: flex-start;
            max-width: 80px;
            animation: pulse 1.5s infinite;
        }}
        
        @keyframes pulse {{
            0%, 100% {{ opacity: 1; }}
            50% {{ opacity: 0.5; }}
        }}
    </style>
</head>
<body>
    <div class="chat-container">
        <div class="chat-header">
            <h2>{client['name']} Assistant</h2>
            <p style="margin: 5px 0 0 0; opacity: 0.9; font-size: 14px;">Powered by Agent.Forge</p>
        </div>
        
        <div class="chat-messages" id="chatMessages">
            <div class="message assistant">
                {client['welcome_message']}
            </div>
        </div>
        
        <div class="chat-input">
            <input type="text" id="messageInput" placeholder="Type your message..." maxlength="500">
            <button id="sendButton">Send</button>
        </div>
    </div>
    
    <script>
        const widgetId = '{widget_id}';
        const chatMessages = document.getElementById('chatMessages');
        const messageInput = document.getElementById('messageInput');
        const sendButton = document.getElementById('sendButton');
        
        let sessionId = 'session_' + Math.random().toString(36).substr(2, 9);
        let visitorId = 'visitor_' + Math.random().toString(36).substr(2, 9);
        
        function addMessage(content, role) {{
            const messageDiv = document.createElement('div');
            messageDiv.className = `message ${{role}}`;
            messageDiv.textContent = content;
            chatMessages.appendChild(messageDiv);
            chatMessages.scrollTop = chatMessages.scrollHeight;
        }}
        
        function showTyping() {{
            const typingDiv = document.createElement('div');
            typingDiv.className = 'message typing';
            typingDiv.textContent = '...';
            typingDiv.id = 'typing';
            chatMessages.appendChild(typingDiv);
            chatMessages.scrollTop = chatMessages.scrollHeight;
        }}
        
        function hideTyping() {{
            const typing = document.getElementById('typing');
            if (typing) typing.remove();
        }}
        
        async function sendMessage() {{
            const message = messageInput.value.trim();
            if (!message) return;
            
            addMessage(message, 'user');
            messageInput.value = '';
            showTyping();
            
            try {{
                const response = await fetch(`/widget/${{widgetId}}/chat`, {{
                    method: 'POST',
                    headers: {{
                        'Content-Type': 'application/json',
                    }},
                    body: JSON.stringify({{
                        message: message,
                        session_id: sessionId,
                        visitor_id: visitorId
                    }})
                }});
                
                const data = await response.json();
                hideTyping();
                
                if (data.response) {{
                    addMessage(data.response, 'assistant');
                }} else {{
                    addMessage('Sorry, I encountered an error. Please try again.', 'assistant');
                }}
                
            }} catch (error) {{
                hideTyping();
                addMessage('Sorry, I cannot connect right now. Please try again later.', 'assistant');
            }}
        }}
        
        sendButton.addEventListener('click', sendMessage);
        messageInput.addEventListener('keypress', (e) => {{
            if (e.key === 'Enter') {{
                sendMessage();
            }}
        }});
        
        messageInput.focus();
    </script>
</body>
</html>'''
        
        return HTMLResponse(content=widget_html)

@app.post("/widget/{widget_id}/chat")
async def chat_with_widget(widget_id: str, message_data: ChatMessage):
    """Handle widget chat - The new runtime forge"""
    
    async with db_pool.acquire() as conn:
        # 1. Get Agent Soul (System Prompt)
        agent_info = await conn.fetchrow(
            """
            SELECT a.system_prompt, a.model, a.temperature, a.max_tokens, c.id as client_id
            FROM agents a
            JOIN clients c ON a.client_id = c.id
            WHERE c.widget_id = $1 AND a.active = true AND c.active = true
            LIMIT 1
            """,
            widget_id
        )
        
        if not agent_info:
            raise HTTPException(status_code=404, detail="Widget not found or agent is inactive")

        client_id = agent_info['client_id']
        system_prompt = agent_info['system_prompt']

        # 2. Get Conversation History (L1 Working State)
        session_id = message_data.session_id or f"session_{secrets.token_urlsafe(8)}"
        
        conversation_history_records = await conn.fetch(
            """
            SELECT role, content FROM messages
            WHERE conversation_id = (
                SELECT id FROM conversations WHERE session_id = $1 AND client_id = $2
            )
            ORDER BY created_at ASC
            LIMIT 20
            """,
            session_id, client_id
        )
        
        def format_history(records):
            if not records:
                return ""
            history_str = "\n\n--- Conversation History ---\n"
            for record in records:
                history_str += f"{record['role'].capitalize()}: {record['content']}\n"
            return history_str

        formatted_history = format_history(conversation_history_records)

        # 3. Dynamic Knowledge Retrieval
        search_terms = message_data.message.lower().split()
        search_query = ' & '.join(search_terms)

        knowledge_records = await conn.fetch(
            """
            SELECT title, content
            FROM knowledge_entries
            WHERE client_id = $1
              AND active = true
              AND to_tsvector('english', title || ' ' || content) @@ to_tsquery('english', $2)
            ORDER BY priority DESC, ts_rank(to_tsvector('english', title || ' ' || content), to_tsquery('english', $2)) DESC
            LIMIT 5
            """,
            client_id, search_query
        )

        def format_knowledge(records):
            if not records:
                return ""
            knowledge_str = "\n\n--- Relevant Knowledge ---\n"
            for record in records:
                knowledge_str += f"Title: {record['title']}\nContent: {record['content']}\n---\n"
            return knowledge_str

        formatted_knowledge = format_knowledge(knowledge_records)

        # 4. Forge the Runtime Prompt
        final_prompt = (
            f"--- System Prompt ---\n{system_prompt}"
            f"{formatted_knowledge}"
            f"{formatted_history}"
            f"\n--- Current Request ---\nUser: {message_data.message}\nAssistant:"
        )

        # 5. Execute and Respond (Placeholder)
        # In a real scenario, you would send `final_prompt` to an LLM API.
        # For now, we return the forged prompt to demonstrate the context is built correctly.
        
        conversation = await conn.fetchrow(
            "SELECT id FROM conversations WHERE session_id = $1 AND client_id = $2",
            session_id, client_id
        )
        
        if not conversation:
            conversation_id = str(uuid.uuid4())
            visitor_id = message_data.visitor_id or f"visitor_{secrets.token_urlsafe(8)}"
            await conn.execute(
                """
                INSERT INTO conversations (id, client_id, session_id, visitor_id, started_at)
                VALUES ($1, $2, $3, $4, $5)
                """,
                conversation_id, client_id, session_id, visitor_id, datetime.utcnow()
            )
        else:
            conversation_id = conversation['id']

        # Store user message
        await conn.execute(
            "INSERT INTO messages (conversation_id, role, content) VALUES ($1, 'user', $2)",
            conversation_id, message_data.message
        )
        
        # Store assistant response (the forged prompt for now)
        await conn.execute(
            "INSERT INTO messages (conversation_id, role, content) VALUES ($1, 'assistant', $2)",
            conversation_id, final_prompt 
        )

        return {
            "response": final_prompt,
            "session_id": session_id,
            "comment": "This is the forged runtime prompt. In production, this would be sent to an LLM."
        }


# ===============================
# HEALTH CHECK (The Beacons)
# ===============================

@app.get("/health")
async def health_check():
    """Health check (The light of Eärendil)"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "message": "Agent.Forge is operational - The light of the Silmarils shines eternal"
    }

# ===============================
# INTENT ANALYTICS (The Seeing Stones)
# ===============================

@app.get("/clients/{client_id}/analytics/intents")
async def get_intent_analytics(client_id: str, current_user: dict = Depends(get_current_user)):
    """Get intent analytics for a client (The palantír reveals all)"""
    
    async with db_pool.acquire() as conn:
        # Verify client access
        if not await verify_client_access(current_user, client_id, conn):
            raise HTTPException(status_code=403, detail="Access denied to this client")
        
        # Get intent distribution from recent conversations
        intent_stats = await conn.fetch(
            """
            WITH recent_messages AS (
                SELECT m.content, c.client_id 
                FROM messages m
                JOIN conversations c ON m.conversation_id = c.id
                WHERE c.client_id = $1 
                AND m.role = 'user'
                AND m.created_at >= NOW() - INTERVAL '30 days'
                ORDER BY m.created_at DESC
                LIMIT 1000
            )
            SELECT COUNT(*) as message_count
            FROM recent_messages
            """,
            client_id
        )
        
        # Get top conversation patterns
        conversation_patterns = await conn.fetch(
            """
            SELECT 
                DATE_TRUNC('day', m.created_at) as date,
                COUNT(*) as message_count,
                COUNT(DISTINCT c.session_id) as unique_sessions
            FROM messages m
            JOIN conversations c ON m.conversation_id = c.id
            WHERE c.client_id = $1 
            AND m.created_at >= NOW() - INTERVAL '30 days'
            GROUP BY DATE_TRUNC('day', m.created_at)
            ORDER BY date DESC
            """,
            client_id
        )
        
        return {
            "client_id": client_id,
            "analytics_period": "30_days",
            "total_messages": intent_stats[0]['message_count'] if intent_stats else 0,
            "daily_patterns": [
                {
                    "date": row['date'].isoformat(),
                    "messages": row['message_count'],
                    "unique_sessions": row['unique_sessions']
                }
                for row in conversation_patterns
            ],
            "intent_engine_status": "active",
            "supported_intents": [intent.value for intent in IntentType]
        }

# ===============================
# ONBOARDING SYSTEM (The Great Journey)
# ===============================

@app.post("/onboarding/start")
async def start_onboarding(current_user: dict = Depends(get_current_user)):
    """Start client onboarding journey (Begin the quest)"""
    progress = await onboarding_engine.start_onboarding(
        current_user['team_id'], 
        current_user['id']
    )
    
    return {
        "client_id": progress.client_id,
        "current_stage": progress.current_stage.value,
        "completion_percentage": progress.completion_percentage,
        "next_action": progress.next_action,
        "stage_config": onboarding_engine.stage_configs[progress.current_stage]
    }

@app.get("/onboarding/{client_id}/progress")
async def get_onboarding_progress(client_id: str, current_user: dict = Depends(get_current_user)):
    """Get onboarding progress (Check the map)"""
    
    # Verify access to client
    async with db_pool.acquire() as conn:
        if not await verify_client_access(current_user, client_id, conn):
            raise HTTPException(status_code=403, detail="Access denied to this client")
    
    progress = await onboarding_engine.get_progress(client_id)
    
    return {
        "client_id": progress.client_id,
        "current_stage": progress.current_stage.value,
        "completed_stages": [stage.value for stage in progress.completed_stages],
        "completion_percentage": progress.completion_percentage,
        "next_action": progress.next_action,
        "data_collected": progress.data_collected,
        "stage_config": onboarding_engine.stage_configs[progress.current_stage]
    }

@app.post("/onboarding/{client_id}/submit")
async def submit_onboarding_stage(
    client_id: str, 
    stage_data: Dict[str, Any],
    current_user: dict = Depends(get_current_user)
):
    """Submit stage data and advance (Take the next step)"""
    
    # Verify access to client
    async with db_pool.acquire() as conn:
        if not await verify_client_access(current_user, client_id, conn):
            raise HTTPException(status_code=403, detail="Access denied to this client")
    
    try:
        progress = await onboarding_engine.submit_stage_data(client_id, stage_data)
        
        return {
            "success": True,
            "client_id": progress.client_id,
            "current_stage": progress.current_stage.value,
            "completion_percentage": progress.completion_percentage,
            "next_action": progress.next_action,
            "stage_config": onboarding_engine.stage_configs[progress.current_stage] if progress.current_stage != OnboardingStage.COMPLETED else None
        }
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/onboarding/{client_id}/widget-code")
async def get_widget_code(client_id: str, current_user: dict = Depends(get_current_user)):
    """Get generated widget code (The final prize)"""
    
    # Verify access to client
    async with db_pool.acquire() as conn:
        if not await verify_client_access(current_user, client_id, conn):
            raise HTTPException(status_code=403, detail="Access denied to this client")
    
    # Check if onboarding is complete
    progress = await onboarding_engine.get_progress(client_id)
    if progress.current_stage != OnboardingStage.COMPLETED:
        raise HTTPException(
            status_code=400, 
            detail=f"Onboarding not complete. Current stage: {progress.current_stage.value}"
        )
    
    widget_code = await onboarding_engine.generate_widget_code(client_id)
    
    return {
        "client_id": client_id,
        "widget_ready": True,
        **widget_code
    }

@app.get("/onboarding/stats")
async def get_onboarding_stats(current_user: dict = Depends(get_current_user)):
    """Get team onboarding statistics (Survey the realm)"""
    
    stats = await onboarding_engine.get_onboarding_stats(current_user['team_id'])
    
    return {
        "team_id": current_user['team_id'],
        **stats
    }

@app.get("/")
async def root():
    """Welcome message (The gates of Minas Tirith)"""
    return {
        "message": "Welcome to Agent.Forge - The Backend of Valinor",
        "version": "1.0.0",
        "endpoints": {
            "auth": "/auth/*",
            "teams": "/teams/*", 
            "clients": "/clients/*",
            "widgets": "/widget/*",
            "health": "/health"
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)