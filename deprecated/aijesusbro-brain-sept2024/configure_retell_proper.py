#!/usr/bin/env python3
"""
Configure Retell AI properly using the actual API documentation
Based on retellapi.md from the knowledge base
"""

import httpx
import asyncio
import json
from typing import Dict, Any

# Retell Configuration
RETELL_API_KEY = "key_819a6edef632ded41fe1c1ef7f12"
RETELL_BASE_URL = "https://api.retellai.com"

# Twilio Configuration (WORKING!)
TWILIO_ACCOUNT_SID = "ACd7564cf277675642888a72f63d1655a3"
TWILIO_API_KEY = "SK451b658e7397ec5ad179ae1686ab5caf"
TWILIO_API_SECRET = "Z2lG0aDvABPaX7jE4eZ1xdvYU0tpQaOA"

# Brain webhook
BRAIN_WEBHOOK_URL = "http://localhost:8081/webhooks/retell"

class RetellConfigurator:
    def __init__(self):
        self.headers = {
            "Authorization": f"Bearer {RETELL_API_KEY}",
            "Content-Type": "application/json"
        }

    async def create_retell_llm(self):
        """Create Retell LLM configuration first"""
        print("🧠 Creating Retell LLM configuration...")

        llm_config = {
            "general_prompt": """You are the AI assistant for AI Jesus Bro, a cutting-edge AI consultancy and development company specializing in organizational intelligence and voice AI systems.

Your role is to:
1. Professionally handle all incoming calls with expertise and warmth
2. Gather detailed information about the caller's AI needs and current challenges
3. Qualify leads for our premium services: custom AI development, business automation, AI consulting, voice AI systems, and organizational intelligence platforms
4. Schedule follow-up calls or meetings when appropriate
5. Demonstrate deep knowledge about AI, machine learning, automation, and digital transformation

Always maintain a professional yet approachable tone. You represent innovation and expertise.

Key services we offer:
- Custom AI Development: Building tailored AI solutions for specific business needs
- Business Automation: Streamlining operations with intelligent systems
- AI Consulting: Strategic guidance for AI adoption and implementation
- Voice AI Systems: Advanced conversational AI like this very system you're part of
- Organizational Intelligence Platforms: Building "brains" for companies that remember everything and act autonomously

If asked about pricing, mention that we provide custom quotes based on specific needs and that our solutions typically deliver 10x ROI.

Remember: You are not just an answering service. You are the first impression of a company that builds the future.""",
            "begin_message": "Hello, you've reached AI Jesus Bro, where we transform businesses with cutting-edge AI. How can I help revolutionize your operations today?",
            "inbound_dynamic_variables_webhook_url": BRAIN_WEBHOOK_URL
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{RETELL_BASE_URL}/create-retell-llm",
                headers=self.headers,
                json=llm_config
            )

            if response.status_code in [200, 201]:
                llm = response.json()
                print(f"✅ LLM created: {llm.get('llm_id')}")
                return llm.get('llm_id')
            else:
                print(f"❌ Failed to create LLM: {response.status_code}")
                print(f"Response: {response.text}")
                return None

    async def create_agent(self, llm_id: str):
        """Create AI Jesus Bro agent with proper configuration"""
        print("🤖 Creating AI Jesus Bro Agent...")

        agent_config = {
            "agent_name": "AI Jesus Bro Assistant",
            "response_engine": {
                "type": "retell-llm",
                "llm_id": llm_id
            },
            "voice_id": "11labs-Adrian",  # Professional male voice
            "language": "en-US",
            "webhook_url": BRAIN_WEBHOOK_URL,
            "interruption_sensitivity": 0.8,
            "backchannel_frequency": 0.9,
            "backchannel_words": ["yeah", "uh-huh", "I see", "got it"],
            "reminder_trigger_ms": 10000,
            "reminder_max_count": 3,
            "responsiveness": 0.8,
            "voice_temperature": 0.7,
            "voice_speed": 1.0,
            "enable_voicemail_detection": True,
            "voicemail_message": "Hi, this is AI Jesus Bro calling. We noticed your interest in AI solutions. Please give us a call back at your convenience.",
            "end_call_after_silence_ms": 600000,  # 10 minutes
            "max_call_duration_ms": 3600000,  # 1 hour
            "ambient_sound": "call-center",
            "pronunciation_dictionary": [
                {"word": "AI", "phoneme": "eɪ aɪ", "alphabet": "ipa"},
                {"word": "GHL", "phoneme": "dʒi eɪtʃ el", "alphabet": "ipa"},
                {"word": "MCP", "phoneme": "em si pi", "alphabet": "ipa"}
            ],
            "boosted_keywords": ["AI Jesus Bro", "organizational intelligence", "voice AI"]
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{RETELL_BASE_URL}/create-agent",
                headers=self.headers,
                json=agent_config
            )

            if response.status_code in [200, 201]:
                agent = response.json()
                print(f"✅ Agent created: {agent.get('agent_id')}")
                return agent.get('agent_id')
            else:
                print(f"❌ Failed to create agent: {response.status_code}")
                print(f"Response: {response.text}")
                return None

    async def import_phone_numbers(self, agent_id: str):
        """Import Twilio phone numbers to Retell"""
        print("📱 Importing phone numbers...")

        phone_numbers = [
            "+13239685736",  # Primary - FREE FROM VAPI!
            "+17027109167",
            "+17027186386",
            "+17027104257",
            "+17027124212",
            "+17027104174",
            "+18669658975",
            "+17255021112"
        ]

        results = []
        async with httpx.AsyncClient() as client:
            for number in phone_numbers:
                print(f"  Importing {number}...")

                number_config = {
                    "phone_number": number,
                    "provider": "twilio",
                    "twilio_account_sid": TWILIO_ACCOUNT_SID,
                    "twilio_auth_token": f"{TWILIO_API_KEY}:{TWILIO_API_SECRET}",  # Using API key format
                    "inbound_agent_id": agent_id,
                    "outbound_agent_id": agent_id
                }

                response = await client.post(
                    f"{RETELL_BASE_URL}/import-phone-number",
                    headers=self.headers,
                    json=number_config
                )

                if response.status_code in [200, 201]:
                    print(f"  ✅ {number} imported")
                    results.append({"number": number, "status": "success"})
                else:
                    print(f"  ⚠️  {number} failed: {response.text}")
                    results.append({"number": number, "status": "failed", "error": response.text})

        return results

    async def update_twilio_webhooks(self, agent_id: str):
        """Update Twilio webhooks to point to Retell"""
        print("🔄 Updating Twilio webhooks...")

        import requests
        from requests.auth import HTTPBasicAuth

        auth = HTTPBasicAuth(TWILIO_API_KEY, TWILIO_API_SECRET)

        # Get Retell webhook URL for this agent
        retell_webhook = f"https://api.retellai.com/twilio-voice-webhook/{agent_id}"
        print(f"  Retell webhook: {retell_webhook}")

        # Get all phone numbers
        numbers_url = f"https://api.twilio.com/2010-04-01/Accounts/{TWILIO_ACCOUNT_SID}/IncomingPhoneNumbers.json"
        response = requests.get(numbers_url, auth=auth)

        if response.status_code == 200:
            numbers = response.json()['incoming_phone_numbers']

            for number in numbers:
                phone = number['phone_number']
                sid = number['sid']

                print(f"  Updating {phone}...")

                update_url = f"https://api.twilio.com/2010-04-01/Accounts/{TWILIO_ACCOUNT_SID}/IncomingPhoneNumbers/{sid}.json"
                update_data = {
                    'VoiceUrl': retell_webhook,
                    'VoiceMethod': 'POST',
                    'StatusCallback': BRAIN_WEBHOOK_URL + "/twilio-status",
                    'StatusCallbackMethod': 'POST'
                }

                update_response = requests.post(update_url, auth=auth, data=update_data)

                if update_response.status_code == 200:
                    print(f"    ✅ Updated to Retell webhook")
                else:
                    print(f"    ❌ Failed: {update_response.text}")

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
                for agent in agents[:5]:  # Show first 5
                    print(f"  - {agent.get('agent_name', 'Unnamed')} ({agent.get('agent_id')})")

            # Test phone numbers
            response = await client.get(
                f"{RETELL_BASE_URL}/list-phone-numbers",
                headers=self.headers
            )

            if response.status_code == 200:
                numbers = response.json()
                print(f"✅ Found {len(numbers)} phone numbers configured")
                for number in numbers[:10]:  # Show first 10
                    print(f"  - {number.get('phone_number')}")

