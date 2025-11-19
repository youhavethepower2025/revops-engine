import { Hono } from 'hono';
import { cors } from 'hono/cors';
import { generateId, generateToken, hashPassword, verifyPassword, authMiddleware } from './lib/auth.js';
import { emitEvent, generateTraceId } from './lib/events.js';
import { indexHTML } from './lib/index-html.js';
import { appHTML } from './lib/app-html.js';
import { dashboardV2HTML } from './lib/dashboard-v2-html.js';

const app = new Hono();

// CORS for frontend
app.use('/*', cors());

// Health check
app.get('/health', (c) => {
  return c.json({ status: 'ok', environment: c.env.ENVIRONMENT || 'unknown' });
});

// Serve frontend HTML
app.get('/', (c) => {
  return c.html(indexHTML);
});

app.get('/dashboard', (c) => {
  return c.html(appHTML);
});

app.get('/dashboard-v2', (c) => {
  return c.html(dashboardV2HTML);
});

// CRM subdomain routes (aijesusbro.com/crm)
app.get('/crm', (c) => {
  return c.html(indexHTML);
});

app.get('/crm/dashboard', (c) => {
  return c.html(appHTML);
});

// Test Workers AI
app.get('/test/ai', async (c) => {
  try {
    const llama = await c.env.AI.run('@cf/meta/llama-3.1-70b-instruct', {
      messages: [
        { role: 'user', content: 'Write a one-sentence cold email subject line for a B2B SaaS company.' }
      ],
      max_tokens: 50
    });

    const qwen = await c.env.AI.run('@cf/qwen/qwen1.5-14b-chat-awq', {
      messages: [
        { role: 'user', content: 'Extract the company name: John Doe is CEO of Acme Corp.' }
      ],
      max_tokens: 20
    });

    return c.json({ llama, qwen });
  } catch (err) {
    return c.json({ error: err.message }, 500);
  }
});

// Test Browser Rendering
app.get('/test/scrape', async (c) => {
  try {
    const { scrapeCompanyWebsite } = await import('./lib/scraper.js');
    const domain = c.req.query('domain') || 'anthropic.com';
    const result = await scrapeCompanyWebsite(domain, c.env);
    return c.json(result);
  } catch (err) {
    return c.json({ error: err.message, stack: err.stack }, 500);
  }
});

// Test Research Agent
app.get('/test/research', async (c) => {
  try {
    // Create a test lead
    const { generateId } = await import('./lib/auth.js');
    const { generateTraceId, emitEvent } = await import('./lib/events.js');
    const { researchLead } = await import('./agents/research.js');

    const account_id = generateId();
    const lead_id = generateId();
    const trace_id = generateTraceId();

    // Create test account
    await c.env.DB.prepare(`
      INSERT INTO accounts (id, name, settings, created_at, updated_at)
      VALUES (?, ?, ?, ?, ?)
    `).bind(account_id, 'Test Account', '{}', Date.now(), Date.now()).run();

    // Insert test lead
    await c.env.DB.prepare(`
      INSERT INTO leads (id, account_id, name, email, company, status, created_at, updated_at)
      VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    `).bind(
      lead_id,
      account_id,
      'John Doe',
      'john@example.com',
      c.req.query('company') || 'anthropic.com',
      'new',
      Date.now(),
      Date.now()
    ).run();

    // Run research
    const result = await researchLead(lead_id, account_id, trace_id, c.env);

    // Get updated lead
    const lead = await c.env.DB.prepare('SELECT * FROM leads WHERE id = ?').bind(lead_id).first();

    return c.json({
      result,
      lead: {
        ...lead,
        metadata: JSON.parse(lead.metadata || '{}')
      }
    });
  } catch (err) {
    return c.json({ error: err.message, stack: err.stack }, 500);
  }
});

// Test Outreach Agent
app.get('/test/outreach', async (c) => {
  try {
    const { generateId } = await import('./lib/auth.js');
    const { generateTraceId } = await import('./lib/events.js');
    const { generateOutreach } = await import('./agents/outreach.js');

    const account_id = generateId();
    const lead_id = generateId();
    const campaign_id = generateId();
    const trace_id = generateTraceId();

    // Create test account
    await c.env.DB.prepare(`
      INSERT INTO accounts (id, name, settings, created_at, updated_at)
      VALUES (?, ?, ?, ?, ?)
    `).bind(account_id, 'Test Account', '{}', Date.now(), Date.now()).run();

    // Create test campaign
    await c.env.DB.prepare(`
      INSERT INTO campaigns (id, account_id, name, status, config, created_at)
      VALUES (?, ?, ?, ?, ?, ?)
    `).bind(
      campaign_id,
      account_id,
      'Test Campaign',
      'active',
      JSON.stringify({
        value_proposition: 'We help B2B SaaS companies close more deals with AI-powered outreach',
        differentiators: 'Fully autonomous, learns what works, adapts in real-time',
        sender_name: 'Alex Morgan',
        sender_email: 'alex@aijesusbro.com',
        company_name: 'The Exit'
      }),
      Date.now()
    ).run();

    // Create test lead with research data
    await c.env.DB.prepare(`
      INSERT INTO leads (id, account_id, campaign_id, name, email, company, metadata, status, created_at, updated_at)
      VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    `).bind(
      lead_id,
      account_id,
      campaign_id,
      'Sarah Chen',
      'sarah@example.com',
      'Anthropic',
      JSON.stringify({
        research: {
          company: {
            companyName: 'Anthropic',
            description: 'AI safety and research company building reliable, interpretable AI systems',
            industry: 'Artificial Intelligence',
            employeeCount: '100-500'
          }
        }
      }),
      'contacted',
      Date.now(),
      Date.now()
    ).run();

    // Run outreach
    const result = await generateOutreach(lead_id, account_id, trace_id, c.env);

    // Get generated conversation
    const conversation = await c.env.DB.prepare(
      'SELECT * FROM conversations WHERE lead_id = ?'
    ).bind(lead_id).first();

    return c.json({
      result,
      conversation: conversation ? {
        ...conversation,
        messages: JSON.parse(conversation.messages)
      } : null
    });
  } catch (err) {
    return c.json({ error: err.message, stack: err.stack }, 500);
  }
});

