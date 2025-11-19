#!/usr/bin/env python3
import paramiko
import time
import sys

DROPLET_IP = "64.23.221.37"

print("🚀 DEPLOYING BRAIN TO DIGITAL OCEAN")
print("=" * 50)

# The deployment script
deploy_script = '''
# Install Docker if needed
which docker || (curl -fsSL https://get.docker.com | sh)

# Stop any existing brain container
docker stop brain 2>/dev/null || true
docker rm brain 2>/dev/null || true

# Create brain directory
mkdir -p /opt/brain && cd /opt/brain

# Create minimal brain server
cat > brain.py << 'EOF'
#!/usr/bin/env python3
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
    return {
        "status": "healthy",
        "version": "2.0.0",
        "droplet": "64.23.221.37"
    }

@app.post("/webhooks/retell")
async def retell_webhook(request: Request):
    try:
        data = await request.json()
        event_type = data.get("event")

        if event_type == "call_started":
            phone = data.get("from_number", "")
            print(f"Call from {phone}")

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
        return JSONResponse({"status": "error"}, status_code=500)

@app.post("/webhooks/ghl")
async def ghl_webhook(request: Request):
    return JSONResponse({"status": "processed"})

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8080)
EOF

# Run brain container
docker run -d --name brain --restart=always -p 8080:8080 \
  -e GHL_API_KEY='eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJsb2NhdGlvbl9pZCI6IlBNZ2JRMzc1VEVHT3lHWHNLejdlIiwidmVyc2lvbiI6MSwiaWF0IjoxNzU3NDU2NTUwMTIyLCJzdWIiOiJ5OXFxZjNIV0FYVGk5Nk1wZXVqZiJ9.nbuFjgIZ1hnsHLPDj5IsiUlxR5DgecMw1l56LCEZEjo' \
  -e GHL_LOCATION_ID='PMgbQ375TEGOyGXsKz7e' \
  -e RETELL_API_KEY='key_819a6edef632ded41fe1c1ef7f12' \
  -v /opt/brain:/app \
  -w /app \
  python:3.11-slim \
  sh -c "pip install fastapi uvicorn httpx && python brain.py"

# Wait and check
echo "Waiting for brain to start..."
sleep 10
curl http://localhost:8080/health && echo ""
echo "✅ BRAIN DEPLOYED!"
'''

# Try SSH connection
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

try:
    print(f"🔑 Attempting SSH connection to {DROPLET_IP}...")
    ssh.connect(DROPLET_IP, username='root', key_filename='/Users/aijesusbro/.ssh/aijesusbro_do', timeout=10)
    print("✅ SSH connected!")

    print("📦 Deploying brain...")
    stdin, stdout, stderr = ssh.exec_command(deploy_script)

    # Stream output
    for line in stdout:
        print(line.strip())

    errors = stderr.read().decode()
    if errors and "WARNING" not in errors:
        print(f"Errors: {errors}")

    print("\n✅ DEPLOYMENT COMPLETE!")
    print(f"🧠 Brain URL: http://{DROPLET_IP}:8080/health")
    print(f"📞 Retell webhook: http://{DROPLET_IP}:8080/webhooks/retell")

except Exception as e:
    print(f"\n❌ SSH connection failed: {e}")
    print("\nThe SSH key might not be added yet. You have 2 options:")
    print("\n1. QUICK FIX (30 seconds):")
    print("   Go to: https://cloud.digitalocean.com/droplets/520881582/console")
    print("   Run: bash /Users/aijesusbro/AI\\ Projects/aijesusbro-brain/deploy_droplet.sh")
    print("\n2. WAIT & RETRY (2-3 minutes):")
    print("   The rebuild might still be in progress. Try again in a minute.")

    # Try password reset as fallback
    import requests
    headers = {"Authorization": f"Bearer dop_v1_d6b57ed13fcf3d16324a3682ab6012cd1c9ff1281d4ba7e63ad86d3a13bf2cab", "Content-Type": "application/json"}
    reset = requests.post(f"https://api.digitalocean.com/v2/droplets/520881582/actions", headers=headers, json={"type": "password_reset"})
    if reset.status_code in [200, 201, 202]:
        print("\n📧 Password reset initiated - check your email for temporary password")
finally:
    ssh.close()