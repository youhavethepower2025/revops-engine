# AGENT.FORGE DEPLOYMENT GUIDE
## The Complete Manual for Launching Your Empire

**From Medellín with love and game theory** 🇨🇴

---

## OVERVIEW: THE REALM ARCHITECTURE

Agent.Forge deploys across three kingdoms:

1. **Backend API** → Railway (FastAPI + PostgreSQL)
2. **Frontend Portal** → Cloudflare Pages (Dashboard)  
3. **Widget CDN** → Cloudflare (Embeddable scripts)

**Total deployment time:** ~15 minutes  
**Total monthly cost:** $5-20 (FREE tier possible)

---

## PHASE 1: BACKEND DEPLOYMENT (Railway)

### Step 1: Prepare the Kingdom
```bash
# Clone your realm
git clone <your-repo>
cd agent-forge

# Create Railway project
railway login
railway new agent-forge-api
```

### Step 2: Configure the Database
```bash
# Add PostgreSQL service
railway add postgresql

# Get database URL (save this!)
railway variables
# Copy DATABASE_URL value
```

### Step 3: Set Environment Variables
```bash
railway variables set JWT_SECRET=$(openssl rand -hex 32)
railway variables set ENVIRONMENT=production
railway variables set CORS_ORIGINS=https://agent.forge,https://your-domain.com
```

### Step 4: Deploy the Backend
```bash
# Deploy from backend directory
cd backend/
railway up
```

**Your API will be live at:** `https://your-app.railway.app`

### Step 5: Initialize the Database
```bash
# Run database migrations
railway connect postgresql
# Then run the schema.sql file
\i database/schema.sql
```

---

## PHASE 2: FRONTEND DEPLOYMENT (Cloudflare Pages)

### Step 1: Prepare Cloudflare
- Log into Cloudflare Dashboard
- Go to Pages → Create a project
- Connect your Git repository

### Step 2: Configure Build Settings
```yaml
# In Cloudflare Pages:
Build command: echo "Static site - no build needed"
Build output directory: frontend/
Root directory: /
```

### Step 3: Set Environment Variables
```
API_BASE_URL = https://your-app.railway.app
WIDGET_CDN_URL = https://your-pages.pages.dev  
ENVIRONMENT = production
```

### Step 4: Custom Domain (Optional)
- Go to Pages → Custom domains
- Add your domain (e.g., `agent.forge`)
- Update DNS records as instructed

**Your portal will be live at:** `https://your-pages.pages.dev`

---

## PHASE 3: WIDGET CDN SETUP

### Step 1: Deploy Widget Script
The widget.js file gets served from your Cloudflare Pages automatically at:
```
https://your-domain.com/widget.js?id=WIDGET_ID
```

### Step 2: Test Widget Deployment
Create a test HTML file:
```html
<!DOCTYPE html>
<html>
<head><title>Widget Test</title></head>
<body>
    <h1>Testing Agent.Forge Widget</h1>
    <script src="https://your-domain.com/widget.js?id=test_widget"></script>
</body>
</html>
```

---

## PHASE 4: DOMAIN & DNS SETUP

### Backend Domain (Railway)
```bash
# Add custom domain in Railway dashboard
# Point your DNS to Railway:
CNAME api.agent.forge → your-app.railway.app
```

### Frontend Domain (Cloudflare)
```bash
# In Cloudflare Pages:
A     agent.forge → Cloudflare IP (auto-managed)
CNAME www → agent.forge
```

---

## PRODUCTION CONFIGURATION

### Environment Variables Checklist

**Railway (Backend):**
```env
DATABASE_URL=postgresql://...
JWT_SECRET=your-32-character-hex-secret
ENVIRONMENT=production
CORS_ORIGINS=https://agent.forge,https://www.agent.forge
```

**Cloudflare Pages (Frontend):**
```env
API_BASE_URL=https://api.agent.forge
WIDGET_CDN_URL=https://agent.forge
ENVIRONMENT=production
```

### Security Headers (Already configured)
- CSP (Content Security Policy)
- X-Frame-Options: DENY
- X-Content-Type-Options: nosniff
- HSTS (via Cloudflare)

---

## TESTING YOUR DEPLOYMENT

### 1. API Health Check
```bash
curl https://api.agent.forge/health
# Should return: {"status": "healthy", "message": "..."}
```

### 2. Authentication Test
```bash
curl -X POST https://api.agent.forge/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com", "password": "testpass123"}'
```

