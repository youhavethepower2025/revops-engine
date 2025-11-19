// Outreach Agent - Job Hunt Edition
// Generates customized cover letters and application materials

import { emitEvent, generateTraceId } from '../lib/events.js';
import { generateId } from '../lib/auth.js';
import {
  logError,
  logOperationStart,
  logOperationSuccess,
  logWarning
} from '../lib/error-logger.js';

/**
 * Generate application materials for a role
 * Creates customized cover letter based on fit analysis
 */
export async function generateApplication(role_id, account_id, trace_id, env) {
  const startTime = Date.now();
  let role, profile; // Declare outside try block so they're accessible in catch

  await logOperationStart({
    operation: 'generate_application',
    agent_type: 'outreach',
    entity_type: 'role',
    entity_id: role_id,
    account_id,
    trace_id
  }, env);

  try {
    // Get role with full context
    role = await env.DB.prepare(`
      SELECT r.*, o.name as org_name, o.domain, o.description as org_description,
             o.culture_notes, o.industry
      FROM roles r
      JOIN organizations o ON o.id = r.org_id
      WHERE r.id = ? AND r.account_id = ?
    `).bind(role_id, account_id).first();

    if (!role) {
      await logWarning({
        message: 'Role not found',
        operation: 'generate_application',
        agent_type: 'outreach',
        entity_id: role_id,
        account_id,
        trace_id
      }, env);
      return { success: false, error: 'Role not found' };
    }

    // Check if fit analysis has been done
    if (!role.fit_score || !role.positioning_strategy) {
      await logWarning({
        message: 'Fit analysis not completed for role',
        operation: 'generate_application',
        agent_type: 'outreach',
        entity_id: role_id,
        account_id,
        trace_id,
        metadata: { role_title: role.role_title, org_name: role.org_name }
      }, env);
      return {
        success: false,
        error: 'Please run fit analysis first (POST /api/roles/:id/analyze-fit)'
      };
    }

    // Get user profile
    profile = await env.DB.prepare(`
      SELECT * FROM user_profile WHERE account_id = ?
    `).bind(account_id).first();

    if (!profile) {
      await logWarning({
        message: 'User profile not found',
        operation: 'generate_application',
        agent_type: 'outreach',
        entity_id: role_id,
        account_id,
        trace_id
      }, env);
      return { success: false, error: 'User profile not found' };
    }

    console.log(`Generating application: ${profile.full_name} → ${role.role_title} at ${role.org_name}`);

    // Parse JSON fields
    const keyExperiences = JSON.parse(role.key_experiences_to_highlight || '[]');
    const roleRequirements = JSON.parse(role.requirements || '[]');
    const profileExperience = JSON.parse(profile.experience || '[]');

    // Build prompt for cover letter generation
    const prompt = `You are writing a compelling cover letter for John Kruze applying to ${role.org_name} for the ${role.role_title} position.

CANDIDATE BACKGROUND:
${profile.summary}

KEY EXPERIENCES TO EMPHASIZE (from fit analysis):
${keyExperiences.map((exp, i) => `${i + 1}. ${exp}`).join('\n')}

POSITIONING STRATEGY:
${role.positioning_strategy}

ROLE REQUIREMENTS (top priorities):
${roleRequirements.slice(0, 5).map((req, i) => `${i + 1}. ${req}`).join('\n')}

COMPANY INFO:
Name: ${role.org_name}
Industry: ${role.industry || 'Technology'}
Description: ${role.org_description || 'No description'}
Culture: ${role.culture_notes || 'No culture info'}

COVER LETTER GUIDELINES:
- Length: 3-4 paragraphs, ~250-350 words total
- Tone: Professional but authentic, confident without arrogance
- Focus: Match YOUR experience to THEIR needs (not generic)

Structure:
1. Opening hook (1-2 sentences):
   - Reference something specific about the company or role
   - Show you've done research, not sending generic applications

2. Why you're uniquely qualified (1 paragraph):
   - Highlight 2-3 key experiences that directly match their top requirements
   - Be specific: numbers, outcomes, technologies
   - Example: "I've built X which resulted in Y" not "I have experience with X"

3. Value proposition (1 paragraph):
   - What you'll bring to the team
   - How your unique background (MCP pioneer, production systems, cross-functional) solves their problems
   - Connect your experience to their company stage/needs

4. Close (2-3 sentences):
   - Express genuine interest in the specific work they're doing
   - Clear call to action: "I'd welcome the opportunity to discuss..."
   - Professional sign-off

AVOID:
- Generic openings like "I am writing to apply for..."
- Clichés like "I would be a great fit" or "perfect opportunity"
- Repeating your resume - tell the STORY behind the bullet points
- Apologizing or hedging ("I may not have X but...")
- Overly formal language - write like you'd talk to a colleague

WRITE THE COVER LETTER NOW.
Respond with ONLY the cover letter text (no JSON, no markdown, no "Here is the cover letter:").`;

    const aiResponse = await env.AI.run('@cf/meta/llama-3.1-70b-instruct', {
      messages: [
        {
          role: 'system',
          content: 'You are an expert cover letter writer for senior technical roles. Write compelling, specific, authentic cover letters. Respond with ONLY the cover letter text, no other formatting.'
        },
        {
          role: 'user',
          content: prompt
        }
      ],
      max_tokens: 1000
    });

    const coverLetter = aiResponse.response.trim();

    // Generate email subject and body
    const emailSubject = `Application: ${role.role_title} - ${profile.full_name}`;

    const emailBody = `Dear Hiring Team,

I'm reaching out to apply for the ${role.role_title} position at ${role.org_name}.

${coverLetter}

I've attached my resume and would welcome the opportunity to discuss how my experience with ${keyExperiences[0] || 'AI systems'} could contribute to your team.

Best regards,
${profile.full_name}
${profile.email}
${profile.linkedin_url || ''}`;

    // Create draft application
    const app_id = generateId();
    const timestamp = Date.now();

    await env.DB.prepare(`
      INSERT INTO applications (
        id, role_id, org_id, account_id, cover_letter,
        email_subject, email_body, email_to,
        status, created_at, updated_at
      ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    `).bind(
      app_id,
      role_id,
      role.org_id,
      account_id,
      coverLetter,
      emailSubject,
      emailBody,
      null, // email_to will be filled in when user is ready to send
      'draft', // Always draft, user reviews before sending
      timestamp,
      timestamp
    ).run();

    // Note: decision_logs table has foreign key to leads table
    // For job hunt, we use events table for activity tracking instead

    // Emit event
    await emitEvent(env.DB, {
      trace_id,
      account_id,
      event_type: 'application_generated',
      entity_type: 'application',
      entity_id: app_id,
      payload: {
        role_id,
        org_id: role.org_id,
        role_title: role.role_title,
        org_name: role.org_name
      }
    });

    const duration = Date.now() - startTime;

    await logOperationSuccess({
      operation: 'generate_application',
      agent_type: 'outreach',
      entity_type: 'application',
      entity_id: app_id,
      account_id,
      trace_id,
      duration_ms: duration,
      result: {
        application_id: app_id,
        role_title: role.role_title,
        org_name: role.org_name,
        cover_letter_length: coverLetter.length
      }
    }, env);

    return {
      success: true,
      application_id: app_id,
      role_id,
      cover_letter: coverLetter,
      email_subject: emailSubject,
      preview: coverLetter.substring(0, 200) + '...',
      message: 'Application generated and saved as draft. Review and edit before sending.'
    };

  } catch (err) {
    await logError({
      error: err,
      operation: 'generate_application',
      agent_type: 'outreach',
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
