#!/bin/bash

# Deploy the INTELLIGENT version of ClearVC Amber Brain

echo "🧠 Deploying INTELLIGENT ClearVC Amber Brain"
echo "==========================================="

cd "/Users/aijesusbro/AI Projects/ClearVC/amber-brain"

# Stop any existing servers
echo "Stopping existing servers..."
pkill -f smart_server.py 2>/dev/null
pkill -f simple_server.py 2>/dev/null
pkill -f intelligent_server.py 2>/dev/null

# Start the intelligent server
echo "Starting intelligent server with real GHL integration..."
python3 intelligent_server.py > intelligent_server.log 2>&1 &

sleep 3

# Test it's running
if curl -s http://localhost:8000/health | grep -q "intelligent"; then
    echo "✅ Intelligent server is running!"
    echo ""
    echo "Features enabled:"
    echo "  ✓ Real GHL contact lookup"
    echo "  ✓ Intelligent caller categorization"
    echo "  ✓ Persistent SQLite memory"
    echo "  ✓ AI-powered call summaries"
    echo "  ✓ Actual tool implementations"
    echo "  ✓ Automatic GHL updates"
    echo ""
    echo "📍 Webhook URL: https://clearvc.aijesusbro.com/webhook"
    echo ""
    echo "Test endpoints:"
    echo "  /test-ghl/{phone} - Test GHL lookup"
    echo "  /conversations - View recent calls"
    echo ""
else
    echo "⚠️ Server starting... check intelligent_server.log for details"
fi