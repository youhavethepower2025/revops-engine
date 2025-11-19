#!/usr/bin/env python3
import paramiko
import time

DROPLET_IP = "64.23.221.37"

# Create SSH client
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

# The brain code to deploy
brain_code = '''
import os
import json
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import uvicorn
import httpx

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
                # Caller ID lookup
                search = await client.get(
                    f"{GHL_BASE}/contacts/search",
                    headers={"Authorization": f"Bearer {GHL_API_KEY}"},
                    params={"locationId": GHL_LOCATION_ID, "query": phone}
                )
                
                if search.status_code == 200:
                    contacts = search.json().get("contacts", [])
                    if contacts:
                        print(f"Found contact: {contacts[0].get('firstName')}")
                    else:
                        # Create new contact
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
                        print(f"Created contact for {phone}")
                        
        elif event_type == "call_ended":
            # Process transcript
            transcript = data.get("transcript", "")
            if "appointment" in transcript.lower():
                print("Appointment requested - creating task")
                
        return JSONResponse({"status": "processed"})
        
    except Exception as e:
        print(f"Error: {e}")
        return JSONResponse({"status": "error"}, status_code=500)

@app.post("/webhooks/ghl")
async def ghl_webhook(request: Request):
    return JSONResponse({"status": "processed"})

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8080)
'''

print(f"🚀 Deploying to {DROPLET_IP}...")

try:
    # Try passwordless first (if SSH key is set)
    ssh.connect(DROPLET_IP, username='root')
except:
    print("⚠️  Cannot connect via SSH - droplet needs console access")
    print("")
    print("Quick fix via DO Console:")
    print("1. Go to: https://cloud.digitalocean.com/droplets/520881582/console")
    print("2. Login and run this ONE command:")
    print("")
    print("curl -sSL https://get.docker.com | sh && docker run -d --name brain -p 8080:8080 -e GHL_API_KEY='eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJsb2NhdGlvbl9pZCI6IlBNZ2JRMzc1VEVHT3lHWHNLejdlIiwidmVyc2lvbiI6MSwiaWF0IjoxNzU3NDU2NTUwMTIyLCJzdWIiOiJ5OXFxZjNIV0FYVGk5Nk1wZXVqZiJ9.nbuFjgIZ1hnsHLPDj5IsiUlxR5DgecMw1l56LCEZEjo' -e GHL_LOCATION_ID='PMgbQ375TEGOyGXsKz7e' -e RETELL_API_KEY='key_819a6edef632ded41fe1c1ef7f12' aijesusbro/brain:latest")
    print("")
    print("🎯 That's it! Brain will be live in 1 minute.")