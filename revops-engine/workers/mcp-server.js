// RevOps Engine MCP Server
export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    
    // MCP endpoint
    if (url.pathname === "/mcp") {
      return handleMCP(request, env);
    }
    
    // Health check
    if (url.pathname === "/health") {
      return new Response(JSON.stringify({ status: "ok", app: "revops-engine" }), {
        headers: { "Content-Type": "application/json" }
      });
    }
    
    return new Response("Not Found", { status: 404 });
  }
};

async function handleMCP(request, env) {
  const { jsonrpc, id, method, params } = await request.json();
  
  if (method === "initialize") {
    return json({
      jsonrpc: "2.0",
      id,
      result: {
        protocolVersion: "2024-11-05",
        capabilities: { tools: {} },
        serverInfo: {
          name: "revops-engine-mcp",
          version: "1.0.0"
        }
      }
    });
  }
  
  if (method === "tools/list") {
    return json({
      jsonrpc: "2.0",
      id,
      result: {
        tools: [
          {
            name: "start_campaign",
            description: "Research companies and generate outreach for a campaign",
            inputSchema: {
              type: "object",
              properties: {
                campaign_name: { type: "string" },
                criteria: {
                  type: "object",
                  properties: {
                    industry: { type: "string" },
                    stage: { type: "string" },
                    roles: { type: "array", items: { type: "string" } },
                    count: { type: "integer" }
                  }
                },
                user_id: { type: "string" }
              },
              required: ["campaign_name", "criteria", "user_id"]
            }
          },
          {
            name: "review_prospects",
            description: "Browse researched contacts for a campaign",
            inputSchema: {
              type: "object",
              properties: {
                campaign_id: { type: "string" },
                status: { type: "string" },
                limit: { type: "integer", default: 50 }
              },
              required: ["campaign_id"]
            }
          },
          {
            name: "approve_outreach",
            description: "Review and approve messages for sending",
            inputSchema: {
              type: "object",
              properties: {
                message_id: { type: "string" },
                approved: { type: "boolean" }
              },
              required: ["message_id", "approved"]
            }
          },
          {
            name: "track_campaign",
            description: "Get engagement metrics for a campaign",
            inputSchema: {
              type: "object",
              properties: {
                campaign_id: { type: "string" }
              },
              required: ["campaign_id"]
            }
          },
          {
            name: "find_warm_leads",
            description: "Identify high-engagement prospects",
            inputSchema: {
              type: "object",
              properties: {
                campaign_id: { type: "string" },
                min_engagement: { type: "integer", default: 2 }
              },
              required: ["campaign_id"]
            }
          }
        ]
      }
    });
  }
  
  if (method === "tools/call") {
    const { name, arguments: args } = params;
    const result = await executeTool(name, args, env);
    
    return json({
      jsonrpc: "2.0",
      id,
      result: {
        content: [{
          type: "text",
          text: JSON.stringify(result, null, 2)
        }]
      }
    });
  }
  
  return json({
    jsonrpc: "2.0",
    id,
    error: { code: -32601, message: "Method not found" }
  });
}

async function executeTool(name, args, env) {
  switch (name) {
    case "start_campaign":
      return await handle_start_campaign(args, env);
    case "review_prospects":
      return await handle_review_prospects(args, env);
    case "approve_outreach":
      return await handle_approve_outreach(args, env);
    case "track_campaign":
      return await handle_track_campaign(args, env);
    case "find_warm_leads":
      return await handle_find_warm_leads(args, env);
    default:
      throw new Error(`Unknown tool: ${name}`);
  }
}

