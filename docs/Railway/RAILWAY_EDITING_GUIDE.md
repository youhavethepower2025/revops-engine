# ✏️ Railway Editing & Management Guide

**How to edit, update, and manage your spectrum-demo deployment on Railway**

---

## 🎯 OVERVIEW

Once deployed to Railway, you have multiple ways to edit and update your application:

1. **Code Changes** - Update code and redeploy
2. **Environment Variables** - Change config without redeploying
3. **Database Operations** - Seed agents, run queries, migrations
4. **Agent Prompts** - Update agent behavior in production
5. **Hot Fixes** - Quick patches and rollbacks

---

## 1️⃣ CODE CHANGES & REDEPLOYMENT

### Method A: Git Push (Recommended for CI/CD)

**If connected to GitHub:**

```bash
cd "/Users/aijesusbro/AI Projects/spectrum-demo"

# Make your changes to brain_server.py or any file
nano brain_server.py

# Commit and push
git add .
git commit -m "Update: your change description"
git push

# Railway automatically detects push and redeploys!
# Watch deployment: railway logs -f
```

**Advantages:**
- Automatic deployment on push
- Git history of all changes
- Easy rollbacks to previous commits
- Team collaboration ready

### Method B: Railway CLI (Faster for quick changes)

**Direct deployment without git:**

```bash
cd "/Users/aijesusbro/AI Projects/spectrum-demo"

# Make your changes
nano brain_server.py

# Deploy directly to Railway
railway up

# Watch deployment
railway logs -f
```

**Advantages:**
- Faster than git workflow
- Good for testing changes
- No git commit required

### Method C: Railway Dashboard (Web-based editing)

**Edit files directly in Railway UI:**

1. Go to https://railway.app/dashboard
2. Select your spectrum-demo project
3. Click on your service
4. Go to "Settings" → "Service Settings"
5. Use the file browser to edit files

**Advantages:**
- No local development needed
- Quick fixes from anywhere
- Good for emergencies

**Disadvantages:**
- No local testing before deploy
- Harder to manage complex changes

---

## 2️⃣ ENVIRONMENT VARIABLES

### View Current Variables

```bash
# List all environment variables
railway variables

# Or via Railway Dashboard:
# Project → Variables tab
```

### Add New Variable

```bash
# Via CLI
railway variables set NEW_KEY="new_value"

# Example: Add new API key
railway variables set OPENAI_API_KEY="sk-..."

# Service restarts automatically with new variable
```

### Update Existing Variable

```bash
# Update ANTHROPIC_API_KEY
railway variables set ANTHROPIC_API_KEY="sk-ant-new-key..."

# Automatic restart to pick up new value
```

### Delete Variable

```bash
# Via CLI
railway variables delete KEY_NAME

# Or via Dashboard:
# Project → Variables → Click X next to variable
```

### Bulk Variable Updates

Create a file with all variables:

```bash
# Create variables.txt
cat > variables.txt <<EOF
ANTHROPIC_API_KEY=sk-ant-...
GHL_API_KEY=ey...
GHL_LOCATION_ID=PMgb...
VAPI_API_KEY=bb0d...
RETELL_API_KEY=key_...
EOF

# Apply all variables
while IFS='=' read -r key value; do
  railway variables set "$key"="$value"
done < variables.txt
```

**IMPORTANT:** Variables take effect immediately, causing a service restart!

---

## 3️⃣ DATABASE OPERATIONS

### Connect to PostgreSQL

```bash
# Open psql shell
railway connect

# Or get connection string
railway variables | grep DATABASE_URL
```

### Seed Agents in Production

```bash
# Method 1: Run seed script remotely
railway run python seed_now.py

# Method 2: Connect and run SQL
railway connect
\i /path/to/seed_agents.sql
```

### View Agents

```bash
railway connect

# Once in psql:
SELECT id, name, role, enabled
FROM spectrum_agents
WHERE client_id = 'demo';
```

