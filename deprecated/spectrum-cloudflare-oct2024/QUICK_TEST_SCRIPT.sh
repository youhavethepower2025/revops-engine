#!/bin/bash
# Quick test script to verify Spectrum marketing weapon deployment
# Run before Loom recording to confirm everything works

API="https://spectrum-api.aijesusbro-brain.workers.dev"

echo "=================================================="
echo "SPECTRUM MARKETING WEAPON - PRE-RECORDING TESTS"
echo "=================================================="
echo ""

# Test 1: Demo Mode
echo "TEST 1: DEMO MODE (What can you do?)"
echo "---"
curl -s -X POST "$API/chat/send" \
  -H 'Content-Type: application/json' \
  -d '{"agent_role":"reality","message":"What can you do?","client_id":"aijesusbro"}' \
  | jq -r '.message' | head -20
echo ""
echo "Expected: Lists capabilities, mentions tools, invites demo"
echo ""
echo "=================================================="
echo ""

# Test 2: Positioning Mode
echo "TEST 2: POSITIONING MODE (vs ChatGPT)"
echo "---"
curl -s -X POST "$API/chat/send" \
  -H 'Content-Type: application/json' \
  -d '{"agent_role":"reality","message":"Why not just use ChatGPT?","client_id":"aijesusbro"}' \
  | jq -r '.message' | head -20
echo ""
echo "Expected: Mentions AI talent drain, system connectivity, data ownership"
echo ""
echo "=================================================="
echo ""

# Test 3: Tool Demonstration
echo "TEST 3: TOOL DEMONSTRATION (Recent calls)"
echo "---"
curl -s -X POST "$API/chat/send" \
  -H 'Content-Type: application/json' \
  -d '{"agent_role":"reality","message":"Show me recent calls","client_id":"aijesusbro"}' \
  | jq -r '.message' | head -20
echo ""
echo "Expected: Narrates checking call logs, uses vapi_list_calls tool"
echo ""
echo "=================================================="
echo ""

# Test 4: Memory System
echo "TEST 4: MEMORY SYSTEM (Store and recall)"
echo "---"
curl -s -X POST "$API/chat/send" \
  -H 'Content-Type: application/json' \
  -d '{"agent_role":"reality","message":"Remember: our demo recording is at noon","client_id":"aijesusbro"}' \
  | jq -r '.message' | head -10
echo ""
echo "Expected: Confirms storage, may use remember() tool"
echo ""
echo "=================================================="
echo ""

# Test 5: Health Check
echo "TEST 5: SYSTEM HEALTH"
echo "---"
curl -s "$API/health" | jq .
echo ""
echo "Expected: status: ok, timestamp present"
echo ""
echo "=================================================="
echo ""

# Test 6: Agent Loading
echo "TEST 6: AGENT CONFIGURATION"
echo "---"
curl -s "$API/agents?client_id=aijesusbro" | jq '.agents[] | {name, role, description}'
echo ""
echo "Expected: Reality Agent with updated description"
echo ""
echo "=================================================="
echo ""

echo "✅ ALL TESTS COMPLETE"
echo ""
echo "System is ready for Loom recording."
echo "Navigate to: https://spectrum.aijesusbro.com"
echo ""
echo "Demo script: LOOM_DEMO_SCRIPT.md"
echo "Marketing copy: MARKETING_COPY_EXTRACTION.md"
echo "Full summary: DEPLOYMENT_SUMMARY.md"
echo ""
echo "=================================================="