// API routes
const api = new Hono();

// ============================================================================
// PUBLIC ENDPOINTS (no auth required)
// ============================================================================

// Create account
api.post('/accounts', async (c) => {
  try {
    const { name, email, password } = await c.req.json();

    if (!name || !email || !password) {
      return c.json({ error: 'Missing required fields: name, email, password' }, 400);
    }

    // Check if email exists
    const existing = await c.env.DB.prepare(
      'SELECT id FROM users WHERE email = ?'
    ).bind(email).first();

    if (existing) {
      return c.json({ error: 'Email already registered' }, 409);
    }

    const account_id = generateId();
    const user_id = generateId();
    const timestamp = Date.now();
    const password_hash = await hashPassword(password);

    // Create account
    await c.env.DB.prepare(`
      INSERT INTO accounts (id, name, settings, created_at, updated_at)
      VALUES (?, ?, ?, ?, ?)
    `).bind(account_id, name, JSON.stringify({}), timestamp, timestamp).run();

    // Create owner user
    await c.env.DB.prepare(`
      INSERT INTO users (id, account_id, email, role, auth_token, created_at)
      VALUES (?, ?, ?, ?, ?, ?)
    `).bind(user_id, account_id, email, 'owner', password_hash, timestamp).run();

    // Generate JWT
    const token = await generateToken(user_id, account_id, c.env);

    // Emit event
    const trace_id = generateTraceId();
    await emitEvent(c.env.DB, {
      trace_id,
      account_id,
      event_type: 'account_created',
      entity_type: 'account',
      entity_id: account_id,
      payload: { name, email }
    });

    return c.json({
      account_id,
      user_id,
      token,
      account: { id: account_id, name }
    }, 201);
  } catch (err) {
    console.error('Error creating account:', err);
    return c.json({ error: 'Failed to create account' }, 500);
  }
});

// Login
api.post('/login', async (c) => {
  try {
    const { email, password } = await c.req.json();

    if (!email || !password) {
      return c.json({ error: 'Missing required fields: email, password' }, 400);
    }

    // Get user
    const user = await c.env.DB.prepare(`
      SELECT u.id, u.account_id, u.auth_token, a.name as account_name
      FROM users u
      JOIN accounts a ON a.id = u.account_id
      WHERE u.email = ?
    `).bind(email).first();

    if (!user) {
      return c.json({ error: 'Invalid email or password' }, 401);
    }

    // Verify password
    const valid = await verifyPassword(password, user.auth_token);
    if (!valid) {
      return c.json({ error: 'Invalid email or password' }, 401);
    }

    // Generate JWT
    const token = await generateToken(user.id, user.account_id, c.env);

    return c.json({
      token,
      user_id: user.id,
      account_id: user.account_id,
      account: { id: user.account_id, name: user.account_name }
    });
  } catch (err) {
    console.error('Error logging in:', err);
    return c.json({ error: 'Login failed' }, 500);
  }
});

// Strategy endpoints (public - no auth required)
api.get('/strategies', async (c) => {
  const { listStrategies } = await import('./lib/strategies.js');
  const strategies = listStrategies();

  return c.json({
    strategies: strategies.map(s => ({
      id: s.id,
      name: s.name,
      description: s.description,
      steps: s.steps.length,
      metadata: s.metadata
    }))
  });
});

api.get('/strategies/:id', async (c) => {
  const { getStrategy } = await import('./lib/strategies.js');
  const strategy = getStrategy(c.req.param('id'));

  if (!strategy) {
    return c.json({ error: 'Strategy not found' }, 404);
  }

  return c.json({ strategy });
});

// Webhook endpoints (public - no auth required)
api.post('/webhooks/email', async (c) => {
  const { handleEmailEvent } = await import('./webhooks/email-events.js');
  return await handleEmailEvent(c.req, c.env);
});

// ============================================================================
// PROTECTED ENDPOINTS (auth required)
// ============================================================================

// Apply auth middleware to all routes below
api.use('/*', authMiddleware);

// Get account
api.get('/accounts/:id', async (c) => {
  const account_id = c.get('accountId');
  const requested_id = c.req.param('id');

  // Users can only access their own account
  if (account_id !== requested_id) {
    return c.json({ error: 'Forbidden' }, 403);
  }

  const account = await c.env.DB.prepare(
    'SELECT id, name, settings, created_at FROM accounts WHERE id = ?'
  ).bind(account_id).first();

  if (!account) {
    return c.json({ error: 'Account not found' }, 404);
  }

  return c.json(account);
});

// ============================================================================
// Analytics endpoints
// Decision logs - show AI reasoning for entities
api.get('/decision_logs', async (c) => {
  const account_id = c.get('accountId');
  const entity_id = c.req.query('entity_id');
  const entity_type = c.req.query('entity_type');
  const agent_type = c.req.query('agent_type');
  const limit = parseInt(c.req.query('limit') || '10');

  let query = 'SELECT * FROM decision_logs WHERE account_id = ?';
  const params = [account_id];

  if (entity_id) {
    query += ' AND (lead_id = ? OR conversation_id = ? OR campaign_id = ?)';
    params.push(entity_id, entity_id, entity_id);
  }

  if (agent_type) {
    query += ' AND agent_type = ?';
    params.push(agent_type);
  }

  query += ' ORDER BY timestamp DESC LIMIT ?';
  params.push(limit);

  const logs = await c.env.DB.prepare(query).bind(...params).all();

  const formatted = logs.results.map(log => ({
    id: log.id,
    trace_id: log.trace_id,
    agent_type: log.agent_type,
    lead_id: log.lead_id,
    conversation_id: log.conversation_id,
    campaign_id: log.campaign_id,
    input_context: JSON.parse(log.input_context || '{}'),
    reasoning: log.reasoning,
    decision: JSON.parse(log.decision || '{}'),
    outcome: JSON.parse(log.outcome || '{}'),
    timestamp: log.timestamp
  }));

  return c.json({ decision_logs: formatted });
});

api.get('/analytics', async (c) => {
  // TODO: Get analytics data
  return c.json({ error: 'Not implemented' }, 501);
});

api.get('/analytics/patterns', async (c) => {
  // TODO: Get learned patterns
  return c.json({ error: 'Not implemented' }, 501);
});