### Update Agent Prompt

**Option A: Via SQL**

```bash
railway connect

UPDATE spectrum_agents
SET system_prompt = 'Your new prompt here...'
WHERE role = 'strategist' AND client_id = 'demo';
```

**Option B: Via API Endpoint**

```bash
# Get your Railway URL
RAILWAY_URL=$(railway domain)

# Update agent prompt
curl -X PUT "$RAILWAY_URL/admin/agents/strategist?client_id=demo" \
  -H "Content-Type: application/json" \
  -d '{
    "system_prompt": "You are a strategic advisor with new instructions..."
  }'
```

**Option C: Update in Code and Redeploy**

```bash
# Edit seed_agents.sql locally
nano seed_agents.sql

# Commit and push
git add seed_agents.sql
git commit -m "Update strategist prompt"
git push

# Re-seed in production
railway run python seed_now.py
```

### Run Database Migrations

```bash
# Create migration script
cat > migrate.py <<EOF
import asyncio
import asyncpg
import os

async def migrate():
    conn = await asyncpg.connect(os.getenv('DATABASE_URL'))

    # Add new column
    await conn.execute("""
        ALTER TABLE spectrum_agents
        ADD COLUMN IF NOT EXISTS new_field TEXT;
    """)

    print("✅ Migration complete")
    await conn.close()

asyncio.run(migrate())
EOF

# Run migration on Railway
railway run python migrate.py
```

### Backup Database

```bash
# Get database connection info
railway variables | grep DATABASE_URL

# Export to local file
pg_dump $(railway variables | grep DATABASE_URL | cut -d'=' -f2-) > backup.sql

# Or via Railway CLI
railway run pg_dump > backup.sql
```

### Restore Database

```bash
# From local backup
cat backup.sql | railway connect

# Or
psql $(railway variables | grep DATABASE_URL | cut -d'=' -f2-) < backup.sql
```

---

## 4️⃣ EDITING AGENT PROMPTS IN PRODUCTION

### Method 1: Admin API Endpoint (Easiest)

```bash
RAILWAY_URL=$(railway domain)

# Update Strategic Advisor
curl -X PUT "$RAILWAY_URL/admin/agents/strategist?client_id=demo" \
  -H "Content-Type: application/json" \
  -d @- <<EOF
{
  "system_prompt": "You are a strategic advisor focused on AI-first business transformation.

Your approach:
- Challenge conventional thinking about AI adoption
- Focus on competitive moats in an AI-driven world
- Help leaders think 10x, not 10%
- Identify where AI creates leverage vs busywork

Remember:
- Be direct and challenging, not diplomatic
- Use first principles thinking
- Focus on strategic advantages that AI enables

Current date: {current_date}"
}
EOF
```

### Method 2: Direct SQL Update

```bash
railway connect

UPDATE spectrum_agents
SET system_prompt = 'New prompt text here...',
    updated_at = CURRENT_TIMESTAMP
WHERE role = 'strategist' AND client_id = 'demo';

# Verify update
SELECT name, LEFT(system_prompt, 100) as prompt_preview
FROM spectrum_agents
WHERE role = 'strategist';
```

### Method 3: Python Script

```bash
# Create update_agent.py
cat > update_agent.py <<EOF
import asyncio
import asyncpg
import os

async def update_agent(role, new_prompt):
    conn = await asyncpg.connect(os.getenv('DATABASE_URL'))

    await conn.execute("""
        UPDATE spectrum_agents
        SET system_prompt = \$1, updated_at = CURRENT_TIMESTAMP
        WHERE role = \$2 AND client_id = 'demo'
    """, new_prompt, role)

    print(f"✅ Updated {role} agent")
    await conn.close()

new_prompt = """
You are a strategic advisor...
[Full prompt here]
"""

asyncio.run(update_agent('strategist', new_prompt))
EOF

# Run on Railway
railway run python update_agent.py
```

