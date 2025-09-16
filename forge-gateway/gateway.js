
const express = require('express');
const axios = require('axios');

const app = express();
app.use(express.json());

const SPECTRUM_URL = 'http://localhost:8080/sse';
const SPECTRUM_HEALTH_URL = 'http://localhost:8080/health';
const PORT = 8002;

// Log requests for clarity
app.use((req, res, next) => {
  console.log(`[FORGE-GATEWAY] ${new Date().toISOString()} - ${req.method} ${req.path}`);
  next();
});

/**
 * Health check endpoint.
 * Checks the gateway's status and its connection to the Spectrum server.
 */
app.get('/health', async (req, res) => {
  console.log('[FORGE-GATEWAY] Health check initiated.');
  try {
    const spectrumHealth = await axios.get(SPECTRUM_HEALTH_URL);
    res.status(200).json({
      gateway_status: 'healthy',
      spectrum_status: spectrumHealth.data,
      timestamp: new Date().toISOString()
    });
  } catch (error) {
    console.error('[FORGE-GATEWAY] Spectrum health check failed:', error.message);
    res.status(500).json({
      gateway_status: 'healthy',
      spectrum_status: 'unreachable',
      error: error.message
    });
  }
});

/**
 * Main endpoint for receiving tool calls from THE FORGE.
 * Translates and forwards them to the Spectrum MCP server.
 */
app.post('/mcp', async (req, res) => {
  const { tool, args } = req.body;

  if (!tool || !args) {
    console.error('[FORGE-GATEWAY] Invalid request body:', req.body);
    return res.status(400).json({ error: 'Request must include "tool" and "args" fields.' });
  }

  console.log(`[FORGE-GATEWAY] Received tool call: ${tool}`);

  const jsonRpcPayload = {
    jsonrpc: '2.0',
    method: 'tools/call',
    params: {
      name: tool,
      arguments: args
    },
    id: Date.now() // Using timestamp as a simple unique ID
  };

  try {
    console.log('[FORGE-GATEWAY] Forwarding to Spectrum MCP:', JSON.stringify(jsonRpcPayload, null, 2));
    const spectrumResponse = await axios.post(SPECTRUM_URL, jsonRpcPayload, {
      headers: { 'Content-Type': 'application/json' }
    });

    const responseData = spectrumResponse.data;
    console.log('[FORGE-GATEWAY] Received from Spectrum MCP:', JSON.stringify(responseData, null, 2));

    if (responseData.error) {
      // Handle JSON-RPC errors
      console.error('[FORGE-GATEWAY] Spectrum MCP returned an error:', responseData.error.message);
      res.status(500).json({
        source: 'spectrum-mcp-error',
        code: responseData.error.code,
        message: responseData.error.message
      });
    } else if (responseData.result && responseData.result.content && responseData.result.content[0]) {
      // Handle successful responses
      const resultText = responseData.result.content[0].text;
      res.status(200).send(resultText);
    } else {
      // Handle unexpected success formats
      console.error('[FORGE-GATEWAY] Unexpected response structure from Spectrum MCP.');
      res.status(500).json({ error: 'Unexpected response structure from Spectrum MCP.' });
    }

  } catch (error) {
    console.error('[FORGE-GATEWAY] Error communicating with Spectrum MCP:', error.message);
    res.status(500).json({
      source: 'gateway-error',
      error: 'Failed to communicate with Spectrum MCP.',
      details: error.message
    });
  }
});

app.listen(PORT, () => {
  console.log(`
  ████████╗ ██████╗  ██████╗  ██████╗ ███████╗
  ╚══██╔══╝██╔═══██╗██╔════╝ ██╔════╝ ██╔════╝
     ██║   ██║   ██║██║  ███╗██║  ███╗█████╗
     ██║   ██║   ██║██║   ██║██║   ██║██╔══╝
     ██║   ╚██████╔╝╚██████╔╝╚██████╔╝███████╗
     ╚═╝    ╚═════╝  ╚═════╝  ╚═════╝ ╚══════╝
  `);
  console.log('THE FORGE GATEWAY IS ALIVE.');
  console.log(`Listening on http://localhost:${PORT}`);
  console.log('Ready to bridge the gap.');
  console.log('This is the Way.');
});
