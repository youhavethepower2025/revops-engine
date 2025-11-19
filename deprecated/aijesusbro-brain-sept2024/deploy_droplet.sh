#!/bin/bash
# Direct deployment to DO droplet

DROPLET_IP="64.23.221.37"

echo "🧠 DEPLOYING BRAIN TO DIGITAL OCEAN"
echo "======================================"
echo ""
echo "Run this ONE command in the DO console:"
echo ""
echo "Go to: https://cloud.digitalocean.com/droplets/520881582/console"
echo ""
echo "Then paste this entire block:"
echo "----------------------------------------"
cat << 'DEPLOY'
# Install Docker if needed
which docker || (curl -fsSL https://get.docker.com | sh)

# Create brain directory
mkdir -p /opt/brain && cd /opt/brain

# Create the brain server
cat > brain.py << 'EOF'
#!/usr/bin/env python3
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
    return {
        "status": "healthy",
        "version": "2.0.0",
        "droplet": "64.23.221.37",
        "timestamp": datetime.now().isoformat()
    }

@app.post("/webhooks/retell")
async def retell_webhook(request: Request):
    try:
        data = await request.json()
        event_type = data.get("event")

        if event_type == "call_started":
            phone = data.get("from_number", "")
            print(f"📞 Call from {phone}")

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
                                "source": "AI Phone System",
                                "tags": ["ai-captured"]
                            }
                        )
                        print(f"✅ Created contact for {phone}")

        return JSONResponse({"status": "processed"})
    except Exception as e:
        return JSONResponse({"status": "error"}, status_code=500)

@app.post("/webhooks/ghl")
async def ghl_webhook(request: Request):
    return JSONResponse({"status": "processed"})

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8080)
EOF

# Run it
docker run -d --name brain --restart=always -p 8080:8080 \
  -e GHL_API_KEY='eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJsb2NhdGlvbl9pZCI6IlBNZ2JRMzc1VEVHT3lHWHNLejdlIiwidmVyc2lvbiI6MSwiaWF0IjoxNzU3NDU2NTUwMTIyLCJzdWIiOiJ5OXFxZjNIV0FYVGk5Nk1wZXVqZiJ9.nbuFjgIZ1hnsHLPDj5IsiUlxR5DgecMw1l56LCEZEjo' \
  -e GHL_LOCATION_ID='PMgbQ375TEGOyGXsKz7e' \
  -e RETELL_API_KEY='key_819a6edef632ded41fe1c1ef7f12' \
  -v /opt/brain:/app \
  -w /app \
  python:3.11-slim \
  sh -c "pip install fastapi uvicorn httpx && python brain.py"

# Check status
sleep 5 && curl http://localhost:8080/health && echo ""
echo "✅ Brain deployed!"
DEPLOY
echo "----------------------------------------"
echo ""
echo "After running, your brain will be live at:"
echo "http://$DROPLET_IP:8080/health"
echo ""
echo "Retell webhook: http://$DROPLET_IP:8080/webhooks/retell"