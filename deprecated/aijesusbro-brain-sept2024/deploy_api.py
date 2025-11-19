#!/usr/bin/env python3
import requests
import base64
import time

DO_API_TOKEN = "dop_v1_d6b57ed13fcf3d16324a3682ab6012cd1c9ff1281d4ba7e63ad86d3a13bf2cab"
DROPLET_ID = "520881582"
DROPLET_IP = "64.23.221.37"

headers = {
    "Authorization": f"Bearer {DO_API_TOKEN}",
    "Content-Type": "application/json"
}

# Install Docker and run brain via user data
install_script = '''#!/bin/bash
apt-get update
apt-get install -y docker.io docker-compose python3-pip

mkdir -p /opt/brain
cd /opt/brain

# Create requirements
cat > requirements.txt << EOF
fastapi==0.104.1
uvicorn==0.24.0
httpx==0.25.2
asyncpg==0.29.0
redis==5.0.1
psycopg2-binary==2.9.9
EOF

# Create the brain server
cat > brain_server.py << 'BRAIN'
import os
import json
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import uvicorn
import httpx
from datetime import datetime

app = FastAPI(title="AI Jesus Bro Brain")

GHL_API_KEY = os.getenv("GHL_API_KEY")
GHL_LOCATION_ID = os.getenv("GHL_LOCATION_ID") 
RETELL_API_KEY = os.getenv("RETELL_API_KEY")
GHL_BASE = "https://rest.gohighlevel.com/v1"

@app.get("/health")
async def health():
    return {"status": "healthy", "version": "2.0.0", "droplet": "64.23.221.37"}

@app.post("/webhooks/retell")
async def retell_webhook(request: Request):
    try:
        data = await request.json()
        event_type = data.get("event")
        
        if event_type == "call_started":
            phone = data.get("from_number", "")
            async with httpx.AsyncClient() as client:
                search = await client.get(
                    f"{GHL_BASE}/contacts/search",
                    headers={"Authorization": f"Bearer {GHL_API_KEY}"},
                    params={"locationId": GHL_LOCATION_ID, "query": phone}
                )
                if search.status_code == 200:
                    contacts = search.json().get("contacts", [])
                    if not contacts:
                        await client.post(
                            f"{GHL_BASE}/contacts",
                            headers={"Authorization": f"Bearer {GHL_API_KEY}"},
                            json={
                                "locationId": GHL_LOCATION_ID,
                                "phone": phone,
                                "firstName": "New",
                                "lastName": "Lead",
                                "source": "AI Phone System"
                            }
                        )
        return JSONResponse({"status": "processed"})
    except Exception as e:
        print(f"Error: {e}")
        return JSONResponse({"status": "error"}, status_code=500)

@app.post("/webhooks/ghl") 
async def ghl_webhook(request: Request):
    return JSONResponse({"status": "processed"})

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8080)
BRAIN

# Run with Docker
docker run -d --name brain \
  -p 8080:8080 \
  -e GHL_API_KEY="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJsb2NhdGlvbl9pZCI6IlBNZ2JRMzc1VEVHT3lHWHNLejdlIiwidmVyc2lvbiI6MSwiaWF0IjoxNzU3NDU2NTUwMTIyLCJzdWIiOiJ5OXFxZjNIV0FYVGk5Nk1wZXVqZiJ9.nbuFjgIZ1hnsHLPDj5IsiUlxR5DgecMw1l56LCEZEjo" \
  -e GHL_LOCATION_ID="PMgbQ375TEGOyGXsKz7e" \
  -e RETELL_API_KEY="key_819a6edef632ded41fe1c1ef7f12" \
  -v /opt/brain:/app \
  -w /app \
  python:3.11-slim \
  sh -c "pip install -r requirements.txt && python brain_server.py"
'''

# Execute on droplet via user data
print("🚀 Deploying brain via DO API...")
response = requests.post(
    f"https://api.digitalocean.com/v2/droplets/{DROPLET_ID}/actions",
    headers=headers,
    json={"type": "power_cycle", "user_data": base64.b64encode(install_script.encode()).decode()}
)

if response.status_code in [200, 201, 202]:
    print(f"✅ Deployment initiated on {DROPLET_IP}")
    print("⏰ Wait 2-3 minutes for setup")
    print(f"📍 Brain will be at: http://{DROPLET_IP}:8080/health")
else:
    # Fallback: Use App Platform
    print("Using App Platform instead...")
    app_spec = {
        "name": "aijesusbro-brain",
        "region": "sfo",
        "services": [{
            "name": "brain",
            "source_dir": "/",
            "http_port": 8080,
            "instance_count": 1,
            "instance_size_slug": "basic-xxs",
            "run_command": "python brain_server.py",
            "build_command": "pip install -r requirements.txt"
        }]
    }
    response = requests.post(
        "https://api.digitalocean.com/v2/apps",
        headers=headers, 
        json={"spec": app_spec}
    )
    if response.status_code in [200, 201]:
        print(f"✅ App created: {response.json()['app']['live_url']}")