#!/usr/bin/env node
/**
 * MCP stdio-to-HTTP bridge with comprehensive logging
 * All logs saved to /Users/aijesusbro/AI Projects/mcp_logs/
 */

const readline = require('readline');
const https = require('https');
const fs = require('fs');
const path = require('path');

const SERVER_URL = process.argv[2];
if (!SERVER_URL) {
  console.error('Usage: mcp-http-bridge-with-logging.js <server-url>');
  process.exit(1);
}

// Setup logging directory
const LOG_DIR = '/Users/aijesusbro/AI Projects/mcp_logs';
const LOG_FILE = path.join(LOG_DIR, `mcp_bridge_${new Date().toISOString().split('T')[0]}.log`);
const REQUEST_LOG = path.join(LOG_DIR, `mcp_requests_${new Date().toISOString().split('T')[0]}.jsonl`);
const RESPONSE_LOG = path.join(LOG_DIR, `mcp_responses_${new Date().toISOString().split('T')[0]}.jsonl`);

// Ensure log directory exists
if (!fs.existsSync(LOG_DIR)) {
  fs.mkdirSync(LOG_DIR, { recursive: true });
}

// Log to both stderr and file
const log = (msg, level = 'INFO') => {
  const timestamp = new Date().toISOString();
  const logEntry = `[${timestamp}] [${level}] ${msg}`;
  
  // Write to stderr (for immediate console feedback)
  process.stderr.write(`[Bridge] ${msg}\n`);
  
  // Append to log file
  fs.appendFileSync(LOG_FILE, logEntry + '\n');
};

// Log JSON data to separate files for easy parsing
const logRequest = (request) => {
  const entry = {
    timestamp: new Date().toISOString(),
    type: 'request',
    method: request.method,
    id: request.id,
    data: request
  };
  fs.appendFileSync(REQUEST_LOG, JSON.stringify(entry) + '\n');
};

const logResponse = (response, requestMethod) => {
  const entry = {
    timestamp: new Date().toISOString(),
    type: 'response',
    requestMethod: requestMethod,
    id: response.id,
    data: response
  };
  fs.appendFileSync(RESPONSE_LOG, JSON.stringify(entry) + '\n');
};

log(`Starting bridge to ${SERVER_URL}`);
log(`Logs will be saved to: ${LOG_DIR}`);

// Setup stdio interface
const rl = readline.createInterface({
  input: process.stdin,
  output: process.stdout,
  terminal: false
});

// Handle JSON-RPC messages from Claude
rl.on('line', async (line) => {
  try {
    const request = JSON.parse(line);
    log(`Request received: ${request.method} (id: ${request.id})`);
    logRequest(request);
    
    // Forward to HTTP server
    log(`Forwarding to ${SERVER_URL}`);
    const startTime = Date.now();
    
    const response = await fetch(SERVER_URL, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json'
      },
      body: JSON.stringify(request)
    });
    
    const responseTime = Date.now() - startTime;
    log(`Response received in ${responseTime}ms - Status: ${response.status}`);
    
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }
    
    const result = await response.json();
    logResponse(result, request.method);
    
    // Send response back to Claude via stdout
    process.stdout.write(JSON.stringify(result) + '\n');
    log(`Response sent back to Claude for: ${request.method}`);
    
  } catch (error) {
    log(`Error: ${error.message}`, 'ERROR');
    log(`Stack trace: ${error.stack}`, 'ERROR');
    
    // Send error response in JSON-RPC format
    const errorResponse = {
      jsonrpc: '2.0',
      error: {
        code: -32603,
        message: `Bridge error: ${error.message}`
      },
      id: null
    };
    
    logResponse(errorResponse, 'ERROR');
    process.stdout.write(JSON.stringify(errorResponse) + '\n');
  }
});

// Handle errors on stdin
rl.on('error', (error) => {
  log(`Readline error: ${error.message}`, 'ERROR');
});

// Handle termination gracefully
process.on('SIGTERM', () => {
  log('Received SIGTERM, shutting down gracefully');
  process.exit(0);
});

process.on('SIGINT', () => {
  log('Received SIGINT, shutting down gracefully');
  process.exit(0);
});

process.on('uncaughtException', (error) => {
  log(`Uncaught exception: ${error.message}`, 'FATAL');
  log(`Stack trace: ${error.stack}`, 'FATAL');
  process.exit(1);
});

process.on('unhandledRejection', (reason, promise) => {
  log(`Unhandled rejection at: ${promise}, reason: ${reason}`, 'FATAL');
  process.exit(1);
});

// Log startup complete
log('Bridge initialization complete, waiting for requests...');

// Keep process alive
process.stdin.resume();