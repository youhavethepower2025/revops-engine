#!/bin/bash
# Use wrangler's authenticated session to set subdomain via API

ACCOUNT_ID="bbd9ec5819a97651cc9f481c1c275c3d"

# Generate a subdomain name (lowercase, alphanumeric, hyphens only)
SUBDOMAIN="aijesusbro-brain-$(date +%s | tail -c 6)"

echo "🔧 Setting workers.dev subdomain: ${SUBDOMAIN}.workers.dev"

# Use curl with wrangler's OAuth token
# We'll extract the token from wrangler's internal state
cd "/Users/aijesusbro/AI Projects/cloudeflareMCP"

# Create a temporary worker config to make an API call through wrangler
npx wrangler whoami 2>&1 | grep -q "logged in" && {
  echo "✓ Authenticated with Cloudflare"

  # Use wrangler's fetch command (it handles auth for us)
  # Create a temp JS file that makes the API call
  cat > /tmp/set_subdomain.js << 'EOF'
export default {
  async fetch(request, env) {
    const ACCOUNT_ID = "bbd9ec5819a97651cc9f481c1c275c3d";
    const SUBDOMAIN = "aijesusbro-brain";

    try {
      // First, check current settings
      const checkUrl = `https://api.cloudflare.com/client/v4/accounts/${ACCOUNT_ID}/workers/subdomain`;
      console.log("Checking subdomain:", checkUrl);

      const checkResp = await fetch(checkUrl, {
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${env.CF_API_TOKEN}`
        }
      });

      const checkData = await checkResp.json();
      console.log("Current subdomain:", JSON.stringify(checkData));

      if (checkData.result && checkData.result.subdomain) {
        return new Response(`Subdomain already set: ${checkData.result.subdomain}.workers.dev`);
      }

      // Set subdomain if not already set
      const setUrl = `https://api.cloudflare.com/client/v4/accounts/${ACCOUNT_ID}/workers/subdomain`;
      const setResp = await fetch(setUrl, {
        method: 'PUT',
        headers: {
          'Authorization': `Bearer ${env.CF_API_TOKEN}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ subdomain: SUBDOMAIN })
      });

      const setData = await setResp.json();
      return new Response(JSON.stringify(setData, null, 2));

    } catch (error) {
      return new Response(`Error: ${error.message}`);
    }
  }
}
EOF

  echo "Created API call worker, but need API token..."
  echo ""
  echo "Manual API call required:"
  echo ""
  echo "curl -X PUT 'https://api.cloudflare.com/client/v4/accounts/${ACCOUNT_ID}/workers/subdomain' \\"
  echo "  -H 'Authorization: Bearer YOUR_API_TOKEN' \\"
  echo "  -H 'Content-Type: application/json' \\"
  echo "  -d '{\"subdomain\": \"${SUBDOMAIN}\"}'"
  echo ""
  echo "OR: Visit dashboard once to auto-create subdomain"
}
