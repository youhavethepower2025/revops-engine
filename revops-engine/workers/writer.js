// RevOps Writer Worker - Generate personalized outreach emails
export default {
  async fetch(request, env) {
    if (request.method !== "POST") {
      return new Response("Method not allowed", { status: 405 });
    }

    const { prospect, research_notes, campaign_context } = await request.json();

    // Use Workers AI to generate personalized email
    try {
      const prompt = `Write a personalized outreach email to ${prospect.person_name}, ${prospect.person_title} at ${prospect.company_name}.

Context:
${JSON.stringify(research_notes, null, 2)}

Campaign: ${campaign_context?.name || "General Outreach"}

Requirements:
- Subject line (compelling, under 50 chars)
- Body (3-4 paragraphs, value-first approach)
- Personal, not generic
- Reference specific talking points from research
- Clear call-to-action

Format as JSON: {subject: "...", body: "..."}`;

      // Call Workers AI
      const response = await env.AI.run('@cf/qwen/qwen-2.5-7b-instruct', {
        messages: [
          { role: "user", content: prompt }
        ],
        max_tokens: 800
      });

      // Parse AI response (in production, use structured output)
      const ai_text = response.response || "";
      let subject = `Quick question about ${prospect.company_name}`;
      let body = ai_text;

      // Try to extract subject if AI included it
      if (ai_text.includes("Subject:")) {
        const parts = ai_text.split("Subject:");
        if (parts.length > 1) {
          subject = parts[1].split("\n")[0].trim();
          body = parts.slice(1).join("Subject:").replace(subject, "").trim();
        }
      }

      return new Response(JSON.stringify({
        success: true,
        prospect_id: prospect.id,
        message: {
          subject,
          body,
          personalization_score: 0.85,
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


