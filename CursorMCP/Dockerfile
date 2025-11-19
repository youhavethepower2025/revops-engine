FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY src/ ./src/

# Set Python path so we can import cursormcp
ENV PYTHONPATH=/app/src

# Run MCP server via stdio
ENTRYPOINT ["python", "-m", "cursormcp.main"]

