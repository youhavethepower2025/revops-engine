// Queue Consumer: Processes agent tasks from queues
// This worker handles messages from org-tasks and role-tasks queues

import { discoverCareersUrl } from './agents/discover-careers-url.js';
import { scrapeCompanyJobs } from './agents/scrape-jobs.js';
import { researchRole } from './agents/research-job.js';
import { determineFit } from './agents/strategy-job.js';
import { generateApplication } from './agents/outreach-job.js';

export default {
  async queue(batch, env) {
    console.log(`[QueueConsumer] Processing ${batch.messages.length} messages from ${batch.queue}`);

    for (const message of batch.messages) {
      try {
        const task = message.body;
        console.log(`[QueueConsumer] Processing task: ${task.type}`);

        switch (task.type) {
          case 'discover_careers_url':
            await processDiscoverURL(task, env);
            break;

          case 'scrape_jobs':
            await processScrapeJobs(task, env);
            break;

          case 'research_and_analyze':
            await processResearchAndAnalyze(task, env);
            break;

          case 'generate_application':
            await processGenerateApp(task, env);
            break;

          default:
            console.error(`[QueueConsumer] Unknown task type: ${task.type}`);
        }

        // Acknowledge message (remove from queue)
        message.ack();
      } catch (error) {
        console.error(`[QueueConsumer] Error processing message:`, error);
        // Message will be retried automatically (up to max_retries)
        // After max_retries, goes to dead letter queue
        message.retry();
      }
    }
  }
};

async function processDiscoverURL(task, env) {
  console.log(`[DiscoverURL] Starting for ${task.org_name}`);

  try {
    const result = await discoverCareersUrl(
      task.org_id,
      task.domain,
      task.org_name,
      'account_john_kruze',
      task.trace_id,
      env
    );

    console.log(`[DiscoverURL] Success: ${result.url} (method: ${result.method})`);

    // Notify coordinator of completion
    await notifyCoordinator(env, task.org_id, {
      agent: 'discover_careers_url',
      result: {
        url: result.url,
        method: result.method
      }
    });
  } catch (error) {
    console.error(`[DiscoverURL] Failed for ${task.org_name}:`, error);
    await notifyCoordinator(env, task.org_id, {
      agent: 'discover_careers_url',
      error: error.message
    });
    throw error;
  }
}

async function processScrapeJobs(task, env) {
  console.log(`[ScrapeJobs] Starting for ${task.org_name} at ${task.careers_url}`);

  try {
    const result = await scrapeCompanyJobs(
      task.org_id,
      'account_john_kruze',
      task.careers_url,
      task.trace_id,
      env
    );

    console.log(`[ScrapeJobs] Success: ${result.roles.length} roles found`);

    // Notify coordinator of completion
    await notifyCoordinator(env, task.org_id, {
      agent: 'scrape_jobs',
      result: {
        roles: result.roles,
        jobs_found: result.roles.length
      }
    });
  } catch (error) {
    console.error(`[ScrapeJobs] Failed for ${task.org_name}:`, error);
    await notifyCoordinator(env, task.org_id, {
      agent: 'scrape_jobs',
      error: error.message
    });
    throw error;
  }
}

async function processResearchAndAnalyze(task, env) {
  console.log(`[ResearchAndAnalyze] Starting for role ${task.role_id}`);

  try {
    // Step 1: Research role (extract requirements)
    console.log(`[ResearchAndAnalyze] Step 1: Researching role ${task.role_id}`);
    const researchResult = await researchRole(
      task.role_id,
      'account_john_kruze',
      task.trace_id,
      env
    );

    console.log(`[ResearchAndAnalyze] Research complete: ${researchResult.extracted.requirements?.length || 0} requirements`);

    // Step 2: Analyze fit (immediately after research)
    console.log(`[ResearchAndAnalyze] Step 2: Analyzing fit for role ${task.role_id}`);
    const fitResult = await determineFit(
      task.role_id,
      'account_john_kruze',
      task.trace_id,
      env
    );

    console.log(`[ResearchAndAnalyze] Fit analysis complete: ${fitResult.fit_score}/100`);

    // Get role title for reporting
    const role = await env.DB.prepare(
      'SELECT role_title FROM roles WHERE id = ?'
    ).bind(task.role_id).first();

    // Notify coordinator of completion
    await notifyCoordinator(env, task.org_id, {
      agent: 'role_analyzed',
      result: {
        role_id: task.role_id,
        role_title: role?.role_title || 'Unknown',
        fit_score: fitResult.fit_score,
        action: fitResult.action
      }
    });
  } catch (error) {
    console.error(`[ResearchAndAnalyze] Failed for role ${task.role_id}:`, error);
    await notifyCoordinator(env, task.org_id, {
      agent: 'role_analyzed',
      error: error.message
    });
    throw error;
  }
}

async function processGenerateApp(task, env) {
  console.log(`[GenerateApp] Starting for role ${task.role_id}`);

  try {
    const result = await generateApplication(
      task.role_id,
      'account_john_kruze',
      task.trace_id,
      env
    );

    console.log(`[GenerateApp] Success: Application ${result.application_id} generated`);

    // Notify coordinator of completion
    await notifyCoordinator(env, task.org_id, {
      agent: 'application_generated',
      result: {
        application_id: result.application_id,
        role_id: task.role_id
      }
    });
  } catch (error) {
    console.error(`[GenerateApp] Failed for role ${task.role_id}:`, error);
    await notifyCoordinator(env, task.org_id, {
      agent: 'application_generated',
      error: error.message
    });
    throw error;
  }
}

async function notifyCoordinator(env, org_id, payload) {
  try {
    // Get Durable Object stub for this organization
    const id = env.ORG_COORDINATOR.idFromName(org_id);
    const coordinator = env.ORG_COORDINATOR.get(id);

    // Call the coordinator's agent-complete endpoint
    const response = await coordinator.fetch('http://coordinator/agent-complete', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });

    if (!response.ok) {
      console.error(`[NotifyCoordinator] Failed: ${response.status} ${await response.text()}`);
    } else {
      console.log(`[NotifyCoordinator] Success: Notified coordinator for org ${org_id}`);
    }
  } catch (error) {
    console.error(`[NotifyCoordinator] Error:`, error);
    // Don't throw - we don't want to retry the entire agent task just because notification failed
  }
}