// Events endpoint (for debugging/observability)
api.get('/events', async (c) => {
  const account_id = c.get('accountId');
  const limit = parseInt(c.req.query('limit') || '100');
  const event_type = c.req.query('event_type');

  try {
    let query = 'SELECT * FROM events WHERE account_id = ?';
    const params = [account_id];

    if (event_type) {
      query += ' AND event_type = ?';
      params.push(event_type);
    }

    query += ' ORDER BY timestamp DESC LIMIT ?';
    params.push(limit);

    const result = await c.env.DB.prepare(query).bind(...params).all();

    return c.json({
      events: result.results.map(e => ({
        ...e,
        payload: JSON.parse(e.payload)
      }))
    });
  } catch (err) {
    console.error('Error fetching events:', err);
    return c.json({ error: 'Failed to fetch events' }, 500);
  }
});

// ============================================================================
// JOB HUNT API ENDPOINTS
// ============================================================================

// ----- ORGANIZATIONS -----

// List all organizations
api.get('/organizations', async (c) => {
  const account_id = c.get('accountId');
  const status = c.req.query('status');
  const priority = c.req.query('priority');

  try {
    let query = `
      SELECT o.*,
        (SELECT COUNT(*) FROM roles WHERE org_id = o.id) as role_count
      FROM organizations o
      WHERE o.account_id = ?
    `;
    const params = [account_id];

    if (status) {
      query += ' AND o.status = ?';
      params.push(status);
    }

    if (priority) {
      query += ' AND o.priority = ?';
      params.push(parseInt(priority));
    }

    query += ' ORDER BY o.priority ASC, o.created_at DESC';

    const result = await c.env.DB.prepare(query).bind(...params).all();

    return c.json({
      organizations: result.results.map(org => ({
        ...org,
        tech_stack: JSON.parse(org.tech_stack || '[]')
      }))
    });
  } catch (err) {
    console.error('Error fetching organizations:', err);
    return c.json({ error: 'Failed to fetch organizations' }, 500);
  }
});

// Create organization
api.post('/organizations', async (c) => {
  const account_id = c.get('accountId');
  const { name, domain, linkedin_slug, priority, notes } = await c.req.json();

  if (!name) {
    return c.json({ error: 'Organization name is required' }, 400);
  }

  try {
    // DEDUPLICATION: Check if org already exists by domain or name
    let existingOrg = null;

    if (domain) {
      // First check by domain (most reliable)
      existingOrg = await c.env.DB.prepare(`
        SELECT * FROM organizations
        WHERE account_id = ? AND domain = ?
      `).bind(account_id, domain).first();
    }

    if (!existingOrg) {
      // Check by name (case-insensitive)
      existingOrg = await c.env.DB.prepare(`
        SELECT * FROM organizations
        WHERE account_id = ? AND LOWER(name) = LOWER(?)
      `).bind(account_id, name).first();
    }

    if (existingOrg) {
      // Organization already exists - return it with deduplication flag
      const trace_id = generateTraceId();
      await emitEvent(c.env.DB, {
        trace_id,
        account_id,
        event_type: 'organization_deduplication',
        entity_type: 'organization',
        entity_id: existingOrg.id,
        payload: {
          attempted_name: name,
          attempted_domain: domain,
          existing_name: existingOrg.name,
          existing_domain: existingOrg.domain,
          matched_by: domain ? 'domain' : 'name'
        }
      });

      console.log(`🔄 DEDUPLICATION: Organization "${name}" already exists (ID: ${existingOrg.id})`);

      return c.json({
        organization: existingOrg,
        already_existed: true,
        message: `Organization "${existingOrg.name}" already exists`
      }, 200);
    }

    // No duplicate found - create new organization
    const org_id = generateId();
    const timestamp = Date.now();

    await c.env.DB.prepare(`
      INSERT INTO organizations (
        id, account_id, name, domain, linkedin_slug, priority, notes,
        status, created_at, updated_at
      ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    `).bind(
      org_id, account_id, name, domain || null, linkedin_slug || null,
      priority || 3, notes || null, 'active', timestamp, timestamp
    ).run();

    const org = await c.env.DB.prepare(
      'SELECT * FROM organizations WHERE id = ?'
    ).bind(org_id).first();

    // Emit event
    const trace_id = generateTraceId();
    await emitEvent(c.env.DB, {
      trace_id,
      account_id,
      event_type: 'organization_created',
      entity_type: 'organization',
      entity_id: org_id,
      payload: { name, domain }
    });

    console.log(`✅ CREATED: New organization "${name}" (ID: ${org_id})`);

    return c.json({ organization: org, already_existed: false }, 201);
  } catch (err) {
    console.error('Error creating organization:', err);
    return c.json({ error: 'Failed to create organization' }, 500);
  }
});

// Get organization with roles and people
api.get('/organizations/:id', async (c) => {
  const account_id = c.get('accountId');
  const org_id = c.req.param('id');

  try {
    const org = await c.env.DB.prepare(`
      SELECT * FROM organizations WHERE id = ? AND account_id = ?
    `).bind(org_id, account_id).first();

    if (!org) {
      return c.json({ error: 'Organization not found' }, 404);
    }

    const roles = await c.env.DB.prepare(`
      SELECT * FROM roles WHERE org_id = ? ORDER BY created_at DESC
    `).bind(org_id).all();

    const people = await c.env.DB.prepare(`
      SELECT * FROM people WHERE org_id = ? ORDER BY contact_priority DESC
    `).bind(org_id).all();

    return c.json({
      organization: {
        ...org,
        tech_stack: JSON.parse(org.tech_stack || '[]')
      },
      roles: roles.results.map(r => ({
        ...r,
        requirements: JSON.parse(r.requirements || '[]'),
        nice_to_haves: JSON.parse(r.nice_to_haves || '[]'),
        tech_stack: JSON.parse(r.tech_stack || '[]'),
        key_experiences_to_highlight: JSON.parse(r.key_experiences_to_highlight || '[]'),
        potential_concerns: JSON.parse(r.potential_concerns || '[]')
      })),
      people: people.results.map(p => ({
        ...p,
        common_connections: JSON.parse(p.common_connections || '[]')
      }))
    });
  } catch (err) {
    console.error('Error fetching organization:', err);
    return c.json({ error: 'Failed to fetch organization' }, 500);
  }
});

