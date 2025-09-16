#!/bin/bash

# Railway Deployment Script for ClearVC Amber Brain

set -e

echo "🚂 Railway Deployment for ClearVC Amber Brain"
echo "============================================"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Check Railway CLI
check_railway() {
    if ! command -v railway &> /dev/null; then
        echo -e "${YELLOW}Railway CLI not found. Installing...${NC}"
        npm install -g @railway/cli
    fi
    echo -e "${GREEN}✓ Railway CLI ready${NC}"
}

# Login to Railway
railway_login() {
    echo -e "${YELLOW}Logging into Railway...${NC}"
    railway login
    echo -e "${GREEN}✓ Logged in to Railway${NC}"
}

# Initialize project
init_project() {
    echo -e "${YELLOW}Initializing Railway project...${NC}"

    # Check if already linked
    if [ -f ".railway/config.json" ]; then
        echo -e "${BLUE}Project already linked${NC}"
    else
        railway link
    fi
}

# Set environment variables
set_env_vars() {
    echo -e "${YELLOW}Setting environment variables...${NC}"

    # Check if .env.production exists
    if [ ! -f ".env.production" ]; then
        echo -e "${RED}Please create .env.production with your production credentials${NC}"
        echo "Example:"
        echo "  cp .env.example .env.production"
        echo "  # Edit .env.production with production values"
        exit 1
    fi

    # Read .env.production and set in Railway
    while IFS='=' read -r key value; do
        # Skip comments and empty lines
        if [[ ! "$key" =~ ^# ]] && [[ -n "$key" ]]; then
            # Remove quotes from value
            value="${value%\"}"
            value="${value#\"}"
            echo -e "  Setting ${key}"
            railway variables set "$key=$value" --service amber-brain
        fi
    done < .env.production

    echo -e "${GREEN}✓ Environment variables set${NC}"
}

# Deploy to Railway
deploy() {
    echo -e "${YELLOW}Deploying to Railway...${NC}"

    # Add PostgreSQL plugin if not exists
    echo -e "${BLUE}Adding PostgreSQL database...${NC}"
    railway add --plugin postgresql || echo "PostgreSQL might already be added"

    # Deploy the application
    railway up

    echo -e "${GREEN}✓ Deployment initiated${NC}"
}

# Get deployment URL
get_url() {
    echo -e "${YELLOW}Getting deployment URL...${NC}"
    DEPLOY_URL=$(railway domain)

    if [ -z "$DEPLOY_URL" ]; then
        echo -e "${YELLOW}Generating domain...${NC}"
        railway domain --generate
        DEPLOY_URL=$(railway domain)
    fi

    echo -e "${GREEN}✓ Deployment URL: ${DEPLOY_URL}${NC}"
}

# Show webhook URLs
show_webhooks() {
    echo ""
    echo -e "${BLUE}==================================${NC}"
    echo -e "${BLUE}📍 Webhook URLs for Retell:${NC}"
    echo -e "${BLUE}==================================${NC}"
    echo ""
    echo "Call Start:    ${DEPLOY_URL}/webhooks/retell/call-started"
    echo "Call End:      ${DEPLOY_URL}/webhooks/retell/call-ended"
    echo "Transcript:    ${DEPLOY_URL}/webhooks/retell/transcript-update"
    echo "Tool Call:     ${DEPLOY_URL}/webhooks/retell/tool-call"
    echo ""
    echo -e "${GREEN}Copy these URLs to your Retell dashboard${NC}"
}

# Monitor logs
show_logs() {
    echo -e "${YELLOW}Showing deployment logs...${NC}"
    railway logs --tail 50
}

# Main deployment flow
main() {
    echo -e "${BLUE}Starting Railway deployment...${NC}"
    echo ""

    check_railway
    railway_login
    init_project
    set_env_vars
    deploy

    echo ""
    echo -e "${GREEN}==================================${NC}"
    echo -e "${GREEN}✅ Deployment Complete!${NC}"
    echo -e "${GREEN}==================================${NC}"

    get_url
    show_webhooks

    echo ""
    echo -e "${YELLOW}Commands:${NC}"
    echo "  View logs:     railway logs"
    echo "  Open console:  railway open"
    echo "  Redeploy:      railway up"
    echo "  Stop:          railway down"
    echo ""
}

# Handle arguments
case "${1:-}" in
    logs)
        railway logs --tail 100
        ;;
    status)
        railway status
        ;;
    vars)
        railway variables
        ;;
    restart)
        railway restart
        ;;
    down)
        railway down
        echo -e "${YELLOW}Service stopped${NC}"
        ;;
    url)
        get_url
        show_webhooks
        ;;
    *)
        main
        ;;
esac