### 3. Widget Test
Visit: `https://agent.forge/widget/test_widget_id`

### 4. Portal Test
Visit: `https://agent.forge` and create account

---

## MONITORING & MAINTENANCE

### Railway Monitoring
- Built-in metrics dashboard
- Log streaming: `railway logs`
- Resource usage tracking

### Cloudflare Analytics  
- Pages analytics (built-in)
- Real User Monitoring (RUM)
- Security insights

### Custom Monitoring (Optional)
Add health check endpoints:
```python
# In your FastAPI app
@app.get("/metrics")
async def metrics():
    return {
        "active_clients": await count_active_clients(),
        "conversations_today": await count_todays_conversations(),
        "uptime": get_uptime()
    }
```

---

## SCALING & OPTIMIZATION

### Database Optimization
```sql
-- Add indexes for performance
CREATE INDEX CONCURRENTLY idx_messages_created_at_desc 
ON messages (created_at DESC);

CREATE INDEX CONCURRENTLY idx_conversations_client_started 
ON conversations (client_id, started_at DESC);
```

### Railway Scaling
- Auto-scales by default
- Monitor CPU/memory usage
- Upgrade plan if needed ($5-20/month)

### Cloudflare Optimization
- Automatic CDN caching
- Bandwidth alliance (FREE)
- Global edge distribution

---

## BACKUP & DISASTER RECOVERY

### Database Backups (Railway)
```bash
# Daily automated backups (included)
# Manual backup:
railway connect postgresql
pg_dump your_database > backup.sql
```

### Code Backups
- Git repository (primary backup)
- Railway deployment history
- Cloudflare Pages deployment history

---

## COST BREAKDOWN

### FREE Tier Possible:
- Railway: $5/month (Hobby plan)
- Cloudflare Pages: FREE (100k requests/month)
- PostgreSQL: Included with Railway
- **Total: $5/month**

### Production Scale:
- Railway Pro: $20/month (better resources)
- Cloudflare Pro: $20/month (advanced features)
- **Total: $40/month**

### Enterprise Scale:
- Railway Team: $100/month
- Cloudflare Business: $200/month
- **Total: $300/month**

---

## COMMON ISSUES & SOLUTIONS

### Issue: CORS Errors
```bash
# Solution: Update CORS_ORIGINS
railway variables set CORS_ORIGINS=https://your-domain.com
railway redeploy
```

### Issue: Database Connection
```bash
# Check DATABASE_URL format:
postgresql://user:pass@host:port/dbname
```

### Issue: Widget Not Loading
```bash
# Check widget.js URL and CORS headers
curl -I https://your-domain.com/widget.js
```

### Issue: Authentication Failing
```bash
# Regenerate JWT secret:
railway variables set JWT_SECRET=$(openssl rand -hex 32)
```

---

## DEVELOPMENT WORKFLOW

### Local Development
```bash
# Backend
cd backend/
pip install -r requirements.txt
uvicorn main:app --reload

# Frontend  
cd frontend/
python -m http.server 8080
```

### Staging Environment
```bash
# Create staging branch
git checkout -b staging
railway environment staging
railway up
```

### Production Deployment
```bash
git checkout main
git push origin main
# Railway auto-deploys on push
# Cloudflare Pages auto-deploys on push
```

---

## SUCCESS METRICS

Your deployment is successful when:

✅ API health check returns 200  
✅ User registration works  
✅ Widget loads on external sites  
✅ Portal dashboard displays  
✅ Database queries execute  
✅ HTTPS certificates active  
✅ Analytics tracking works  

---

## NEXT STEPS AFTER DEPLOYMENT

1. **Create your first client** via the portal
2. **Deploy widget** to a test website  
3. **Configure knowledge base** with client info
4. **Set up team members** and permissions
5. **Monitor analytics** and conversations
6. **Scale as needed** based on usage

---

## THE COLOMBIAN ADVANTAGE

Deployed from Medellín with:
- 10x cost efficiency vs Silicon Valley
- No VC pressure for unnecessary complexity
- Pure value-based architectural decisions
- $14k peso lunches while managing billion-dollar platforms

**Your empire is now live. Go forth and deploy intelligence across the digital realm.** 🚀

---

**Need help?** 
- Check the logs: `railway logs`
- Review the architecture: `ARCHITECTURE.md`
- Test the endpoints: Use the provided curl commands

**The realm awaits your command.** ⚔️