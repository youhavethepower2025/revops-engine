// Main Worker Entry Point - Multi-tenant routing

import { Env } from './types';
import { ClientBrain } from './brain';

export { ClientBrain };

export default {
  async fetch(request: Request, env: Env, ctx: ExecutionContext): Promise<Response> {
    const url = new URL(request.url);

    // Health check for the worker itself
    if (url.pathname === '/') {
      return new Response(JSON.stringify({
        name: 'Retell Brain MCP',
        version: '1.0.0',
        description: 'Multi-tenant AI Infrastructure as a Service',
        endpoints: {
          mcp: '/mcp?client_id={id}',
          retell_webhook: '/retell/webhook?client_id={id}',
          ghl_webhook: '/ghl/webhook?client_id={id}',
          health: '/health?client_id={id}'
        },
        status: 'operational',
        timestamp: Date.now()
      }), {
        headers: { 'Content-Type': 'application/json' }
      });
    }

    // Extract client_id from query params or request body
    let clientId = url.searchParams.get('client_id');

    if (!clientId && request.method === 'POST') {
      try {
        const body = await request.clone().json();
        clientId = body.client_id || body.call?.metadata?.client_id;
      } catch (e) {
        // Body parsing failed, continue without client_id
      }
    }

    if (!clientId) {
      return new Response(JSON.stringify({
        error: 'Missing client_id parameter'
      }), {
        status: 400,
        headers: { 'Content-Type': 'application/json' }
      });
    }

    // Get the Durable Object for this client
    const id = env.BRAIN.idFromName(clientId);
    const brain = env.BRAIN.get(id);

    // Forward the request to the client's brain
    return brain.fetch(request);
  }
};
