#!/usr/bin/env python3
"""
Update Retell agent with the single webhook URL
"""

import requests
import json

# Retell API configuration
RETELL_API_KEY = "key_a47c5e5797da167dc067f8096e80"  # From your MCP server
RETELL_BASE_URL = "https://api.retellai.com"

# The ONE webhook URL
WEBHOOK_URL = "https://clearvc.aijesusbro.com/webhook"

def list_agents():
    """List all Retell agents"""
    headers = {
        "Authorization": f"Bearer {RETELL_API_KEY}",
        "Content-Type": "application/json"
    }

    response = requests.get(
        f"{RETELL_BASE_URL}/agent",
        headers=headers
    )

    print(f"Status: {response.status_code}")

    if response.status_code == 200:
        agents = response.json()
        print(f"\nFound {len(agents)} agents:")
        for agent in agents:
            print(f"  - ID: {agent.get('agent_id')}")
            print(f"    Name: {agent.get('agent_name', 'Unnamed')}")
            print(f"    Current webhook: {agent.get('webhook_server_url', 'Not set')}")
        return agents
    else:
        print(f"Error: {response.text}")
        return []

def update_agent_webhook(agent_id: str):
    """Update specific agent with our webhook"""
    headers = {
        "Authorization": f"Bearer {RETELL_API_KEY}",
        "Content-Type": "application/json"
    }

    # Update with single webhook for all events
    update_data = {
        "webhook_server_url": WEBHOOK_URL,
        "end_call_after_silence_ms": 10000,
        "enable_transcription_formatting": True
    }

    response = requests.patch(
        f"{RETELL_BASE_URL}/agent/{agent_id}",
        headers=headers,
        json=update_data
    )

    if response.status_code == 200:
        print(f"\n✅ Updated agent {agent_id}")
        print(f"   Webhook set to: {WEBHOOK_URL}")
        return True
    else:
        print(f"\n❌ Failed to update agent {agent_id}")
        print(f"   Error: {response.text}")
        return False

def main():
    print("🔧 Updating Retell Agent Webhooks")
    print("==================================")
    print(f"Target webhook: {WEBHOOK_URL}")
    print("")

    # List all agents
    agents = list_agents()

    if not agents:
        print("No agents found or API error")
        return

    # Look for ClearVC/Amber agent
    clearvc_agent = None
    for agent in agents:
        name = agent.get('agent_name', '').lower()
        if 'clearvc' in name or 'amber' in name or 'clear' in name:
            clearvc_agent = agent
            break

    if clearvc_agent:
        print(f"\n🎯 Found ClearVC agent: {clearvc_agent.get('agent_name')}")
        agent_id = clearvc_agent.get('agent_id')

        # Update it
        if update_agent_webhook(agent_id):
            print("\n✅ SUCCESS! ClearVC agent now using intelligent webhook")
            print(f"   All events will go to: {WEBHOOK_URL}")
            print("\n🧠 Features now active:")
            print("   - Real GHL contact lookup")
            print("   - Intelligent caller categorization")
            print("   - Working tool implementations")
            print("   - Persistent conversation memory")
    else:
        print("\n⚠️  No ClearVC agent found. Available agents:")
        for i, agent in enumerate(agents):
            print(f"   {i+1}. {agent.get('agent_name', 'Unnamed')} ({agent.get('agent_id')})")

        choice = input("\nEnter number to update (or Enter to skip): ").strip()
        if choice and choice.isdigit():
            idx = int(choice) - 1
            if 0 <= idx < len(agents):
                agent_id = agents[idx].get('agent_id')
                update_agent_webhook(agent_id)

if __name__ == "__main__":
    main()