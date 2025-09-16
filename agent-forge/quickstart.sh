#!/bin/bash
# AGENT.FORGE QUICK START
# Get everything running in one command
# From Medellín - This is the way

set -e

echo "
████████╗██╗  ██╗███████╗    ███████╗ ██████╗ ██████╗  ██████╗ ███████╗
╚══██╔══╝██║  ██║██╔════╝    ██╔════╝██╔═══██╗██╔══██╗██╔════╝ ██╔════╝
   ██║   ███████║█████╗      █████╗  ██║   ██║██████╔╝██║  ███╗█████╗  
   ██║   ██╔══██║██╔══╝      ██╔══╝  ██║   ██║██╔══██╗██║   ██║██╔══╝  
   ██║   ██║  ██║███████╗    ██║     ╚██████╔╝██║  ██║╚██████╔╝███████╗
   ╚═╝   ╚═╝  ╚═╝╚══════╝    ╚═╝      ╚═════╝ ╚═╝  ╚═╝ ╚═════╝ ╚══════╝

         CONTEXT IS RUNTIME - The Architecture That Executes Itself
                    Built from Medellín with Game Theory
"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# Check if running on macOS or Linux
if [[ "$OSTYPE" == "darwin"* ]]; then
    echo "🍎 Detected macOS"
    OPEN_CMD="open"
else
    echo "🐧 Detected Linux"
    OPEN_CMD="xdg-open"
fi

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to wait for service
wait_for_service() {
    local url=$1
    local name=$2
    local max_attempts=30
    local attempt=0
    
    echo -n "Waiting for $name to start"
    while [ $attempt -lt $max_attempts ]; do
        if curl -s "$url" > /dev/null 2>&1; then
            echo -e " ${GREEN}✅${NC}"
            return 0
        fi
        echo -n "."
        sleep 1
        attempt=$((attempt + 1))
    done
    echo -e " ${RED}❌${NC}"
    return 1
}

# Step 1: Check prerequisites
echo "📋 Checking prerequisites..."

if ! command_exists python3; then
    echo -e "${RED}❌ Python 3 not found. Please install Python 3.8+${NC}"
    exit 1
fi

if ! command_exists node; then
    echo -e "${RED}❌ Node.js not found. Please install Node.js 16+${NC}"
    exit 1
fi

if ! command_exists docker; then
    echo -e "${YELLOW}⚠️  Docker not found. Using local setup (install Docker for production)${NC}"
    USE_DOCKER=false
else
    USE_DOCKER=true
fi

echo -e "${GREEN}✅ Prerequisites satisfied${NC}\n"

# Step 2: Setup environment
echo "🔧 Setting up environment..."

# Create necessary directories
mkdir -p logs
mkdir -p deployment/ssl

# Check for .env file
if [ ! -f .env ]; then
    echo "Creating .env file..."
    cat > .env << 'EOL'
# AGENT.FORGE CONFIGURATION
DATABASE_URL=postgresql://localhost/agentforge
JWT_SECRET=your-secret-key-change-this
ENVIRONMENT=development

# Add your API keys here
OPENAI_API_KEY=
ANTHROPIC_API_KEY=
GROQ_API_KEY=
EOL
    echo -e "${YELLOW}⚠️  Please add your API keys to .env file${NC}"
fi

# Load environment
set -a
source .env
set +a

echo -e "${GREEN}✅ Environment configured${NC}\n"

# Step 3: Choose deployment method
echo "🚀 Choose deployment method:"
echo "1) Docker (Recommended for production)"
echo "2) Local development"
echo -n "Enter choice [1-2]: "
read -r choice

