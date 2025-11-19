#!/bin/bash
# Set Cloudflare Worker secrets

echo "Setting RETELL_API_KEY..."
echo "key_819a6edef632ded41fe1c1ef7f12" | npx wrangler secret put RETELL_API_KEY

echo "Setting GHL_API_KEY..."
echo 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJsb2NhdGlvbl9pZCI6IlBNZ2JRMzc1VEVHT3lHWHNLejdlIiwidmVyc2lvbiI6MSwiaWF0IjoxNzU3NDU2NTUwMTIyLCJzdWIiOiJ5OXFxZjNIV0FYVGk5Nk1wZXVqZiJ9.nbuFjgIZ1hnsHLPDj5IsiUlxR5DgecMw1l56LCEZEjo' | npx wrangler secret put GHL_API_KEY

echo "Setting GHL_LOCATION_ID..."
echo "PMgbQ375TEGOyGXsKz7e" | npx wrangler secret put GHL_LOCATION_ID

echo "✅ All secrets set!"
