// Content Grapher Worker - Build entity/concept relationships
export default {
  async fetch(request, env) {
    if (request.method !== "POST") {
      return new Response("Method not allowed", { status: 405 });
    }

    const { insights, topic } = await request.json();

    try {
      // Use Workers AI to identify relationships
      const prompt = `Analyze these insights about "${topic}" and identify relationships:

${JSON.stringify(insights, null, 2)}

Identify:
1. Entities (people, organizations, concepts)
2. Relationships between entities
3. Relationship strength (0-1)

Format as JSON: {entities: [...], relationships: [{entity_a, relationship, entity_b, strength}]}`;

      const response = await env.AI.run('@cf/qwen/qwen-2.5-7b-instruct', {
        messages: [
          { role: "user", content: prompt }
        ],
        max_tokens: 800
      });

      // Parse AI response
      let graph_data = { entities: [], relationships: [] };
      try {
        graph_data = JSON.parse(response.response || "{}");
      } catch {
        // Fallback
        graph_data = {
          entities: [topic],
          relationships: []
        };
      }

      return new Response(JSON.stringify({
        success: true,
        topic,
        graph: graph_data,
        entities_count: graph_data.entities?.length || 0,
        relationships_count: graph_data.relationships?.length || 0
      }), {
        headers: { "Content-Type": "application/json" }
      });
    } catch (error) {
      return new Response(JSON.stringify({
        success: false,
        error: error.message
      }), {
        status: 500,
        headers: { "Content-Type": "application/json" }
      });
    }
  }
};


