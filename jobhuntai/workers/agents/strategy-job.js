// Strategy Agent - Job Hunt Edition
// Analyzes candidate-role fit, generates positioning strategy

import { emitEvent } from '../lib/events.js';
import {
  logError,
  logOperationStart,
  logOperationSuccess,
  logWarning
} from '../lib/error-logger.js';

/**
 * Determine fit between candidate and role
 * Scores the match and creates positioning strategy
 */
export async function determineFit(role_id, account_id, trace_id, env) {
  const startTime = Date.now();
  let role, profile;

  await logOperationStart({
    operation: 'determine_fit',
    agent_type: 'strategy',
    entity_type: 'role',
    entity_id: role_id,
    account_id,
    trace_id
  }, env);

  try {
    // Get role with organization context
    role = await env.DB.prepare(`
      SELECT r.*, o.name as org_name, o.description as org_description,
             o.culture_notes, o.tech_stack as org_tech_stack, o.industry,
             o.funding_stage, o.employee_count
      FROM roles r
      JOIN organizations o ON o.id = r.org_id
      WHERE r.id = ? AND r.account_id = ?
    `).bind(role_id, account_id).first();

    if (!role) {
      await logWarning({
        message: 'Role not found',
        operation: 'determine_fit',
        agent_type: 'strategy',
        entity_id: role_id,
        account_id,
        trace_id
      }, env);
      return { success: false, error: 'Role not found' };
    }

    // Get user profile
    profile = await env.DB.prepare(`
      SELECT * FROM user_profile WHERE account_id = ?
    `).bind(account_id).first();

    if (!profile) {
      await logWarning({
        message: 'User profile not found',
        operation: 'determine_fit',
        agent_type: 'strategy',
        entity_id: role_id,
        account_id,
        trace_id
      }, env);
      return { success: false, error: 'User profile not found' };
    }

    console.log(`Analyzing fit: ${profile.full_name} → ${role.role_title} at ${role.org_name}`);

    // Parse JSON fields
    const profileSkills = JSON.parse(profile.skills || '[]');
    const profileExperience = JSON.parse(profile.experience || '[]');
    const profileTargetRoles = JSON.parse(profile.target_roles || '[]');
    const roleRequirements = JSON.parse(role.requirements || '[]');
    const roleTechStack = JSON.parse(role.tech_stack || '[]');

    // Build context-rich prompt for AI analysis
    const prompt = `You are analyzing whether candidate John Kruze is a strong fit for this role.

CANDIDATE PROFILE:
Name: ${profile.full_name}
Summary: ${profile.summary}
Skills: ${profileSkills.join(', ')}
Target Roles: ${profileTargetRoles.join(', ')}
Compensation Min: $${profile.compensation_min}

Key Experience Highlights:
${profileExperience.map((exp, i) => `
${i + 1}. ${exp.title} at ${exp.company} (${exp.duration})
   Highlights: ${exp.highlights.slice(0, 3).join('; ')}
`).join('\n')}

ROLE DETAILS:
Title: ${role.role_title}
Company: ${role.org_name}
Industry: ${role.industry || 'Unknown'}
Funding Stage: ${role.funding_stage || 'Unknown'}
Company Size: ${role.employee_count || 'Unknown'}
Description: ${role.org_description || 'No description'}
Location: ${role.location || 'Unknown'}
Salary Range: ${role.salary_range || 'Not specified'}

Requirements:
${roleRequirements.slice(0, 10).join('\n')}

Tech Stack: ${roleTechStack.join(', ')}
Culture: ${role.culture_notes || 'No culture info'}

ANALYZE FIT AND RESPOND WITH VALID JSON (no markdown, no extra text):
{
  "fitScore": 85,
  "confidence": 90,
  "positioningStrategy": "Lead with MCP pioneer status and production deployment experience. Emphasize the rare combination of technical depth and cross-functional communication.",
  "keyStrengths": ["MCP first cohort", "3 production systems with 13+ days uptime", "Cross-domain communication"],
  "experiencesToHighlight": ["51 MCP tools across 8 categories", "Multi-agent orchestration", "90-second deployment pipeline"],
  "potentialConcerns": ["No formal ML degree - counter with 18 months production AI experience", "Self-taught - frame as rapid learning velocity"],
  "coverLetterAngle": "technical_depth",
  "action": "apply_now",
  "reasoning": "Excellent fit because..."
}

Scoring criteria:
- 90-100: Perfect fit, apply immediately (rare match of all key requirements + cultural fit)
- 75-89: Strong fit, good opportunity (meets most requirements, good growth potential)
- 60-74: Moderate fit, consider if other factors align (stretch role or missing key skills)
- Below 60: Weak fit, probably skip (fundamental misalignment)

Cover letter angles:
- "technical_depth": For roles requiring deep technical expertise
- "velocity": For fast-moving startups valuing shipping speed
- "cross_functional": For roles requiring business + technical communication
- "production_expertise": For roles emphasizing reliability and scale
- "innovation": For cutting-edge/research-focused roles

Actions:
- "apply_now": High fit, no blockers
- "wait_for_referral": Good fit but competitive, referral would help
- "skip": Poor fit, not worth applying

Be honest and realistic. Don't inflate fit scores. Consider:
1. Skills match (does candidate have required technical skills?)
2. Experience level (is this the right seniority?)
3. Domain fit (does candidate's background align with role?)
4. Compensation alignment (is salary range acceptable?)
5. Cultural fit (based on candidate's preferences and company culture)`;

    const aiResponse = await env.AI.run('@cf/meta/llama-3.1-70b-instruct', {
      messages: [
        {
          role: 'system',
          content: 'You are an expert career advisor and recruiter. Analyze candidate-role fit with brutal honesty. Respond ONLY with valid JSON.'
        },
        {
          role: 'user',
          content: prompt
        }
      ],
      max_tokens: 900
    });

    // Parse AI response
    let strategy;
    try {
      const responseText = aiResponse.response.trim();
      const jsonMatch = responseText.match(/```json\n?([\s\S]*?)\n?```/) || responseText.match(/\{[\s\S]*\}/);
      const jsonText = jsonMatch ? (jsonMatch[1] || jsonMatch[0]) : responseText;
      strategy = JSON.parse(jsonText);

      // Validate required fields
      if (!strategy.fitScore || !strategy.reasoning || !strategy.action) {
        throw new Error('Missing required fields in strategy response');
      }

    } catch (parseError) {
      console.error('Failed to parse strategy response:', aiResponse.response);
      // Fallback strategy
      strategy = {
        fitScore: 50,
        confidence: 40,
        positioningStrategy: 'Unable to analyze fit automatically. Manual review recommended.',
        keyStrengths: ['Production AI experience', 'MCP expertise'],
        experiencesToHighlight: ['Multi-agent systems', 'Edge deployment'],
        potentialConcerns: ['Analysis failed - review manually'],
        coverLetterAngle: 'technical_depth',
        action: 'wait_for_referral',
        reasoning: 'Automatic fit analysis failed. Review role manually before applying.'
      };
    }

    // Update role with fit analysis (only using columns that exist)
    const now = Date.now();
    await env.DB.prepare(`
      UPDATE roles
      SET fit_score = ?, fit_reasoning = ?, positioning_strategy = ?,
          key_experiences_to_highlight = ?, potential_concerns = ?,
          updated_at = ?
      WHERE id = ? AND account_id = ?
    `).bind(
      strategy.fitScore,
      strategy.reasoning,
      strategy.positioningStrategy,
      JSON.stringify(strategy.experiencesToHighlight || []),
      JSON.stringify(strategy.potentialConcerns || []),
      now,
      role_id,
      account_id
    ).run();

    // Emit event
    await emitEvent(env.DB, {
      trace_id,
      account_id,
      event_type: 'fit_analyzed',
      entity_type: 'role',
      entity_id: role_id,
      payload: {
        role_title: role.role_title,
        org_name: role.org_name,
        fit_score: strategy.fitScore,
        action: strategy.action
      }
    });

    const duration = Date.now() - startTime;

    await logOperationSuccess({
      operation: 'determine_fit',
      agent_type: 'strategy',
      entity_type: 'role',
      entity_id: role_id,
      account_id,
      trace_id,
      duration_ms: duration,
      result: {
        fit_score: strategy.fitScore,
        action: strategy.action,
        role_title: role.role_title,
        org_name: role.org_name
      }
    }, env);

    return {
      success: true,
      role_id,
      role_title: role.role_title,
      org_name: role.org_name,
      fit_score: strategy.fitScore,
      action: strategy.action,
      strategy
    };

  } catch (err) {
    await logError({
      error: err,
      operation: 'determine_fit',
      agent_type: 'strategy',
      entity_type: 'role',
      entity_id: role_id,
      account_id,
      trace_id,
      metadata: {
        role_title: role?.role_title,
        org_name: role?.org_name
      }
    }, env);

    return {
      success: false,
      role_id,
      error: err.message
    };
  }
}
