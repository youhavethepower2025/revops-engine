#!/bin/bash

# Railway Direct Deployment Script
# Uses Railway CLI with token authentication

set -e

echo "🚀 ClearVC Amber Brain - Railway Deployment"
echo "========================================="

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Change to amber-brain directory
cd "/Users/aijesusbro/AI Projects/ClearVC/amber-brain"

# Method 1: Try browserless login
echo -e "${YELLOW}Attempting Railway authentication...${NC}"

# Get a new token via browserless login
railway login --browserless 2>/dev/null || {
    echo -e "${YELLOW}Browserless login not available. Trying token auth...${NC}"

    # Method 2: Use existing token
    if [ -z "$RAILWAY_TOKEN" ]; then
        echo -e "${RED}No RAILWAY_TOKEN found${NC}"
        echo "Please run: export RAILWAY_TOKEN=your_token_here"
        echo "Get token from: https://railway.app/account/tokens"
        exit 1
    fi
}

# Create new project
echo -e "${YELLOW}Creating new Railway project...${NC}"
railway init -n clearvc-amber-brain

# Add PostgreSQL database
echo -e "${YELLOW}Adding PostgreSQL database...${NC}"
railway add --database postgresql

# Set environment variables
echo -e "${YELLOW}Setting environment variables...${NC}"

# Check if .env exists
if [ -f .env ]; then
    source .env
    railway variables set \
        RETELL_API_KEY="$RETELL_API_KEY" \
        GHL_API_KEY="$GHL_API_KEY" \
        GHL_LOCATION_ID="$GHL_LOCATION_ID" \
        OPENAI_API_KEY="$OPENAI_API_KEY" \
        TELEGRAM_BOT_TOKEN="$TELEGRAM_BOT_TOKEN" \
        TELEGRAM_CHAT_ID="$TELEGRAM_CHAT_ID"
else
    echo -e "${YELLOW}No .env file found. Set variables manually in Railway dashboard${NC}"
fi

# Deploy
echo -e "${YELLOW}Deploying to Railway...${NC}"
railway up --detach

# Wait for deployment
echo -e "${YELLOW}Waiting for deployment to initialize...${NC}"
sleep 10

# Get domain
echo -e "${YELLOW}Getting deployment URL...${NC}"
DOMAIN=$(railway domain 2>/dev/null || echo "")

if [ -z "$DOMAIN" ]; then
    echo -e "${YELLOW}Generating domain...${NC}"
    railway domain --generate
    DOMAIN=$(railway domain)
fi

# Display results
echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}✅ Deployment Complete!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "📍 Deployment URL: https://${DOMAIN}"
echo ""
echo "📝 Webhook URLs for Retell:"
echo "  Call Start:  https://${DOMAIN}/webhooks/retell/call-started"
echo "  Call End:    https://${DOMAIN}/webhooks/retell/call-ended"
echo "  Transcript:  https://${DOMAIN}/webhooks/retell/transcript-update"
echo "  Tool Call:   https://${DOMAIN}/webhooks/retell/tool-call"
echo ""
echo -e "${GREEN}View logs: railway logs${NC}"
echo -e "${GREEN}Open dashboard: railway open${NC}"