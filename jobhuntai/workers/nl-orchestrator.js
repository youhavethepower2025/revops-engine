// Natural Language Orchestrator
// Parses user intent and triggers autonomous agent workflows

import { generateId } from './lib/utils.js';

/**
 * Handle natural language input and orchestrate job search
 */
export async function handleNaturalLanguage(input, env) {
  console.log(`[NL Orchestrator] Processing: "${input}"`);

  // Use Workers AI to parse intent
  const intentResponse = await env.AI.run('@cf/meta/llama-3.1-70b-instruct', {
    messages: [{
      role: 'system',
      content: `You are a job search orchestration parser. Extract intent from user input and return JSON.

Return format:
{
  "action": "find_jobs" | "check_status" | "review_applications" | "add_company" | "rescrape" | "get_high_fit",
  "companies": ["CompanyName1", "CompanyName2"],
  "filters": {
    "role_types": ["ml", "backend", "frontend"],
    "min_fit_score": 75,
    "locations": ["remote", "sf", "nyc"]
  },
  "org_id": "optional-if-user-references-specific-org",
  "force": false
}

Examples:
- "Find ML jobs at Anthropic" → action: find_jobs, companies: ["Anthropic"], filters: {role_types: ["ml"]}
- "Check status" → action: check_status
- "Show high-fit roles" → action: get_high_fit
- "Add OpenAI" → action: add_company, companies: ["OpenAI"]
- "Rescrape Hugging Face" → action: rescrape, companies: ["Hugging Face"], force: true

Be smart about company name variations:
- "meta" or "facebook" → "Meta"
- "google" or "deepmind" → "Google DeepMind"
- "openai" or "chatgpt" → "OpenAI"`
    }, {
      role: 'user',
      content: input
    }],
    response_format: { type: 'json_object' }
  });

  const intent = JSON.parse(intentResponse.response);
  console.log(`[NL Orchestrator] Parsed intent:`, intent);

  // Route to appropriate handler
  switch (intent.action) {
    case 'find_jobs':
      return await orchestrateFindJobs(intent, env);

    case 'check_status':
      return await getJobSearchStatus(intent, env);

    case 'review_applications':
    case 'get_high_fit':
      return await getApplicationsForReview(intent, env);

    case 'add_company':
      return await addCompanies(intent, env);

    case 'rescrape':
      return await rescrapeCompanies(intent, env);

    default:
      return {
        success: false,
        message: `Unknown action: ${intent.action}. Try: "Find jobs at [company]" or "Check status"`
      };
  }
}

/**
 * Orchestrate job search for multiple companies
 */
async function orchestrateFindJobs(intent, env) {
  const results = [];

  for (const companyName of intent.companies || []) {
    try {
      // Check if org exists
      let org = await env.DB.prepare(
        'SELECT id, name, domain FROM organizations WHERE LOWER(name) = LOWER(?)'
      ).bind(companyName).first();

      // Create if doesn't exist
      if (!org) {
        console.log(`[Orchestrate] Creating new org: ${companyName}`);

        // Use AI to find company domain
        const domainResponse = await env.AI.run('@cf/meta/llama-3.1-70b-instruct', {
          messages: [{
            role: 'user',
            content: `What is the primary website domain for ${companyName}? Reply ONLY with the domain like "anthropic.com" or "huggingface.co". No explanation.`
          }]
        });

        const domain = domainResponse.response.trim().toLowerCase().replace(/^(https?:\/\/)?(www\.)?/, '');

        const org_id = generateId();
        await env.DB.prepare(`
          INSERT INTO organizations (
            id, account_id, name, domain, priority, status, created_at, updated_at
          ) VALUES (?, 'account_john_kruze', ?, ?, 1, 'active', ?, ?)
        `).bind(org_id, companyName, domain, Date.now(), Date.now()).run();

        org = { id: org_id, name: companyName, domain };
      }

      // Get Durable Object stub for this organization
      const id = env.ORG_COORDINATOR.idFromName(org.id);
      const coordinator = env.ORG_COORDINATOR.get(id);

      // Trigger orchestration
      const orchestrateResponse = await coordinator.fetch('http://coordinator/orchestrate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ force: intent.force || false })
      });

      const orchestrateResult = await orchestrateResponse.json();

      results.push({
        company: companyName,
        org_id: org.id,
        status: orchestrateResult.status,
        phase: orchestrateResult.phase,
        message: orchestrateResult.message
      });
    } catch (error) {
      console.error(`[Orchestrate] Error for ${companyName}:`, error);
      results.push({
        company: companyName,
        status: 'error',
        error: error.message
      });
    }
  }

  return {
    success: true,
    message: `Started job search for ${intent.companies.length} ${intent.companies.length === 1 ? 'company' : 'companies'}`,
    companies: results,
    estimated_completion: '2-5 minutes',
    next_steps: 'System will autonomously:\n1. Discover careers page\n2. Scrape all job listings\n3. Research each role\n4. Analyze your fit\n5. Generate applications for high-fit roles (>75 score)\n\nCheck status in a few minutes!'
  };
}

/**
 * Get status of all job searches
 */
