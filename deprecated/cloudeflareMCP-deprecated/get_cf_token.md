# Generate Fresh Cloudflare API Token

The key in keys.txt appears to be expired or wrong format.

**Quick Fix (30 seconds):**

1. Page opening now: https://dash.cloudflare.com/profile/api-tokens
2. Click "Create Token"
3. Use template: "Edit Cloudflare Workers"
4. Click "Continue to summary"
5. Click "Create Token"
6. Copy the token
7. Run:

```bash
export CF_TOKEN="your_new_token_here"

curl -X PUT "https://api.cloudflare.com/client/v4/accounts/bbd9ec5819a97651cc9f481c1c275c3d/workers/subdomain" \
  -H "Authorization: Bearer $CF_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"subdomain": "aijesusbro-brain"}'
```

Then back to me with the token and I'll finish deployment.
