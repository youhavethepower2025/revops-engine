// Job Scraping Agent - Fetches real job postings from careers pages
// Extracts descriptions, requirements, and specific URLs

import { emitEvent } from '../lib/events.js';
import { generateId } from '../lib/auth.js';
import { logError, logOperationStart, logOperationSuccess } from '../lib/error-logger.js';

/**
 * Scrape jobs from a company's careers page
 * Uses AI to extract job details from HTML
 *
 * @param {string} org_id - Organization ID
 * @param {string} account_id - Account ID
 * @param {string} careersUrl - Careers page URL (from discovery agent or cache)
 * @param {string} trace_id - Trace ID for event tracking
 * @param {object} env - Worker environment
 */
export async function scrapeCompanyJobs(org_id, account_id, careersUrl, trace_id, env) {
  const startTime = Date.now();
  let org;

  await logOperationStart({
    operation: 'scrape_jobs',
    agent_type: 'research',
    entity_type: 'organization',
    entity_id: org_id,
    account_id,
    trace_id
  }, env);

  try {
    // Get organization
    org = await env.DB.prepare(`
      SELECT * FROM organizations WHERE id = ? AND account_id = ?
    `).bind(org_id, account_id).first();

    if (!org) {
      return { success: false, error: 'Organization not found' };
    }

    console.log(`🔍 Scraping jobs from ${org.name} at ${careersUrl}`);

    let careersHtml = null;

    // Fetch careers page (URL provided by discovery agent)
    console.log(`  Fetching: ${careersUrl}`);
    const response = await fetch(careersUrl, {
      headers: {
        'User-Agent': 'Mozilla/5.0 (compatible; JobHuntBot/1.0)',
      }
    });

    if (!response.ok) {
      console.log(`  ✗ HTTP ${response.status} for ${careersUrl}`);
      return {
        success: false,
        error: `Careers page returned ${response.status}`,
        careers_url: careersUrl
      };
    }

    careersHtml = await response.text();
    console.log(`  ✓ Fetched careers page (${careersHtml.length} bytes)`);

    // Use AI to extract job listings from HTML
    const extractionPrompt = `Extract job listings from this careers page HTML. Find job titles, URLs, and any visible descriptions.

HTML (truncated to first 8000 chars):
${careersHtml.substring(0, 8000)}

Respond with ONLY valid JSON (no markdown, no extra text):
{
  "jobs": [
    {
      "title": "Software Engineer",
      "url": "https://company.com/jobs/software-engineer",
      "department": "Engineering",
      "location": "San Francisco, CA",
      "description": "Brief description if visible on listing page"
    }
  ]
}

Extract up to 15 jobs. If no jobs found, return {"jobs": []}.
Focus on engineering, product, and technical roles.`;

    const extractionResponse = await env.AI.run('@cf/meta/llama-3.1-70b-instruct', {
      messages: [
        {
          role: 'system',
          content: 'You are a web scraping expert. Extract structured data from HTML. Respond ONLY with valid JSON.'
        },
        {
          role: 'user',
          content: extractionPrompt
        }
      ],
      max_tokens: 2000
    });

    // Parse job listings
    let jobListings;
    try {
      const responseText = extractionResponse.response.trim();
      const jsonMatch = responseText.match(/```json\n?([\s\S]*?)\n?```/) || responseText.match(/\{[\s\S]*\}/);
      const jsonText = jsonMatch ? (jsonMatch[1] || jsonMatch[0]) : responseText;
      jobListings = JSON.parse(jsonText);

      if (!jobListings.jobs || !Array.isArray(jobListings.jobs)) {
        throw new Error('Invalid response format');
      }
    } catch (parseError) {
      console.error('Failed to parse job listings:', extractionResponse.response);
      return {
        success: false,
        error: 'Failed to parse job listings from AI response'
      };
    }

    console.log(`  Found ${jobListings.jobs.length} jobs`);

    // For each job, fetch full details
    const createdRoles = [];
    const now = Date.now();

    for (const job of jobListings.jobs.slice(0, 10)) { // Limit to 10 jobs
      try {
        console.log(`  📄 Processing: ${job.title}`);

        // Check if role already exists
        const existing = await env.DB.prepare(`
          SELECT id FROM roles
          WHERE org_id = ? AND role_title = ? AND account_id = ?
        `).bind(org_id, job.title, account_id).first();

        if (existing) {
          console.log(`    ↳ Already exists, skipping`);
          continue;
        }

        // Validate and fetch full job posting if we have a specific URL
        let fullDescription = job.description || '';
        let requirements = [];
        let validatedJobUrl = null;

        if (job.url && job.url !== careersUrl && job.url.startsWith('http')) {
          try {
            console.log(`    ↳ Validating URL: ${job.url}`);

            // Validate URL first (HEAD request)
            const headResponse = await fetch(job.url, {
              method: 'HEAD',
              redirect: 'follow',
              headers: {
                'User-Agent': 'Mozilla/5.0 (compatible; JobHuntBot/1.0)',
              }
            });

            if (!headResponse.ok) {
              console.log(`    ⚠ URL validation failed (${headResponse.status}), using careers page URL`);
              validatedJobUrl = careersUrl;
            } else {
              console.log(`    ✓ URL validated, fetching details...`);
              validatedJobUrl = job.url;

              // Fetch full job posting
              const jobResponse = await fetch(job.url, {
                headers: {
                  'User-Agent': 'Mozilla/5.0 (compatible; JobHuntBot/1.0)',
                }
              });

              if (jobResponse.ok) {
                const jobHtml = await jobResponse.text();

                // Use AI to extract structured data from job posting
                const detailPrompt = `Extract job details from this job posting HTML.

HTML (first 6000 chars):
${jobHtml.substring(0, 6000)}

Respond with ONLY valid JSON:
{
  "description": "Full job description (2-3 paragraphs)",
  "requirements": ["Requirement 1", "Requirement 2", ...],
  "nice_to_haves": ["Nice to have 1", ...],
  "location": "City, State/Country",
  "salary_range": "If mentioned",
  "work_arrangement": "remote/hybrid/onsite"
}`;

                const detailResponse = await env.AI.run('@cf/meta/llama-3.1-70b-instruct', {
                  messages: [
                    { role: 'system', content: 'Extract structured job posting data. Respond ONLY with valid JSON.' },
                    { role: 'user', content: detailPrompt }
                  ],
                  max_tokens: 1500
                });

                try {
                  const detailText = detailResponse.response.trim();
                  const detailMatch = detailText.match(/```json\n?([\s\S]*?)\n?```/) || detailText.match(/\{[\s\S]*\}/);
                  const detailJson = detailMatch ? (detailMatch[1] || detailMatch[0]) : detailText;
                  const details = JSON.parse(detailJson);

                  fullDescription = details.description || fullDescription;
                  requirements = details.requirements || [];

                  // Update job object with extracted details
                  if (details.location) job.location = details.location;
                  if (details.salary_range) job.salary_range = details.salary_range;
                  if (details.work_arrangement) job.work_arrangement = details.work_arrangement;

                } catch (err) {
                  console.log(`    ⚠ Could not parse job details, using listing info`);
                }
              } else {
                console.log(`    ⚠ Job URL fetch failed (${jobResponse.status})`);
                validatedJobUrl = careersUrl;
              }
            }
          } catch (fetchError) {
            console.log(`    ⚠ Could not fetch job posting: ${fetchError.message}`);
            validatedJobUrl = careersUrl;
          }
        } else {
          // No specific job URL, use careers page URL
          validatedJobUrl = careersUrl;
        }

        // Only create role if we have essential data
        if (!job.title || job.title.length < 5) {
          console.log(`    ✗ Skipping - invalid title: ${job.title}`);
          continue;
        }

        // Create role with complete data
        const role_id = generateId();
        await env.DB.prepare(`
          INSERT INTO roles (
            id, org_id, account_id, role_title, department, location,
            work_arrangement, job_url, description, requirements,
            status, created_at, updated_at
          ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        `).bind(
          role_id,
          org_id,
          account_id,
          job.title,
          job.department || null,
          job.location || null,
          job.work_arrangement || null,
          validatedJobUrl,  // Use validated URL
          fullDescription || null,
          JSON.stringify(requirements),
          'identified',
          now,
          now
        ).run();

        console.log(`    ✓ Created: ${job.title}`);
        createdRoles.push({ id: role_id, title: job.title });

        // Emit event
        await emitEvent(env.DB, {
          trace_id,
          account_id,
          event_type: 'role_scraped',
          entity_type: 'role',
          entity_id: role_id,
          payload: { role_title: job.title, org_id, has_description: !!fullDescription }
        });

      } catch (err) {
        console.error(`    ✗ Error processing ${job.title}:`, err);
        continue;
      }
    }

    const duration = Date.now() - startTime;

    await logOperationSuccess({
      operation: 'scrape_jobs',
      agent_type: 'research',
      entity_type: 'organization',
      entity_id: org_id,
      account_id,
      trace_id,
      duration_ms: duration,
      result: {
        org_name: org.name,
        jobs_found: jobListings.jobs.length,
        roles_created: createdRoles.length
      }
    }, env);

    return {
      success: true,
      org_id,
      org_name: org.name,
      careers_url: careersUrl,
      jobs_found: jobListings.jobs.length,
      roles_created: createdRoles.length,
      roles: createdRoles
    };

  } catch (err) {
    await logError({
      error: err,
      operation: 'scrape_jobs',
      agent_type: 'research',
      entity_type: 'organization',
      entity_id: org_id,
      account_id,
      trace_id,
      metadata: { org_name: org?.name }
    }, env);

    return {
      success: false,
      org_id,
      error: err.message
    };
  }
}
