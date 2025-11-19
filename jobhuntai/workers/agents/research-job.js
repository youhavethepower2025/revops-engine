// Research Agent - Job Hunt Edition
// Enriches organizations and roles with scraped data + AI extraction

import { scrapeCompanyWebsite } from '../lib/scraper.js';
import { emitEvent, generateTraceId } from '../lib/events.js';
import { generateId } from '../lib/auth.js';
import {
  logError,
  logOperationStart,
  logOperationSuccess,
  logWarning
} from '../lib/error-logger.js';

/**
 * Research an organization (company)
 * Scrapes website, extracts structured info, updates database
 */
export async function researchOrganization(org_id, account_id, trace_id, env) {
  const startTime = Date.now();

  // Log operation start
  await logOperationStart({
    operation: 'research_organization',
    agent_type: 'research',
    entity_type: 'organization',
    entity_id: org_id,
    account_id,
    trace_id
  }, env);

  try {
    // Get organization
    const org = await env.DB.prepare(`
      SELECT * FROM organizations WHERE id = ? AND account_id = ?
    `).bind(org_id, account_id).first();

    if (!org) {
      await logWarning({
        message: 'Organization not found',
        operation: 'research_organization',
        agent_type: 'research',
        entity_id: org_id,
        account_id,
        trace_id
      }, env);
      return { success: false, error: 'Organization not found' };
    }

    if (!org.domain) {
      await logWarning({
        message: 'Organization has no domain to research',
        operation: 'research_organization',
        agent_type: 'research',
        entity_id: org_id,
        account_id,
        trace_id,
        metadata: { org_name: org.name }
      }, env);
      return { success: false, error: 'Organization has no domain to research' };
    }

    // Scrape company website
    console.log(`Researching organization: ${org.name} (${org.domain})`);
    const websiteData = await scrapeCompanyWebsite(org.domain, env);

    // Use AI to extract structured company info
    const prompt = `Analyze this company and extract key information for a job candidate researching them:

Company Name: ${org.name}
Website Title: ${websiteData.title}
Description: ${websiteData.description}
Domain: ${org.domain}

Extract and return ONLY valid JSON (no markdown, no extra text):
{
  "description": "2-3 sentence summary of what the company does",
  "industry": "Primary industry (e.g. Artificial Intelligence, SaaS, Enterprise Software)",
  "employeeCount": "Estimated employee count or range (e.g. 50-200, 500+)",
  "fundingStage": "Funding stage if identifiable (Seed/Series A/B/C/D/Public/Bootstrapped/Unknown)",
  "techStack": ["Array", "of", "technologies", "mentioned"],
  "cultureKeywords": ["Keywords", "about", "culture", "values"],
  "keyInitiatives": "Current projects or focus areas mentioned",
  "hiringSignals": "Are they hiring? Recent growth? Any signals about company health"
}`;

    const aiResponse = await env.AI.run('@cf/meta/llama-3.1-70b-instruct', {
      messages: [
        {
          role: 'system',
          content: 'You are a research assistant. Extract structured data from company information. Respond ONLY with valid JSON, no other text.'
        },
        {
          role: 'user',
          content: prompt
        }
      ],
      max_tokens: 600
    });

    // Parse AI response
    let extracted;
    try {
      const responseText = aiResponse.response.trim();
      // Handle markdown-wrapped JSON
      const jsonMatch = responseText.match(/```json\n?([\s\S]*?)\n?```/) || responseText.match(/\{[\s\S]*\}/);
      const jsonText = jsonMatch ? (jsonMatch[1] || jsonMatch[0]) : responseText;
      extracted = JSON.parse(jsonText);
    } catch (parseError) {
      console.error('Failed to parse AI response:', aiResponse.response);
      // Fallback to basic data
      extracted = {
        description: websiteData.description || 'No description available',
        industry: 'Unknown',
        employeeCount: 'Unknown',
        fundingStage: 'Unknown',
        techStack: [],
        cultureKeywords: [],
        keyInitiatives: 'No information available',
        hiringSignals: 'No information available'
      };
    }

    // Update organization with extracted data
    const culture_notes = `Culture: ${extracted.cultureKeywords.join(', ')}. Focus: ${extracted.keyInitiatives}. Hiring: ${extracted.hiringSignals}`;
    const research_quality = websiteData.error ? 40 : 80; // Lower quality if scraping failed

    await env.DB.prepare(`
      UPDATE organizations
      SET description = ?, industry = ?, employee_count = ?, funding_stage = ?,
          tech_stack = ?, culture_notes = ?, researched_at = ?,
          research_quality_score = ?, updated_at = ?
      WHERE id = ? AND account_id = ?
    `).bind(
      extracted.description,
      extracted.industry,
      extracted.employeeCount,
      extracted.fundingStage,
      JSON.stringify(extracted.techStack),
      culture_notes,
      Date.now(),
      research_quality,
      Date.now(),
      org_id,
      account_id
    ).run();

    // Emit event
    await emitEvent(env.DB, {
      trace_id,
      account_id,
      event_type: 'organization_researched',
      entity_type: 'organization',
      entity_id: org_id,
      payload: {
        name: org.name,
        domain: org.domain,
        research_quality
      }
    });

    const duration = Date.now() - startTime;

    // Log success
    await logOperationSuccess({
      operation: 'research_organization',
      agent_type: 'research',
      entity_type: 'organization',
      entity_id: org_id,
      account_id,
      trace_id,
      duration_ms: duration,
      result: { research_quality, org_name: org.name }
    }, env);

    return {
      success: true,
      org_id,
      company_info: extracted,
      research_quality
    };

  } catch (err) {
    // Log error
    await logError({
      error: err,
      operation: 'research_organization',
      agent_type: 'research',
      entity_type: 'organization',
      entity_id: org_id,
      account_id,
      trace_id,
      metadata: { org_name: org?.name, domain: org?.domain }
    }, env);

    return {
      success: false,
      org_id,
      error: err.message,
      error_id: err.error_id,
      trace_id: err.trace_id || trace_id
    };
  }
}

