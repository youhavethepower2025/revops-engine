#!/bin/bash
# Quick test script for Dockerized CursorMCP

set -e

echo "🧪 Testing CursorMCP Docker Container"
echo ""

# Test 1: Initialize
echo "1. Testing initialize..."
echo '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{}}' | \
docker-compose run --rm \
  -e CLOUDFLARE_API_TOKEN=gWbANxar1WFWh-GTi2IhtcdUBmmw2Cb47KIz9Q1n \
  -e CLOUDFLARE_ACCOUNT_ID=bbd9ec5819a97651cc9f481c1c275c3d \
  cursormcp 2>&1 | grep -E '(serverInfo|error)' | head -3

echo ""
echo "2. Testing tools/list..."
echo '{"jsonrpc":"2.0","id":2,"method":"tools/list","params":{}}' | \
docker-compose run --rm \
  -e CLOUDFLARE_API_TOKEN=gWbANxar1WFWh-GTi2IhtcdUBmmw2Cb47KIz9Q1n \
  -e CLOUDFLARE_ACCOUNT_ID=bbd9ec5819a97651cc9f481c1c275c3d \
  cursormcp 2>&1 | python3 -c "
import sys, json
for line in sys.stdin:
    if line.strip().startswith('{'):
        try:
            data = json.loads(line)
            if 'result' in data and 'tools' in data['result']:
                tools = data['result']['tools']
                print(f'   ✅ Found {len(tools)} tools')
                print(f'   Sample: {[t[\"name\"] for t in tools[:5]]}')
                break
        except:
            pass
"

echo ""
echo "3. Testing cloudflare_list_workers..."
echo '{"jsonrpc":"2.0","id":3,"method":"tools/call","params":{"name":"cloudflare_list_workers","arguments":{}}}' | \
docker-compose run --rm \
  -e CLOUDFLARE_API_TOKEN=gWbANxar1WFWh-GTi2IhtcdUBmmw2Cb47KIz9Q1n \
  -e CLOUDFLARE_ACCOUNT_ID=bbd9ec5819a97651cc9f481c1c275c3d \
  cursormcp 2>&1 | python3 -c "
import sys, json
for line in sys.stdin:
    if line.strip().startswith('{'):
        try:
            data = json.loads(line)
            if 'result' in data and 'content' in data['result']:
                content = data['result']['content'][0]['text']
                result = json.loads(content)
                if 'error' in result:
                    print(f'   ⚠️  {result[\"error\"]}')
                else:
                    count = result.get('count', 0)
                    print(f'   ✅ Found {count} Cloudflare workers')
                    if count > 0:
                        workers = result.get('workers', [])[:3]
                        for w in workers:
                            name = w.get('id') or w.get('name', 'unknown')
                            print(f'      - {name}')
                break
        except Exception as e:
            pass
"

echo ""
echo "✅ Docker tests completed!"
echo ""
echo "📋 Next: Add to Cursor MCP config (see CURSOR_SETUP.md)"

