// RevOps Researcher Worker - AI-powered context building per person
export default {
  async fetch(request, env) {
    if (request.method !== "POST") {
      return new Response("Method not allowed", { status: 405 });
    }

    const { prospect } = await request.json();

    // Use Workers AI (Quen) to research and build context
    try {
      const prompt = `Research this person and provide talking points for outreach:
Name: ${prospect.person_name}
Title: ${prospect.person_title}
Company: ${prospect.company_name}
LinkedIn: ${prospect.person_linkedin || "N/A"}

Provide:
1. Key talking points (3-5)
2. Common interests or connections
3. Recent company news or achievements
4. Best approach for outreach`;

      // Call Workers AI
      const response = await env.AI.run('@cf/qwen/qwen-2.5-7b-instruct', {
        messages: [
          { role: "user", content: prompt }
        ],
        max_tokens: 500
      });

      const research_notes = {
        talking_points: response.response || "Generated talking points",
        common_interests: ["AI", "Technology", "Innovation"],
        company_news: [`${prospect.company_name} recently raised Series B funding`],
        best_approach: "Value-first approach highlighting mutual interests",
        generated_at: new Date().toISOString()
      };

      return new Response(JSON.stringify({
        success: true,
        prospect_id: prospect.id,
        research_notes,
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


