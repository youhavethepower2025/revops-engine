# AGENT.FORGE DEPLOYMENT MASTERPLAN
## From Local Forge to Global Platform

---

## 🎯 DEPLOYMENT OVERVIEW - ELITE VERSION

**Stack**: Cloudflare (Frontend) + Railway (Backend + PostgreSQL + Redis)
**Features**: Consciousness Weaving, Quantum Memory, Narrative Orchestration, Boundary Guardian
**Timeline**: 2-3 weeks to production
**Cost**: ~$30-70/month initially

---

## 📋 PRE-DEPLOYMENT CHECKLIST

### Required Accounts
- [ ] Railway account (backend + PostgreSQL + Redis)
- [ ] Cloudflare account (frontend + CDN)
- [ ] OpenAI/Anthropic/Groq API keys
- [ ] GitHub account (version control)
- [ ] Domain name (agent-forge.com or similar)

### Local Environment Ready
- [ ] Docker installed and working
- [ ] Node.js 18+ installed
- [ ] Python 3.10+ installed
- [ ] PostgreSQL client installed
- [ ] Redis client installed

---

## 🚀 PHASE 1: LOCAL DEVELOPMENT & TESTING (Days 1-3)

### Step 1: Complete Local Setup
```bash
# Clone and setup
cd agent-forge
python -m venv venv
source venv/bin/activate
pip install -r backend/requirements.txt

# Frontend setup
cd frontend
npm install

# Database setup with Redis
docker-compose up -d postgres redis

# Verify consciousness systems
python -c "from backend.quantum_memory_engine import AgentMemoryEngine; print('✅ Memory Engine')"
python -c "from backend.consciousness_weaver import ConsciousnessWeaver; print('✅ Consciousness Weaver')"
python -c "from backend.boundary_guardian import BoundaryGuardian; print('✅ Boundary Guardian')"
python -c "from backend.narrative_orchestrator import NarrativeOrchestrator; print('✅ Narrative Orchestrator')"
```

### Step 2: Environment Configuration
```bash
# Create .env.local
cat > backend/.env.local << EOF
DATABASE_URL=postgresql://forge:forge123@localhost/agentforge
REDIS_URL=redis://localhost:6379
JWT_SECRET=$(openssl rand -hex 32)
OPENAI_API_KEY=your_key_here
ENVIRONMENT=development
EOF

# Create frontend env
cat > frontend/.env.local << EOF
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_WIDGET_URL=http://localhost:3000/widget
EOF
```

### Step 3: Test Everything Locally
```bash
# Run backend with consciousness systems
cd backend
uvicorn main:app --reload --port 8000

# Run frontend (new terminal)
cd frontend
npm run dev

# Test the elite endpoints
curl http://localhost:8000/health
curl http://localhost:8000/elite/consciousness/test/state
curl http://localhost:8000/elite/memory/test/analytics

# Test widget with consciousness
curl -X POST http://localhost:8000/widget/test/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Hello",
    "consciousness_mode": "narrative",
    "emotional_state": {"curiosity": 0.8, "excitement": 0.6}
  }'
```

### Step 4: Verify All Systems
```bash
# Test consciousness weaving
python -c "
from backend.consciousness_weaver import ConsciousnessWeaver
weaver = ConsciousnessWeaver()
print('Consciousness layers:', list(weaver.consciousness_state.layer_weights.keys()))
"

# Test memory engine
python -c "
from backend.quantum_memory_engine import AgentMemoryEngine, MemoryLayer
print('Memory layers:', [l.value for l in MemoryLayer])
"

# Test boundary guardian
python -c "
from backend.boundary_guardian import BoundaryGuardian, SafetyLevel
guardian = BoundaryGuardian()
print('Safety levels:', [l.value for l in SafetyLevel])
"
```

---

## 🌐 PHASE 2: DATABASE & REDIS SETUP (Days 4-5)

### Step 1: PostgreSQL on Railway
```bash
# Add PostgreSQL to your Railway project
railway add postgresql

# Get connection string
railway variables

# Connect and run migrations
psql $DATABASE_URL < database/schema.sql

# Or use Railway's direct connection
railway connect postgresql
```

### Step 2: Redis on Railway (or Upstash for free tier)
```bash
# Option A: Add Redis to Railway
railway add redis

# Option B: Use Upstash (better free tier)
# 1. Go to upstash.com
# 2. Create Redis database (10K commands/day free)
# 3. Get connection URL

# Test connection
redis-cli -u $REDIS_URL ping
```

