// Content Synthesizer Worker - Generate structured reports
export default {
  async fetch(request, env) {
    if (request.method !== "POST") {
      return new Response("Method not allowed", { status: 405 });
    }

    const { topic, insights, sources, knowledge_graph } = await request.json();

    try {
      // Use Workers AI to synthesize report
      const prompt = `Create a comprehensive technical report about "${topic}".

Sources analyzed: ${sources.length}
Key insights: ${insights.length}

Insights:
${JSON.stringify(insights.slice(0, 20), null, 2)}

Knowledge Graph:
${JSON.stringify(knowledge_graph, null, 2)}

Generate a structured report with:
1. Executive Summary
2. Key Findings
3. Detailed Analysis
4. Trends and Patterns
5. Conclusions
6. Citations (list all source URLs)

Format as markdown.`;

      const response = await env.AI.run('@cf/qwen/qwen-2.5-7b-instruct', {
        messages: [
          { role: "user", content: prompt }
        ],
        max_tokens: 2000
      });

      const report_content = response.response || `# Report: ${topic}\n\nAnalysis complete.`;

      return new Response(JSON.stringify({
        success: true,
        topic,
        report: {
          title: `Research Report: ${topic}`,
          content: report_content,
          sources_count: sources.length,
          insights_count: insights.length,
          generated_at: new Date().toISOString()
        }
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


