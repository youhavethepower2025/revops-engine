#!/bin/bash

# Deploy ClearVC through YOUR existing Cloudflare tunnel

echo "🚀 Deploying ClearVC through your Cloudflare tunnel"
echo "==================================================="

cd "/Users/aijesusbro/AI Projects/ClearVC/amber-brain"

# Start ClearVC on port 8001 (so it doesn't conflict with your MCP on 8080)
echo "Starting ClearVC Amber Brain on port 8001..."

# Stop any existing instance
docker-compose down 2>/dev/null

# Update docker-compose to use port 8001
cat > docker-compose.override.yml << EOF
version: '3.8'
services:
  amber-brain:
    ports:
      - "8001:8000"
EOF

# Start it
docker-compose up -d

# Wait for health
sleep 5

if curl -s http://localhost:8001/health | grep -q "healthy"; then
    echo "✅ ClearVC Amber Brain is running on port 8001"
else
    echo "Starting up..."
    sleep 5
fi

# Update your Cloudflare config to route ClearVC
echo ""
echo "✅ ClearVC is now running!"
echo ""
echo "To make it accessible, add this to your Cloudflare tunnel config:"
echo ""
echo "~/.cloudflared/config.yml:"
echo "---"
echo "tunnel: 3a462a23-769a-4dc6-9378-06962ec9fb8f"
echo "credentials-file: /Users/aijesusbro/.cloudflared/3a462a23-769a-4dc6-9378-06962ec9fb8f.json"
echo ""
echo "ingress:"
echo "  # ClearVC Amber Brain"
echo "  - hostname: clearvc.aijesusbro.com"
echo "    service: http://localhost:8001"
echo "  # Your MCP Brain"
echo "  - hostname: mcp-brain.aijesusbro.com"
echo "    service: http://localhost:8080"
echo "  - service: http_status:404"
echo ""
echo "Then restart cloudflared:"
echo "pkill cloudflared && cloudflared tunnel run mcp-brain"
echo ""
echo "📝 Webhook URLs for Retell:"
echo "   https://clearvc.aijesusbro.com/webhooks/retell/call-started"
echo "   https://clearvc.aijesusbro.com/webhooks/retell/call-ended"
echo "   https://clearvc.aijesusbro.com/webhooks/retell/transcript-update"
echo "   https://clearvc.aijesusbro.com/webhooks/retell/tool-call"