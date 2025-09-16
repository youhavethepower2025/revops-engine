#!/bin/bash
# AGENT.FORGE DEPLOYMENT SCRIPT
# Deploy to production this weekend
# From Medellín with game theory optimal strategy

set -e  # Exit on error

echo "================================================"
echo "🚀 AGENT.FORGE DEPLOYMENT - CONTEXT IS RUNTIME"
echo "================================================"
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check environment
check_environment() {
    echo "📋 Checking environment..."
    
    # Check Python
    if ! command -v python3 &> /dev/null; then
        echo -e "${RED}❌ Python 3 not found${NC}"
        exit 1
    fi
    echo -e "${GREEN}✅ Python 3 found${NC}"
    
    # Check PostgreSQL connection
    if ! command -v psql &> /dev/null; then
        echo -e "${YELLOW}⚠️  PostgreSQL client not found (optional)${NC}"
    else
        echo -e "${GREEN}✅ PostgreSQL client found${NC}"
    fi
    
    # Check Node.js for gateway
    if ! command -v node &> /dev/null; then
        echo -e "${RED}❌ Node.js not found (needed for gateway)${NC}"
        exit 1
    fi
    echo -e "${GREEN}✅ Node.js found${NC}"
    
    echo ""
}

# Setup Python environment
setup_backend() {
    echo "🔧 Setting up backend..."
    
    cd /Users/aijesusbro/AI\ Projects/agent-forge
    
    # Create virtual environment if not exists
    if [ ! -d "venv" ]; then
        echo "Creating Python virtual environment..."
        python3 -m venv venv
    fi
    
    # Activate virtual environment
    source venv/bin/activate
    
    # Upgrade pip
    pip install --upgrade pip
    
    # Install dependencies
    echo "Installing Python dependencies..."
    pip install -r requirements.txt
    
    # Install additional optimization dependencies
    pip install numpy httpx
    
    echo -e "${GREEN}✅ Backend setup complete${NC}"
    echo ""
}

# Setup gateway
setup_gateway() {
    echo "🔧 Setting up gateway..."
    
    cd /Users/aijesusbro/AI\ Projects/forge-gateway
    
    # Install Node dependencies
    echo "Installing Node dependencies..."
    npm install
    
    echo -e "${GREEN}✅ Gateway setup complete${NC}"
    echo ""
}

# Database setup
setup_database() {
    echo "🗄️ Setting up database..."
    
    if [ -z "$DATABASE_URL" ]; then
        echo -e "${YELLOW}⚠️  DATABASE_URL not set. Using default local database${NC}"
        export DATABASE_URL="postgresql://localhost/agentforge"
    fi
    
    cd /Users/aijesusbro/AI\ Projects/agent-forge
    
    # Create database if not exists (local only)
    if [[ "$DATABASE_URL" == *"localhost"* ]]; then
        echo "Creating local database..."
        createdb agentforge 2>/dev/null || echo "Database already exists"
        
        # Run schema
        echo "Applying database schema..."
        psql agentforge < database/schema.sql
    else
        echo "Using remote database: $DATABASE_URL"
        echo -e "${YELLOW}⚠️  Make sure to run schema.sql on your remote database${NC}"
    fi
    
    echo -e "${GREEN}✅ Database setup complete${NC}"
    echo ""
}

# Create environment file
create_env_file() {
    echo "📝 Creating environment configuration..."
    
    cd /Users/aijesusbro/AI\ Projects/agent-forge
    
    if [ ! -f ".env" ]; then
        cat > .env << EOL
# AGENT.FORGE ENVIRONMENT CONFIGURATION
# Context IS Runtime - Game Theory Optimal

# Database
DATABASE_URL=${DATABASE_URL:-postgresql://localhost/agentforge}

# JWT Secret (generate a new one for production!)
JWT_SECRET=$(openssl rand -hex 32)

# LLM API Keys (add your keys here)
OPENAI_API_KEY=${OPENAI_API_KEY:-}
ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY:-}
GROQ_API_KEY=${GROQ_API_KEY:-}

# Server Configuration
HOST=0.0.0.0
PORT=8000
WORKERS=4

# Environment
ENVIRONMENT=${ENVIRONMENT:-development}

# Cloudflare (for production)
CLOUDFLARE_ACCOUNT_ID=${CLOUDFLARE_ACCOUNT_ID:-}
CLOUDFLARE_API_TOKEN=${CLOUDFLARE_API_TOKEN:-}

# Railway (for production)
RAILWAY_TOKEN=${RAILWAY_TOKEN:-}
EOL
        echo -e "${GREEN}✅ Created .env file${NC}"
    else
        echo -e "${YELLOW}⚠️  .env file already exists${NC}"
    fi
    
    # Load environment
    source .env
    
    echo ""
}

