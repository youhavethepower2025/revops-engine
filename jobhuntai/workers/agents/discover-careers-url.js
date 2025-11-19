// Career URL Discovery Agent
// Finds the REAL careers page URL for any company
// Uses: 1) Hardcoded patterns (fast), 2) AI search (slow but smart)

import { emitEvent } from '../lib/events.js';
import { logError, logOperationStart, logOperationSuccess } from '../lib/error-logger.js';

/**
 * Discover the careers page URL for an organization
 *
 * Strategy:
 * 1. Try common URL patterns first (fast path - 8 patterns)
 * 2. If all fail, use Workers AI to search (slow path but intelligent)
 * 3. Validate discovered URL before saving
 * 4. Cache result in database
 *
 * @param {string} org_id - Organization ID
 * @param {string} domain - Company domain (e.g., "anthropic.com")
 * @param {string} company_name - Company name (e.g., "Anthropic")
 * @param {object} env - Worker environment (DB, AI bindings)
 * @returns {Promise<object>} Discovery result with URL and method
 */
export async function discoverCareersUrl(org_id, domain, company_name, account_id, trace_id, env) {
  const startTime = Date.now();

  await logOperationStart({
    operation: 'discover_careers_url',
    agent_type: 'discovery',
    entity_type: 'organization',
    entity_id: org_id,
    account_id,
    trace_id
  }, env);

  try {
    console.log(`🔍 Discovering careers URL for ${company_name} (${domain})`);

    // Step 1: Try hardcoded patterns (fast path)
    const patterns = [
      `https://www.${domain}/careers`,
      `https://${domain}/careers`,
      `https://www.${domain}/jobs`,
      `https://${domain}/jobs`,
      `https://jobs.${domain}`,
      `https://careers.${domain}`,
      `https://www.${domain}/company/careers`,
      `https://${domain}/company/careers`,
    ];

    for (let i = 0; i < patterns.length; i++) {
      const url = patterns[i];
      console.log(`  Trying pattern ${i + 1}/${patterns.length}: ${url}`);

      try {
        const response = await fetch(url, {
          method: 'HEAD',
          redirect: 'follow',
          headers: {
            'User-Agent': 'Mozilla/5.0 (compatible; JobHuntBot/1.0)',
          }
        });

        if (response.ok) {
          console.log(`  ✓ Found via hardcoded pattern: ${url}`);

          // Save to database
          await saveDiscoveredUrl(org_id, url, 'hardcoded', env);

          // Emit event
          await emitEvent(env.DB, {
            trace_id,
            account_id,
            event_type: 'careers_url_discovered',
            entity_type: 'organization',
            entity_id: org_id,
            payload: {
              url,
              method: 'hardcoded',
              pattern_index: i,
              total_patterns: patterns.length
            }
          });

          const duration = Date.now() - startTime;
          await logOperationSuccess({
            operation: 'discover_careers_url',
            agent_type: 'discovery',
            entity_type: 'organization',
            entity_id: org_id,
            account_id,
            trace_id,
            duration_ms: duration,
            result: { url, method: 'hardcoded', patterns_tried: i + 1 }
          }, env);

          return {
            success: true,
            careers_url: url,
            discovery_method: 'hardcoded',
            patterns_tried: i + 1,
            total_patterns: patterns.length
          };
        }
      } catch (err) {
        // Try next pattern
        console.log(`  ✗ Pattern failed: ${err.message}`);
        continue;
      }
    }

    // Step 2: All patterns failed, try AI-powered search
    console.log(`  ⚠ All hardcoded patterns failed. Using AI search...`);

    // Use Workers AI to intelligently search for careers URL
    const searchPrompt = `Find the careers/jobs page URL for ${company_name}.

Company details:
- Name: ${company_name}
- Domain: ${domain}

Common patterns to consider:
- Third-party boards: jobs.lever.co/${company_name.toLowerCase()}, ${company_name.toLowerCase().replace(/\s+/g, '')}.greenhouse.io
- Subdomains: jobs.${domain}, careers.${domain}
- Different domains: (e.g., Meta uses metacareers.com)
- Path variations: /${domain}/careers, /${domain}/jobs

Respond with ONLY the most likely URL, nothing else. No explanation, just the URL.`;

    const aiResponse = await env.AI.run('@cf/meta/llama-3.1-70b-instruct', {
      messages: [
        {
          role: 'system',
          content: 'You are a web URL discovery expert. Given a company name and domain, you find their careers page URL. Respond with ONLY the URL, no explanation.'
        },
        {
          role: 'user',
          content: searchPrompt
        }
      ],
      max_tokens: 100
    });

    // Extract URL from AI response
    const discoveredUrl = extractUrl(aiResponse.response);

    if (!discoveredUrl) {
      console.log(`  ✗ AI could not find a valid URL`);

      await emitEvent(env.DB, {
        trace_id,
        account_id,
        event_type: 'careers_url_discovery_failed',
        entity_type: 'organization',
        entity_id: org_id,
        payload: {
          company_name,
          domain,
          patterns_tried: patterns.length,
          ai_response: aiResponse.response
        }
      });

      return {
        success: false,
        error: 'No careers page found',
        patterns_tried: patterns.length,
        tried_urls: patterns,
        ai_attempted: true
      };
    }

    console.log(`  🤖 AI suggested: ${discoveredUrl}`);

    // Step 3: Validate AI-discovered URL
    try {
      const validation = await fetch(discoveredUrl, {
        method: 'HEAD',
        redirect: 'follow',
        headers: {
          'User-Agent': 'Mozilla/5.0 (compatible; JobHuntBot/1.0)',
        }
      });

      if (!validation.ok) {
        console.log(`  ✗ AI-suggested URL returned ${validation.status}`);

        await emitEvent(env.DB, {
          trace_id,
          account_id,
          event_type: 'careers_url_validation_failed',
          entity_type: 'organization',
          entity_id: org_id,
          payload: {
            url: discoveredUrl,
            status: validation.status,
            method: 'ai_search'
          }
        });

        return {
          success: false,
          error: `AI-suggested URL returned ${validation.status}`,
          suggested_url: discoveredUrl,
          patterns_tried: patterns.length
        };
      }

      // Valid URL found via AI!
      console.log(`  ✓ AI-discovered URL validated: ${discoveredUrl}`);

      // Save to database
      await saveDiscoveredUrl(org_id, discoveredUrl, 'ai_search', env);

      // Emit success event
      await emitEvent(env.DB, {
        trace_id,
        account_id,
        event_type: 'careers_url_discovered',
        entity_type: 'organization',
        entity_id: org_id,
        payload: {
          url: discoveredUrl,
          method: 'ai_search',
          patterns_tried: patterns.length
        }
      });

      const duration = Date.now() - startTime;
      await logOperationSuccess({
        operation: 'discover_careers_url',
        agent_type: 'discovery',
        entity_type: 'organization',
        entity_id: org_id,
        account_id,
        trace_id,
        duration_ms: duration,
        result: { url: discoveredUrl, method: 'ai_search', patterns_tried: patterns.length }
      }, env);

      return {
        success: true,
        careers_url: discoveredUrl,
        discovery_method: 'ai_search',
        patterns_tried: patterns.length
      };

    } catch (validationErr) {
      console.log(`  ✗ Error validating AI-suggested URL: ${validationErr.message}`);

      return {
        success: false,
        error: 'Failed to validate AI-suggested URL',
        suggested_url: discoveredUrl,
        validation_error: validationErr.message
      };
    }

  } catch (err) {
    await logError({
      error: err,
      operation: 'discover_careers_url',
      agent_type: 'discovery',
      entity_type: 'organization',
      entity_id: org_id,
      account_id,
      trace_id,
      metadata: { company_name, domain }
    }, env);

    return {
      success: false,
      error: err.message
    };
  }
}

/**
 * Save discovered careers URL to database
 */
async function saveDiscoveredUrl(org_id, url, method, env) {
  const now = Date.now();

  await env.DB.prepare(`
    UPDATE organizations SET
      careers_url = ?,
      careers_url_discovered_at = ?,
      careers_url_last_checked = ?,
      careers_url_discovery_method = ?
    WHERE id = ?
  `).bind(url, now, now, method, org_id).run();

  console.log(`  💾 Saved to database: ${url} (method: ${method})`);
}

/**
 * Extract URL from AI response text
 */
function extractUrl(text) {
  if (!text) return null;

  // Remove markdown code blocks
  text = text.replace(/```[a-z]*\n?/g, '').trim();

  // Try to find HTTP/HTTPS URL
  const urlMatch = text.match(/https?:\/\/[^\s"'<>]+/);
  if (urlMatch) {
    return urlMatch[0].replace(/[.,;!?)]+$/, ''); // Remove trailing punctuation
  }

  return null;
}