// Scrape jobs from organization's careers page
api.post('/organizations/:id/scrape-jobs', async (c) => {
  const account_id = c.get('accountId');
  const org_id = c.req.param('id');
  const trace_id = generateTraceId();

  try {
    // Step 1: Get organization
    const org = await c.env.DB.prepare(`
      SELECT * FROM organizations WHERE id = ? AND account_id = ?
    `).bind(org_id, account_id).first();

    if (!org) {
      return c.json({ success: false, error: 'Organization not found' }, 404);
    }

    // Step 2: Check if we have a cached careers URL
    let careersUrl = org.careers_url;
    let urlSource = 'cached';

    const CACHE_TTL = 7 * 24 * 60 * 60 * 1000; // 7 days in milliseconds
    const isCacheStale = !careersUrl ||
      !org.careers_url_discovered_at ||
      (Date.now() - org.careers_url_discovered_at > CACHE_TTL);

    // Step 3: If no URL or stale, discover it
    if (isCacheStale) {
      console.log(`🔍 Careers URL cache ${careersUrl ? 'stale' : 'missing'}, discovering...`);

      const { discoverCareersUrl } = await import('./agents/discover-careers-url.js');
      const discovery = await discoverCareersUrl(
        org_id,
        org.domain,
        org.name,
        account_id,
        trace_id,
        c.env
      );

      if (discovery.success) {
        careersUrl = discovery.careers_url;
        urlSource = 'discovered';
        console.log(`✓ Discovered: ${careersUrl} (method: ${discovery.discovery_method})`);
      } else {
        return c.json({
          success: false,
          error: 'Could not find careers page',
          discovery_details: discovery
        }, 404);
      }
    } else {
      console.log(`✓ Using cached careers URL: ${careersUrl}`);
    }

    // Step 4: Scrape jobs from discovered/cached URL
    const { scrapeCompanyJobs } = await import('./agents/scrape-jobs.js');
    const result = await scrapeCompanyJobs(
      org_id,
      account_id,
      careersUrl,
      trace_id,
      c.env
    );

    // Step 5: Add metadata to response
    return c.json({
      ...result,
      careers_url_source: urlSource,
      careers_url: careersUrl
    });

  } catch (err) {
    console.error('Error scraping jobs:', err);
    return c.json({
      success: false,
      error: 'Failed to scrape jobs',
      details: err.message
    }, 500);
  }
});

// Update organization
api.patch('/organizations/:id', async (c) => {
  const account_id = c.get('accountId');
  const org_id = c.req.param('id');
  const updates = await c.req.json();

  try {
    const allowedFields = [
      'name', 'domain', 'linkedin_slug', 'description', 'industry',
      'employee_count', 'funding_stage', 'tech_stack', 'culture_notes',
      'priority', 'status', 'notes', 'research_quality_score'
    ];

    const setClause = [];
    const params = [];

    for (const [key, value] of Object.entries(updates)) {
      if (allowedFields.includes(key)) {
        setClause.push(`${key} = ?`);
        params.push(key === 'tech_stack' ? JSON.stringify(value) : value);
      }
    }

    if (setClause.length === 0) {
      return c.json({ error: 'No valid fields to update' }, 400);
    }

    setClause.push('updated_at = ?');
    params.push(Date.now());
    params.push(org_id, account_id);

    await c.env.DB.prepare(`
      UPDATE organizations SET ${setClause.join(', ')}
      WHERE id = ? AND account_id = ?
    `).bind(...params).run();

    return c.json({ success: true });
  } catch (err) {
    console.error('Error updating organization:', err);
    return c.json({ error: 'Failed to update organization' }, 500);
  }
});

// Research organization (trigger Research Agent)
api.post('/organizations/:id/research', async (c) => {
  const account_id = c.get('accountId');
  const org_id = c.req.param('id');
  const trace_id = generateTraceId();

  try {
    const { researchOrganization } = await import('./agents/research-job.js');
    const result = await researchOrganization(org_id, account_id, trace_id, c.env);

    return c.json(result);
  } catch (err) {
    console.error('Error researching organization:', err);
    return c.json({ error: 'Failed to research organization' }, 500);
  }
});

// ----- ROLES -----

// List all roles
api.get('/roles', async (c) => {
  const account_id = c.get('accountId');
  const org_id = c.req.query('org_id');
  const status = c.req.query('status');
  const min_fit_score = c.req.query('min_fit_score');

  try {
    let query = `
      SELECT r.*, o.name as org_name
      FROM roles r
      JOIN organizations o ON o.id = r.org_id
      WHERE r.account_id = ?
    `;
    const params = [account_id];

    if (org_id) {
      query += ' AND r.org_id = ?';
      params.push(org_id);
    }

    if (status) {
      query += ' AND r.status = ?';
      params.push(status);
    }

    if (min_fit_score) {
      query += ' AND r.fit_score >= ?';
      params.push(parseInt(min_fit_score));
    }

    query += ' ORDER BY r.fit_score DESC NULLS LAST, r.posted_date DESC';

    const result = await c.env.DB.prepare(query).bind(...params).all();

    return c.json({
      roles: result.results.map(r => ({
        ...r,
        requirements: JSON.parse(r.requirements || '[]'),
        nice_to_haves: JSON.parse(r.nice_to_haves || '[]'),
        tech_stack: JSON.parse(r.tech_stack || '[]'),
        key_experiences_to_highlight: JSON.parse(r.key_experiences_to_highlight || '[]'),
        potential_concerns: JSON.parse(r.potential_concerns || '[]')
      }))
    });
  } catch (err) {
    console.error('Error fetching roles:', err);
    return c.json({ error: 'Failed to fetch roles' }, 500);
  }
});