### Method 4: Environment Variable Prompts (Advanced)

**For frequently changing prompts:**

```python
# In brain_server.py, modify agent loading:
system_prompt = os.getenv(f"{role.upper()}_PROMPT", agent['system_prompt'])
```

Then update via Railway variables:

```bash
railway variables set STRATEGIST_PROMPT="Your new prompt..."

# No code deploy needed!
```

---

## 5️⃣ HOT FIXES & ROLLBACKS

### Quick Hotfix Process

```bash
# 1. Make quick fix
nano brain_server.py

# 2. Test locally (if possible)
python brain_server.py

# 3. Deploy immediately
railway up

# 4. Monitor logs
railway logs -f

# 5. Test in production
curl $(railway domain)/health
```

### Rollback to Previous Version

**If using GitHub:**

```bash
# View recent commits
git log --oneline -5

# Rollback to specific commit
git revert <commit-hash>
git push

# Or hard reset (dangerous!)
git reset --hard <commit-hash>
git push --force
```

**Via Railway Dashboard:**

1. Go to your service
2. Click "Deployments" tab
3. Find previous successful deployment
4. Click "Redeploy"

### Emergency Restart

```bash
# Restart service without redeploying
railway service restart

# Watch logs
railway logs -f
```

### Disable Service (Emergency)

```bash
# Via Railway Dashboard:
# Service → Settings → Pause Service

# Or via CLI (if available)
railway service stop
```

---

## 6️⃣ LIVE DEBUGGING

### View Real-Time Logs

```bash
# Follow logs in real-time
railway logs -f

# Filter logs
railway logs -f | grep ERROR

# Last 100 lines
railway logs --tail 100
```

### Shell Into Running Container

```bash
# Open shell in production container
railway shell

# Once inside:
ls -la
cat brain_server.py
python
>>> import asyncpg
>>> # Test database connection
```

### Run One-Off Commands

```bash
# Execute command in production environment
railway run python -c "import asyncpg; print('Connected!')"

# Run database query
railway run python -c "
import asyncio, asyncpg, os
async def test():
    conn = await asyncpg.connect(os.getenv('DATABASE_URL'))
    result = await conn.fetchval('SELECT COUNT(*) FROM spectrum_agents')
    print(f'Agents: {result}')
asyncio.run(test())
"
```

### Test Endpoints

```bash
# Get Railway URL
RAILWAY_URL=$(railway domain)

# Test health
curl $RAILWAY_URL/health

# Test agents
curl "$RAILWAY_URL/agents?client_id=demo"

# Test chat
curl -X POST $RAILWAY_URL/chat/send \
  -H "Content-Type: application/json" \
  -d '{"client_id":"demo","agent_role":"strategist","message":"Test"}'
```

---

## 7️⃣ SCALING & PERFORMANCE

### Vertical Scaling (More Resources)

```bash
# Via Railway Dashboard:
# Project → Service → Settings → Resources
# Adjust CPU/Memory sliders
# Click "Save"
```

### Horizontal Scaling (More Instances)

Edit `railway.toml`:

```toml
[environments.production.deploy]
numReplicas = 3  # Run 3 instances
```

```bash
# Commit and push
git add railway.toml
git commit -m "Scale to 3 instances"
git push
```

### Monitor Performance

```bash
# Check metrics
railway metrics

# Or via Dashboard:
# Project → Service → Metrics tab
```

---

## 8️⃣ COMMON WORKFLOWS

### Workflow 1: Update Agent Prompt

```bash
# 1. Update via API
RAILWAY_URL=$(railway domain)
curl -X PUT "$RAILWAY_URL/admin/agents/strategist?client_id=demo" \
  -H "Content-Type: application/json" \
  -d '{"system_prompt":"New prompt..."}'

# 2. Test immediately
curl -X POST $RAILWAY_URL/chat/send \
  -H "Content-Type: application/json" \
  -d '{"client_id":"demo","agent_role":"strategist","message":"Test new prompt"}'

# 3. If good, update seed_agents.sql locally
nano seed_agents.sql

# 4. Commit for future deployments
git add seed_agents.sql
git commit -m "Update strategist prompt"
git push
```

