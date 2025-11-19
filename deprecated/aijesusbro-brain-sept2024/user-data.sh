#!/bin/bash
# User data script for Digital Ocean droplet
# This runs automatically when the droplet is created

# Update system
apt-get update
apt-get upgrade -y

# Install required tools
apt-get install -y git docker-compose python3-pip redis-server nginx certbot python3-certbot-nginx

# Create brain directory
mkdir -p /opt/aijesusbro-brain
cd /opt/aijesusbro-brain

# Create docker-compose.yml
cat > docker-compose.yml <<'EOF'
version: '3.8'

services:
  postgres:
    image: postgres:15-alpine
    container_name: brain-postgres
    environment:
      POSTGRES_USER: brain
      POSTGRES_PASSWORD: brain_secure_2024
      POSTGRES_DB: aijesusbro_brain
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U brain -d aijesusbro_brain"]
      interval: 10s
      timeout: 5s
      retries: 5
    restart: unless-stopped

  redis:
    image: redis:7-alpine
    container_name: brain-redis
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5
    restart: unless-stopped

  brain:
    image: aijesusbro/brain:latest
    container_name: aijesusbro-brain
    ports:
      - "8080:8080"
    environment:
      DATABASE_URL: postgresql://brain:brain_secure_2024@postgres:5432/aijesusbro_brain
      REDIS_URL: redis://redis:6379
      GHL_API_KEY: ${GHL_API_KEY}
      GHL_LOCATION_ID: ${GHL_LOCATION_ID}
      RETELL_API_KEY: ${RETELL_API_KEY}
      DO_API_TOKEN: ${DO_API_TOKEN}
      CLIENT_NAME: aijesusbro
      PORT: 8080
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    restart: unless-stopped

volumes:
  postgres_data:
EOF

# Create environment file
cat > .env <<'EOF'
GHL_API_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJsb2NhdGlvbl9pZCI6IlBNZ2JRMzc1VEVHT3lHWHNLejdlIiwidmVyc2lvbiI6MSwiaWF0IjoxNzU3NDU2NTUwMTIyLCJzdWIiOiJ5OXFxZjNIV0FYVGk5Nk1wZXVqZiJ9.nbuFjgIZ1hnsHLPDj5IsiUlxR5DgecMw1l56LCEZEjo
GHL_LOCATION_ID=PMgbQ375TEGOyGXsKz7e
RETELL_API_KEY=key_819a6edef632ded41fe1c1ef7f12
DO_API_TOKEN=dop_v1_d6b57ed13fcf3d16324a3682ab6012cd1c9ff1281d4ba7e63ad86d3a13bf2cab
TWILIO_ACCOUNT_SID=ACd7564cf277675642888a72f63d1655a3
TWILIO_API_KEY=SK451b658e7397ec5ad179ae1686ab5caf
TWILIO_API_SECRET=Z2lG0aDvABPaX7jE4eZ1xdvYU0tpQaOA
EOF

# Copy brain files (we'll build the image from your local files)
# For now, use a pre-built image or build locally and push to Docker Hub

# Create Dockerfile
cat > Dockerfile <<'EOF'
FROM python:3.11-slim

RUN apt-get update && apt-get install -y gcc postgresql-client curl && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Create a basic brain server (simplified version)
RUN pip install fastapi uvicorn httpx asyncpg redis psycopg2-binary

# We'll mount the actual code via volume or copy it
COPY brain_server.py .
COPY enhanced_tools.py .
COPY tool_implementations.py .
COPY enhanced_webhook_handler.py .

EXPOSE 8080
CMD ["python", "brain_server.py"]
EOF

# Download brain files from GitHub or your repository
# For now, we'll create a minimal brain server
cat > brain_server.py <<'EOF'
#!/usr/bin/env python3
"""Minimal brain server for production"""

import os
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import uvicorn

app = FastAPI(title="AI Jesus Bro Brain")

@app.get("/health")
async def health():
    return {"status": "healthy", "version": "2.0.0", "location": "Digital Ocean"}

@app.post("/webhooks/retell")
async def retell_webhook(request: Request):
    data = await request.json()
    # Process webhook
    return JSONResponse({"status": "processed"})

@app.post("/webhooks/ghl")
async def ghl_webhook(request: Request):
    data = await request.json()
    # Process webhook
    return JSONResponse({"status": "processed"})

@app.post("/sse")
async def sse_endpoint(request: Request):
    data = await request.json()
    # Handle MCP calls
    return JSONResponse({"jsonrpc": "2.0", "result": {"status": "ok"}, "id": data.get("id", 1)})

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8080)
EOF

# Build the Docker image
docker build -t aijesusbro/brain:latest .

# Start the stack
docker-compose up -d

# Setup nginx for SSL (optional)
cat > /etc/nginx/sites-available/brain <<'EOF'
server {
    listen 80;
    server_name _;

    location / {
        proxy_pass http://localhost:8080;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
EOF

ln -s /etc/nginx/sites-available/brain /etc/nginx/sites-enabled/
rm /etc/nginx/sites-enabled/default
nginx -t && systemctl restart nginx

# Create a systemd service for auto-restart
cat > /etc/systemd/system/aijesusbro-brain.service <<'EOF'
[Unit]
Description=AI Jesus Bro Brain
After=docker.service
Requires=docker.service

[Service]
Type=simple
Restart=always
WorkingDirectory=/opt/aijesusbro-brain
ExecStart=/usr/bin/docker-compose up
ExecStop=/usr/bin/docker-compose down

[Install]
WantedBy=multi-user.target
EOF

systemctl enable aijesusbro-brain

# Log completion
echo "AI JESUS BRO BRAIN DEPLOYED!" > /root/deployment.log
date >> /root/deployment.log
docker ps >> /root/deployment.log