// Create role
api.post('/roles', async (c) => {
  const account_id = c.get('accountId');
  const {
    org_id, role_title, job_url, department, level,
    salary_range, location, work_arrangement, notes
  } = await c.req.json();

  if (!org_id || !role_title) {
    return c.json({ error: 'org_id and role_title are required' }, 400);
  }

  try {
    // DEDUPLICATION: Check if role already exists at this org (case-insensitive)
    const existingRole = await c.env.DB.prepare(`
      SELECT r.*, o.name as org_name
      FROM roles r
      JOIN organizations o ON o.id = r.org_id
      WHERE r.org_id = ? AND LOWER(r.role_title) = LOWER(?)
    `).bind(org_id, role_title).first();

    if (existingRole) {
      // Role already exists at this org - return it with deduplication flag
      const trace_id = generateTraceId();
      await emitEvent(c.env.DB, {
        trace_id,
        account_id,
        event_type: 'role_deduplication',
        entity_type: 'role',
        entity_id: existingRole.id,
        payload: {
          attempted_title: role_title,
          existing_title: existingRole.role_title,
          org_id,
          org_name: existingRole.org_name
        }
      });

      console.log(`🔄 DEDUPLICATION: Role "${role_title}" already exists at ${existingRole.org_name} (ID: ${existingRole.id})`);

      return c.json({
        role: existingRole,
        already_existed: true,
        message: `Role "${existingRole.role_title}" already exists at this organization`
      }, 200);
    }

    // No duplicate found - create new role
    const role_id = generateId();
    const timestamp = Date.now();

    await c.env.DB.prepare(`
      INSERT INTO roles (
        id, org_id, account_id, role_title, department, level,
        job_url, salary_range, location, work_arrangement, notes,
        status, created_at, updated_at
      ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    `).bind(
      role_id, org_id, account_id, role_title, department || null, level || null,
      job_url || null, salary_range || null, location || null,
      work_arrangement || null, notes || null, 'identified', timestamp, timestamp
    ).run();

    const role = await c.env.DB.prepare(`
      SELECT r.*, o.name as org_name
      FROM roles r
      JOIN organizations o ON o.id = r.org_id
      WHERE r.id = ?
    `).bind(role_id).first();

    // Emit event
    const trace_id = generateTraceId();
    await emitEvent(c.env.DB, {
      trace_id,
      account_id,
      event_type: 'role_created',
      entity_type: 'role',
      entity_id: role_id,
      payload: { role_title, org_id }
    });

    console.log(`✅ CREATED: New role "${role_title}" at ${role.org_name} (ID: ${role_id})`);

    return c.json({ role, already_existed: false }, 201);
  } catch (err) {
    console.error('Error creating role:', err);
    return c.json({ error: 'Failed to create role' }, 500);
  }
});

// Get role details
api.get('/roles/:id', async (c) => {
  const account_id = c.get('accountId');
  const role_id = c.req.param('id');

  try {
    const role = await c.env.DB.prepare(`
      SELECT r.*, o.name as org_name, o.domain as org_domain, o.description as org_description
      FROM roles r
      JOIN organizations o ON o.id = r.org_id
      WHERE r.id = ? AND r.account_id = ?
    `).bind(role_id, account_id).first();

    if (!role) {
      return c.json({ error: 'Role not found' }, 404);
    }

    const applications = await c.env.DB.prepare(`
      SELECT * FROM applications WHERE role_id = ? ORDER BY created_at DESC
    `).bind(role_id).all();

    const interviews = await c.env.DB.prepare(`
      SELECT * FROM interviews WHERE role_id = ? ORDER BY scheduled_at DESC
    `).bind(role_id).all();

    return c.json({
      role: {
        ...role,
        requirements: JSON.parse(role.requirements || '[]'),
        nice_to_haves: JSON.parse(role.nice_to_haves || '[]'),
        tech_stack: JSON.parse(role.tech_stack || '[]'),
        key_experiences_to_highlight: JSON.parse(role.key_experiences_to_highlight || '[]'),
        potential_concerns: JSON.parse(role.potential_concerns || '[]')
      },
      applications: applications.results,
      interviews: interviews.results
    });
  } catch (err) {
    console.error('Error fetching role:', err);
    return c.json({ error: 'Failed to fetch role' }, 500);
  }
});

// Research role (scrape job posting)
api.post('/roles/:id/research', async (c) => {
  const account_id = c.get('accountId');
  const role_id = c.req.param('id');
  const trace_id = generateTraceId();

  try {
    const { researchRole } = await import('./agents/research-job.js');
    const result = await researchRole(role_id, account_id, trace_id, c.env);

    return c.json(result);
  } catch (err) {
    console.error('Error researching role:', err);
    return c.json({ error: 'Failed to research role' }, 500);
  }
});

// Analyze fit (trigger Strategy Agent)
api.post('/roles/:id/analyze-fit', async (c) => {
  const account_id = c.get('accountId');
  const role_id = c.req.param('id');
  const trace_id = generateTraceId();

  try {
    const { determineFit } = await import('./agents/strategy-job.js');
    const result = await determineFit(role_id, account_id, trace_id, c.env);

    return c.json(result);
  } catch (err) {
    console.error('Error analyzing fit:', err);
    return c.json({ error: 'Failed to analyze fit' }, 500);
  }
});

// Generate application (trigger Outreach Agent)
api.post('/roles/:id/generate-application', async (c) => {
  const account_id = c.get('accountId');
  const role_id = c.req.param('id');
  const trace_id = generateTraceId();

  try {
    const { generateApplication } = await import('./agents/outreach-job.js');
    const result = await generateApplication(role_id, account_id, trace_id, c.env);

    return c.json(result);
  } catch (err) {
    console.error('Error generating application:', err);
    return c.json({ error: 'Failed to generate application' }, 500);
  }
});

// Update role
api.patch('/roles/:id', async (c) => {
  const account_id = c.get('accountId');
  const role_id = c.req.param('id');
  const updates = await c.req.json();

  try {
    const allowedFields = [
      'role_title', 'department', 'level', 'job_url', 'posted_date',
      'salary_range', 'location', 'work_arrangement', 'requirements',
      'nice_to_haves', 'tech_stack', 'fit_score', 'fit_reasoning',
      'positioning_strategy', 'key_experiences_to_highlight',
      'potential_concerns', 'status', 'applied_at', 'notes'
    ];

    const setClause = [];
    const params = [];

    for (const [key, value] of Object.entries(updates)) {
      if (allowedFields.includes(key)) {
        setClause.push(`${key} = ?`);
        const jsonFields = ['requirements', 'nice_to_haves', 'tech_stack',
                           'key_experiences_to_highlight', 'potential_concerns'];
        params.push(jsonFields.includes(key) ? JSON.stringify(value) : value);
      }
    }

    if (setClause.length === 0) {
      return c.json({ error: 'No valid fields to update' }, 400);
    }

    setClause.push('updated_at = ?');
    params.push(Date.now());
    params.push(role_id, account_id);

    await c.env.DB.prepare(`
      UPDATE roles SET ${setClause.join(', ')}
      WHERE id = ? AND account_id = ?
    `).bind(...params).run();

    return c.json({ success: true });
  } catch (err) {
    console.error('Error updating role:', err);
    return c.json({ error: 'Failed to update role' }, 500);
  }
});

