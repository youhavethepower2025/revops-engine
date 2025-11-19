// Durable Object: Organization Coordinator
// Brain that orchestrates all job search activities for one organization

import { generateId } from '../lib/utils.js';

export class OrgCoordinator {
  constructor(state, env) {
    this.state = state;
    this.env = env;
  }

  async fetch(request) {
    const url = new URL(request.url);
    const path = url.pathname;

    // Route internal requests
    if (path === '/orchestrate') {
      return this.orchestrateJobSearch(request);
    }

    if (path === '/agent-complete') {
      return this.handleAgentComplete(request);
    }

    if (path === '/status') {
      return this.getStatus();
    }

    if (path === '/reset') {
      return this.reset();
    }

    return new Response('Not found', { status: 404 });
  }

  async orchestrateJobSearch(request) {
    const body = request.method === 'POST' ? await request.json() : {};
    const force = body.force || false;

    // Get current state
    let state = await this.state.storage.get('state');

    if (!state) {
      // Initialize state for first time
      const org = await this.getOrganization();
      state = {
        org_id: this.state.id.toString(),
        org_name: org.name,
        org_domain: org.domain,
        phase: 'idle',
        careersUrl: null,
        careersUrlSource: null,
        jobsFound: 0,
        rolesResearched: 0,
        rolesAnalyzed: 0,
        highFitRoles: [],
        applicationsGenerated: 0,
        lastScraped: null,
        lastError: null,
        retryCount: 0,
        createdAt: Date.now(),
        updatedAt: Date.now()
      };
      await this.state.storage.put('state', state);
    }

    // Check if already running
    if (state.phase !== 'idle' && state.phase !== 'complete' && state.phase !== 'error' && !force) {
      return new Response(JSON.stringify({
        status: 'already_running',
        phase: state.phase,
        message: `Job search already in progress (phase: ${state.phase})`
      }), {
        headers: { 'Content-Type': 'application/json' }
      });
    }

    // Phase 1: Discover careers URL (if not cached or forced)
    if (!state.careersUrl || force) {
      console.log(`[OrgCoordinator ${state.org_name}] Phase 1: Discovering careers URL`);

      state.phase = 'discovering_url';
      state.updatedAt = Date.now();
      await this.state.storage.put('state', state);

      // Send to queue
      await this.env.ORG_QUEUE.send({
        type: 'discover_careers_url',
        org_id: state.org_id,
        domain: state.org_domain,
        org_name: state.org_name,
        trace_id: generateId(),
        timestamp: Date.now()
      });

      return new Response(JSON.stringify({
        status: 'orchestrating',
        phase: 'discovering_url',
        org: state.org_name,
        message: 'Discovering careers page URL...'
      }), {
        headers: { 'Content-Type': 'application/json' }
      });
    }

    // Phase 2: Scrape jobs
    console.log(`[OrgCoordinator ${state.org_name}] Phase 2: Scraping jobs from ${state.careersUrl}`);

    state.phase = 'scraping_jobs';
    state.jobsFound = 0;
    state.rolesResearched = 0;
    state.rolesAnalyzed = 0;
    state.highFitRoles = [];
    state.updatedAt = Date.now();
    await this.state.storage.put('state', state);

    await this.env.ORG_QUEUE.send({
      type: 'scrape_jobs',
      org_id: state.org_id,
      org_name: state.org_name,
      careers_url: state.careersUrl,
      trace_id: generateId(),
      timestamp: Date.now()
    });

    return new Response(JSON.stringify({
      status: 'orchestrating',
      phase: 'scraping_jobs',
      org: state.org_name,
      careers_url: state.careersUrl,
      message: 'Scraping job listings...'
    }), {
      headers: { 'Content-Type': 'application/json' }
    });
  }

