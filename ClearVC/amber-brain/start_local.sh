#!/bin/bash

# Start ClearVC Amber Brain locally and expose via ngrok

echo "🚀 Starting ClearVC Amber Brain Locally"
echo "======================================="

cd "/Users/aijesusbro/AI Projects/ClearVC/amber-brain"

# Check if ngrok is installed
if ! command -v ngrok &> /dev/null; then
    echo "Installing ngrok..."
    brew install ngrok
fi

# Start the app in background
echo "Starting Amber Brain..."
docker-compose up -d

# Wait for it to start
sleep 5

# Check if running
if curl -s http://localhost:8000/health | grep -q "healthy"; then
    echo "✅ Amber Brain is running"
else
    echo "⚠️ Amber Brain might still be starting..."
fi

# Start ngrok
echo "Starting ngrok tunnel..."
ngrok http 8000 &

sleep 3

# Get ngrok URL
NGROK_URL=$(curl -s http://localhost:4040/api/tunnels | python3 -c "import sys, json; print(json.load(sys.stdin)['tunnels'][0]['public_url'])" 2>/dev/null)

if [ -z "$NGROK_URL" ]; then
    echo "Getting ngrok URL..."
    sleep 2
    NGROK_URL=$(curl -s http://localhost:4040/api/tunnels | python3 -c "import sys, json; print(json.load(sys.stdin)['tunnels'][0]['public_url'])" 2>/dev/null)
fi

echo ""
echo "✅ ClearVC Amber Brain is live!"
echo "================================"
echo ""
echo "🔗 Public URL: $NGROK_URL"
echo ""
echo "📝 Webhook URLs for Retell:"
echo "   Call Start:  $NGROK_URL/webhooks/retell/call-started"
echo "   Call End:    $NGROK_URL/webhooks/retell/call-ended"
echo "   Transcript:  $NGROK_URL/webhooks/retell/transcript-update"
echo "   Tool Call:   $NGROK_URL/webhooks/retell/tool-call"
echo ""
echo "This URL will work immediately for testing!"

# Save URL
echo $NGROK_URL > deployment_url.txt