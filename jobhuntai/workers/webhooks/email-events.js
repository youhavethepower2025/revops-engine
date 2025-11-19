/**
 * Email Event Webhook Handler
 *
 * Receives delivery, open, click, and reply events from email provider
 * Updates agent_outcomes table for eval agent to analyze
 */

import { emitEvent } from '../lib/events.js';
import { generateId } from '../lib/auth.js';

/**
 * Handle incoming email event webhook
 */
export async function handleEmailEvent(request, env) {
  try {
    const event = await request.json();

    // Extract event data (adapt based on email provider format)
    const {
      lead_id,
      account_id,
      campaign_id,
      event_type, // 'delivered', 'opened', 'clicked', 'replied'
      timestamp,
      metadata
    } = event;

    if (!lead_id || !account_id || !event_type) {
      return new Response(JSON.stringify({ error: 'Missing required fields' }), {
        status: 400,
        headers: { 'Content-Type': 'application/json' }
      });
    }

    // Get or create outcome record for this lead
    let outcome = await env.DB.prepare(`
      SELECT * FROM agent_outcomes
      WHERE lead_id = ? AND account_id = ?
      ORDER BY created_at DESC
      LIMIT 1
    `).bind(lead_id, account_id).first();

    const now = Date.now();

    if (outcome) {
      // Update existing outcome
      const updates = [];
      const values = [];

      if (event_type === 'sent') {
        updates.push('email_sent = ?');
        values.push(1);
      } else if (event_type === 'delivered') {
        updates.push('email_delivered = ?');
        values.push(1);
      } else if (event_type === 'opened') {
        updates.push('email_opened = ?');
        values.push(1);
      } else if (event_type === 'clicked') {
        updates.push('email_clicked = ?');
        values.push(1);
      } else if (event_type === 'replied') {
        updates.push('email_replied = ?');
        values.push(1);
      }

      if (updates.length > 0) {
        updates.push('updated_at = ?');
        values.push(now, outcome.id);

        await env.DB.prepare(`
          UPDATE agent_outcomes
          SET ${updates.join(', ')}
          WHERE id = ?
        `).bind(...values).run();
      }

      // Emit event for observability
      await emitEvent(env.DB, {
        trace_id: outcome.trace_id,
        account_id,
        event_type: `email_${event_type}`,
        entity_type: 'lead',
        entity_id: lead_id,
        payload: {
          campaign_id,
          outcome_id: outcome.id,
          timestamp
        }
      });

      // If this is a reply, trigger eval agent
      if (event_type === 'replied') {
        await triggerEval(lead_id, account_id, outcome.trace_id, env);
      }

      return new Response(JSON.stringify({
        success: true,
        outcome_id: outcome.id,
        updated: event_type
      }), {
        headers: { 'Content-Type': 'application/json' }
      });

    } else {
      // Create new outcome record
      const outcome_id = generateId();
      const trace_id = metadata?.trace_id || generateId();

      await env.DB.prepare(`
        INSERT INTO agent_outcomes (
          id, trace_id, account_id, campaign_id, lead_id,
          agent_type,
          email_sent, email_delivered, email_opened, email_clicked, email_replied,
          created_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
      `).bind(
        outcome_id,
        trace_id,
        account_id,
        campaign_id || 'unknown',
        lead_id,
        'outreach', // Initial outcome from outreach agent
        event_type === 'sent' ? 1 : 0,
        event_type === 'delivered' ? 1 : 0,
        event_type === 'opened' ? 1 : 0,
        event_type === 'clicked' ? 1 : 0,
        event_type === 'replied' ? 1 : 0,
        now,
        now
      ).run();

      await emitEvent(env.DB, {
        trace_id,
        account_id,
        event_type: `email_${event_type}`,
        entity_type: 'lead',
        entity_id: lead_id,
        payload: {
          campaign_id,
          outcome_id,
          timestamp
        }
      });

      return new Response(JSON.stringify({
        success: true,
        outcome_id,
        created: event_type
      }), {
        headers: { 'Content-Type': 'application/json' }
      });
    }

  } catch (error) {
    console.error('Email event webhook error:', error);
    return new Response(JSON.stringify({ error: error.message }), {
      status: 500,
      headers: { 'Content-Type': 'application/json' }
    });
  }
}

/**
 * Trigger eval agent to analyze this lead's performance
 */
async function triggerEval(lead_id, account_id, trace_id, env) {
  try {
    const { evaluateLead } = await import('../agents/eval.js');

    // Run eval asynchronously (don't block webhook response)
    env.ctx.waitUntil(
      evaluateLead(lead_id, account_id, trace_id, env)
    );

  } catch (error) {
    console.error('Failed to trigger eval:', error);
  }
}

/**
 * Simulate email events for testing
 */
export async function simulateEmailEvent(lead_id, account_id, campaign_id, event_type, env) {
  const mockRequest = {
    json: async () => ({
      lead_id,
      account_id,
      campaign_id,
      event_type,
      timestamp: Date.now(),
      metadata: {}
    })
  };

  return await handleEmailEvent(mockRequest, env);
}
