FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY brain_production.py brain_server.py
COPY enhanced_tools.py .
COPY tool_implementations.py .
COPY enhanced_webhook_handler.py .

# Create logs directory
RUN mkdir -p /app/logs

# Health check endpoint
EXPOSE 8080

# Run the brain server
CMD ["python", "brain_server.py"]