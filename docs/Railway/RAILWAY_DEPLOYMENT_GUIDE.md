# 🚂 Railway Deployment Guide for Spectrum-Demo

**Updated:** October 25, 2025
**Railway API Token:** e2b95fb3-364c-4fef-8fd2-abc75f7bf28a

---

## ✅ PRE-DEPLOYMENT CHECKLIST

Your project is **ready for Railway deployment**. Here's what's configured:

- ✅ **requirements.txt** - Updated with latest compatible versions
- ✅ **railway.toml** - Railway configuration file
- ✅ **PORT binding** - Server reads PORT from environment (line 1963 in brain_server.py)
- ✅ **Host binding** - Server binds to 0.0.0.0 (required for Railway)
- ✅ **Health check** - `/health` endpoint configured
- ✅ **Environment variables** - Ready to configure in Railway dashboard
- ✅ **Railway API token** - Updated in .env

---

## 🎯 DEPLOYMENT STRATEGY

### Option 1: GitHub Integration (Recommended)

**Why:** Automatic deployments on every push, easier rollbacks, CI/CD ready

**Steps:**
1. Create GitHub repo for spectrum-demo
2. Push code to GitHub
3. Connect Railway to GitHub repo
4. Railway automatically deploys on push

### Option 2: Railway CLI (Faster for testing)

**Why:** Deploy directly from local machine, no GitHub required

**Steps:**
1. Install Railway CLI
2. Run `railway login`
3. Run `railway init`
4. Run `railway up`

---

## 📋 STEP-BY-STEP DEPLOYMENT

### Phase 1: Setup Railway CLI

```bash
# Install Railway CLI (if not already installed)
npm i -g @railway/cli

# OR with brew
brew install railway

# Login with your API token
export RAILWAY_TOKEN=e2b95fb3-364c-4fef-8fd2-abc75f7bf28a
railway login
```

### Phase 2: Create Railway Project

```bash
cd "/Users/aijesusbro/AI Projects/spectrum-demo"

# Initialize Railway project
railway init

# When prompted:
# - Project name: spectrum-demo
# - Environment: production
```

### Phase 3: Add PostgreSQL Database

```bash
# Add PostgreSQL service to your project
railway add --database postgresql

# Railway will automatically create a PostgreSQL instance
# and set the DATABASE_URL environment variable
```

**Important:** Railway's PostgreSQL sets `DATABASE_URL` automatically. You don't need to configure it manually!

### Phase 4: Configure Environment Variables

```bash
# Set environment variables via CLI
railway variables set ANTHROPIC_API_KEY="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"

railway variables set GHL_API_KEY="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJsb2NhdGlvbl9pZCI6IlBNZ2JRMzc1VEVHT3lHWHNLejdlIiwidmVyc2lvbiI6MSwiaWF0IjoxNzU3NDU2NTUwMTIyLCJzdWIiOiJ5OXFxZjNIV0FYVGk5Nk1wZXVqZiJ9.nbuFjgIZ1hnsHLPDj5IsiUlxR5DgecMw1l56LCEZEjo"

railway variables set GHL_LOCATION_ID="PMgbQ375TEGOyGXsKz7e"

railway variables set VAPI_API_KEY="bb0d907c-0834-420e-932c-f3f25f8221ad"

railway variables set RETELL_API_KEY="key_819a6edef632ded41fe1c1ef7f12"
```

**Or via Railway Dashboard:**
1. Go to https://railway.app/dashboard
2. Select your spectrum-demo project
3. Click "Variables" tab
4. Add each variable manually

### Phase 5: Deploy!

```bash
# Deploy to Railway
railway up

# This will:
# 1. Upload your code
# 2. Install dependencies from requirements.txt
# 3. Start the server with: python brain_server.py
# 4. Health check at /health
```

### Phase 6: Monitor Deployment

```bash
# Watch deployment logs
railway logs

# Get deployment URL
railway status

# Open in browser
railway open
```

---

## 🔧 RAILWAY.TOML CONFIGURATION

Your `railway.toml` is configured with:

```toml
[build]
builder = "NIXPACKS"              # Railway's build system
buildCommand = "pip install -r requirements.txt"

[deploy]
startCommand = "python brain_server.py"  # How to start your app
healthcheckPath = "/health"              # Health check endpoint
healthcheckTimeout = 300                 # 5 minute timeout for startup
restartPolicyType = "ON_FAILURE"         # Auto-restart on crash
restartPolicyMaxRetries = 10             # Max restart attempts
```

---

## 🗄️ DATABASE CONNECTION

Railway automatically provides `DATABASE_URL` when you add PostgreSQL.

