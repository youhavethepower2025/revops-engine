// Content Search Worker - Multi-source search
export default {
  async fetch(request, env) {
    if (request.method !== "POST") {
      return new Response("Method not allowed", { status: 405 });
    }

    const { topic, source_types = ["web", "academic", "social", "blog"], max_results = 50 } = await request.json();

    // Mock multi-source search
    // In production: Google Search API, arXiv, Twitter API, etc.
    const sources = [];
    
    // Simulate search results from different sources
    source_types.forEach((type, idx) => {
      for (let i = 0; i < Math.min(max_results / source_types.length, 15); i++) {
        sources.push({
          id: `source_${type}_${i}`,
          url: `https://example.com/${type}/${topic.replace(/\s+/g, '-')}-${i}`,
          title: `${topic} - ${type} source ${i + 1}`,
          source_type: type,
          snippet: `Relevant content about ${topic} from ${type} source`,
          published_at: new Date(Date.now() - i * 86400000).toISOString()
        });
      }
    });

    return new Response(JSON.stringify({
      success: true,
      topic,
      sources,
      count: sources.length
    }), {
      headers: { "Content-Type": "application/json" }
    });
  }
};