async function getJobSearchStatus(intent, env) {
  // Get all organizations
  const orgs = await env.DB.prepare(`
    SELECT id, name, domain, created_at
    FROM organizations
    WHERE account_id = 'account_john_kruze'
    ORDER BY created_at DESC
    LIMIT 20
  `).all();

  const statuses = [];

  for (const org of orgs.results) {
    try {
      // Get Durable Object status
      const id = env.ORG_COORDINATOR.idFromName(org.id);
      const coordinator = env.ORG_COORDINATOR.get(id);

      const statusResponse = await coordinator.fetch('http://coordinator/status');
      const status = await statusResponse.json();

      if (status.status !== 'not_initialized') {
        statuses.push({
          company: org.name,
          phase: status.phase,
          jobs_found: status.jobsFound,
          high_fit_count: status.highFitRoles?.length || 0,
          applications_generated: status.applicationsGenerated,
          last_scraped: status.lastScraped,
          careers_url: status.careersUrl
        });
      }
    } catch (error) {
      console.error(`[Status] Error for ${org.name}:`, error);
    }
  }

  // Get overall stats from database
  const stats = await env.DB.prepare(`
    SELECT
      COUNT(DISTINCT o.id) as total_companies,
      COUNT(DISTINCT r.id) as total_roles,
      COUNT(DISTINCT CASE WHEN r.fit_score >= 75 THEN r.id END) as high_fit_roles,
      COUNT(DISTINCT a.id) as total_applications
    FROM organizations o
    LEFT JOIN roles r ON r.org_id = o.id
    LEFT JOIN applications a ON a.role_id = r.id
    WHERE o.account_id = 'account_john_kruze'
  `).first();

  return {
    success: true,
    overall_stats: {
      companies: stats.total_companies,
      roles_found: stats.total_roles,
      high_fit_roles: stats.high_fit_roles,
      applications: stats.total_applications
    },
    active_searches: statuses.filter(s => s.phase !== 'complete' && s.phase !== 'error'),
    completed_searches: statuses.filter(s => s.phase === 'complete'),
    all_companies: statuses
  };
}

/**
 * Get applications ready for review
 */
async function getApplicationsForReview(intent, env) {
  const min_score = intent.filters?.min_fit_score || 75;

  const applications = await env.DB.prepare(`
    SELECT
      a.id as app_id,
      a.status,
      a.created_at,
      r.id as role_id,
      r.role_title,
      r.fit_score,
      r.location,
      r.work_arrangement,
      o.name as company_name,
      o.domain
    FROM applications a
    JOIN roles r ON a.role_id = r.id
    JOIN organizations o ON a.org_id = o.id
    WHERE a.account_id = 'account_john_kruze'
      AND r.fit_score >= ?
      AND a.status = 'draft'
    ORDER BY r.fit_score DESC, a.created_at DESC
    LIMIT 50
  `).bind(min_score).all();

  return {
    success: true,
    count: applications.results.length,
    applications: applications.results.map(app => ({
      application_id: app.app_id,
      company: app.company_name,
      role: app.role_title,
      fit_score: app.fit_score,
      location: app.location,
      work_arrangement: app.work_arrangement,
      status: app.status,
      created: new Date(app.created_at).toISOString()
    })),
    message: applications.results.length > 0
      ? `Found ${applications.results.length} draft applications ready for review`
      : 'No draft applications found. Start a job search to generate applications!'
  };
}

/**
 * Add companies without triggering search yet
 */
async function addCompanies(intent, env) {
  const results = [];

  for (const companyName of intent.companies || []) {
    try {
      // Check if exists
      const existing = await env.DB.prepare(
        'SELECT id FROM organizations WHERE LOWER(name) = LOWER(?)'
      ).bind(companyName).first();

      if (existing) {
        results.push({
          company: companyName,
          status: 'already_exists',
          org_id: existing.id
        });
        continue;
      }

      // Use AI to find domain
      const domainResponse = await env.AI.run('@cf/meta/llama-3.1-70b-instruct', {
        messages: [{
          role: 'user',
          content: `What is the primary website domain for ${companyName}? Reply ONLY with the domain like "anthropic.com". No explanation.`
        }]
      });

      const domain = domainResponse.response.trim().toLowerCase().replace(/^(https?:\/\/)?(www\.)?/, '');

      const org_id = generateId();
      await env.DB.prepare(`
        INSERT INTO organizations (
          id, account_id, name, domain, priority, status, created_at, updated_at
        ) VALUES (?, 'account_john_kruze', ?, ?, 1, 'active', ?, ?)
      `).bind(org_id, companyName, domain, Date.now(), Date.now()).run();

      results.push({
        company: companyName,
        status: 'created',
        org_id,
        domain
      });
    } catch (error) {
      results.push({
        company: companyName,
        status: 'error',
        error: error.message
      });
    }
  }

  return {
    success: true,
    message: `Added ${results.filter(r => r.status === 'created').length} new companies`,
    results
  };
}

/**
 * Force re-scrape of existing companies
 */
async function rescrapeCompanies(intent, env) {
  const results = [];

  for (const companyName of intent.companies || []) {
    const org = await env.DB.prepare(
      'SELECT id FROM organizations WHERE LOWER(name) = LOWER(?)'
    ).bind(companyName).first();

    if (!org) {
      results.push({
        company: companyName,
        status: 'not_found',
        message: 'Company not in database. Use "add company" first.'
      });
      continue;
    }

    // Trigger orchestration with force=true
    const id = env.ORG_COORDINATOR.idFromName(org.id);
    const coordinator = env.ORG_COORDINATOR.get(id);

    const response = await coordinator.fetch('http://coordinator/orchestrate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ force: true })
    });

    const result = await response.json();

    results.push({
      company: companyName,
      status: result.status,
      phase: result.phase
    });
  }

  return {
    success: true,
    message: `Re-scraping ${results.length} ${results.length === 1 ? 'company' : 'companies'}`,
    results
  };
}
