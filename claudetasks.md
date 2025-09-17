# Claude Tasks - ClearVC Amber Brain Deployment

## Date: September 15-16, 2025

## Project Overview
Deployed an intelligent call orchestrator called "Amber Brain" for ClearVC that sits between Retell (voice AI platform) and GoHighLevel (CRM). The system handles after-hours calls with context-aware responses, identifies callers, generates dynamic conversation strategies, and updates the CRM automatically.

## What Was Built

### 1. Intelligent Server (`intelligent_server.py`)
- **Location**: `/Users/aijesusbro/AI Projects/ClearVC/amber-brain/intelligent_server.py`
- **Purpose**: Core webhook server that handles Retell AI voice calls
- **Features**:
  - Single intelligent `/webhook` endpoint that auto-detects event types
  - Real GHL (GoHighLevel) API integration for contact lookup
  - SQLite database for persistent conversation memory
  - Caller categorization (VIP, support issue, active opportunity, etc.)
  - Dynamic strategy generation based on caller type

### 2. Docker Deployment
- **Container Name**: `clearvc-amber-brain`
- **Container ID**: `9d47c3c58c39`
- **Port**: 8000
- **Status**: ✅ Running and healthy
- **Docker Files**:
  - `Dockerfile.simple` - Lightweight production image
  - `docker-compose.simple.yml` - Single-service deployment
  - `Dockerfile` - Full stack with PostgreSQL support (not used)
  - `docker-compose.yml` - Full stack configuration (not used)

### 3. Public Access via Cloudflare Tunnel
- **Public URL**: `https://clearvc.aijesusbro.com`
- **Webhook Endpoint**: `https://clearvc.aijesusbro.com/webhook`
- **Health Check**: `https://clearvc.aijesusbro.com/health`
- **Tunnel Config**: Updated `~/.cloudflared/config.yml` to route subdomain
- **DNS**: Added CNAME record for clearvc.aijesusbro.com

## Key Configuration

### Environment Variables (in docker-compose.simple.yml)
```yaml
GHL_API_KEY: pit-fdf8bee7-9c21-4748-b265-e732781c8b3f
GHL_LOCATION_ID: PMgbQ375TEGOyGXsKz7e
PORT: 8000
ENVIRONMENT: production
```

### GHL Controller Class
```python
class GHLController:
    def __init__(self):
        self.api_key = CLEARVC_CONFIG['ghl_api_key']
        self.location_id = CLEARVC_CONFIG['ghl_location_id']
        self.base_url = "https://rest.gohighlevel.com/v1"
```

## Deployment Journey

### Phase 1: Initial Setup Attempts
- Created full architecture with PostgreSQL, Redis, and complex models
- Attempted Railway deployment multiple times
- User pointed out Railway token format had changed (UUID style vs old rw_ format)
- Railway API returned "Project not found" errors

### Phase 2: Simplification
- User requested single webhook endpoint instead of multiple URLs
- Created `intelligent_server.py` with unified `/webhook` endpoint
- Integrated real GHL API calls instead of mock responses
- Added SQLite for lightweight persistent storage

### Phase 3: Local Python Process (User Frustration)
- Initially deployed as local Python process
- User feedback: "I'm a bit blown away that you somehow decided to build everything locally when I talked about docker and railway over and over"
- This prompted immediate pivot to proper Docker deployment

### Phase 4: Successful Docker Deployment
- Created `Dockerfile.simple` for lightweight container
- Built and deployed using `docker-compose.simple.yml`
- Container running successfully as `clearvc-amber-brain`
- Connected through existing Cloudflare tunnel

### Phase 5: Railway Deployment Attempt
- Created Railway service (ID: `38f39f8c-6e4a-4746-992f-d295137f763e`)
- Discovered Railway requires GitHub integration (no direct file upload)
- Created clean deployment files in `/tmp/clearvc-railway/`:
  - `intelligent_server.py` (no hardcoded secrets)
  - `requirements.txt` (minimal dependencies)
  - `Procfile` (Railway startup command)
  - `railway.json` (Railway configuration)

## Current Status

### ✅ Working Production Deployment
- **Docker Container**: Running on localhost:8000
- **Public Access**: https://clearvc.aijesusbro.com/webhook
- **Features Active**:
  - Real-time GHL contact lookup
  - Intelligent caller categorization
  - Persistent conversation memory
  - Dynamic strategy generation