# Start services
start_services() {
    echo "🚀 Starting services..."
    
    # Kill any existing processes
    echo "Stopping any existing services..."
    pkill -f "uvicorn main:app" 2>/dev/null || true
    pkill -f "node gateway.js" 2>/dev/null || true
    
    sleep 2
    
    # Start backend
    echo "Starting backend server..."
    cd /Users/aijesusbro/AI\ Projects/agent-forge/backend
    source ../venv/bin/activate
    
    # Use optimized version if available
    if [ -f "optimized/main_v2.py" ]; then
        echo "Using optimized Context IS Runtime engine..."
        nohup python3 optimized/main_v2.py > ../logs/backend.log 2>&1 &
    else
        nohup uvicorn main:app --host 0.0.0.0 --port 8000 --reload > ../logs/backend.log 2>&1 &
    fi
    
    echo "Backend starting on http://localhost:8000"
    
    # Start gateway
    echo "Starting gateway..."
    cd /Users/aijesusbro/AI\ Projects/forge-gateway
    nohup node gateway.js > logs/gateway.log 2>&1 &
    
    echo "Gateway starting on http://localhost:8002"
    
    echo -e "${GREEN}✅ Services started${NC}"
    echo ""
}

# Create log directories
create_logs() {
    mkdir -p /Users/aijesusbro/AI\ Projects/agent-forge/logs
    mkdir -p /Users/aijesusbro/AI\ Projects/forge-gateway/logs
}

# Test endpoints
test_endpoints() {
    echo "🧪 Testing endpoints..."
    
    sleep 5  # Wait for services to start
    
    # Test backend health
    echo -n "Testing backend health... "
    if curl -s http://localhost:8000/health > /dev/null; then
        echo -e "${GREEN}✅${NC}"
    else
        echo -e "${RED}❌${NC}"
    fi
    
    # Test backend v2 health
    echo -n "Testing optimized backend... "
    if curl -s http://localhost:8000/health/v2 > /dev/null; then
        echo -e "${GREEN}✅${NC}"
    else
        echo -e "${YELLOW}⚠️  Optimized endpoint not available${NC}"
    fi
    
    # Test gateway health
    echo -n "Testing gateway... "
    if curl -s http://localhost:8002/health > /dev/null; then
        echo -e "${GREEN}✅${NC}"
    else
        echo -e "${RED}❌${NC}"
    fi
    
    echo ""
}

# Show status
show_status() {
    echo "================================================"
    echo "📊 DEPLOYMENT STATUS"
    echo "================================================"
    echo ""
    echo "🔥 Context IS Runtime Engine: ACTIVE"
    echo "🚀 Backend API: http://localhost:8000"
    echo "🌉 Gateway: http://localhost:8002"
    echo "📚 API Documentation: http://localhost:8000/docs"
    echo ""
    echo "Key Endpoints:"
    echo "  - Health: http://localhost:8000/health/v2"
    echo "  - Auth: http://localhost:8000/auth/login"
    echo "  - Widget Chat: http://localhost:8000/widget/{widget_id}/chat/v2"
    echo "  - Analytics: http://localhost:8000/analytics/runtime/{widget_id}"
    echo ""
    echo "Logs:"
    echo "  - Backend: tail -f agent-forge/logs/backend.log"
    echo "  - Gateway: tail -f forge-gateway/logs/gateway.log"
    echo ""
    echo -e "${GREEN}🎯 READY FOR DEPLOYMENT!${NC}"
    echo ""
    echo "Next steps:"
    echo "1. Add your LLM API keys to .env file"
    echo "2. Configure your database connection"
    echo "3. Deploy to Railway: railway up"
    echo "4. Deploy frontend to Cloudflare Pages"
    echo ""
}

# Main deployment flow
main() {
    echo "Starting deployment process..."
    echo ""
    
    check_environment
    create_logs
    setup_backend
    setup_gateway
    create_env_file
    setup_database
    start_services
    test_endpoints
    show_status
}

# Handle script arguments
case "${1:-}" in
    "start")
        start_services
        show_status
        ;;
    "stop")
        echo "Stopping services..."
        pkill -f "uvicorn main:app" 2>/dev/null || true
        pkill -f "node gateway.js" 2>/dev/null || true
        echo "Services stopped"
        ;;
    "restart")
        $0 stop
        sleep 2
        $0 start
        ;;
    "status")
        show_status
        ;;
    "test")
        test_endpoints
        ;;
    *)
        main
        ;;
esac