  async handleAgentComplete(request) {
    const { agent, result, error } = await request.json();
    const state = await this.state.storage.get('state');

    console.log(`[OrgCoordinator ${state.org_name}] Agent complete: ${agent}`, result);

    if (error) {
      console.error(`[OrgCoordinator ${state.org_name}] Agent error:`, error);
      state.lastError = error;
      state.retryCount += 1;

      // If too many retries, mark as error
      if (state.retryCount > 3) {
        state.phase = 'error';
        await this.state.storage.put('state', state);
        return new Response(JSON.stringify({ status: 'error', error }), { status: 500 });
      }

      // Otherwise, retry
      await this.state.storage.put('state', state);
      return new Response(JSON.stringify({ status: 'retrying' }));
    }

    // Reset retry count on success
    state.retryCount = 0;

    // Handle different agent completions
    if (agent === 'discover_careers_url') {
      state.careersUrl = result.url;
      state.careersUrlSource = result.method;
      state.phase = 'url_discovered';
      state.updatedAt = Date.now();
      await this.state.storage.put('state', state);

      // Automatically trigger scraping
      setTimeout(() => {
        this.orchestrateJobSearch(new Request('http://coordinator/orchestrate'));
      }, 100);

      return new Response(JSON.stringify({ status: 'success', next: 'scraping_jobs' }));
    }

    if (agent === 'scrape_jobs') {
      state.jobsFound = result.roles.length;
      state.phase = 'jobs_scraped';
      state.lastScraped = Date.now();
      state.updatedAt = Date.now();
      await this.state.storage.put('state', state);

      // If no jobs found, mark as complete
      if (result.roles.length === 0) {
        state.phase = 'complete';
        await this.state.storage.put('state', state);
        await this.notifyComplete(state);
        return new Response(JSON.stringify({ status: 'complete', jobs_found: 0 }));
      }

      // Send each role to role queue for parallel processing
      console.log(`[OrgCoordinator ${state.org_name}] Sending ${result.roles.length} roles to queue`);

      for (const role of result.roles) {
        await this.env.ROLE_QUEUE.send({
          type: 'research_and_analyze',
          role_id: role.id,
          org_id: state.org_id,
          trace_id: generateId(),
          timestamp: Date.now()
        });
      }

      state.phase = 'processing_roles';
      await this.state.storage.put('state', state);

      return new Response(JSON.stringify({
        status: 'processing',
        jobs_found: result.roles.length,
        phase: 'processing_roles'
      }));
    }

    if (agent === 'role_analyzed') {
      state.rolesAnalyzed += 1;
      state.updatedAt = Date.now();

      // If high fit, automatically generate application
      if (result.fit_score >= 75) {
        console.log(`[OrgCoordinator ${state.org_name}] High fit role (${result.fit_score}): ${result.role_id}`);

        state.highFitRoles.push({
          role_id: result.role_id,
          fit_score: result.fit_score,
          role_title: result.role_title
        });

        // Send to queue to generate application
        await this.env.ROLE_QUEUE.send({
          type: 'generate_application',
          role_id: result.role_id,
          org_id: state.org_id,
          trace_id: generateId(),
          timestamp: Date.now()
        });
      }

      await this.state.storage.put('state', state);

      // Check if all roles processed
      if (state.rolesAnalyzed >= state.jobsFound) {
        console.log(`[OrgCoordinator ${state.org_name}] All roles analyzed, waiting for applications...`);
        state.phase = 'generating_applications';
        await this.state.storage.put('state', state);
      }

      return new Response(JSON.stringify({
        status: 'success',
        progress: `${state.rolesAnalyzed}/${state.jobsFound} roles analyzed`
      }));
    }

    if (agent === 'application_generated') {
      state.applicationsGenerated += 1;
      state.updatedAt = Date.now();
      await this.state.storage.put('state', state);

      // Check if all high-fit applications generated
      if (state.applicationsGenerated >= state.highFitRoles.length) {
        console.log(`[OrgCoordinator ${state.org_name}] Complete! ${state.applicationsGenerated} applications generated`);
        state.phase = 'complete';
        await this.state.storage.put('state', state);
        await this.notifyComplete(state);
      }

      return new Response(JSON.stringify({
        status: 'success',
        progress: `${state.applicationsGenerated}/${state.highFitRoles.length} applications generated`
      }));
    }

    return new Response(JSON.stringify({ status: 'unknown_agent' }), { status: 400 });
  }

  async notifyComplete(state) {
    console.log(`[OrgCoordinator ${state.org_name}] Notifying DevMCP of completion`);

    // TODO: POST to DevMCP webhook when ready
    // await fetch('http://localhost:8080/webhooks/jobhunt', {
    //   method: 'POST',
    //   headers: { 'Content-Type': 'application/json' },
    //   body: JSON.stringify({
    //     event: 'job_search_complete',
    //     org_id: state.org_id,
    //     org_name: state.org_name,
    //     jobs_found: state.jobsFound,
    //     high_fit_count: state.highFitRoles.length,
    //     applications_generated: state.applicationsGenerated,
    //     high_fit_roles: state.highFitRoles,
    //     timestamp: Date.now()
    //   })
    // });

    // Log event to database
    await this.env.DB.prepare(`
      INSERT INTO events (id, trace_id, account_id, event_type, entity_type, entity_id, payload, timestamp)
      VALUES (?, ?, 'account_john_kruze', 'job_search_complete', 'organization', ?, ?, ?)
    `).bind(
      generateId(),
      generateId(),
      state.org_id,
      JSON.stringify({
        jobs_found: state.jobsFound,
        high_fit_count: state.highFitRoles.length,
        applications_generated: state.applicationsGenerated
      }),
      Date.now()
    ).run();
  }

  async getStatus() {
    const state = await this.state.storage.get('state');

    if (!state) {
      return new Response(JSON.stringify({
        status: 'not_initialized',
        message: 'No job search initiated yet'
      }), {
        headers: { 'Content-Type': 'application/json' }
      });
    }

    return new Response(JSON.stringify(state), {
      headers: { 'Content-Type': 'application/json' }
    });
  }

  async reset() {
    await this.state.storage.deleteAll();
    return new Response(JSON.stringify({ status: 'reset' }), {
      headers: { 'Content-Type': 'application/json' }
    });
  }

  async getOrganization() {
    const org_id = this.state.id.toString();
    const org = await this.env.DB.prepare(
      'SELECT * FROM organizations WHERE id = ?'
    ).bind(org_id).first();

    if (!org) {
      throw new Error(`Organization ${org_id} not found in database`);
    }

    return org;
  }
}