### Workflow 2: Add New Environment Variable

```bash
# 1. Add variable
railway variables set NEW_API_KEY="value"

# 2. Update code to use it
nano brain_server.py
# Add: NEW_API_KEY = os.getenv("NEW_API_KEY")

# 3. Deploy updated code
git add brain_server.py
git commit -m "Add support for NEW_API_KEY"
git push

# 4. Test
railway logs -f
```

### Workflow 3: Database Schema Change

```bash
# 1. Create migration script
cat > migrations/add_field.py <<EOF
import asyncio, asyncpg, os
async def migrate():
    conn = await asyncpg.connect(os.getenv('DATABASE_URL'))
    await conn.execute("ALTER TABLE spectrum_agents ADD COLUMN tags JSONB DEFAULT '[]'")
    await conn.close()
asyncio.run(migrate())
EOF

# 2. Run migration
railway run python migrations/add_field.py

# 3. Update code to use new field
nano brain_server.py

# 4. Deploy
git push

# 5. Verify
railway connect
\d spectrum_agents
```

### Workflow 4: Quick Fix Emergency

```bash
# 1. Make fix
nano brain_server.py

# 2. Deploy immediately (skip git)
railway up

# 3. Monitor
railway logs -f

# 4. Once stable, commit properly
git add brain_server.py
git commit -m "Hotfix: description"
git push
```

---

## 9️⃣ BEST PRACTICES

### Do's ✅

- **Test locally first** before deploying
- **Use git commits** for all code changes
- **Monitor logs** after deployment
- **Backup database** before schema changes
- **Test endpoints** after updates
- **Document changes** in commit messages
- **Use staging environment** for risky changes

### Don'ts ❌

- **Don't edit production files** directly in Railway dashboard
- **Don't hardcode secrets** - use environment variables
- **Don't deploy without testing** health endpoint
- **Don't skip database backups** before migrations
- **Don't force push** to main branch in production
- **Don't delete DATABASE_URL** variable (Railway auto-sets it)

---

## 🔟 TROUBLESHOOTING

### "Changes not reflecting"

```bash
# 1. Verify deployment succeeded
railway logs | grep "Deployment successful"

# 2. Hard refresh deployment
railway service restart

# 3. Check correct service
railway status

# 4. Verify variables
railway variables
```

### "Can't connect to database"

```bash
# 1. Check DATABASE_URL exists
railway variables | grep DATABASE_URL

# 2. Verify PostgreSQL service running
railway status

# 3. Test connection
railway connect

# 4. Check logs for errors
railway logs | grep -i database
```

### "Agent prompts not updating"

```bash
# 1. Verify update applied
railway connect
SELECT system_prompt FROM spectrum_agents WHERE role = 'strategist';

# 2. Check updated_at timestamp
SELECT role, updated_at FROM spectrum_agents;

# 3. Test via API
curl "$RAILWAY_URL/admin/agents/strategist?client_id=demo"
```

---

## 📊 SUMMARY

You can edit your Railway deployment through:

1. **Code:** Git push or `railway up`
2. **Variables:** `railway variables set`
3. **Database:** `railway connect` or `railway run python script.py`
4. **Agents:** API endpoint, SQL, or redeploy
5. **Emergency:** `railway service restart` or rollback

**Most common editing tasks:**

```bash
# Update code
git push                                           # Auto-deploys

# Update environment variable
railway variables set KEY="value"                  # Auto-restarts

# Update agent prompt
curl -X PUT $URL/admin/agents/role                 # Instant

# Database operation
railway run python script.py                       # Immediate

# View logs
railway logs -f                                    # Real-time
```

---

**You have full control over your Railway deployment! 🚀**
