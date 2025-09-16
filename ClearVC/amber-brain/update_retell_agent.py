#!/usr/bin/env python3
"""
Update Retell Agent Webhook URLs
This will update the ClearVC agent to point to their Railway deployment
"""

import requests
import os
from dotenv import load_dotenv

load_dotenv()

# Retell API configuration
RETELL_API_KEY = os.getenv("RETELL_API_KEY")
RETELL_BASE_URL = "https://api.retell.ai/v1"

# ClearVC Agent configuration
CLEARVC_AGENT_ID = "clearvc_amber"  # Replace with actual agent ID
RAILWAY_URL = "https://clearvc-amber-brain.up.railway.app"  # Replace with actual Railway URL

def update_agent_webhooks(agent_id: str, base_url: str):
    """
    Update Retell agent webhook URLs
    """
    headers = {
        "Authorization": f"Bearer {RETELL_API_KEY}",
        "Content-Type": "application/json"
    }

    # Webhook configuration
    webhook_config = {
        "webhook_url": f"{base_url}/webhooks/retell/call-started",
        "call_end_webhook_url": f"{base_url}/webhooks/retell/call-ended",
        "transcript_webhook_url": f"{base_url}/webhooks/retell/transcript-update",
        "function_call_webhook_url": f"{base_url}/webhooks/retell/tool-call",
    }

    # Update agent
    response = requests.patch(
        f"{RETELL_BASE_URL}/agents/{agent_id}",
        headers=headers,
        json=webhook_config
    )

    if response.status_code == 200:
        print(f"✅ Successfully updated agent {agent_id}")
        print(f"   Webhooks now point to: {base_url}")
        return True
    else:
        print(f"❌ Failed to update agent: {response.status_code}")
        print(f"   Response: {response.text}")
        return False

def list_agents():
    """
    List all Retell agents to find the right one
    """
    headers = {
        "Authorization": f"Bearer {RETELL_API_KEY}"
    }

    response = requests.get(
        f"{RETELL_BASE_URL}/agents",
        headers=headers
    )

    if response.status_code == 200:
        agents = response.json()
        print("\n📋 Available Retell Agents:")
        print("-" * 50)
        for agent in agents:
            print(f"ID: {agent.get('agent_id')}")
            print(f"Name: {agent.get('name')}")
            print(f"Current Webhook: {agent.get('webhook_url', 'Not set')}")
            print("-" * 50)
        return agents
    else:
        print(f"Failed to list agents: {response.text}")
        return []

def main():
    print("🚀 Retell Agent Webhook Updater")
    print("=" * 50)

    if not RETELL_API_KEY:
        print("❌ RETELL_API_KEY not found in environment")
        print("   Please set it in .env file")
        return

    # First, list all agents
    agents = list_agents()

    if not agents:
        print("No agents found or API error")
        return

    # Ask user to confirm agent ID
    print("\n" + "=" * 50)
    agent_id = input("Enter the agent ID for ClearVC (or press Enter to skip): ").strip()

    if not agent_id:
        print("Skipped - no agent ID provided")
        return

    # Ask for Railway URL
    railway_url = input(f"Enter Railway URL (or press Enter for default: {RAILWAY_URL}): ").strip()
    if not railway_url:
        railway_url = RAILWAY_URL

    # Confirm before updating
    print("\n" + "=" * 50)
    print(f"Will update agent: {agent_id}")
    print(f"With base URL: {railway_url}")
    print("\nWebhooks will be:")
    print(f"  - Call Start: {railway_url}/webhooks/retell/call-started")
    print(f"  - Call End: {railway_url}/webhooks/retell/call-ended")
    print(f"  - Transcript: {railway_url}/webhooks/retell/transcript-update")
    print(f"  - Tool Call: {railway_url}/webhooks/retell/tool-call")
    print("=" * 50)

    confirm = input("\nProceed? (y/n): ").strip().lower()
    if confirm == 'y':
        update_agent_webhooks(agent_id, railway_url)
    else:
        print("Cancelled")

if __name__ == "__main__":
    main()