### Step 3: Update Database Schema
```sql
-- Add new tables for quantum memory
CREATE TABLE IF NOT EXISTS memory_fields (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    client_id UUID REFERENCES clients(id),
    consciousness_level DECIMAL(3,2) DEFAULT 0.1,
    mode VARCHAR(50) DEFAULT 'conversational',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS journey_instances (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    client_id UUID REFERENCES clients(id),
    template_id UUID REFERENCES journey_templates(id),
    phase VARCHAR(50) DEFAULT 'setup',
    state JSONB,
    started_at TIMESTAMP DEFAULT NOW(),
    completed_at TIMESTAMP
);
```

---

## 🚂 PHASE 3: RAILWAY BACKEND DEPLOYMENT (Days 6-7)

### Step 1: Prepare for Railway
```bash
# Create railway.json
cat > backend/railway.json << EOF
{
  "build": {
    "builder": "NIXPACKS"
  },
  "deploy": {
    "startCommand": "uvicorn main:app --host 0.0.0.0 --port \\$PORT",
    "restartPolicyType": "ON_FAILURE",
    "restartPolicyMaxRetries": 10
  }
}
EOF

# Create Procfile
echo "web: uvicorn main:app --host 0.0.0.0 --port \$PORT" > backend/Procfile
```

### Step 2: Deploy to Railway
```bash
# Install Railway CLI
npm install -g @railway/cli

# Login and initialize
railway login
cd backend
railway init

# Link to project
railway link

# Add environment variables in Railway dashboard
# DATABASE_URL, REDIS_URL, JWT_SECRET, OPENAI_API_KEY

# Deploy
railway up

# Get deployment URL
railway status
```

### Step 3: Test Production Backend
```bash
# Test health endpoint
curl https://your-app.railway.app/health

# Test auth
curl -X POST https://your-app.railway.app/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"test123","team_name":"Test Team"}'
```

---

## ☁️ PHASE 4: CLOUDFLARE FRONTEND DEPLOYMENT (Days 8-9)

### Step 1: Prepare Next.js for Cloudflare
```bash
cd frontend

# Update next.config.js for static export
cat > next.config.js << EOF
module.exports = {
  output: 'export',
  images: {
    unoptimized: true
  },
  env: {
    NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL
  }
}
EOF

# Build for production
npm run build
```

### Step 2: Deploy to Cloudflare Pages
```bash
# Install Wrangler CLI
npm install -g wrangler

# Login to Cloudflare
wrangler login

# Create Pages project
wrangler pages project create agent-forge

# Deploy
wrangler pages publish out --project-name agent-forge

# Set environment variables in Cloudflare dashboard
# NEXT_PUBLIC_API_URL = https://your-backend.railway.app
```

### Step 3: Configure Custom Domain
```bash
# In Cloudflare Dashboard:
# 1. Go to Pages > agent-forge > Custom domains
# 2. Add your domain
# 3. Configure DNS records
# 4. Enable SSL
```

---

## 🔧 PHASE 5: INTEGRATION & TESTING (Days 10-12)

### Step 1: Widget Testing
```html
<!-- Test widget on a sample page -->
<!DOCTYPE html>
<html>
<head>
    <title>Widget Test</title>
</head>
<body>
    <h1>Test Page</h1>
    <script src="https://your-domain.com/widget.js?id=test_widget_id"></script>
</body>
</html>
```

### Step 2: End-to-End Testing
```bash
# Create test script
cat > test_e2e.py << 'EOF'
import requests
import json

API_URL = "https://your-backend.railway.app"

# Test registration
register_response = requests.post(
    f"{API_URL}/auth/register",
    json={
        "email": "e2e@test.com",
        "password": "test123",
        "team_name": "E2E Test"
    }
)
token = register_response.json()["token"]

# Test client creation
headers = {"Authorization": f"Bearer {token}"}
client_response = requests.post(
    f"{API_URL}/clients",
    headers=headers,
    json={
        "name": "Test Client",
        "domain": "testclient.com"
    }
)
print("Client created:", client_response.json())
EOF

python test_e2e.py
```

### Step 3: Performance Testing
```bash
# Install artillery for load testing
npm install -g artillery

# Create test config
cat > load_test.yml << EOF
config:
  target: "https://your-backend.railway.app"
  phases:
    - duration: 60
      arrivalRate: 10
scenarios:
  - name: "Widget Chat"
    flow:
      - post:
          url: "/widget/test_widget_id/chat"
          json:
            message: "Hello"
            session_id: "test_session"
EOF

artillery run load_test.yml
```

---

## 🔍 PHASE 6: MONITORING & OPTIMIZATION (Days 13-14)