async def main():
    print("🚀 AI JESUS BRO - PROPER RETELL CONFIGURATION")
    print("="*50)
    print("Using Twilio API Key authentication")
    print(f"Account: {TWILIO_ACCOUNT_SID}")
    print(f"API Key: {TWILIO_API_KEY}")
    print("")

    configurator = RetellConfigurator()

    # Step 1: Create LLM configuration
    llm_id = await configurator.create_retell_llm()
    if not llm_id:
        print("Failed to create LLM. Check API key and try again.")
        return

    # Step 2: Create agent with LLM
    agent_id = await configurator.create_agent(llm_id)
    if not agent_id:
        print("Failed to create agent.")
        return

    # Step 3: Import phone numbers
    results = await configurator.import_phone_numbers(agent_id)
    successful = [r for r in results if r['status'] == 'success']
    print(f"Successfully imported {len(successful)} numbers")

    # Step 4: Update Twilio webhooks
    await configurator.update_twilio_webhooks(agent_id)

    # Step 5: Test configuration
    await configurator.test_configuration()

    print("\n✅ CONFIGURATION COMPLETE!")
    print(f"Agent ID: {agent_id}")
    print(f"LLM ID: {llm_id}")
    print("\nYour AI Jesus Bro voice system is ready!")
    print("Test by calling any of your numbers.")
    print("\nNext steps:")
    print("1. Deploy brain to Digital Ocean for production")
    print("2. Update BRAIN_WEBHOOK_URL to production URL")
    print("3. Monitor calls in Retell dashboard")

if __name__ == "__main__":
    asyncio.run(main())