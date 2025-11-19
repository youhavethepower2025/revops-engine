// RevOps Tracker Worker - Monitor email engagement
export default {
  async fetch(request, env) {
    if (request.method === "POST") {
      // Webhook handler for email events
      const { message_id, event_type, data } = await request.json();

      // Store interaction in database
      const interaction = {
        id: `interaction_${Date.now()}`,
        message_id,
        type: event_type, // open, click, reply
        data: JSON.stringify(data),
        timestamp: Math.floor(Date.now() / 1000)
      };

      // In production, insert into D1
      // await env.DB.prepare("INSERT INTO interactions ...").run(...)

      return new Response(JSON.stringify({
        success: true,
        interaction
      }), {
        headers: { "Content-Type": "application/json" }
      });
    }

    // GET - Get engagement stats for a message or campaign
    const url = new URL(request.url);
    const message_id = url.searchParams.get("message_id");
    const campaign_id = url.searchParams.get("campaign_id");

    // In production, query D1 for interactions
    const stats = {
      opens: Math.floor(Math.random() * 10),
      clicks: Math.floor(Math.random() * 5),
      replies: Math.floor(Math.random() * 2),
      last_activity: new Date().toISOString()
    };

    return new Response(JSON.stringify({
      success: true,
      message_id,
      campaign_id,
      stats
    }), {
      headers: { "Content-Type": "application/json" }
    });
  }
};


