# Forge Gateway - Secure MCP Proxy

A secure gateway that bridges REST API calls to the Spectrum MCP server's JSON-RPC interface.

## Security Features

- **API Key Authentication**: All requests require a valid Bearer token
- **Rate Limiting**: 100 requests per minute per IP
- **Input Sanitization**: Tool names are sanitized to prevent injection
- **Timeout Protection**: 30-second timeout on MCP requests
- **Local Only Binding**: Listens on 127.0.0.1 by default

## Setup

1. Install dependencies:
```bash
npm install
```

2. Configure environment:
```bash
cp .env.example .env
# Edit .env and set your GATEWAY_API_KEY
```

3. Run the gateway:
```bash
# Insecure version (for testing only)
node gateway.js

# Secure version (for production)
node gateway_secure.js
```

## API Usage

### Health Check
```bash
curl http://localhost:8002/health
```

### MCP Tool Call (requires authentication)
```bash
curl -X POST http://localhost:8002/mcp \
  -H "Authorization: Bearer your-api-key-here" \
  -H "Content-Type: application/json" \
  -d '{
    "tool": "example_tool",
    "args": {
      "param1": "value1"
    }
  }'
```

## Security Configuration

### API Key
Set the `GATEWAY_API_KEY` environment variable. If not set, a random key will be generated and displayed on startup.

### Rate Limiting
Default: 100 requests per minute per IP address. Modify `RATE_LIMIT` in the code to adjust.

### Binding Address
By default binds to 127.0.0.1 (localhost only). To expose externally (not recommended), modify the listen call.

## Error Responses

- `401 Unauthorized`: Invalid or missing API key
- `429 Too Many Requests`: Rate limit exceeded
- `503 Service Unavailable`: MCP server is down
- `504 Gateway Timeout`: MCP request timed out

## Production Deployment

1. Use a proper process manager (PM2, systemd, etc.)
2. Set a strong API key
3. Consider putting behind a reverse proxy (nginx)
4. Enable HTTPS if exposing externally
5. Monitor logs for suspicious activity