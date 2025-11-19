#!/usr/bin/env python3
"""
Configure Retell AI with Twilio SIP and AI Jesus Bro settings
Run this after confirming Twilio credentials
"""

import httpx
import asyncio
import json
from typing import List, Dict

# Retell Configuration
RETELL_API_KEY = "key_819a6edef632ded41fe1c1ef7f12"
RETELL_BASE_URL = "https://api.retellai.com"

# FUCK YES WE GOT THE REAL CREDS!
TWILIO_ACCOUNT_SID = "ACd7564cf277675642888a72f63d1655a3"
TWILIO_API_KEY = "SK451b658e7397ec5ad179ae1686ab5caf"
TWILIO_API_SECRET = "Z2lG0aDvABPaX7jE4eZ1xdvYU0tpQaOA"

# AI Jesus Bro Brain Webhook
BRAIN_WEBHOOK_URL = "http://localhost:8081/webhooks/retell"  # Will update to production later

class RetellConfigurator:
    def __init__(self):
        self.headers = {
            "Authorization": f"Bearer {RETELL_API_KEY}",
            "Content-Type": "application/json"
        }

    async def create_agent(self):
        """Create AI Jesus Bro agent"""
        print("🤖 Creating AI Jesus Bro Agent...")

        # Let's use the simpler v1 API endpoint
        agent_config = {
            "agent_name": "AI Jesus Bro Assistant",
            "voice_id": "11labs-Adam",  # Using a standard voice
            "prompt": "You are the AI assistant for AI Jesus Bro, a cutting-edge AI consultancy. Professionally handle calls, gather information about AI needs, and qualify leads for our services including custom AI development, automation, consulting, and voice AI systems.",
            "webhook_url": BRAIN_WEBHOOK_URL
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{RETELL_BASE_URL}/create-agent",
                headers=self.headers,
                json=agent_config
            )

            if response.status_code == 200:
                agent = response.json()
                print(f"✅ Agent created: {agent['agent_id']}")
                return agent['agent_id']
            else:
                print(f"❌ Failed to create agent: {response.text}")
                return None

    async def configure_twilio_sip(self):
        """Configure Twilio as SIP provider"""
        print("📞 Configuring Twilio SIP...")

        sip_config = {
            "provider": "twilio",
            "account_sid": TWILIO_ACCOUNT_SID,
            "api_key": TWILIO_API_KEY,
            "api_secret": TWILIO_API_SECRET,
            "webhook_url": BRAIN_WEBHOOK_URL
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{RETELL_BASE_URL}/configure-sip",
                headers=self.headers,
                json=sip_config
            )

            if response.status_code == 200:
                print("✅ Twilio SIP configured")
                return True
            else:
                print(f"❌ Failed to configure SIP: {response.text}")
                return False

    async def import_phone_numbers(self, agent_id: str):
        """Import all AI Jesus Bro phone numbers"""
        print("📱 Importing phone numbers...")

        phone_numbers = [
            "+13239685736",  # Primary - now free from Vapi!
            "+17027109167",
            "+17027186386",
            "+17027104257",
            "+17027124212",
            "+17027104174",
            "+18669658975"
        ]

        async with httpx.AsyncClient() as client:
            for number in phone_numbers:
                print(f"  Importing {number}...")

                number_config = {
                    "phone_number": number,
                    "provider": "twilio",
                    "agent_id": agent_id,
                    "nickname": f"AIJesusBro-{number[-4:]}"
                }

                response = await client.post(
                    f"{RETELL_BASE_URL}/register-phone-number",
                    headers=self.headers,
                    json=number_config
                )

                if response.status_code == 200:
                    print(f"  ✅ {number} imported")
                else:
                    print(f"  ⚠️  {number} failed: {response.text}")

        print("✅ Phone number import complete")

    async def update_twilio_webhooks(self, agent_id: str):
        """Update Twilio to point to Retell"""
        print("🔄 Updating Twilio webhooks...")

        # Get Retell's Twilio webhook URL
        retell_webhook = f"https://api.retell.ai/twilio-voice-webhook/{agent_id}"

        print(f"Webhook URL for Twilio: {retell_webhook}")
        print("\n📋 MANUAL STEP NEEDED:")
        print("Go to Twilio console and update voice webhook for each number to:")
        print(f"  {retell_webhook}")
        print("\nOr wait for Digital Ocean deployment for production URL")

    async def test_configuration(self):
        """Test the configuration"""
        print("\n🧪 Testing configuration...")

        async with httpx.AsyncClient() as client:
            # Test agent list
            response = await client.get(
                f"{RETELL_BASE_URL}/list-agents",
                headers=self.headers
            )

            if response.status_code == 200:
                agents = response.json()
                print(f"✅ Found {len(agents)} agents")
                for agent in agents:
                    print(f"  - {agent['agent_name']} ({agent['agent_id']})")

            # Test phone numbers
            response = await client.get(
                f"{RETELL_BASE_URL}/list-phone-numbers",
                headers=self.headers
            )

            if response.status_code == 200:
                numbers = response.json()
                print(f"✅ Found {len(numbers)} phone numbers")
                for number in numbers:
                    print(f"  - {number['phone_number']}")

async def main():
    print("🚀 AI JESUS BRO - RETELL CONFIGURATION")
    print("="*50)

    print("✅ Using Twilio API Key authentication")
    print(f"   Account: {TWILIO_ACCOUNT_SID}")
    print(f"   API Key: {TWILIO_API_KEY}")

    configurator = RetellConfigurator()

    # Step 1: Create agent
    agent_id = await configurator.create_agent()
    if not agent_id:
        print("Failed to create agent. Check API key.")
        return

    # Step 2: Configure Twilio SIP
    if not await configurator.configure_twilio_sip():
        print("Failed to configure SIP. Check Twilio credentials.")
        return

    # Step 3: Import phone numbers
    await configurator.import_phone_numbers(agent_id)

    # Step 4: Update webhooks
    await configurator.update_twilio_webhooks(agent_id)

    # Step 5: Test
    await configurator.test_configuration()

    print("\n✅ CONFIGURATION COMPLETE!")
    print(f"Agent ID: {agent_id}")
    print("\nNext steps:")
    print("1. Update Twilio webhook URLs in console")
    print("2. Deploy brain to Digital Ocean")
    print("3. Update BRAIN_WEBHOOK_URL to production")

if __name__ == "__main__":
    asyncio.run(main())