case $choice in
    1)
        if [ "$USE_DOCKER" = false ]; then
            echo -e "${RED}Docker not installed. Falling back to local setup.${NC}"
            choice=2
        else
            echo -e "\n${GREEN}Starting with Docker...${NC}"
            
            # Stop any existing containers
            docker-compose down 2>/dev/null || true
            
            # Start services
            docker-compose up -d
            
            # Wait for services
            wait_for_service "http://localhost:8000/health" "Backend API"
            wait_for_service "http://localhost:8002/health" "Gateway"
            
            echo -e "\n${GREEN}✅ All services started with Docker${NC}"
        fi
        ;;
    2)
        echo -e "\n${GREEN}Starting local development setup...${NC}"
        
        # Setup Python virtual environment
        if [ ! -d "venv" ]; then
            echo "Creating Python virtual environment..."
            python3 -m venv venv
        fi
        
        # Activate and install Python dependencies
        source venv/bin/activate
        pip install -q --upgrade pip
        pip install -q -r requirements.txt
        pip install -q numpy httpx
        
        # Install Node dependencies for gateway
        cd forge-gateway
        npm install --silent
        cd ..
        
        # Setup local PostgreSQL database
        if command_exists psql; then
            echo "Setting up database..."
            createdb agentforge 2>/dev/null || echo "Database already exists"
            psql agentforge < database/schema.sql 2>/dev/null || echo "Schema already applied"
        else
            echo -e "${YELLOW}⚠️  PostgreSQL not found. Using in-memory database${NC}"
        fi
        
        # Start services
        echo "Starting services..."
        
        # Kill any existing processes
        pkill -f "uvicorn" 2>/dev/null || true
        pkill -f "node gateway.js" 2>/dev/null || true
        sleep 2
        
        # Start backend
        cd backend
        if [ -f "optimized/main_v2.py" ]; then
            echo "Using optimized Context IS Runtime engine..."
            nohup python3 optimized/main_v2.py > ../logs/backend.log 2>&1 &
        else
            nohup uvicorn main:app --host 0.0.0.0 --port 8000 > ../logs/backend.log 2>&1 &
        fi
        cd ..
        
        # Start gateway
        cd forge-gateway
        nohup node gateway.js > ../logs/gateway.log 2>&1 &
        cd ..
        
        # Wait for services
        wait_for_service "http://localhost:8000/health" "Backend API"
        wait_for_service "http://localhost:8002/health" "Gateway"
        
        echo -e "\n${GREEN}✅ All services started locally${NC}"
        ;;
    *)
        echo -e "${RED}Invalid choice${NC}"
        exit 1
        ;;
esac

# Step 4: Run initial tests
echo -e "\n🧪 Running health checks..."

# Test backend
if curl -s http://localhost:8000/health/v2 | grep -q "healthy"; then
    echo -e "  ${GREEN}✅${NC} Backend API: healthy"
else
    echo -e "  ${RED}❌${NC} Backend API: not responding"
fi

# Test gateway
if curl -s http://localhost:8002/health | grep -q "healthy"; then
    echo -e "  ${GREEN}✅${NC} Gateway: healthy"
else
    echo -e "  ${YELLOW}⚠️${NC} Gateway: not responding"
fi

# Step 5: Display dashboard
echo -e "\n${GREEN}═══════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}🎯 AGENT.FORGE IS READY!${NC}"
echo -e "${GREEN}═══════════════════════════════════════════════════════════${NC}\n"

echo "📚 Documentation: http://localhost:8000/docs"
echo "🔥 Backend API: http://localhost:8000"
echo "🌉 Gateway: http://localhost:8002"
echo ""
echo "Quick Actions:"
echo "  1) View API docs: $OPEN_CMD http://localhost:8000/docs"
echo "  2) Monitor system: python3 monitor.py"
echo "  3) Run tests: python3 test_performance.py"
echo "  4) View logs: tail -f logs/backend.log"
echo "  5) Stop services: ./deploy.sh stop"
echo ""
echo -e "${YELLOW}Next Steps:${NC}"
echo "  1. Add your LLM API keys to .env file"
echo "  2. Create your first client via API"
echo "  3. Deploy widget to your website"
echo "  4. Monitor conversations in real-time"
echo ""
echo -e "${GREEN}Context IS Runtime - The conversation doesn't happen ON the system${NC}"
echo -e "${GREEN}The conversation IS the system. Welcome to the future.${NC}"
echo ""
echo "Built from Medellín with 🔥 and ☕"
echo "This is the way."

# Optional: Open browser
echo -e "\n${YELLOW}Press Enter to open API documentation in browser, or Ctrl+C to skip${NC}"
read -r
$OPEN_CMD http://localhost:8000/docs
