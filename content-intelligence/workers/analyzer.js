// Content Analyzer Worker - AI extraction of insights
export default {
  async fetch(request, env) {
    if (request.method !== "POST") {
      return new Response("Method not allowed", { status: 405 });
    }

    const { source_content, topic } = await request.json();
    const { title, content } = source_content;

    try {
      // Use Workers AI to extract insights
      const prompt = `Analyze this content about "${topic}" and extract key insights:

Title: ${title}
Content: ${content.substring(0, 4000)}

Extract:
1. Key claims/assertions (3-5)
2. Supporting evidence for each claim
3. Confidence level (0-1) for each claim
4. Important entities mentioned
5. Relationships between concepts

Format as JSON array of insights: [{claim, evidence, confidence, entities, relationships}]`;

      const response = await env.AI.run('@cf/qwen/qwen-2.5-7b-instruct', {
        messages: [
          { role: "user", content: prompt }
        ],
        max_tokens: 1000
      });

      // Parse AI response (in production, use structured output)
      let insights = [];
      try {
        insights = JSON.parse(response.response || "[]");
      } catch {
        // Fallback if AI doesn't return valid JSON
        insights = [{
          claim: response.response || "Key insight extracted",
          evidence: content.substring(0, 500),
          confidence: 0.8,
          entities: [],
          relationships: []
        }];
      }

      return new Response(JSON.stringify({
        success: true,
        source_id: source_content.source_id,
        insights,
        count: insights.length,
        ai_model: "qwen-2.5-7b-instruct"
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


