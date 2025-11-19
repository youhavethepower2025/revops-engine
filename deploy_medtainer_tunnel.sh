#!/bin/bash
# Deploy Cloudflare Tunnel for MedTainer
# Creates: https://medtainer.aijesusbro.com → http://localhost:8000

set -e

SERVER="root@24.199.118.227"
TUNNEL_NAME="medtainer"
DOMAIN="medtainer.aijesusbro.com"

echo "🚀 Deploying Cloudflare Tunnel for MedTainer..."
echo ""

# Step 1: Check current state
echo "📋 Step 1: Checking current server state..."
ssh $SERVER <<'ENDSSH'
echo "=== Docker Containers ==="
docker ps --format 'table {{.Names}}\t{{.Ports}}'
echo ""
echo "=== Listening Ports ==="
netstat -tlnp 2>/dev/null | grep LISTEN | grep -E ':(80|443|8000)' || echo "Ports 80, 443, 8000 check complete"
echo ""
echo "=== Cloudflared Status ==="
which cloudflared && cloudflared --version || echo "cloudflared not installed"
ENDSSH

echo ""
read -p "Continue with installation? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Aborted."
    exit 1
fi

# Step 2: Install cloudflared
echo ""
echo "📦 Step 2: Installing cloudflared..."
ssh $SERVER <<'ENDSSH'
cd /tmp
wget -q https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64.deb
dpkg -i cloudflared-linux-amd64.deb
cloudflared --version
ENDSSH

# Step 3: Authenticate with Cloudflare
echo ""
echo "🔐 Step 3: Authenticating with Cloudflare..."
echo "This will open a browser window. Please login to Cloudflare."
echo ""
read -p "Press enter to continue..."
ssh $SERVER "cloudflared tunnel login"

# Step 4: Create tunnel
echo ""
echo "🌐 Step 4: Creating tunnel '$TUNNEL_NAME'..."
ssh $SERVER "cloudflared tunnel create $TUNNEL_NAME || echo 'Tunnel may already exist'"

# Step 5: Get tunnel ID
echo ""
echo "🔍 Step 5: Getting tunnel ID..."
TUNNEL_ID=$(ssh $SERVER "cloudflared tunnel list | grep $TUNNEL_NAME | awk '{print \$1}'")
echo "Tunnel ID: $TUNNEL_ID"

# Step 6: Create config file
echo ""
echo "📝 Step 6: Creating tunnel config..."
ssh $SERVER <<ENDSSH
mkdir -p ~/.cloudflared
cat > ~/.cloudflared/config.yml <<'EOF'
tunnel: $TUNNEL_ID
credentials-file: /root/.cloudflared/$TUNNEL_ID.json

ingress:
  - hostname: $DOMAIN
    service: http://localhost:8000
  - service: http_status:404
EOF
cat ~/.cloudflared/config.yml
ENDSSH

# Step 7: Create DNS record
echo ""
echo "🌍 Step 7: Creating DNS record..."
ssh $SERVER "cloudflared tunnel route dns $TUNNEL_NAME $DOMAIN || echo 'DNS may already exist'"

# Step 8: Install as systemd service
echo ""
echo "⚙️  Step 8: Installing as systemd service..."
ssh $SERVER <<'ENDSSH'
cloudflared service install
systemctl enable cloudflared
systemctl start cloudflared
systemctl status cloudflared --no-pager
ENDSSH

# Step 9: Test the endpoint
echo ""
echo "🧪 Step 9: Testing HTTPS endpoint..."
sleep 5
curl -s https://$DOMAIN/health | python3 -m json.tool || echo "Waiting for DNS propagation..."

# Step 10: Security - Close port 8000 (commented out for safety)
echo ""
echo "🔒 Step 10: Security recommendation..."
echo "After confirming the tunnel works, close port 8000:"
echo "  ssh $SERVER 'ufw allow 80/tcp && ufw allow 443/tcp && ufw deny 8000/tcp && ufw enable'"
echo ""

echo "✅ Deployment complete!"
echo ""
echo "🎯 Your MedTainer brain is now accessible at:"
echo "   https://$DOMAIN"
echo ""
echo "📋 Test the endpoint:"
echo "   curl https://$DOMAIN/health"
echo "   curl https://$DOMAIN/mcp/tools"
echo ""
echo "🔧 Manage the tunnel:"
echo "   ssh $SERVER 'systemctl status cloudflared'"
echo "   ssh $SERVER 'systemctl restart cloudflared'"
echo "   ssh $SERVER 'journalctl -u cloudflared -f'"
