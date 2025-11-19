// Content Fetcher Worker - Full-text extraction + parsing
export default {
  async fetch(request, env) {
    if (request.method !== "POST") {
      return new Response("Method not allowed", { status: 405 });
    }

    const { source } = await request.json();
    const { url, source_type } = source;

    try {
      // Fetch full content
      let content = "";
      let title = source.title || "";

      if (source_type === "web" || source_type === "blog") {
        // Use Browser API for JS-heavy sites
        const page = await env.BROWSER.newPage();
        await page.goto(url);
        content = await page.content();
        title = await page.title();
        await page.close();
      } else {
        // Direct fetch for simple content
        const response = await fetch(url);
        content = await response.text();
      }

      // Extract main content (simplified - in production use readability library)
      const extracted = {
        title,
        content: content.substring(0, 50000), // Limit size
        word_count: content.split(/\s+/).length,
        fetched_at: new Date().toISOString()
      };

      return new Response(JSON.stringify({
        success: true,
        source_id: source.id,
        url,
        extracted
      }), {
        headers: { "Content-Type": "application/json" }
      });
    } catch (error) {
      return new Response(JSON.stringify({
        success: false,
        error: error.message,
        url
      }), {
        status: 500,
        headers: { "Content-Type": "application/json" }
      });
    }
  }
};


