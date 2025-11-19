// RevOps Engine Main API Worker
import { Hono } from 'hono';

const app = new Hono();

// Health check
app.get('/', (c) => {
  return c.json({ status: 'ok', service: 'revops-engine' });
});

// Route to specialized workers
app.post('/search', async (c) => {
  // Forward to search worker
  const response = await fetch('https://revops-search.aijesusbro-brain.workers.dev', {
    method: 'POST',
    body: JSON.stringify(await c.req.json()),
    headers: { 'Content-Type': 'application/json' }
  });
  return c.json(await response.json());
});

app.post('/scrape', async (c) => {
  const response = await fetch('https://revops-scraper.aijesusbro-brain.workers.dev', {
    method: 'POST',
    body: JSON.stringify(await c.req.json()),
    headers: { 'Content-Type': 'application/json' }
  });
  return c.json(await response.json());
});

app.post('/enrich', async (c) => {
  const response = await fetch('https://revops-enrichment.aijesusbro-brain.workers.dev', {
    method: 'POST',
    body: JSON.stringify(await c.req.json()),
    headers: { 'Content-Type': 'application/json' }
  });
  return c.json(await response.json());
});

app.post('/research', async (c) => {
  const response = await fetch('https://revops-researcher.aijesusbro-brain.workers.dev', {
    method: 'POST',
    body: JSON.stringify(await c.req.json()),
    headers: { 'Content-Type': 'application/json' }
  });
  return c.json(await response.json());
});

app.post('/write', async (c) => {
  const response = await fetch('https://revops-writer.aijesusbro-brain.workers.dev', {
    method: 'POST',
    body: JSON.stringify(await c.req.json()),
    headers: { 'Content-Type': 'application/json' }
  });
  return c.json(await response.json());
});

app.all('/tracker/*', async (c) => {
  const response = await fetch(`https://revops-tracker.aijesusbro-brain.workers.dev${c.req.path}`, {
    method: c.req.method,
    body: c.req.method !== 'GET' ? JSON.stringify(await c.req.json()) : undefined,
    headers: { 'Content-Type': 'application/json' }
  });
  return c.json(await response.json());
});

export default app;