/**
 * Research a role (job posting)
 * Scrapes job URL, extracts requirements, updates database
 */
export async function researchRole(role_id, account_id, trace_id, env) {
  const startTime = Date.now();

  await logOperationStart({
    operation: 'research_role',
    agent_type: 'research',
    entity_type: 'role',
    entity_id: role_id,
    account_id,
    trace_id
  }, env);

  try {
    // Get role and organization
    const role = await env.DB.prepare(`
      SELECT r.*, o.name as org_name, o.domain as org_domain
      FROM roles r
      JOIN organizations o ON o.id = r.org_id
      WHERE r.id = ? AND r.account_id = ?
    `).bind(role_id, account_id).first();

    if (!role) {
      return { success: false, error: 'Role not found' };
    }

    if (!role.job_url) {
      return { success: false, error: 'No job URL provided for this role' };
    }

    console.log(`Researching role: ${role.role_title} at ${role.org_name}`);

    // Scrape job posting
    const response = await fetch(role.job_url, {
      headers: {
        'User-Agent': 'Mozilla/5.0 (compatible; JobHuntBot/1.0)',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
      }
    });

    if (!response.ok) {
      return {
        success: false,
        error: `Failed to fetch job posting: HTTP ${response.status}`
      };
    }

    const html = await response.text();

    // Extract job details with AI
    const prompt = `Analyze this job posting and extract structured requirements:

Job Title: ${role.role_title}
Company: ${role.org_name}
URL: ${role.job_url}
HTML Content (first 4000 chars): ${html.substring(0, 4000)}

Extract and return ONLY valid JSON (no markdown, no extra text):
{
  "requirements": ["Required qualification 1", "Required qualification 2", "..."],
  "niceToHaves": ["Preferred skill 1", "Preferred skill 2", "..."],
  "techStack": ["Technology 1", "Technology 2", "..."],
  "responsibilities": ["Responsibility 1", "Responsibility 2", "..."],
  "salaryRange": "Salary if mentioned, or null",
  "location": "Location (City/Remote/Hybrid)",
  "workArrangement": "Remote, Hybrid, or Onsite"
}

Be specific and extract actual requirements from the posting, not generic ones.`;

    const aiResponse = await env.AI.run('@cf/meta/llama-3.1-70b-instruct', {
      messages: [
        {
          role: 'system',
          content: 'You are a job posting analyzer. Extract structured requirements from job descriptions. Respond ONLY with valid JSON.'
        },
        {
          role: 'user',
          content: prompt
        }
      ],
      max_tokens: 800
    });

    // Parse AI response
    let extracted;
    try {
      const responseText = aiResponse.response.trim();
      const jsonMatch = responseText.match(/```json\n?([\s\S]*?)\n?```/) || responseText.match(/\{[\s\S]*\}/);
      const jsonText = jsonMatch ? (jsonMatch[1] || jsonMatch[0]) : responseText;
      extracted = JSON.parse(jsonText);
    } catch (parseError) {
      console.error('Failed to parse AI response:', aiResponse.response);
      // Fallback
      extracted = {
        requirements: ['Unable to extract requirements'],
        niceToHaves: [],
        techStack: [],
        responsibilities: [],
        salaryRange: null,
        location: role.location || 'Unknown',
        workArrangement: role.work_arrangement || 'Unknown'
      };
    }

    // Update role with extracted data
    await env.DB.prepare(`
      UPDATE roles
      SET requirements = ?, nice_to_haves = ?, tech_stack = ?,
          salary_range = ?, location = ?, work_arrangement = ?, updated_at = ?
      WHERE id = ? AND account_id = ?
    `).bind(
      JSON.stringify(extracted.requirements),
      JSON.stringify(extracted.niceToHaves),
      JSON.stringify(extracted.techStack),
      extracted.salaryRange || role.salary_range,
      extracted.location || role.location,
      extracted.workArrangement || role.work_arrangement,
      Date.now(),
      role_id,
      account_id
    ).run();

    // Emit event
    await emitEvent(env.DB, {
      trace_id,
      account_id,
      event_type: 'role_researched',
      entity_type: 'role',
      entity_id: role_id,
      payload: {
        role_title: role.role_title,
        org_name: role.org_name,
        requirements_count: extracted.requirements.length
      }
    });

    const duration = Date.now() - startTime;

    await logOperationSuccess({
      operation: 'research_role',
      agent_type: 'research',
      entity_type: 'role',
      entity_id: role_id,
      account_id,
      trace_id,
      duration_ms: duration,
      result: { role_title: role.role_title, org_name: role.org_name }
    }, env);

    return {
      success: true,
      role_id,
      extracted
    };

  } catch (err) {
    await logError({
      error: err,
      operation: 'research_role',
      agent_type: 'research',
      entity_type: 'role',
      entity_id: role_id,
      account_id,
      trace_id,
      metadata: { role_title: role?.role_title, org_name: role?.org_name }
    }, env);

    return {
      success: false,
      role_id,
      error: err.message,
      error_id: err.error_id,
      trace_id: err.trace_id || trace_id
    };
  }
}
