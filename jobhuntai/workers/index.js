// Main entry point for JobHunt AI Worker
// Exports: HTTP handler, Durable Object, Queue consumer

import app from './api.js';
import { OrgCoordinator } from './durable-objects/org-coordinator.js';
import queueConsumer from './queue-consumer.js';
import { handleNaturalLanguage } from './nl-orchestrator.js';

// Add natural language orchestration endpoint
app.post('/api/orchestrate', async (c) => {
  try {
    const { query } = await c.req.json();

    if (!query) {
      return c.json({ error: 'Missing query parameter' }, 400);
    }

    const result = await handleNaturalLanguage(query, c.env);
    return c.json(result);
  } catch (error) {
    console.error('[Orchestrate] Error:', error);
    return c.json({ error: error.message }, 500);
  }
});

// Add coordinator status endpoint for debugging
app.get('/api/coordinator/:org_id/status', async (c) => {
  try {
    const org_id = c.params.org_id;
    const id = c.env.ORG_COORDINATOR.idFromName(org_id);
    const coordinator = c.env.ORG_COORDINATOR.get(id);

    const response = await coordinator.fetch('http://coordinator/status');
    const status = await response.json();

    return c.json(status);
  } catch (error) {
    console.error('[CoordinatorStatus] Error:', error);
    return c.json({ error: error.message }, 500);
  }
});

// Add coordinator orchestration trigger endpoint
app.post('/api/coordinator/:org_id/orchestrate', async (c) => {
  try {
    const org_id = c.params.org_id;
    const body = await c.req.json().catch(() => ({}));

    const id = c.env.ORG_COORDINATOR.idFromName(org_id);
    const coordinator = c.env.ORG_COORDINATOR.get(id);

    const response = await coordinator.fetch('http://coordinator/orchestrate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body)
    });

    const result = await response.json();
    return c.json(result);
  } catch (error) {
    console.error('[CoordinatorOrchestrate] Error:', error);
    return c.json({ error: error.message }, 500);
  }
});

// Export HTTP handler (default)
export default app;

// Export Durable Object class
export { OrgCoordinator };

// Export queue consumer
export const queue = queueConsumer.queue;
