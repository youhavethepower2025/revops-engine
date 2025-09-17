const express = require('express');
const axios = require('axios');
const crypto = require('crypto');

const app = express();
app.use(express.json());

// Configuration
const SPECTRUM_URL = process.env.SPECTRUM_URL || 'http://localhost:8080/sse';
const SPECTRUM_HEALTH_URL = process.env.SPECTRUM_HEALTH_URL || 'http://localhost:8080/health';
const PORT = process.env.PORT || 8002;
const API_KEY = process.env.GATEWAY_API_KEY || crypto.randomBytes(32).toString('hex');

// Simple API key authentication middleware
const authenticate = (req, res, next) => {
  const authHeader = req.headers['authorization'];
  const providedKey = authHeader && authHeader.replace('Bearer ', '');

  if (!providedKey || providedKey !== API_KEY) {
    console.error('[GATEWAY] Authentication failed from', req.ip);
    return res.status(401).json({ error: 'Unauthorized' });
  }

  next();
};

// Rate limiting (simple in-memory)
const rateLimiter = new Map();
const RATE_LIMIT = 100; // requests per minute per IP
const RATE_WINDOW = 60000; // 1 minute

const checkRateLimit = (req, res, next) => {
  const ip = req.ip;
  const now = Date.now();

  if (!rateLimiter.has(ip)) {
    rateLimiter.set(ip, { count: 1, resetTime: now + RATE_WINDOW });
    return next();
  }

  const limit = rateLimiter.get(ip);

  if (now > limit.resetTime) {
    limit.count = 1;
    limit.resetTime = now + RATE_WINDOW;
    return next();
  }

  if (limit.count >= RATE_LIMIT) {
    console.error('[GATEWAY] Rate limit exceeded for', ip);
    return res.status(429).json({ error: 'Too many requests' });
  }

  limit.count++;
  next();
};

// Clean up rate limiter periodically
setInterval(() => {
  const now = Date.now();
  for (const [ip, limit] of rateLimiter.entries()) {
    if (now > limit.resetTime) {
      rateLimiter.delete(ip);
    }
  }
}, 60000);

// Log requests
app.use((req, res, next) => {
  console.log(`[GATEWAY] ${new Date().toISOString()} - ${req.method} ${req.path} - ${req.ip}`);
  next();
});

// Health check endpoint (no auth required)
app.get('/health', async (req, res) => {
  try {
    const spectrumHealth = await axios.get(SPECTRUM_HEALTH_URL, { timeout: 5000 });
    res.status(200).json({
      gateway_status: 'healthy',
      spectrum_status: spectrumHealth.data,
      timestamp: new Date().toISOString()
    });
  } catch (error) {
    res.status(500).json({
      gateway_status: 'healthy',
      spectrum_status: 'unreachable',
      error: error.message
    });
  }
});

// Main MCP endpoint (requires authentication)
app.post('/mcp', authenticate, checkRateLimit, async (req, res) => {
  const { tool, args } = req.body;

  // Validate input
  if (!tool || typeof tool !== 'string') {
    return res.status(400).json({ error: 'Invalid tool parameter' });
  }

  if (!args || typeof args !== 'object') {
    return res.status(400).json({ error: 'Invalid args parameter' });
  }

  // Sanitize tool name (prevent injection)
  const sanitizedTool = tool.replace(/[^a-zA-Z0-9_-]/g, '');

  console.log(`[GATEWAY] Tool call: ${sanitizedTool}`);

  const jsonRpcPayload = {
    jsonrpc: '2.0',
    method: 'tools/call',
    params: {
      name: sanitizedTool,
      arguments: args
    },
    id: Date.now()
  };

  try {
    const spectrumResponse = await axios.post(SPECTRUM_URL, jsonRpcPayload, {
      headers: { 'Content-Type': 'application/json' },
      timeout: 30000 // 30 second timeout
    });

    const responseData = spectrumResponse.data;

    if (responseData.error) {
      console.error('[GATEWAY] MCP error:', responseData.error.message);
      res.status(500).json({
        source: 'mcp-error',
        code: responseData.error.code,
        message: responseData.error.message
      });
    } else if (responseData.result && responseData.result.content && responseData.result.content[0]) {
      const resultText = responseData.result.content[0].text;
      res.status(200).send(resultText);
    } else {
      console.error('[GATEWAY] Unexpected response structure');
      res.status(500).json({ error: 'Unexpected response structure from MCP' });
    }

  } catch (error) {
    console.error('[GATEWAY] Communication error:', error.message);

    if (error.code === 'ECONNREFUSED') {
      res.status(503).json({
        source: 'gateway-error',
        error: 'MCP server is unavailable'
      });
    } else if (error.code === 'ETIMEDOUT') {
      res.status(504).json({
        source: 'gateway-error',
        error: 'MCP request timed out'
      });
    } else {
      res.status(500).json({
        source: 'gateway-error',
        error: 'Failed to communicate with MCP',
        details: error.message
      });
    }
  }
});

// 404 handler
app.use((req, res) => {
  res.status(404).json({ error: 'Endpoint not found' });
});

// Error handler
app.use((err, req, res, next) => {
  console.error('[GATEWAY] Unhandled error:', err);
  res.status(500).json({ error: 'Internal server error' });
});

// Start server
app.listen(PORT, '127.0.0.1', () => {
  console.log(`
  ╔═══════════════════════════════════════════╗
  ║          FORGE GATEWAY (SECURE)           ║
  ╠═══════════════════════════════════════════╣
  ║  Port: ${PORT}                               ║
  ║  Spectrum: ${SPECTRUM_URL}            ║
  ╠═══════════════════════════════════════════╣
  ║  API Key: ${API_KEY.substring(0, 8)}...                 ║
  ╠═══════════════════════════════════════════╣
  ║  Authentication: ✓ Enabled                ║
  ║  Rate Limiting: ✓ 100 req/min             ║
  ║  Binding: 127.0.0.1 only                  ║
  ╚═══════════════════════════════════════════╝
  `);

  if (API_KEY === crypto.randomBytes(32).toString('hex')) {
    console.warn('⚠️  WARNING: Using random API key. Set GATEWAY_API_KEY environment variable.');
  }
});

// Graceful shutdown
process.on('SIGTERM', () => {
  console.log('[GATEWAY] Shutting down gracefully...');
  process.exit(0);
});

process.on('SIGINT', () => {
  console.log('[GATEWAY] Shutting down gracefully...');
  process.exit(0);
});