**Your brain_server.py already reads it correctly:**
```python
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://brain:brain@localhost:5432/brain_mcp")
```

**Railway's DATABASE_URL format:**
```
postgresql://postgres:password@hostname:5432/railway
```

**No additional configuration needed!**

---

## ⚠️ COMMON ISSUES & SOLUTIONS

### Issue 1: "Address already in use" Error

**Cause:** Hardcoded port instead of reading from environment

**Solution:** ✅ Already fixed! Your server reads PORT from env:
```python
port = int(os.getenv("PORT", 8080))
uvicorn.run(app, host="0.0.0.0", port=port)
```

### Issue 2: "Cannot connect to database"

**Cause:** Wrong DATABASE_URL or database not added

**Solution:**
```bash
# Check if database is added
railway status

# If no database, add it
railway add --database postgresql

# Verify DATABASE_URL is set
railway variables
```

### Issue 3: "Health check failed"

**Cause:**
- Server not starting on correct port
- Database connection failing
- Health endpoint not responding

**Solution:**
```bash
# Check logs for errors
railway logs

# Verify health endpoint works
curl https://your-app.railway.app/health

# Common fixes:
# 1. Check DATABASE_URL is set
# 2. Verify all required env vars are set
# 3. Check requirements.txt has all dependencies
```

### Issue 4: "Build failed"

**Cause:** Missing dependencies or incompatible versions

**Solution:**
```bash
# Railway uses Python 3.11+ by default
# Your requirements.txt is compatible ✅

# If you need specific Python version, add .python-version file:
echo "3.13" > .python-version
git add .python-version
railway up
```

### Issue 5: "Deployment successful but app crashes"

**Cause:** Missing environment variables

**Solution:**
```bash
# List current variables
railway variables

# Check logs for specific error
railway logs --tail 100

# Add missing variables
railway variables set KEY="value"
```

---

## 🔍 DEBUGGING COMMANDS

```bash
# View live logs
railway logs -f

# Check service status
railway status

# List environment variables
railway variables

# Get deployment URL
railway domain

# Restart service
railway service restart

# Shell into running container
railway shell

# Run database migrations
railway run python migrate.py
```

---

## 📊 POST-DEPLOYMENT VERIFICATION

After deployment, verify everything works:

### 1. Health Check
```bash
# Get your deployment URL
RAILWAY_URL=$(railway status | grep "URL" | awk '{print $2}')

# Test health endpoint
curl $RAILWAY_URL/health

# Expected response:
# {"status":"healthy","database":"connected","version":"2.0.0"}
```

### 2. List Agents
```bash
curl "$RAILWAY_URL/agents?client_id=demo"

# Should return 3 demo agents
```

### 3. Test Chat
```bash
curl -X POST $RAILWAY_URL/chat/send \
  -H "Content-Type: application/json" \
  -d '{"client_id":"demo","agent_role":"strategist","message":"Hello!"}'

# Should return Claude response
```

### 4. Check Database
```bash
# Connect to Railway PostgreSQL
railway connect

# Run SQL query to verify agents
SELECT name, role FROM spectrum_agents WHERE client_id = 'demo';

# Should show 3 agents
```

---

## 🎨 CUSTOM DOMAIN SETUP

### Add Custom Domain

```bash
# Via CLI
railway domain add spectrum.yourdomain.com

# Or via Dashboard:
# 1. Go to project settings
# 2. Click "Custom Domains"
# 3. Add your domain
# 4. Update DNS with provided CNAME
```

### Update Frontend

Once deployed, update your frontend's API_BASE:

**File:** `aijesusbro.com/spectrum/src/app.js`

```javascript
// Before (Cloudflare)
const API_BASE = "https://spectrum-api.aijesusbro-brain.workers.dev"

// After (Railway)
const API_BASE = "https://spectrum-demo-production.up.railway.app"

// Or with custom domain
const API_BASE = "https://spectrum.aijesusbro.com"
```

---

## 🔄 CI/CD WITH GITHUB

### Setup Automatic Deployments

1. **Push to GitHub:**
```bash
cd "/Users/aijesusbro/AI Projects/spectrum-demo"

# Initialize git if not already
git init

# Add files
git add .
git commit -m "Initial commit: Spectrum-Demo ready for Railway"

# Create GitHub repo and push
gh repo create spectrum-demo --private --push
```

2. **Connect Railway to GitHub:**
```bash
# Link Railway project to GitHub repo
railway link

# Select your spectrum-demo repo
# Railway will now auto-deploy on every push to main
```

3. **Verify Auto-Deploy:**
```bash
# Make a change
echo "# Updated" >> README.md

# Commit and push
git add .
git commit -m "Test auto-deploy"
git push

# Railway automatically deploys!
# Watch with: railway logs -f
```