// ----- PEOPLE -----

// List people
api.get('/people', async (c) => {
  const account_id = c.get('accountId');
  const org_id = c.req.query('org_id');
  const role = c.req.query('role');

  try {
    let query = `
      SELECT p.*, o.name as org_name
      FROM people p
      JOIN organizations o ON o.id = p.org_id
      WHERE p.account_id = ?
    `;
    const params = [account_id];

    if (org_id) {
      query += ' AND p.org_id = ?';
      params.push(org_id);
    }

    if (role) {
      query += ' AND p.role_title LIKE ?';
      params.push(`%${role}%`);
    }

    query += ' ORDER BY p.contact_priority DESC, p.created_at DESC';

    const result = await c.env.DB.prepare(query).bind(...params).all();

    return c.json({
      people: result.results.map(p => ({
        ...p,
        common_connections: JSON.parse(p.common_connections || '[]')
      }))
    });
  } catch (err) {
    console.error('Error fetching people:', err);
    return c.json({ error: 'Failed to fetch people' }, 500);
  }
});

// Create person
api.post('/people', async (c) => {
  const account_id = c.get('accountId');
  const {
    org_id, full_name, role_title, email, linkedin_url,
    department, decision_maker, contact_priority, background_notes
  } = await c.req.json();

  if (!org_id || !full_name) {
    return c.json({ error: 'org_id and full_name are required' }, 400);
  }

  try {
    const person_id = generateId();
    const timestamp = Date.now();

    await c.env.DB.prepare(`
      INSERT INTO people (
        id, org_id, account_id, full_name, role_title, email, linkedin_url,
        department, decision_maker, contact_priority, background_notes,
        created_at, updated_at
      ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    `).bind(
      person_id, org_id, account_id, full_name, role_title || null,
      email || null, linkedin_url || null, department || null,
      decision_maker ? 1 : 0, contact_priority || 0, background_notes || null,
      timestamp, timestamp
    ).run();

    const person = await c.env.DB.prepare(
      'SELECT * FROM people WHERE id = ?'
    ).bind(person_id).first();

    return c.json({ person }, 201);
  } catch (err) {
    console.error('Error creating person:', err);
    return c.json({ error: 'Failed to create person' }, 500);
  }
});

// Update person
api.patch('/people/:id', async (c) => {
  const account_id = c.get('accountId');
  const person_id = c.req.param('id');
  const updates = await c.req.json();

  try {
    const allowedFields = [
      'full_name', 'role_title', 'email', 'linkedin_url', 'department',
      'decision_maker', 'contact_priority', 'background_notes',
      'common_connections', 'contacted_at', 'responded_at', 'last_interaction'
    ];

    const setClause = [];
    const params = [];

    for (const [key, value] of Object.entries(updates)) {
      if (allowedFields.includes(key)) {
        setClause.push(`${key} = ?`);
        params.push(key === 'common_connections' ? JSON.stringify(value) : value);
      }
    }

    if (setClause.length === 0) {
      return c.json({ error: 'No valid fields to update' }, 400);
    }

    setClause.push('updated_at = ?');
    params.push(Date.now());
    params.push(person_id, account_id);

    await c.env.DB.prepare(`
      UPDATE people SET ${setClause.join(', ')}
      WHERE id = ? AND account_id = ?
    `).bind(...params).run();

    return c.json({ success: true });
  } catch (err) {
    console.error('Error updating person:', err);
    return c.json({ error: 'Failed to update person' }, 500);
  }
});

// ----- APPLICATIONS -----

// List applications
api.get('/applications', async (c) => {
  const account_id = c.get('accountId');
  const role_id = c.req.query('role_id');
  const org_id = c.req.query('org_id');
  const status = c.req.query('status');

  try {
    let query = `
      SELECT a.*, r.role_title, o.name as org_name
      FROM applications a
      JOIN roles r ON r.id = a.role_id
      JOIN organizations o ON o.id = a.org_id
      WHERE a.account_id = ?
    `;
    const params = [account_id];

    if (role_id) {
      query += ' AND a.role_id = ?';
      params.push(role_id);
    }

    if (org_id) {
      query += ' AND a.org_id = ?';
      params.push(org_id);
    }

    if (status) {
      query += ' AND a.status = ?';
      params.push(status);
    }

    query += ' ORDER BY a.sent_at DESC NULLS LAST, a.created_at DESC';

    const result = await c.env.DB.prepare(query).bind(...params).all();

    return c.json({
      applications: result.results.map(a => ({
        ...a,
        additional_materials: JSON.parse(a.additional_materials || '[]')
      }))
    });
  } catch (err) {
    console.error('Error fetching applications:', err);
    return c.json({ error: 'Failed to fetch applications' }, 500);
  }
});

// Get application details
api.get('/applications/:id', async (c) => {
  const account_id = c.get('accountId');
  const app_id = c.req.param('id');

  try {
    const application = await c.env.DB.prepare(`
      SELECT a.*, r.role_title, r.job_url, o.name as org_name, o.domain as org_domain
      FROM applications a
      JOIN roles r ON r.id = a.role_id
      JOIN organizations o ON o.id = a.org_id
      WHERE a.id = ? AND a.account_id = ?
    `).bind(app_id, account_id).first();

    if (!application) {
      return c.json({ error: 'Application not found' }, 404);
    }

    return c.json({
      application: {
        ...application,
        additional_materials: JSON.parse(application.additional_materials || '[]')
      }
    });
  } catch (err) {
    console.error('Error fetching application:', err);
    return c.json({ error: 'Failed to fetch application' }, 500);
  }
});