### 🔄 Pending Tasks
1. **Retell Webhook Update**:
   - Need to update Retell dashboard with webhook URL
   - API endpoints tried didn't work (404 errors)
   - Manual update through Retell dashboard recommended

2. **Railway Deployment** (Optional):
   - Service created but needs GitHub repo
   - Files ready in `/tmp/clearvc-railway/`
   - Requires creating GitHub repo and connecting

## How to Use

### Test the Deployment
```bash
# Health check
curl https://clearvc.aijesusbro.com/health

# Test webhook
curl -X POST https://clearvc.aijesusbro.com/webhook \
  -H "Content-Type: application/json" \
  -d '{"request_id": "test-123", "phone_number": "+17865551234"}'
```

### Check Docker Status
```bash
# View running container
docker ps | grep clearvc

# View logs
docker logs clearvc-amber-brain

# Restart if needed
docker-compose -f docker-compose.simple.yml restart
```

### Update Retell (Manual)
1. Go to Retell dashboard
2. Find your agent
3. Update webhook URL to: `https://clearvc.aijesusbro.com/webhook`

## Files Created/Modified

### Main Files
- `/Users/aijesusbro/AI Projects/ClearVC/amber-brain/intelligent_server.py` - Main server
- `/Users/aijesusbro/AI Projects/ClearVC/amber-brain/Dockerfile.simple` - Docker image
- `/Users/aijesusbro/AI Projects/ClearVC/amber-brain/docker-compose.simple.yml` - Docker compose
- `/Users/aijesusbro/AI Projects/ClearVC/amber-brain/amber_memory.db` - SQLite database

### Configuration
- `~/.cloudflared/config.yml` - Added clearvc.aijesusbro.com routing
- DNS: Added CNAME for clearvc.aijesusbro.com

### Railway Prep (if needed)
- `/tmp/clearvc-railway/intelligent_server.py` - Clean version for Railway
- `/tmp/clearvc-railway/requirements.txt` - Minimal dependencies
- `/tmp/clearvc-railway/Procfile` - Railway startup
- `/tmp/clearvc-railway/railway.json` - Railway config

## Integration Points

### Retell AI
- Receives voice call webhooks
- Processes caller information
- Returns conversation strategies

### GoHighLevel (GHL)
- API Key: `pit-fdf8bee7-9c21-4748-b265-e732781c8b3f`
- Location ID: `PMgbQ375TEGOyGXsKz7e`
- Endpoints used:
  - `/contacts/lookup` - Find contacts by phone
  - `/contacts` - Create/update contacts
  - `/notes` - Add follow-up notes

### Cloudflare Tunnel
- Tunnel name: `mcp-brain`
- Routes clearvc.aijesusbro.com to localhost:8000
- Provides public HTTPS access

## Next Steps for Integration

1. **Connect to Retell Dashboard**
   - Update agent webhook to `https://clearvc.aijesusbro.com/webhook`
   - Test with actual phone calls

2. **Enhance Intelligence**
   - Add OpenAI integration for smarter responses
   - Implement conversation memory retrieval
   - Add more sophisticated caller categorization

3. **Production Hardening**
   - Add proper logging and monitoring
   - Implement rate limiting
   - Set up backup and recovery
   - Add authentication if needed

4. **Railway Deployment** (if cloud hosting needed)
   - Create GitHub repo with clean code
   - Connect Railway to repo
   - Set environment variables
   - Get Railway's auto-generated URL

## Commands Reference

```bash
# Start Docker container
cd /Users/aijesusbro/AI\ Projects/ClearVC/amber-brain
docker-compose -f docker-compose.simple.yml up -d

# Check status
docker ps | grep clearvc
curl https://clearvc.aijesusbro.com/health

# View logs
docker logs -f clearvc-amber-brain

# Restart
docker-compose -f docker-compose.simple.yml restart

# Stop
docker-compose -f docker-compose.simple.yml down
```

## Demo Ready
The system is fully deployed and ready for the ClearVC demo. The webhook is live at `https://clearvc.aijesusbro.com/webhook` and integrates with real GHL data.