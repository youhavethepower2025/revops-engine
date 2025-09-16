# 🚀 Deploy ClearVC to Railway - SIMPLE STEPS

## Option 1: Railway Web Deploy (Easiest!)

### Step 1: Package the code
```bash
cd "/Users/aijesusbro/AI Projects/ClearVC/amber-brain"
tar -czf clearvc-brain.tar.gz *
```

### Step 2: Deploy on Railway
1. Go to https://railway.app
2. Click "New Project"
3. Click "Empty Project"
4. Click "Add Service" → "Empty Service"
5. Go to Settings → click "Generate Domain" to get your URL
6. Go to Variables tab, add these:
   ```
   RETELL_API_KEY=your_retell_key
   GHL_API_KEY=clearvc_ghl_key
   GHL_LOCATION_ID=clearvc_location
   OPENAI_API_KEY=your_openai_key
   ```
7. Deploy tab → "Upload a ZIP" → upload the tar.gz file

### Step 3: Add PostgreSQL
1. In same project, click "New"
2. Select "Database" → "PostgreSQL"
3. It auto-connects!

Your URL will be something like:
`https://clearvc-amber-brain-production.up.railway.app`

---

## Option 2: Use Render.com (Alternative)

1. Go to https://render.com
2. New → Web Service
3. "Deploy an existing image from a registry"
4. Build from GitHub repo (can create via web)
5. Free tier available!

---

## Option 3: Deploy Locally First (Testing)

Run ClearVC brain locally and use ngrok for testing:

```bash
# Start locally
cd "/Users/aijesusbro/AI Projects/ClearVC/amber-brain"
./deploy.sh

# In another terminal, expose with ngrok
ngrok http 8000
```

You'll get URL like: `https://abc123.ngrok.io`

---

## Update Retell Agent

Once deployed, run this to update webhooks:

```bash
cd "/Users/aijesusbro/AI Projects/ClearVC/amber-brain"
python update_retell_agent.py
```

Enter:
- Agent ID (find in Retell dashboard)
- Railway URL from above

---

## Test Your Deployment

```bash
# Test health
curl https://your-railway-url.up.railway.app/health

# Should return:
# {"status": "healthy", ...}
```

That's it! ClearVC has their own brain running independently! 🎉