// Update application
api.patch('/applications/:id', async (c) => {
  const account_id = c.get('accountId');
  const app_id = c.req.param('id');
  const updates = await c.req.json();

  try {
    const allowedFields = [
      'cover_letter', 'resume_version', 'additional_materials',
      'email_to', 'email_subject', 'email_body', 'status',
      'applied_via', 'referrer_name', 'notes'
    ];

    const setClause = [];
    const params = [];

    for (const [key, value] of Object.entries(updates)) {
      if (allowedFields.includes(key)) {
        setClause.push(`${key} = ?`);
        params.push(key === 'additional_materials' ? JSON.stringify(value) : value);
      }
    }

    if (setClause.length === 0) {
      return c.json({ error: 'No valid fields to update' }, 400);
    }

    setClause.push('updated_at = ?');
    params.push(Date.now());
    params.push(app_id, account_id);

    await c.env.DB.prepare(`
      UPDATE applications SET ${setClause.join(', ')}
      WHERE id = ? AND account_id = ?
    `).bind(...params).run();

    return c.json({ success: true });
  } catch (err) {
    console.error('Error updating application:', err);
    return c.json({ error: 'Failed to update application' }, 500);
  }
});

// Send application
api.post('/applications/:id/send', async (c) => {
  const account_id = c.get('accountId');
  const app_id = c.req.param('id');
  const { send_via, recipient_email } = await c.req.json();

  try {
    const timestamp = Date.now();

    // Update application status
    await c.env.DB.prepare(`
      UPDATE applications
      SET status = 'sent', sent_at = ?, updated_at = ?
      WHERE id = ? AND account_id = ?
    `).bind(timestamp, timestamp, app_id, account_id).run();

    // Emit event
    const trace_id = generateTraceId();
    await emitEvent(c.env.DB, {
      trace_id,
      account_id,
      event_type: 'application_sent',
      entity_type: 'application',
      entity_id: app_id,
      payload: { send_via, recipient_email }
    });

    return c.json({ success: true, sent_at: timestamp });
  } catch (err) {
    console.error('Error sending application:', err);
    return c.json({ error: 'Failed to send application' }, 500);
  }
});

// ----- INTERVIEWS -----

// List interviews
api.get('/interviews', async (c) => {
  const account_id = c.get('accountId');
  const org_id = c.req.query('org_id');
  const role_id = c.req.query('role_id');
  const status = c.req.query('status');

  try {
    let query = `
      SELECT i.*, r.role_title, o.name as org_name
      FROM interviews i
      JOIN roles r ON r.id = i.role_id
      JOIN organizations o ON o.id = i.org_id
      WHERE i.account_id = ?
    `;
    const params = [account_id];

    if (org_id) {
      query += ' AND i.org_id = ?';
      params.push(org_id);
    }

    if (role_id) {
      query += ' AND i.role_id = ?';
      params.push(role_id);
    }

    if (status) {
      query += ' AND i.status = ?';
      params.push(status);
    }

    query += ' ORDER BY i.scheduled_at ASC';

    const result = await c.env.DB.prepare(query).bind(...params).all();

    return c.json({
      interviews: result.results.map(i => ({
        ...i,
        questions_to_ask: JSON.parse(i.questions_to_ask || '[]'),
        topics_to_cover: JSON.parse(i.topics_to_cover || '[]')
      }))
    });
  } catch (err) {
    console.error('Error fetching interviews:', err);
    return c.json({ error: 'Failed to fetch interviews' }, 500);
  }
});

// Create interview
api.post('/interviews', async (c) => {
  const account_id = c.get('accountId');
  const {
    role_id, interview_type, scheduled_at, duration_minutes,
    location, timezone, interviewer_name, prep_notes
  } = await c.req.json();

  if (!role_id || !interview_type || !scheduled_at) {
    return c.json({ error: 'role_id, interview_type, and scheduled_at are required' }, 400);
  }

  try {
    // Get org_id from role
    const role = await c.env.DB.prepare(
      'SELECT org_id FROM roles WHERE id = ?'
    ).bind(role_id).first();

    if (!role) {
      return c.json({ error: 'Role not found' }, 404);
    }

    const interview_id = generateId();
    const timestamp = Date.now();

    await c.env.DB.prepare(`
      INSERT INTO interviews (
        id, role_id, org_id, account_id, interview_type, interviewer_name,
        scheduled_at, duration_minutes, location, timezone, prep_notes,
        status, created_at, updated_at
      ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    `).bind(
      interview_id, role_id, role.org_id, account_id, interview_type,
      interviewer_name || null, scheduled_at, duration_minutes || 60,
      location || null, timezone || null, prep_notes || null,
      'scheduled', timestamp, timestamp
    ).run();

    const interview = await c.env.DB.prepare(
      'SELECT * FROM interviews WHERE id = ?'
    ).bind(interview_id).first();

    // Emit event
    const trace_id = generateTraceId();
    await emitEvent(c.env.DB, {
      trace_id,
      account_id,
      event_type: 'interview_scheduled',
      entity_type: 'interview',
      entity_id: interview_id,
      payload: { role_id, interview_type, scheduled_at }
    });

    return c.json({ interview }, 201);
  } catch (err) {
    console.error('Error creating interview:', err);
    return c.json({ error: 'Failed to create interview' }, 500);
  }
});

// Update interview
api.patch('/interviews/:id', async (c) => {
  const account_id = c.get('accountId');
  const interview_id = c.req.param('id');
  const updates = await c.req.json();

  try {
    const allowedFields = [
      'interview_type', 'interviewer_name', 'scheduled_at', 'duration_minutes',
      'location', 'timezone', 'prep_notes', 'questions_to_ask', 'topics_to_cover',
      'status', 'interview_notes', 'feedback_received', 'follow_up_sent_at'
    ];

    const setClause = [];
    const params = [];

    for (const [key, value] of Object.entries(updates)) {
      if (allowedFields.includes(key)) {
        setClause.push(`${key} = ?`);
        const jsonFields = ['questions_to_ask', 'topics_to_cover'];
        params.push(jsonFields.includes(key) ? JSON.stringify(value) : value);
      }
    }

    if (setClause.length === 0) {
      return c.json({ error: 'No valid fields to update' }, 400);
    }

    setClause.push('updated_at = ?');
    params.push(Date.now());
    params.push(interview_id, account_id);

    await c.env.DB.prepare(`
      UPDATE interviews SET ${setClause.join(', ')}
      WHERE id = ? AND account_id = ?
    `).bind(...params).run();

    return c.json({ success: true });
  } catch (err) {
    console.error('Error updating interview:', err);
    return c.json({ error: 'Failed to update interview' }, 500);
  }
});