---

## 📈 SCALING CONFIGURATION

### Vertical Scaling (More Resources)

```bash
# Via Dashboard:
# 1. Project Settings > Resources
# 2. Increase CPU/Memory
# 3. Save changes

# Railway automatically restarts with new resources
```

### Horizontal Scaling (Multiple Instances)

Edit `railway.toml`:
```toml
[environments.production.deploy]
numReplicas = 3  # Run 3 instances

# Railway automatically load balances
```

---

## 💰 COST ESTIMATION

**Railway Pricing (Hobby Plan - $5/month):**
- 500 execution hours/month
- 8GB RAM
- 8 vCPU
- Unlimited bandwidth
- PostgreSQL included

**For Spectrum-Demo:**
- FastAPI server: ~$0.50/month (24/7)
- PostgreSQL: ~$5/month (included in plan)
- **Total: ~$5/month** (if you have Hobby plan)

**Free Tier:**
- $5 free credit/month
- Perfect for testing!

---

## 🎯 DEPLOYMENT CHECKLIST

Before deploying, verify:

- [ ] Railway CLI installed and logged in
- [ ] `requirements.txt` has all dependencies
- [ ] `railway.toml` configured
- [ ] Environment variables ready to set
- [ ] PostgreSQL will be added as service
- [ ] Health check endpoint at `/health`
- [ ] Server binds to 0.0.0.0 and reads PORT from env
- [ ] `.env` file NOT committed to git (in .gitignore)

After deploying, verify:

- [ ] Health check returns `{"status":"healthy"}`
- [ ] `/agents` endpoint returns 3 demo agents
- [ ] `/chat/send` returns Claude responses
- [ ] Database connection working
- [ ] All environment variables set correctly
- [ ] Logs show no errors

---

## 🚀 QUICK START (FASTEST PATH)

```bash
# 1. Install Railway CLI
npm i -g @railway/cli

# 2. Login
export RAILWAY_TOKEN=e2b95fb3-364c-4fef-8fd2-abc75f7bf28a
railway login

# 3. Initialize project
cd "/Users/aijesusbro/AI Projects/spectrum-demo"
railway init

# 4. Add PostgreSQL
railway add --database postgresql

# 5. Set environment variables
railway variables set ANTHROPIC_API_KEY="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"
railway variables set GHL_API_KEY="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJsb2NhdGlvbl9pZCI6IlBNZ2JRMzc1VEVHT3lHWHNLejdlIiwidmVyc2lvbiI6MSwiaWF0IjoxNzU3NDU2NTUwMTIyLCJzdWIiOiJ5OXFxZjNIV0FYVGk5Nk1wZXVqZiJ9.nbuFjgIZ1hnsHLPDj5IsiUlxR5DgecMw1l56LCEZEjo"
railway variables set GHL_LOCATION_ID="PMgbQ375TEGOyGXsKz7e"
railway variables set VAPI_API_KEY="bb0d907c-0834-420e-932c-f3f25f8221ad"
railway variables set RETELL_API_KEY="key_819a6edef632ded41fe1c1ef7f12"

# 6. Deploy!
railway up

# 7. Watch deployment
railway logs -f

# 8. Get URL
railway status

# 9. Test
curl $(railway domain)/health
```

**Deployment time: ~3-5 minutes** ⚡

---

## 📞 SUPPORT & TROUBLESHOOTING

### Railway Support
- Docs: https://docs.railway.com
- Discord: https://discord.gg/railway
- Status: https://status.railway.com

### Spectrum-Demo Issues

**If deployment fails:**
1. Check `railway logs` for errors
2. Verify all env vars are set: `railway variables`
3. Ensure PostgreSQL is added: `railway status`
4. Test locally first: `python brain_server.py`

**If health check fails:**
1. Check DATABASE_URL is set
2. Verify database is accessible
3. Check server logs for startup errors
4. Test `/health` endpoint directly

**If agents don't work:**
1. Run seed script: `railway run python seed_now.py`
2. Verify agents in database
3. Check ANTHROPIC_API_KEY is set
4. Test chat endpoint manually

---

## 🎉 SUCCESS!

Once deployed, you'll have:

✅ **Production API** at https://spectrum-demo-production.up.railway.app
✅ **PostgreSQL Database** with 3 demo agents
✅ **Claude Haiku 4.5** integration
✅ **Auto-scaling** and auto-restart
✅ **Health monitoring** at /health
✅ **24/7 uptime** with Railway infrastructure

**Next:** Update your frontend to point to the Railway URL and you're live! 🚀

---

**Questions? Check the logs first, then consult Railway docs!**
