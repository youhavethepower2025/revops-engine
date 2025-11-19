// Content Intelligence Main API Worker
import { Hono } from 'hono';

const app = new Hono();

app.get('/', (c) => {
  return c.json({ status: 'ok', service: 'content-intelligence' });
});

// Route to specialized workers
app.post('/search', async (c) => {
  const response = await fetch('https://content-search.aijesusbro-brain.workers.dev', {
    method: 'POST',
    body: JSON.stringify(await c.req.json()),
    headers: { 'Content-Type': 'application/json' }
  });
  return c.json(await response.json());
});

app.post('/fetch', async (c) => {
  const response = await fetch('https://content-fetcher.aijesusbro-brain.workers.dev', {
    method: 'POST',
    body: JSON.stringify(await c.req.json()),
    headers: { 'Content-Type': 'application/json' }
  });
  return c.json(await response.json());
});

app.post('/analyze', async (c) => {
  const response = await fetch('https://content-analyzer.aijesusbro-brain.workers.dev', {
    method: 'POST',
    body: JSON.stringify(await c.req.json()),
    headers: { 'Content-Type': 'application/json' }
  });
  return c.json(await response.json());
});

app.post('/graph', async (c) => {
  const response = await fetch('https://content-grapher.aijesusbro-brain.workers.dev', {
    method: 'POST',
    body: JSON.stringify(await c.req.json()),
    headers: { 'Content-Type': 'application/json' }
  });
  return c.json(await response.json());
});

app.post('/synthesize', async (c) => {
  const response = await fetch('https://content-synthesizer.aijesusbro-brain.workers.dev', {
    method: 'POST',
    body: JSON.stringify(await c.req.json()),
    headers: { 'Content-Type': 'application/json' }
  });
  return c.json(await response.json());
});

app.all('/monitor/*', async (c) => {
  const response = await fetch(`https://content-monitor.aijesusbro-brain.workers.dev${c.req.path}`, {
    method: c.req.method,
    body: c.req.method !== 'GET' ? JSON.stringify(await c.req.json()) : undefined,
    headers: { 'Content-Type': 'application/json' }
  });
  return c.json(await response.json());
});

export default app;