// ----- USER PROFILE -----

// Get user profile
api.get('/profile', async (c) => {
  const account_id = c.get('accountId');

  try {
    const profile = await c.env.DB.prepare(
      'SELECT * FROM user_profile WHERE account_id = ?'
    ).bind(account_id).first();

    if (!profile) {
      return c.json({ error: 'Profile not found' }, 404);
    }

    return c.json({
      profile: {
        ...profile,
        experience: JSON.parse(profile.experience || '[]'),
        education: JSON.parse(profile.education || '[]'),
        skills: JSON.parse(profile.skills || '[]'),
        certifications: JSON.parse(profile.certifications || '[]'),
        target_roles: JSON.parse(profile.target_roles || '[]'),
        target_companies: JSON.parse(profile.target_companies || '[]'),
        location_preferences: JSON.parse(profile.location_preferences || '[]')
      }
    });
  } catch (err) {
    console.error('Error fetching profile:', err);
    return c.json({ error: 'Failed to fetch profile' }, 500);
  }
});

// Update user profile
api.patch('/profile', async (c) => {
  const account_id = c.get('accountId');
  const updates = await c.req.json();

  try {
    const allowedFields = [
      'full_name', 'email', 'phone', 'location', 'linkedin_url', 'github_url',
      'portfolio_url', 'summary', 'experience', 'education', 'skills',
      'certifications', 'target_roles', 'target_companies', 'compensation_min',
      'location_preferences', 'work_authorization', 'base_resume_md',
      'base_cover_letter_template'
    ];

    const setClause = [];
    const params = [];

    for (const [key, value] of Object.entries(updates)) {
      if (allowedFields.includes(key)) {
        setClause.push(`${key} = ?`);
        const jsonFields = ['experience', 'education', 'skills', 'certifications',
                           'target_roles', 'target_companies', 'location_preferences'];
        params.push(jsonFields.includes(key) ? JSON.stringify(value) : value);
      }
    }

    if (setClause.length === 0) {
      return c.json({ error: 'No valid fields to update' }, 400);
    }

    setClause.push('updated_at = ?');
    params.push(Date.now());
    params.push(account_id);

    await c.env.DB.prepare(`
      UPDATE user_profile SET ${setClause.join(', ')}
      WHERE account_id = ?
    `).bind(...params).run();

    return c.json({ success: true });
  } catch (err) {
    console.error('Error updating profile:', err);
    return c.json({ error: 'Failed to update profile' }, 500);
  }
});

// ----- DASHBOARD STATS -----

// Get job hunt pipeline stats
api.get('/stats/pipeline', async (c) => {
  const account_id = c.get('accountId');

  try {
    // Organizations stats
    const orgs = await c.env.DB.prepare(`
      SELECT
        COUNT(*) as total,
        SUM(CASE WHEN researched_at IS NOT NULL THEN 1 ELSE 0 END) as researched,
        SUM(CASE WHEN status = 'active' THEN 1 ELSE 0 END) as active
      FROM organizations WHERE account_id = ?
    `).bind(account_id).first();

    // Roles stats
    const roles = await c.env.DB.prepare(`
      SELECT
        COUNT(*) as total,
        SUM(CASE WHEN fit_score >= 80 THEN 1 ELSE 0 END) as high_fit,
        SUM(CASE WHEN status = 'identified' THEN 1 ELSE 0 END) as identified,
        SUM(CASE WHEN status = 'applied' THEN 1 ELSE 0 END) as applied,
        SUM(CASE WHEN status = 'interviewing' THEN 1 ELSE 0 END) as interviewing
      FROM roles WHERE account_id = ?
    `).bind(account_id).first();

    // Applications stats
    const apps = await c.env.DB.prepare(`
      SELECT
        SUM(CASE WHEN status = 'draft' THEN 1 ELSE 0 END) as draft,
        SUM(CASE WHEN status = 'sent' THEN 1 ELSE 0 END) as sent,
        SUM(CASE WHEN responded_at IS NOT NULL THEN 1 ELSE 0 END) as responded,
        MIN(sent_at) as first_applied_at
      FROM applications WHERE account_id = ?
    `).bind(account_id).first();

    // Interviews stats
    const interviews = await c.env.DB.prepare(`
      SELECT
        SUM(CASE WHEN status = 'scheduled' THEN 1 ELSE 0 END) as scheduled,
        SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as completed
      FROM interviews WHERE account_id = ?
    `).bind(account_id).first();

    // Calculate response rate
    const response_rate = apps.sent > 0
      ? (apps.responded / apps.sent * 100).toFixed(1)
      : 0;

    // Calculate timeline
    const days_active = apps.first_applied_at
      ? Math.floor((Date.now() - apps.first_applied_at) / (1000 * 60 * 60 * 24))
      : 0;

    const applications_per_week = days_active > 0
      ? (apps.sent / (days_active / 7)).toFixed(1)
      : 0;

    return c.json({
      organizations: orgs,
      roles,
      applications: {
        ...apps,
        response_rate: parseFloat(response_rate)
      },
      interviews,
      timeline: {
        first_applied_at: apps.first_applied_at,
        days_active,
        applications_per_week: parseFloat(applications_per_week)
      }
    });
  } catch (err) {
    console.error('Error fetching pipeline stats:', err);
    return c.json({ error: 'Failed to fetch pipeline stats' }, 500);
  }
});


// Mount API under /api and /crm/api (for custom domain)
app.route('/api', api);
app.route('/crm/api', api);

// 404 handler
app.notFound((c) => {
  return c.json({ error: 'Not found' }, 404);
});

// Error handler
app.onError((err, c) => {
  console.error('Error:', err);
  return c.json({ error: 'Internal server error' }, 500);
});

export default app;
