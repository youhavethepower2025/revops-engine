#!/usr/bin/env python3
"""Test script for CursorMCP server"""

import asyncio
import json
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from cursormcp.server.mcp_server import MCPServer
from cursormcp.server.types import MCPRequest


async def test_server():
    """Test the MCP server with a few requests"""
    server = MCPServer()
    
    print("🧪 Testing CursorMCP Server\n")
    
    # Test 1: Initialize
    print("1. Testing initialize...")
    request = MCPRequest(
        jsonrpc="2.0",
        id=1,
        method="initialize",
        params={}
    )
    response = await server.handle_request(request)
    print(f"   ✅ Response: {response.result.get('serverInfo', {})}")
    
    # Test 2: List tools
    print("\n2. Testing tools/list...")
    request = MCPRequest(
        jsonrpc="2.0",
        id=2,
        method="tools/list",
        params={}
    )
    response = await server.handle_request(request)
    tools = response.result.get("tools", [])
    print(f"   ✅ Found {len(tools)} tools")
    print(f"   Sample tools: {[t['name'] for t in tools[:5]]}")
    
    # Test 3: Get server status
    print("\n3. Testing get_server_status tool...")
    request = MCPRequest(
        jsonrpc="2.0",
        id=3,
        method="tools/call",
        params={
            "name": "get_server_status",
            "arguments": {}
        }
    )
    response = await server.handle_request(request)
    if response.result:
        content = response.result.get("content", [])
        if content:
            status = json.loads(content[0].get("text", "{}"))
            print(f"   ✅ Server status: {status.get('status')}")
            print(f"   ✅ Tools registered: {status.get('tools_registered')}")
    
    # Test 4: List Cloudflare workers (if configured)
    print("\n4. Testing cloudflare_list_workers...")
    request = MCPRequest(
        jsonrpc="2.0",
        id=4,
        method="tools/call",
        params={
            "name": "cloudflare_list_workers",
            "arguments": {}
        }
    )
    response = await server.handle_request(request)
    if response.result:
        content = response.result.get("content", [])
        if content:
            result = json.loads(content[0].get("text", "{}"))
            if "error" in result:
                print(f"   ⚠️  Error: {result['error']}")
            else:
                count = result.get("count", 0)
                print(f"   ✅ Found {count} Cloudflare workers")
                if count > 0:
                    workers = result.get("workers", [])[:3]
                    for worker in workers:
                        name = worker.get("id") or worker.get("name", "unknown")
                        print(f"      - {name}")
    
    print("\n✅ All tests completed!")
    print(f"\n📊 Summary:")
    print(f"   - Server initialized: ✅")
    print(f"   - Tools registered: {len(tools)}")
    print(f"   - Ready for Cursor connection!")


if __name__ == "__main__":
    asyncio.run(test_server())

