# AGENT.FORGE - The Complete Architecture
## Multi-Tenant Agent Deployment Platform

**Philosophy:** Game Theory Optimal from Medellín  
**Stack:** Cloudflare Everything + Railway Backend  
**Vision:** Teams deploy intelligence, clients get magic  

---

## THE MIDDLE-EARTH OF MULTI-TENANCY

### The Shire (Frontend Portal)
- Team members log in and manage their realm
- Create agents like hobbits tend gardens
- Deploy widgets like sending eagles with messages
- Monitor client happiness across the digital landscape

### Rivendell (Backend API)
- FastAPI orchestrating all the magic
- JWT tokens as elven rings of authentication
- PostgreSQL as the memory of Elrond
- Intent-based knowledge flowing like the Bruinen

### Gondor (Client Websites)
- Embedded widgets as beacons of Minas Tirith
- Each client isolated in their own kingdom
- Agents serving as wise counselors
- Knowledge flowing from the Palantír network

---

## THE STACK OF POWER

```yaml
The One Ring (Core Platform):
  - Multi-tenant isolation
  - Intent-based intelligence
  - Real-time deployment
  - Infinite scalability

The Nine Rings (Infrastructure):
  Frontend: Cloudflare Pages (FREE, edge-distributed)
  Backend: Railway + FastAPI (containerized power)
  Database: PostgreSQL (the memory of ages)
  Auth: JWT (simple, unbreakable)
  Storage: Cloudflare R2 (cheaper than Smaug's hoard)
  CDN: Cloudflare (faster than Shadowfax)
  AI: Your choice of models (Groq, OpenAI, Claude)
  Monitoring: Built-in dashboards
  Deployment: Git push to rule them all

The Seven Rings (Features):
  - Team member management
  - Client agent creation
  - Widget embedding system
  - Knowledge base management
  - Analytics and monitoring
  - White-label options
  - Billing integration
```

---

## THE DATABASE OF NÚMENOR

### Table Structure (Designed for Ages)
```sql
-- The Akallabêth of Data

-- Teams (The Houses of the Faithful)
CREATE TABLE teams (
    id UUID PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    domain VARCHAR(255) UNIQUE,
    created_at TIMESTAMP DEFAULT NOW(),
    subscription_tier VARCHAR(50) DEFAULT 'starter',
    active BOOLEAN DEFAULT true
);

-- Team Members (The Dúnedain Rangers)
CREATE TABLE team_members (
    id UUID PRIMARY KEY,
    team_id UUID REFERENCES teams(id),
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    salt VARCHAR(255) NOT NULL,
    role VARCHAR(50) DEFAULT 'member',
    last_login TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Clients (The Realms Under Protection)
CREATE TABLE clients (
    id UUID PRIMARY KEY,
    team_id UUID REFERENCES teams(id),
    name VARCHAR(255) NOT NULL,
    domain VARCHAR(255),
    widget_id VARCHAR(255) UNIQUE,
    active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT NOW(),
    
    -- Client customization
    brand_color VARCHAR(7) DEFAULT '#007bff',
    widget_position VARCHAR(20) DEFAULT 'bottom-right',
    welcome_message TEXT DEFAULT 'Hi! How can I help you today?'
);

-- Agents (The Maiar Servants)
CREATE TABLE agents (
    id UUID PRIMARY KEY,
    client_id UUID REFERENCES clients(id),
    name VARCHAR(255) NOT NULL,
    system_prompt TEXT,
    model VARCHAR(100) DEFAULT 'gpt-3.5-turbo',
    temperature DECIMAL(3,2) DEFAULT 0.7,
    max_tokens INTEGER DEFAULT 500,
    active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Knowledge Base (The Libraries of Minas Tirith)
CREATE TABLE knowledge_entries (
    id UUID PRIMARY KEY,
    client_id UUID REFERENCES clients(id),
    intent VARCHAR(100),
    content_type VARCHAR(50), -- 'core_fact', 'current_info', 'faq'
    title VARCHAR(255),
    content TEXT,
    keywords TEXT[], -- PostgreSQL array for search
    priority INTEGER DEFAULT 1,
    active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Conversations (The Chronicles)
CREATE TABLE conversations (
    id UUID PRIMARY KEY,
    client_id UUID REFERENCES clients(id),
    session_id VARCHAR(255),
    visitor_id VARCHAR(255),
    started_at TIMESTAMP DEFAULT NOW(),
    ended_at TIMESTAMP,
    message_count INTEGER DEFAULT 0
);

-- Messages (The Words of Power)
CREATE TABLE messages (
    id UUID PRIMARY KEY,
    conversation_id UUID REFERENCES conversations(id),
    role VARCHAR(20), -- 'user', 'assistant'
    content TEXT,
    intent VARCHAR(100),
    confidence DECIMAL(3,2),
    response_time_ms INTEGER,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Analytics (The Seeing Stones)
CREATE TABLE analytics_events (
    id UUID PRIMARY KEY,
    client_id UUID REFERENCES clients(id),
    event_type VARCHAR(100),
    event_data JSONB,
    visitor_id VARCHAR(255),
    session_id VARCHAR(255),
    created_at TIMESTAMP DEFAULT NOW()
);
```

