# 🚀 ClearVC Amber Brain - Railway Deployment Guide

## Quick Deploy (No CLI needed!)

### 1. Prepare the Code
```bash
cd ClearVC/amber-brain
git init
git add .
git commit -m "Initial ClearVC Amber Brain"
```

### 2. Create GitHub Repository
- Go to https://github.com/new
- Name: `clearvc-amber-brain`
- Make it private
- Don't initialize with README (we have one)

```bash
git remote add origin https://github.com/YOUR_USERNAME/clearvc-amber-brain.git
git push -u origin main
```

### 3. Deploy to Railway (Web Interface)

1. **Go to Railway**
   - Visit https://railway.app
   - Sign in / Sign up

2. **New Project**
   - Click "New Project"
   - Select "Deploy from GitHub repo"
   - Connect your GitHub if needed
   - Select `clearvc-amber-brain` repo

3. **Add PostgreSQL**
   - In your project, click "New"
   - Select "Database"
   - Choose "PostgreSQL"
   - Railway auto-connects it!

4. **Set Environment Variables**
   Click on your service, go to "Variables" tab, add:

   ```
   # These are REQUIRED:
   RETELL_API_KEY=your_retell_api_key
   GHL_API_KEY=clearvc_ghl_api_key
   GHL_LOCATION_ID=clearvc_location_id
   OPENAI_API_KEY=your_openai_key

   # Optional but recommended:
   TELEGRAM_BOT_TOKEN=clearvc_telegram_token
   TELEGRAM_CHAT_ID=clearvc_chat_id

   # Railway provides these automatically:
   DATABASE_URL=(auto-set by Railway)
   PORT=(auto-set by Railway)
   ```

5. **Generate Domain**
   - Go to "Settings" tab
   - Under "Domains" click "Generate Domain"
   - You'll get something like: `clearvc-amber-brain.up.railway.app`

### 4. Configure Retell Agent

In your Retell dashboard, set the webhook URLs to:

```
Base URL: https://clearvc-amber-brain.up.railway.app

Webhooks:
- Call Start:  https://clearvc-amber-brain.up.railway.app/webhooks/retell/call-started
- Call End:    https://clearvc-amber-brain.up.railway.app/webhooks/retell/call-ended
- Transcript:  https://clearvc-amber-brain.up.railway.app/webhooks/retell/transcript-update
- Tool Call:   https://clearvc-amber-brain.up.railway.app/webhooks/retell/tool-call
```

### 5. Test Your Deployment

Once deployed, test the health endpoint:
```bash
curl https://clearvc-amber-brain.up.railway.app/health
```

Should return:
```json
{
  "status": "healthy",
  "timestamp": "2024-01-15T...",
  "services": {
    "database": true,
    "redis": true,
    "ghl": true
  }
}
```

## 📊 Monitor Your Deployment

### View Logs
- In Railway dashboard, click on your service
- Go to "Logs" tab
- Watch real-time logs

### Check Metrics
- "Metrics" tab shows CPU, Memory, Network usage

### Manage Deployment
- Automatic deploys on git push
- Can disable auto-deploy in Settings
- Manual redeploy button available

## 🔧 Troubleshooting

### If deployment fails:
1. Check logs for errors
2. Verify all environment variables are set
3. Make sure PostgreSQL is attached

### If webhooks aren't working:
1. Verify the domain is active
2. Check Retell agent configuration
3. Test with: `curl -X POST [your-domain]/webhooks/retell/call-started -H "Content-Type: application/json" -d '{"test": true}'`

### Database issues:
- Railway auto-manages PostgreSQL
- Connection string is in DATABASE_URL
- Can view/query in Railway's database plugin

## 🎉 Success!

Once everything is green in Railway:
1. Your brain is running independently
2. No dependency on your MCP infrastructure
3. Auto-scaling handled by Railway
4. SSL/HTTPS included automatically
5. ClearVC has their own dedicated brain!

## 💰 Costs
- Railway Free Tier: $5 credit/month
- Typical usage: ~$10-20/month for this setup
- Scales automatically with usage

## 🚀 Next Steps
1. Test with a real Retell call
2. Monitor logs during calls
3. Check GHL integration working
4. Verify notifications sending