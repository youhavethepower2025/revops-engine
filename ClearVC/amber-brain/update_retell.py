#!/usr/bin/env python3
"""
Update Retell agent to use single webhook URL
"""

import requests
import os
from dotenv import load_dotenv

# Load environment from MCP credentials
load_dotenv("/Users/aijesusbro/AI Projects/mcp_credentials.env")

RETELL_API_KEY = os.getenv("RETELL_API_KEY")
RETELL_BASE_URL = "https://api.retell.ai/v1"

# The ONE webhook URL
WEBHOOK_URL = "https://clearvc.aijesusbro.com/webhook"

def update_clearvc_agent():
    """Update ClearVC agent with single webhook"""

    headers = {
        "Authorization": f"Bearer {RETELL_API_KEY}",
        "Content-Type": "application/json"
    }

    # First, list agents to find ClearVC
    response = requests.get(f"{RETELL_BASE_URL}/agents", headers=headers)

    if response.status_code == 200:
        agents = response.json()

        for agent in agents:
            if "clearvc" in agent.get("name", "").lower() or "amber" in agent.get("name", "").lower():
                agent_id = agent["agent_id"]
                print(f"Found ClearVC agent: {agent_id}")

                # Update with single webhook
                update_data = {
                    "webhook_url": WEBHOOK_URL,
                    "call_end_webhook_url": WEBHOOK_URL,
                    "transcript_webhook_url": WEBHOOK_URL,
                    "function_call_webhook_url": WEBHOOK_URL
                }

                update_response = requests.patch(
                    f"{RETELL_BASE_URL}/agents/{agent_id}",
                    headers=headers,
                    json=update_data
                )

                if update_response.status_code == 200:
                    print(f"✅ Updated agent {agent_id} to use single webhook: {WEBHOOK_URL}")
                    return True
                else:
                    print(f"Failed to update: {update_response.text}")

    return False

if __name__ == "__main__":
    update_clearvc_agent()