---

## THE API OF VALINOR

### Authentication Endpoints (The Gates of Tirion)
```
POST   /auth/login              # Gain entry to the realm
POST   /auth/refresh            # Renew your elvish power
POST   /auth/logout             # Return to mortal lands
GET    /auth/me                 # Know thyself
```

### Team Management (The White Council)
```
GET    /teams/current           # Your domain information
PUT    /teams/current           # Update team settings
GET    /teams/members           # All rangers in service
POST   /teams/members/invite    # Call new allies
DELETE /teams/members/{id}      # Release from service
```

### Client Management (The Stewards of Gondor)
```
GET    /clients                 # All realms under protection
POST   /clients                 # Establish new realm
GET    /clients/{id}            # Realm details
PUT    /clients/{id}            # Update realm
DELETE /clients/{id}            # Abandon realm
GET    /clients/{id}/widget     # The beacon code
```

### Agent Management (The Order of Wizards)
```
GET    /clients/{id}/agents     # All servants of the realm
POST   /clients/{id}/agents     # Summon new agent
PUT    /agents/{id}             # Transform agent nature
DELETE /agents/{id}             # Release agent to Valinor
POST   /agents/{id}/test        # Test agent wisdom
```

### Knowledge Management (The Lore of Middle-earth)
```
GET    /clients/{id}/knowledge  # All realm knowledge
POST   /clients/{id}/knowledge  # Add new lore
PUT    /knowledge/{id}          # Update existing lore
DELETE /knowledge/{id}          # Forget this knowledge
POST   /knowledge/bulk-import   # Import from scrolls
```

### Widget API (The Palantír Network)
```
GET    /widget/{widget_id}      # The seeing stone interface
POST   /widget/{widget_id}/chat # Commune through the stone
GET    /widget/{widget_id}/config # Stone configuration
```

---

## THE FRONTEND REALM

### Portal Structure (The Houses of Healing)
```
/dashboard                      # The main hall
  ├── /overview                 # Realm status at a glance
  ├── /clients                  # Manage protected realms
  │   ├── /new                  # Establish new realm
  │   └── /{id}                 # Specific realm management
  │       ├── /agent            # The realm's counselor
  │       ├── /knowledge        # Realm's library
  │       ├── /analytics        # The seeing stone insights
  │       └── /settings         # Realm customization
  ├── /team                     # The fellowship management
  └── /settings                 # Your preferences
```

### Widget System (The Elessar Stone)
```html
<!-- The One Script to Rule Them All -->
<script src="https://agent.forge/widget.js?id={WIDGET_ID}"></script>

<!-- What mortals see -->
<div id="agent-forge-widget">
  <!-- The comfortable hobbit-hole interface -->
</div>
```

---

## THE DEPLOYMENT PROPHECY

### Phase I: The Fellowship Forms
```bash
# The backend awakens
railway new agent-forge-api
railway add postgresql
railway deploy

# The frontend takes shape  
cloudflare pages create agent-forge-portal
git push cloudflare main
```

### Phase II: The Two Towers Rise
```bash
# Database migrations flow like the Entwash
alembic upgrade head

# Frontend builds like Orthanc
npm run build
cloudflare pages deploy
```

### Phase III: The Return of the Platform
```bash
# Monitoring awakens like the Ents
railway logs --tail

# Analytics flow like the Anduin
select * from analytics_events where event_type = 'widget_interaction';
```

---

## THE INTENT SYSTEM OF THE WISE

### Not RAG (The Foolishness of Saruman)
Instead of chunking knowledge into meaningless pieces, we use the wisdom of intent:

```python
# The Hierarchy of Understanding
client_knowledge = {
    "acme_corp": {
        # L3 - The Unchanging Truth (Like the Music of the Ainur)
        "core_facts": {
            "company": "Acme Corporation",
            "founded": "2010",
            "mission": "Innovation through simplicity"
        },
        
        # L2 - The Current State (Like the affairs of Middle-earth)
        "current_info": {
            "products": ["Widget Pro", "Widget Lite"],
            "pricing": {"pro": 99, "lite": 29},
            "promotion": "20% off this month"
        },
        
        # L1 - The Conversation Flow (Like the path of the Fellowship)
        "conversation": {
            "current_intent": "pricing_inquiry",
            "history": [],
            "context": {}
        },
        
        # Intent Mapping (Like the paths of Númenor)
        "intents": {
            "pricing": ["core_facts.mission", "current_info.pricing", "current_info.promotion"],
            "products": ["current_info.products", "core_facts.company"],
            "support": ["core_facts.company", "current_info.support_hours"],
            "about": ["core_facts.company", "core_facts.founded", "core_facts.mission"]
        }
    }
}
```

---

## THE COLOMBIAN ADVANTAGE

Built from Medellín with:
- 10x cost efficiency of Silicon Valley
- No VC pressure for unnecessary complexity  
- Pure value-based architectural decisions
- $14k peso lunches while architecting billion-dollar platforms

---

## THIS IS THE WAY

The platform that doesn't just deploy agents - it forges them. Where teams become fellowships, clients become realms, and every conversation becomes part of the great music.

**One Platform to Rule Them All** 🔥