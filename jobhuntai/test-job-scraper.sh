#!/bin/bash

# Test the new job scraping agent

API_BASE="https://revops-os-dev.aijesusbro-brain.workers.dev/api"
ACCOUNT_ID="account_john_kruze"

echo "🧪 TESTING JOB SCRAPER"
echo "====================="
echo ""

# Test company: Anthropic (we know they have open roles)
TEST_COMPANY="Anthropic"
TEST_DOMAIN="anthropic.com"

echo "1️⃣  Creating test organization: $TEST_COMPANY"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

ORG_RESPONSE=$(curl -s -X POST "$API_BASE/organizations" \
  -H "Content-Type: application/json" \
  -H "X-Account-Id: $ACCOUNT_ID" \
  -d "{
    \"name\": \"$TEST_COMPANY\",
    \"domain\": \"$TEST_DOMAIN\",
    \"industry\": \"Artificial Intelligence\",
    \"priority\": 1
  }")

echo "$ORG_RESPONSE" | jq '.'

ORG_ID=$(echo "$ORG_RESPONSE" | jq -r '.organization.id // .org_id // empty')

if [ -z "$ORG_ID" ]; then
  # Try getting existing org
  ORG_ID=$(curl -s -X GET "$API_BASE/organizations" \
    -H "X-Account-Id: $ACCOUNT_ID" | jq -r ".organizations[] | select(.domain == \"$TEST_DOMAIN\") | .id" | head -1)
fi

if [ -z "$ORG_ID" ]; then
  echo "❌ Failed to create/find organization"
  exit 1
fi

echo ""
echo "✅ Organization ID: $ORG_ID"
echo ""
echo "2️⃣  Scraping jobs from careers page..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

SCRAPE_RESPONSE=$(curl -s -X POST "$API_BASE/organizations/$ORG_ID/scrape-jobs" \
  -H "Content-Type: application/json" \
  -H "X-Account-Id: $ACCOUNT_ID")

echo "$SCRAPE_RESPONSE" | jq '.'

SUCCESS=$(echo "$SCRAPE_RESPONSE" | jq -r '.success')
ROLES_CREATED=$(echo "$SCRAPE_RESPONSE" | jq -r '.roles_created // 0')

echo ""
if [ "$SUCCESS" = "true" ]; then
  echo "✅ Scraping complete!"
  echo "   📊 Roles created: $ROLES_CREATED"
  echo ""
  echo "3️⃣  Fetching created roles..."
  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
  echo ""

  ROLES=$(curl -s -X GET "$API_BASE/roles?org_id=$ORG_ID" \
    -H "X-Account-Id: $ACCOUNT_ID")

  echo "$ROLES" | jq '.roles[] | {
    title: .role_title,
    has_description: (.description != null),
    has_requirements: ((.requirements | fromjson | length) > 0),
    has_specific_url: (.job_url != null and (.job_url | contains("/careers") | not))
  }'

  echo ""
  echo "🎯 RESULTS:"
  echo "   - Check if roles have descriptions (has_description: true)"
  echo "   - Check if requirements were extracted (has_requirements: true)"
  echo "   - Check if specific URLs found (has_specific_url: true)"
else
  echo "❌ Scraping failed:"
  echo "$SCRAPE_RESPONSE" | jq -r '.error'
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Test complete!"
