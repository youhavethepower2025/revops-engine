#!/bin/bash
# Quick deployment script for vapi-mcp-server

set -e  # Exit on error

echo "🚀 VAPI MCP Server - Quick Deploy Script"
echo "=========================================="
echo ""

# Check if we're in the right directory
if [ ! -f "wrangler.toml" ]; then
    echo "❌ Error: wrangler.toml not found. Are you in the vapi-mcp-server directory?"
    exit 1
fi

# Step 1: Install dependencies
echo "📦 Step 1/6: Installing dependencies..."
npm install
echo "✅ Dependencies installed"
echo ""

# Step 2: Create D1 database
echo "🗄️  Step 2/6: Creating D1 database..."
echo "Note: If database already exists, you'll see an error - that's OK!"
npm run d1:create || echo "Database may already exist, continuing..."
echo ""

echo "⚠️  IMPORTANT: Copy the database_id from above and update wrangler.toml line 8"
echo "Press Enter when you've updated wrangler.toml..."
read

# Step 3: Run database migrations
echo "📊 Step 3/6: Running database migrations..."
npm run d1:execute
echo "✅ Database schema created"
echo ""

# Step 4: Set VAPI API key
echo "🔑 Step 4/6: Setting VAPI API key..."
echo "Get your VAPI API key from: https://vapi.ai/dashboard"
npm run secret:vapi
echo "✅ Secret set"
echo ""

# Step 5: Deploy to Cloudflare
echo "🚀 Step 5/6: Deploying to Cloudflare..."
npm run deploy
echo "✅ Deployed!"
echo ""

# Step 6: Test health endpoint
echo "🏥 Step 6/6: Testing health endpoint..."
sleep 2
curl -s https://vapi-mcp-server.aijesusbro.workers.dev/health | jq '.'
echo ""
echo ""

echo "=========================================="
echo "✅ DEPLOYMENT COMPLETE!"
echo "=========================================="
echo ""
echo "Your MCP server is live at:"
echo "https://vapi-mcp-server.aijesusbro.workers.dev"
echo ""
echo "Next steps:"
echo "1. Add a client: curl -X POST https://vapi-mcp-server.aijesusbro.workers.dev/admin/clients -H 'Content-Type: application/json' -d '{...}'"
echo "2. Configure VAPI agent with MCP tools"
echo "3. Test with a phone call"
echo ""
echo "See DEPLOYMENT.md for detailed instructions."
echo ""
