#!/bin/bash
# Quick deployment of the brain to Digital Ocean

DROPLET_IP="64.23.221.37"
echo "🚀 Deploying Brain to $DROPLET_IP"

# First, let's add our SSH key to the droplet via console
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "⚠️  MANUAL STEP NEEDED:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Go to Digital Ocean Console:"
echo "1. Click on droplet 'brain-aijesusbro'"
echo "2. Go to Access → Reset root password"
echo "3. Check your email for the password"
echo "4. Or use Access → Launch Droplet Console"
echo ""
echo "Then in the console, run these commands:"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "COPY AND PASTE THESE COMMANDS:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
cat << 'COMMANDS'

# Update system
apt update && apt install -y docker.io docker-compose git python3-pip

# Create brain directory
mkdir -p /opt/brain
cd /opt/brain

# Create docker-compose.yml
cat > docker-compose.yml << 'EOF'
version: '3.8'

services:
  postgres:
    image: postgres:15-alpine
    environment:
      POSTGRES_USER: brain
      POSTGRES_PASSWORD: brain_secure_2024
      POSTGRES_DB: aijesusbro_brain
    volumes:
      - postgres_data:/var/lib/postgresql/data
    restart: unless-stopped

  redis:
    image: redis:7-alpine
    restart: unless-stopped

  brain:
    image: python:3.11-slim
    ports:
      - "8080:8080"
    environment:
      DATABASE_URL: postgresql://brain:brain_secure_2024@postgres:5432/aijesusbro_brain
      REDIS_URL: redis://redis:6379
      GHL_API_KEY: "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJsb2NhdGlvbl9pZCI6IlBNZ2JRMzc1VEVHT3lHWHNLejdlIiwidmVyc2lvbiI6MSwiaWF0IjoxNzU3NDU2NTUwMTIyLCJzdWIiOiJ5OXFxZjNIV0FYVGk5Nk1wZXVqZiJ9.nbuFjgIZ1hnsHLPDj5IsiUlxR5DgecMw1l56LCEZEjo"
      GHL_LOCATION_ID: "PMgbQ375TEGOyGXsKz7e"
      RETELL_API_KEY: "key_819a6edef632ded41fe1c1ef7f12"
      PORT: 8080
    volumes:
      - ./app:/app
    working_dir: /app
    command: sh -c "pip install fastapi uvicorn httpx asyncpg redis psycopg2-binary aiohttp && python brain_server.py"
    depends_on:
      - postgres
      - redis
    restart: unless-stopped

volumes:
  postgres_data:
EOF

# Create minimal brain server
mkdir -p app
cat > app/brain_server.py << 'EOF'
#!/usr/bin/env python3
import os
import json
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
import uvicorn
import httpx
from datetime import datetime

app = FastAPI(title="AI Jesus Bro Brain")

# Config
GHL_API_KEY = os.getenv("GHL_API_KEY")
GHL_LOCATION_ID = os.getenv("GHL_LOCATION_ID")
RETELL_API_KEY = os.getenv("RETELL_API_KEY")

@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "version": "2.0.0",
        "location": "Digital Ocean Production",
        "timestamp": datetime.now().isoformat()
    }

@app.post("/webhooks/retell")
async def retell_webhook(request: Request):
    """Handle Retell webhooks"""
    try:
        data = await request.json()
        event_type = data.get("event")

        if event_type == "call_started":
            # Caller ID lookup
            phone = data.get("from_number", "")
            print(f"Call started from {phone}")

        elif event_type == "call_ended":
            # Process transcript and update GHL
            call_id = data.get("call_id")
            transcript = data.get("transcript", "")
            print(f"Call ended: {call_id}")

            # Here we'd do all the GHL automation
            # For now, just acknowledge

        return JSONResponse({"status": "processed", "event": event_type})

    except Exception as e:
        print(f"Error processing webhook: {e}")
        return JSONResponse({"status": "error", "message": str(e)}, status_code=500)

@app.post("/webhooks/ghl")
async def ghl_webhook(request: Request):
    """Handle GHL webhooks"""
    data = await request.json()
    return JSONResponse({"status": "processed"})

@app.post("/sse")
async def sse_endpoint(request: Request):
    """MCP endpoint"""
    data = await request.json()
    method = data.get("method")

    if method == "tools/call":
        tool_name = data.get("params", {}).get("name")
        return JSONResponse({
            "jsonrpc": "2.0",
            "result": {"status": "ok", "tool": tool_name},
            "id": data.get("id", 1)
        })

    return JSONResponse({
        "jsonrpc": "2.0",
        "result": {"status": "ok"},
        "id": data.get("id", 1)
    })

if __name__ == "__main__":
    print("🧠 AI Jesus Bro Brain Starting...")
    print(f"GHL Location: {GHL_LOCATION_ID}")
    print(f"Retell Configured: {'Yes' if RETELL_API_KEY else 'No'}")
    uvicorn.run(app, host="0.0.0.0", port=8080)
EOF

# Start the stack
docker-compose up -d

# Check status
docker-compose ps

echo "✅ Brain deployed! Testing..."
sleep 5
curl http://localhost:8080/health

COMMANDS

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "After running these commands, the brain will be live at:"
echo "http://$DROPLET_IP:8080"
echo ""
echo "Then update Retell webhook to:"
echo "http://$DROPLET_IP:8080/webhooks/retell"