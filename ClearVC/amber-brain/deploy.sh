#!/bin/bash

# ClearVC Amber Brain Deployment Script

set -e

echo "🚀 ClearVC Amber Brain Deployment"
echo "================================"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check for required tools
check_requirements() {
    echo -e "${YELLOW}Checking requirements...${NC}"

    if ! command -v docker &> /dev/null; then
        echo -e "${RED}Docker is not installed. Please install Docker first.${NC}"
        exit 1
    fi

    if ! command -v docker-compose &> /dev/null; then
        echo -e "${RED}Docker Compose is not installed. Please install Docker Compose first.${NC}"
        exit 1
    fi

    echo -e "${GREEN}✓ All requirements met${NC}"
}

# Setup environment
setup_environment() {
    echo -e "${YELLOW}Setting up environment...${NC}"

    if [ ! -f .env ]; then
        echo -e "${YELLOW}Creating .env file from .env.example...${NC}"
        cp .env.example .env
        echo -e "${RED}⚠️  Please edit .env file with your credentials before continuing${NC}"
        echo "Press Enter when ready to continue..."
        read
    fi

    echo -e "${GREEN}✓ Environment configured${NC}"
}

# Build containers
build_containers() {
    echo -e "${YELLOW}Building Docker containers...${NC}"
    docker-compose build --no-cache
    echo -e "${GREEN}✓ Containers built${NC}"
}

# Start services
start_services() {
    echo -e "${YELLOW}Starting services...${NC}"
    docker-compose up -d
    echo -e "${GREEN}✓ Services started${NC}"
}

# Check health
check_health() {
    echo -e "${YELLOW}Checking service health...${NC}"
    sleep 5

    # Check if services are running
    if docker-compose ps | grep -q "amber-brain.*Up"; then
        echo -e "${GREEN}✓ Amber Brain is running${NC}"
    else
        echo -e "${RED}✗ Amber Brain failed to start${NC}"
        docker-compose logs amber-brain
        exit 1
    fi

    # Check API health
    echo -e "${YELLOW}Checking API health...${NC}"
    sleep 3

    if curl -s http://localhost:8000/health | grep -q "healthy"; then
        echo -e "${GREEN}✓ API is healthy${NC}"
    else
        echo -e "${YELLOW}⚠️  API health check failed - may still be starting${NC}"
    fi
}

# Display status
display_status() {
    echo ""
    echo -e "${GREEN}==================================${NC}"
    echo -e "${GREEN}Amber Brain Deployment Complete!${NC}"
    echo -e "${GREEN}==================================${NC}"
    echo ""
    echo "📍 Access Points:"
    echo "   - API: http://localhost:8000"
    echo "   - Docs: http://localhost:8000/docs"
    echo "   - Health: http://localhost:8000/health"
    echo ""
    echo "🔧 Useful Commands:"
    echo "   - View logs: docker-compose logs -f amber-brain"
    echo "   - Stop services: docker-compose down"
    echo "   - Restart: docker-compose restart"
    echo ""
    echo "📝 Webhook URLs for Retell:"
    echo "   - Call Start: http://your-domain.com/webhooks/retell/call-started"
    echo "   - Call End: http://your-domain.com/webhooks/retell/call-ended"
    echo "   - Transcript: http://your-domain.com/webhooks/retell/transcript-update"
    echo "   - Tool Call: http://your-domain.com/webhooks/retell/tool-call"
    echo ""
}

# Main execution
main() {
    check_requirements
    setup_environment
    build_containers
    start_services
    check_health
    display_status
}

# Handle script arguments
case "${1:-}" in
    start)
        docker-compose up -d
        echo -e "${GREEN}Services started${NC}"
        ;;
    stop)
        docker-compose down
        echo -e "${GREEN}Services stopped${NC}"
        ;;
    restart)
        docker-compose restart
        echo -e "${GREEN}Services restarted${NC}"
        ;;
    logs)
        docker-compose logs -f amber-brain
        ;;
    status)
        docker-compose ps
        ;;
    clean)
        docker-compose down -v
        echo -e "${YELLOW}All containers and volumes removed${NC}"
        ;;
    *)
        main
        ;;
esac