### Step 1: Setup Monitoring
```bash
# Railway monitoring (built-in)
railway logs --tail

# Add Sentry for error tracking
pip install sentry-sdk

# In main.py
import sentry_sdk
sentry_sdk.init(dsn="your-sentry-dsn")

# Cloudflare Analytics (automatic)
# Check Pages > Analytics in dashboard
```

### Step 2: Database Optimization
```sql
-- Add indexes for performance
CREATE INDEX idx_messages_conversation_id ON messages(conversation_id);
CREATE INDEX idx_knowledge_client_intent ON knowledge_entries(client_id, intent);
CREATE INDEX idx_conversations_session ON conversations(session_id);

-- Add connection pooling config in backend
# In main.py
db_pool = await asyncpg.create_pool(
    DATABASE_URL,
    min_size=10,
    max_size=20,
    max_queries=50000,
    max_inactive_connection_lifetime=300
)
```

### Step 3: Redis Optimization
```python
# Add Redis connection pooling
redis_pool = redis.ConnectionPool(
    host='redis-host',
    port=6379,
    password='password',
    max_connections=50
)
redis_client = redis.Redis(connection_pool=redis_pool)
```

---

## 🚀 PHASE 7: PRODUCTION LAUNCH (Days 15+)

### Step 1: Final Checklist
- [ ] All tests passing
- [ ] SSL certificates active
- [ ] Backups configured
- [ ] Monitoring active
- [ ] Rate limiting configured
- [ ] CORS properly set
- [ ] Environment variables secured
- [ ] Database migrations complete

### Step 2: Go Live
```bash
# Update DNS to point to Cloudflare
# Update backend URL in frontend
# Clear all caches

# Announce launch
echo "🚀 Agent.Forge is LIVE at https://agent-forge.com"
```

### Step 3: Post-Launch Monitoring
```bash
# Monitor for first 24 hours
railway logs --tail

# Check metrics
curl https://your-backend.railway.app/health
curl https://your-backend.railway.app/metrics

# Monitor user signups
psql $DATABASE_URL -c "SELECT COUNT(*) FROM team_members;"
```

---

## 🔄 CONTINUOUS DEPLOYMENT

### GitHub Actions Setup
```yaml
# .github/workflows/deploy.yml
name: Deploy Agent.Forge

on:
  push:
    branches: [main]

jobs:
  deploy-backend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Deploy to Railway
        env:
          RAILWAY_TOKEN: ${{ secrets.RAILWAY_TOKEN }}
        run: |
          npm install -g @railway/cli
          railway up

  deploy-frontend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Deploy to Cloudflare
        env:
          CLOUDFLARE_API_TOKEN: ${{ secrets.CF_API_TOKEN }}
        run: |
          cd frontend
          npm install
          npm run build
          npx wrangler pages publish out --project-name agent-forge
```

---

## 💰 COST BREAKDOWN

### Monthly Costs (Estimated)
- Railway: $20-50 (backend + PostgreSQL + optional Redis)
- Upstash Redis: $0 (10K commands/day free)
- Cloudflare: $0 (free tier)
- Domain: $10/year
- **Total: $20-50/month**

### Scaling Costs (1000+ users)
- Railway: $100-200 (includes PostgreSQL)
- Redis (Railway or Upstash): $10-50
- Cloudflare: $20 (Pro plan)
- **Total: $130-270/month**

---

## 🆘 TROUBLESHOOTING

### Common Issues

1. **Database Connection Issues**
```bash
# Test connection
psql $DATABASE_URL -c "SELECT 1;"
# Check Railway logs
railway logs
```

2. **CORS Errors**
```python
# Update CORS in main.py
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://agent-forge.com"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

3. **Memory Issues**
```bash
# Scale Railway dyno
railway scale --size medium
```

4. **Widget Not Loading**
```javascript
// Check console for errors
// Verify widget_id exists in database
// Check CORS headers
```

---

## 🎯 SUCCESS METRICS

### Week 1 Goals
- [ ] 10 user signups
- [ ] 100 widget interactions
- [ ] <500ms average response time
- [ ] 99% uptime

### Month 1 Goals
- [ ] 100 active users
- [ ] 10,000 widget interactions
- [ ] 5 paying customers
- [ ] Full dashboard operational

---

## 🔮 NEXT STEPS

After successful deployment:
1. Implement A/B testing framework
2. Add journey marketplace
3. Build mobile apps
4. Create developer SDK
5. Launch affiliate program

---

**Remember**: Deploy incrementally. Test everything. Monitor constantly. Iterate based on user feedback.

**From local forge to global platform - This is the way.** 🚀