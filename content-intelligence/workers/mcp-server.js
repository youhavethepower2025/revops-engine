// Content Intelligence MCP Server
export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    
    if (url.pathname === "/mcp") {
      return handleMCP(request, env);
    }
    
    if (url.pathname === "/health") {
      return new Response(JSON.stringify({ status: "ok", app: "content-intelligence" }), {
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
          name: "content-intelligence-mcp",
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
            name: "research_topic",
            description: "Deep dive research on any subject",
            inputSchema: {
              type: "object",
              properties: {
                topic: { type: "string" },
                depth: { type: "string", default: "standard" },
                max_sources: { type: "integer", default: 50 },
                user_id: { type: "string" }
              },
              required: ["topic", "user_id"]
            }
          },
          {
            name: "monitor_topic",
            description: "Track a subject over time for new content",
            inputSchema: {
              type: "object",
              properties: {
                topic: { type: "string" },
                user_id: { type: "string" }
              },
              required: ["topic", "user_id"]
            }
          },
          {
            name: "query_knowledge",
            description: "Ask questions about researched topics",
            inputSchema: {
              type: "object",
              properties: {
                topic_id: { type: "string" },
                question: { type: "string" }
              },
              required: ["topic_id", "question"]
            }
          },
          {
            name: "generate_report",
            description: "Create structured output/report from research",
            inputSchema: {
              type: "object",
              properties: {
                topic_id: { type: "string" },
                format: { type: "string", default: "markdown" }
              },
              required: ["topic_id"]
            }
          },
          {
            name: "find_sources",
            description: "Get citations for claims in research",
            inputSchema: {
              type: "object",
              properties: {
                topic_id: { type: "string" },
                claim: { type: "string" }
              },
              required: ["topic_id"]
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
    case "research_topic":
      return await handle_research_topic(args, env);
    case "monitor_topic":
      return await handle_monitor_topic(args, env);
    case "query_knowledge":
      return await handle_query_knowledge(args, env);
    case "generate_report":
      return await handle_generate_report(args, env);
    case "find_sources":
      return await handle_find_sources(args, env);
    default:
      throw new Error(`Unknown tool: ${name}`);
  }
}

async function handle_research_topic(args, env) {
  const { topic, depth, max_sources = 50, user_id } = args;
  
  // Create research topic
  const topic_id = `topic_${Date.now()}`;
  await env.DB.prepare(`
    INSERT INTO research_topics (id, user_id, topic, status)
    VALUES (?, ?, ?, 'active')
  `).bind(topic_id, user_id, topic).run();
  
  // Search for sources
  const searchRes = await fetch('https://content-search.aijesusbro-brain.workers.dev', {
    method: 'POST',
    body: JSON.stringify({ topic, max_results: max_sources }),
    headers: { 'Content-Type': 'application/json' }
  });
  const { sources } = await searchRes.json();
  
  // Fetch and analyze each source
  const all_insights = [];
  const all_sources_stored = [];
  
  for (const source of sources.slice(0, max_sources)) {
    // Fetch content
    const fetchRes = await fetch('https://content-fetcher.aijesusbro-brain.workers.dev', {
      method: 'POST',
      body: JSON.stringify({ source }),
      headers: { 'Content-Type': 'application/json' }
    });
    const { extracted } = await fetchRes.json();
    
    // Store source
    const source_id = `source_${Date.now()}_${Math.random()}`;
    await env.DB.prepare(`
      INSERT INTO sources (id, topic_id, user_id, url, title, content, source_type)
      VALUES (?, ?, ?, ?, ?, ?, ?)
    `).bind(source_id, topic_id, user_id, source.url, extracted.title, extracted.content, source.source_type).run();
    all_sources_stored.push({ id: source_id, url: source.url });
    
    // Analyze
    const analyzeRes = await fetch('https://content-analyzer.aijesusbro-brain.workers.dev', {
      method: 'POST',
      body: JSON.stringify({ source_content: { ...extracted, source_id }, topic }),
      headers: { 'Content-Type': 'application/json' }
    });
    const { insights } = await analyzeRes.json();
    
    // Store insights
    for (const insight of insights) {
      const insight_id = `insight_${Date.now()}_${Math.random()}`;
      await env.DB.prepare(`
        INSERT INTO insights (id, source_id, topic_id, user_id, claim, evidence, confidence)
        VALUES (?, ?, ?, ?, ?, ?, ?)
      `).bind(insight_id, source_id, topic_id, user_id, insight.claim, insight.evidence, insight.confidence || 0.8).run();
      all_insights.push(insight);
    }
  }
  
  // Build knowledge graph
  const graphRes = await fetch('https://content-grapher.aijesusbro-brain.workers.dev', {
    method: 'POST',
    body: JSON.stringify({ insights: all_insights, topic }),
    headers: { 'Content-Type': 'application/json' }
  });
  const { graph } = await graphRes.json();
  
  // Store knowledge graph
  for (const rel of graph.relationships || []) {
    const kg_id = `kg_${Date.now()}_${Math.random()}`;
    await env.DB.prepare(`
      INSERT INTO knowledge_graph (id, topic_id, user_id, entity_a, relationship, entity_b, strength)
      VALUES (?, ?, ?, ?, ?, ?, ?)
    `).bind(kg_id, topic_id, user_id, rel.entity_a, rel.relationship, rel.entity_b, rel.strength || 0.5).run();
  }
  
  return {
    success: true,
    topic_id,
    topic,
    sources_count: all_sources_stored.length,
    insights_count: all_insights.length,
    entities_count: graph.entities?.length || 0,
    relationships_count: graph.relationships?.length || 0,
    message: `Research complete. ${all_sources_stored.length} sources analyzed, ${all_insights.length} insights extracted.`
  };
}

async function handle_monitor_topic(args, env) {
  const { topic, user_id } = args;
  
  // Create or update monitoring
  const topic_id = `topic_${Date.now()}`;
  await env.DB.prepare(`
    INSERT INTO research_topics (id, user_id, topic, status)
    VALUES (?, ?, ?, 'monitoring')
    ON CONFLICT(id) DO UPDATE SET status = 'monitoring', updated_at = strftime('%s', 'now')
  `).bind(topic_id, user_id, topic).run();
  
  // Start monitoring worker
  await fetch('https://content-monitor.aijesusbro-brain.workers.dev', {
    method: 'POST',
    body: JSON.stringify({ topic_id, topic, user_id }),
    headers: { 'Content-Type': 'application/json' }
  });
  
  return {
    success: true,
    topic_id,
    topic,
    monitoring: true,
    schedule: "daily"
  };
}

async function handle_query_knowledge(args, env) {
  const { topic_id, question } = args;
  
  // Get insights for topic
  const insights = await env.DB.prepare(`
    SELECT claim, evidence, confidence
    FROM insights
    WHERE topic_id = ?
    ORDER BY confidence DESC
    LIMIT 20
  `).bind(topic_id).all();
  
  // Use AI to answer question based on insights
  const context = insights.results?.map(i => `${i.claim}: ${i.evidence}`).join('\n\n') || '';
  
  const prompt = `Based on this research context, answer the question:

Context:
${context}

Question: ${question}

Provide a clear, evidence-based answer.`;

  const response = await env.AI.run('@cf/qwen/qwen-2.5-7b-instruct', {
    messages: [{ role: "user", content: prompt }],
    max_tokens: 500
  });
  
  return {
    success: true,
    topic_id,
    question,
    answer: response.response || "Answer generated",
    sources_used: insights.results?.length || 0
  };
}

async function handle_generate_report(args, env) {
  const { topic_id, format = "markdown" } = args;
  
  // Get all data for topic
  const topic = await env.DB.prepare(`SELECT * FROM research_topics WHERE id = ?`).bind(topic_id).first();
  const sources = await env.DB.prepare(`SELECT * FROM sources WHERE topic_id = ?`).bind(topic_id).all();
  const insights = await env.DB.prepare(`SELECT * FROM insights WHERE topic_id = ? ORDER BY confidence DESC`).bind(topic_id).all();
  const graph = await env.DB.prepare(`SELECT * FROM knowledge_graph WHERE topic_id = ?`).bind(topic_id).all();
  
  // Synthesize report
  const synthRes = await fetch('https://content-synthesizer.aijesusbro-brain.workers.dev', {
    method: 'POST',
    body: JSON.stringify({
      topic: topic.topic,
      insights: insights.results || [],
      sources: sources.results || [],
      knowledge_graph: { relationships: graph.results || [] }
    }),
    headers: { 'Content-Type': 'application/json' }
  });
  const { report } = await synthRes.json();
  
  // Store report
  const report_id = `report_${Date.now()}`;
  await env.DB.prepare(`
    INSERT INTO reports (id, topic_id, user_id, title, content, sources_count)
    VALUES (?, ?, ?, ?, ?, ?)
  `).bind(report_id, topic_id, topic.user_id, report.title, report.content, sources.results?.length || 0).run();
  
  return {
    success: true,
    report_id,
    topic_id,
    report,
    format
  };
}

async function handle_find_sources(args, env) {
  const { topic_id, claim } = args;
  
  // Search insights for matching claims
  const insights = await env.DB.prepare(`
    SELECT i.*, s.url, s.title, s.source_type
    FROM insights i
    JOIN sources s ON s.id = i.source_id
    WHERE i.topic_id = ? AND (i.claim LIKE ? OR i.evidence LIKE ?)
    ORDER BY i.confidence DESC
    LIMIT 10
  `).bind(topic_id, `%${claim}%`, `%${claim}%`).all();
  
  return {
    success: true,
    topic_id,
    claim,
    sources: insights.results || [],
    count: insights.results?.length || 0
  };
}

function json(data) {
  return new Response(JSON.stringify(data), {
    headers: { "Content-Type": "application/json" }
  });
}


