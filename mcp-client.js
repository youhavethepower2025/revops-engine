#!/usr/bin/env node

/**
 * RevOps MCP Client - Stdio Bridge
 *
 * This script bridges Claude Desktop (stdio) to the RevOps MCP HTTP endpoint.
 * It reads MCP JSON-RPC requests from stdin and forwards them to the HTTP API.
 */

const https = require('https');
const http = require('http');
const readline = require('readline');

// Configuration from environment variables
const API_KEY = process.env.REVOPS_API_KEY;
const ENDPOINT = process.env.REVOPS_ENDPOINT || 'https://mcp.revops.ai/mcp';

if (!API_KEY) {
  console.error(JSON.stringify({
    jsonrpc: '2.0',
    id: null,
    error: {
      code: -32000,
      message: 'REVOPS_API_KEY environment variable is required'
    }
  }));
  process.exit(1);
}

// Parse endpoint URL
const url = new URL(ENDPOINT);
const isHttps = url.protocol === 'https:';
const httpModule = isHttps ? https : http;

// Create readline interface for stdio
const rl = readline.createInterface({
  input: process.stdin,
  output: process.stdout,
  terminal: false
});

// Log to stderr (so it doesn't interfere with JSON-RPC on stdout)
function log(message) {
  if (process.env.DEBUG === 'true') {
    console.error(`[MCP Client] ${message}`);
  }
}

/**
 * Forward MCP request to HTTP endpoint
 */
async function forwardRequest(mcpRequest) {
  return new Promise((resolve, reject) => {
    const requestData = JSON.stringify(mcpRequest);

    const options = {
      hostname: url.hostname,
      port: url.port || (isHttps ? 443 : 80),
      path: url.pathname,
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Content-Length': Buffer.byteLength(requestData),
        'Authorization': `Bearer ${API_KEY}`,
        'User-Agent': 'RevOps-MCP-Client/1.0'
      }
    };

    log(`Sending request to ${ENDPOINT}: ${mcpRequest.method}`);

    const req = httpModule.request(options, (res) => {
      let responseData = '';

      res.on('data', (chunk) => {
        responseData += chunk;
      });

      res.on('end', () => {
        try {
          if (res.statusCode === 200) {
            const response = JSON.parse(responseData);
            log(`Received response: ${JSON.stringify(response).substring(0, 100)}...`);
            resolve(response);
          } else {
            log(`HTTP error ${res.statusCode}: ${responseData}`);
            reject(new Error(`HTTP ${res.statusCode}: ${responseData}`));
          }
        } catch (error) {
          log(`Parse error: ${error.message}`);
          reject(new Error(`Failed to parse response: ${error.message}`));
        }
      });
    });

    req.on('error', (error) => {
      log(`Request error: ${error.message}`);
      reject(error);
    });

    // Set timeout (30 seconds)
    req.setTimeout(30000, () => {
      req.destroy();
      reject(new Error('Request timeout'));
    });

    req.write(requestData);
    req.end();
  });
}

/**
 * Process each line from stdin (MCP JSON-RPC protocol)
 */
rl.on('line', async (line) => {
  try {
    // Parse MCP request
    const mcpRequest = JSON.parse(line);

    // Forward to HTTP endpoint
    const mcpResponse = await forwardRequest(mcpRequest);

    // Write response to stdout (JSON-RPC protocol)
    console.log(JSON.stringify(mcpResponse));
  } catch (error) {
    // Return JSON-RPC error
    const errorResponse = {
      jsonrpc: '2.0',
      id: null,
      error: {
        code: -32603,
        message: error.message || 'Internal error'
      }
    };

    console.log(JSON.stringify(errorResponse));
  }
});

rl.on('close', () => {
  log('MCP client closing');
  process.exit(0);
});

// Handle signals
process.on('SIGINT', () => {
  log('Received SIGINT');
  process.exit(0);
});

process.on('SIGTERM', () => {
  log('Received SIGTERM');
  process.exit(0);
});

log('RevOps MCP Client started');
log(`Endpoint: ${ENDPOINT}`);
log(`API Key: ${API_KEY.substring(0, 20)}...`);
