# AGENT.FORGE BACKEND DOCKERFILE
# The Container of Valinor - Built for Railway Deployment
# 
# From Medellín with love and game theory

FROM python:3.11-slim

# The metadata of power
LABEL maintainer="THE ANON <noreply@agent.forge>"
LABEL description="Agent.Forge Backend - Multi-tenant Agent Deployment Platform"
LABEL version="1.0.0"

# Set working directory
WORKDIR /app

# Install system dependencies (The foundations of Númenor)
RUN apt-get update && apt-get install -y \
    curl \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY backend/ .

# Create non-root user for security (The Rangers' tradition)
RUN useradd -m -u 1000 agentforge && \
    chown -R agentforge:agentforge /app
USER agentforge

# Expose port
EXPOSE 8000

# Health check (The beacons of Gondor)
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Start command
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]