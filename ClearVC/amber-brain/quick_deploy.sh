#!/bin/bash

# Quick Railway Deploy with Browser Auth

echo "🚀 ClearVC Amber Brain - Quick Railway Deploy"
echo "============================================="

cd "/Users/aijesusbro/AI Projects/ClearVC/amber-brain"

# Open Railway login in browser
echo "Opening Railway login in browser..."
echo "After logging in, come back here and press Enter"
open "https://railway.app/login"

read -p "Press Enter after logging in to Railway..."

# Now try Railway CLI
railway login

# Once logged in, deploy
echo "Deploying to Railway..."

# Initialize new project
railway init -n clearvc-amber-brain

# Deploy
railway up --detach

# Get URL
sleep 5
railway domain --generate
DOMAIN=$(railway domain)

echo "✅ Deployed to: https://$DOMAIN"
echo ""
echo "Webhook URLs for Retell:"
echo "  https://$DOMAIN/webhooks/retell/call-started"
echo "  https://$DOMAIN/webhooks/retell/call-ended"
echo "  https://$DOMAIN/webhooks/retell/transcript-update"
echo "  https://$DOMAIN/webhooks/retell/tool-call"