#!/bin/bash

# Start script for ClearVC Amber Brain

echo "🚀 ClearVC Amber Brain Startup"
echo "=============================="

# Check if we want Docker or simple mode
MODE=${1:-simple}

if [ "$MODE" = "docker" ]; then
    echo "Starting in Docker mode (full stack)..."
    docker-compose up -d
    echo "✅ Full stack running with PostgreSQL and Redis"
    echo "   Access at: http://localhost:8001"
else
    echo "Starting in simple mode (lightweight)..."
    pkill -f smart_server.py 2>/dev/null
    python3 smart_server.py > server.log 2>&1 &
    sleep 2
    echo "✅ Simple server running"
    echo "   Access at: http://localhost:8000"
fi

echo ""
echo "📍 Webhook URL: https://clearvc.aijesusbro.com/webhook"
echo "   (Single intelligent endpoint for all Retell events)"
echo ""
echo "To switch modes:"
echo "  ./start.sh simple  - Lightweight Python server"
echo "  ./start.sh docker  - Full Docker stack with database"