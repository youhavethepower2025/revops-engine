// RevOps Search Worker - Query external APIs for companies
export default {
  async fetch(request, env) {
    if (request.method !== "POST") {
      return new Response("Method not allowed", { status: 405 });
    }

    const { criteria } = await request.json();
    const { industry, stage, roles, count = 20 } = criteria || {};

    // Mock search - in production, integrate with Crunchbase, LinkedIn, etc.
    // For now, return sample data structure
    const companies = [];
    
    // Simulate API search results
    for (let i = 0; i < Math.min(count, 20); i++) {
      companies.push({
        id: `company_${i}`,
        name: `Sample ${industry || "AI"} Company ${i + 1}`,
        domain: `company${i + 1}.com`,
        stage: stage || "Series B",
        industry: industry || "AI Infrastructure",
        employees: Math.floor(Math.random() * 500) + 50,
        funding: Math.floor(Math.random() * 50) + 10,
        location: "San Francisco, CA"
      });
    }

    return new Response(JSON.stringify({
      success: true,
      companies,
      count: companies.length,
      criteria
    }), {
      headers: { "Content-Type": "application/json" }
    });
  }
};


