# Make deployment script executable
chmod +x deploy.sh

# Environment variables
export DATABASE_URL="postgresql://agentforge:password@localhost:5432/agentforge"
export JWT_SECRET=$(openssl rand -hex 32)
export ENVIRONMENT="production"

# LLM API Keys (add your own)
export OPENAI_API_KEY=""
export ANTHROPIC_API_KEY=""
export GROQ_API_KEY=""

# Create required directories
mkdir -p logs
mkdir -p deployment/ssl

# Generate self-signed SSL certificate for local testing
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
    -keyout deployment/ssl/key.pem \
    -out deployment/ssl/cert.pem \
    -subj "/C=CO/ST=Antioquia/L=Medellin/O=AgentForge/CN=localhost"

echo "Environment configured for deployment"