async function handle_start_campaign(args, env) {
  const { campaign_name, criteria, user_id } = args;
  
  // Create campaign in database
  const campaign_id = `campaign_${Date.now()}`;
  await env.DB.prepare(`
    INSERT INTO campaigns (id, user_id, name, status, target_criteria)
    VALUES (?, ?, ?, 'active', ?)
  `).bind(campaign_id, user_id, campaign_name, JSON.stringify(criteria)).run();
  
  // Trigger research pipeline (in production, use Workflow)
  // For now, simulate
  const prospects = [];
  
  // Search for companies
  const searchRes = await fetch('https://revops-search.aijesusbro-brain.workers.dev', {
    method: 'POST',
    body: JSON.stringify({ criteria }),
    headers: { 'Content-Type': 'application/json' }
  });
  const { companies } = await searchRes.json();
  
  // Process each company
  for (const company of companies.slice(0, criteria.count || 20)) {
    // Scrape contacts
    const scrapeRes = await fetch('https://revops-scraper.aijesusbro-brain.workers.dev', {
      method: 'POST',
      body: JSON.stringify({ company_domain: company.domain, company_name: company.name }),
      headers: { 'Content-Type': 'application/json' }
    });
    const { contacts } = await scrapeRes.json();
    
    // Process each contact
    for (const contact of contacts) {
      // Enrich
      const enrichRes = await fetch('https://revops-enrichment.aijesusbro-brain.workers.dev', {
        method: 'POST',
        body: JSON.stringify({ contact }),
        headers: { 'Content-Type': 'application/json' }
      });
      const enriched = await enrichRes.json();
      
      // Research
      const researchRes = await fetch('https://revops-researcher.aijesusbro-brain.workers.dev', {
        method: 'POST',
        body: JSON.stringify({ prospect: { ...contact, ...enriched.contact } }),
        headers: { 'Content-Type': 'application/json' }
      });
      const { research_notes } = await researchRes.json();
      
      // Write email
      const writeRes = await fetch('https://revops-writer.aijesusbro-brain.workers.dev', {
        method: 'POST',
        body: JSON.stringify({
          prospect: { ...contact, ...enriched.contact },
          research_notes,
          campaign_context: { name: campaign_name }
        }),
        headers: { 'Content-Type': 'application/json' }
      });
      const { message } = await writeRes.json();
      
      // Store prospect
      const prospect_id = `prospect_${Date.now()}_${Math.random()}`;
      await env.DB.prepare(`
        INSERT INTO prospects (id, campaign_id, user_id, company_name, company_domain,
          person_name, person_email, person_title, person_linkedin, enrichment_data, research_notes, status)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'drafted')
      `).bind(
        prospect_id, campaign_id, user_id, company.name, company.domain,
        contact.name, contact.email, contact.title, contact.linkedin,
        JSON.stringify(enriched.enrichment), JSON.stringify(research_notes)
      ).run();
      
      // Store message
      const message_id = `message_${Date.now()}_${Math.random()}`;
      await env.DB.prepare(`
        INSERT INTO messages (id, prospect_id, campaign_id, user_id, subject, body, status)
        VALUES (?, ?, ?, ?, ?, ?, 'draft')
      `).bind(message_id, prospect_id, campaign_id, user_id, message.subject, message.body).run();
      
      prospects.push({ prospect_id, message_id, status: 'drafted' });
    }
  }
  
  return {
    success: true,
    campaign_id,
    prospects_count: prospects.length,
    prospects,
    message: `${prospects.length} prospects researched and drafts ready for review`
  };
}

async function handle_review_prospects(args, env) {
  const { campaign_id, status, limit = 50 } = args;
  
  const query = env.DB.prepare(`
    SELECT p.*, m.id as message_id, m.subject, m.body, m.status as message_status
    FROM prospects p
    LEFT JOIN messages m ON m.prospect_id = p.id
    WHERE p.campaign_id = ? ${status ? 'AND p.status = ?' : ''}
    ORDER BY p.created_at DESC
    LIMIT ?
  `);
  
  const results = status 
    ? await query.bind(campaign_id, status, limit).all()
    : await query.bind(campaign_id, limit).all();
  
  return {
    success: true,
    campaign_id,
    prospects: results.results || [],
    count: results.results?.length || 0
  };
}

async function handle_approve_outreach(args, env) {
  const { message_id, approved } = args;
  
  if (approved) {
    await env.DB.prepare(`
      UPDATE messages SET status = 'approved' WHERE id = ?
    `).bind(message_id).run();
    
    return { success: true, message_id, status: 'approved' };
  } else {
    await env.DB.prepare(`
      UPDATE messages SET status = 'draft' WHERE id = ?
    `).bind(message_id).run();
    
    return { success: true, message_id, status: 'draft' };
  }
}

async function handle_track_campaign(args, env) {
  const { campaign_id } = args;
  
  // Get message stats
  const messages = await env.DB.prepare(`
    SELECT status, COUNT(*) as count
    FROM messages
    WHERE campaign_id = ?
    GROUP BY status
  `).bind(campaign_id).all();
  
  // Get interaction stats
  const interactions = await env.DB.prepare(`
    SELECT i.type, COUNT(*) as count
    FROM interactions i
    JOIN messages m ON m.id = i.message_id
    WHERE m.campaign_id = ?
    GROUP BY i.type
  `).bind(campaign_id).all();
  
  return {
    success: true,
    campaign_id,
    messages: messages.results || [],
    interactions: interactions.results || []
  };
}

async function handle_find_warm_leads(args, env) {
  const { campaign_id, min_engagement = 2 } = args;
  
  const warm_leads = await env.DB.prepare(`
    SELECT p.*, COUNT(i.id) as engagement_count
    FROM prospects p
    JOIN messages m ON m.prospect_id = p.id
    LEFT JOIN interactions i ON i.message_id = m.id
    WHERE p.campaign_id = ? AND m.status = 'sent'
    GROUP BY p.id
    HAVING engagement_count >= ?
    ORDER BY engagement_count DESC
  `).bind(campaign_id, min_engagement).all();
  
  return {
    success: true,
    campaign_id,
    warm_leads: warm_leads.results || [],
    count: warm_leads.results?.length || 0
  };
}

function json(data) {
  return new Response(JSON.stringify(data), {
    headers: { "Content-Type": "application/json" }
  });
}


