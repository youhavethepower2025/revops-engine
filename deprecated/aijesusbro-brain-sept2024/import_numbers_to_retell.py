#!/usr/bin/env python3
"""
Import Twilio numbers to Retell with proper termination URI
"""

import httpx
import asyncio
import json

# Retell Configuration
RETELL_API_KEY = "key_819a6edef632ded41fe1c1ef7f12"
RETELL_BASE_URL = "https://api.retellai.com"
AGENT_ID = "agent_98681d3ba9a92b678106df24e4"

# Twilio Configuration
TWILIO_ACCOUNT_SID = "ACd7564cf277675642888a72f63d1655a3"
TWILIO_API_KEY = "SK451b658e7397ec5ad179ae1686ab5caf"
TWILIO_API_SECRET = "Z2lG0aDvABPaX7jE4eZ1xdvYU0tpQaOA"
TERMINATION_URI = "sip:aijesusbro-retell-55a3.sip.twilio.com"

async def import_numbers():
    """Import all phone numbers to Retell"""
    print("📱 IMPORTING PHONE NUMBERS TO RETELL")
    print("="*50)

    headers = {
        "Authorization": f"Bearer {RETELL_API_KEY}",
        "Content-Type": "application/json"
    }

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

    async with httpx.AsyncClient() as client:
        for number in phone_numbers:
            print(f"\nImporting {number}...")

            # Proper import configuration with termination URI
            number_config = {
                "phone_number": number,
                "provider": "twilio",
                "twilio_account_sid": TWILIO_ACCOUNT_SID,
                "twilio_auth_token": f"{TWILIO_API_KEY}:{TWILIO_API_SECRET}",
                "termination_uri": TERMINATION_URI,  # Required field!
                "inbound_agent_id": AGENT_ID,
                "outbound_agent_id": AGENT_ID,
                "label": f"AIJesusBro-{number[-4:]}"
            }

            try:
                response = await client.post(
                    f"{RETELL_BASE_URL}/import-phone-number",
                    headers=headers,
                    json=number_config
                )

                if response.status_code in [200, 201]:
                    result = response.json()
                    print(f"  ✅ Success!")
                    print(f"     Phone Number ID: {result.get('phone_number_id')}")
                    print(f"     Status: Active")
                else:
                    print(f"  ❌ Failed: {response.status_code}")
                    print(f"     Error: {response.text}")

                    # If already exists, try to update instead
                    if "already" in response.text.lower():
                        print(f"  ⚠️ Number may already be imported. Checking...")

                        # List existing numbers
                        list_response = await client.get(
                            f"{RETELL_BASE_URL}/list-phone-numbers",
                            headers=headers
                        )

                        if list_response.status_code == 200:
                            existing_numbers = list_response.json()
                            for existing in existing_numbers:
                                if existing.get('phone_number') == number:
                                    print(f"  ✅ Number already configured!")
                                    print(f"     Phone Number ID: {existing.get('phone_number_id')}")
                                    break

            except Exception as e:
                print(f"  ❌ Error: {e}")

        # Final check - list all configured numbers
        print("\n" + "="*50)
        print("📋 FINAL STATUS CHECK")
        print("="*50)

        list_response = await client.get(
            f"{RETELL_BASE_URL}/list-phone-numbers",
            headers=headers
        )

        if list_response.status_code == 200:
            configured_numbers = list_response.json()
            print(f"\n✅ Total numbers in Retell: {len(configured_numbers)}")

            ai_jesus_numbers = []
            for num in configured_numbers:
                phone = num.get('phone_number')
                if phone in phone_numbers:
                    ai_jesus_numbers.append(phone)
                    print(f"  ✅ {phone} - CONFIGURED")
                    print(f"     Agent: {num.get('inbound_agent_id', 'None')}")

            print(f"\n🎉 AI JESUS BRO NUMBERS READY: {len(ai_jesus_numbers)}/{len(phone_numbers)}")

            if len(ai_jesus_numbers) < len(phone_numbers):
                print("\n⚠️ Some numbers may need manual configuration in Retell dashboard")
                print("Go to: dashboard.retellai.com → Phone Numbers")
        else:
            print(f"❌ Could not list numbers: {list_response.text}")

async def test_agent():
    """Test that the agent is properly configured"""
    print("\n🧪 TESTING AGENT CONFIGURATION")
    print("="*50)

    headers = {
        "Authorization": f"Bearer {RETELL_API_KEY}",
        "Content-Type": "application/json"
    }

    async with httpx.AsyncClient() as client:
        # Get agent details
        response = await client.get(
            f"{RETELL_BASE_URL}/get-agent/{AGENT_ID}",
            headers=headers
        )

        if response.status_code == 200:
            agent = response.json()
            print(f"✅ Agent Active: {agent.get('agent_name')}")
            print(f"   Voice: {agent.get('voice_id')}")
            print(f"   Language: {agent.get('language')}")
            print(f"   Webhook: {agent.get('webhook_url')}")
        else:
            print(f"❌ Could not get agent: {response.text}")

async def main():
    await import_numbers()
    await test_agent()

    print("\n" + "="*50)
    print("🚀 CONFIGURATION COMPLETE!")
    print("="*50)
    print("\n✅ Your AI Jesus Bro voice system is configured!")
    print(f"   Agent ID: {AGENT_ID}")
    print(f"   Trunk: {TERMINATION_URI}")
    print("\n📞 TEST YOUR SYSTEM:")
    print("   Call any of your numbers to test the AI agent")
    print("   Monitor calls at: dashboard.retellai.com")
    print("\n🧠 NEXT STEPS:")
    print("   1. Deploy brain to Digital Ocean for production")
    print("   2. Update webhook URLs to production endpoints")
    print("   3. Configure GHL integrations")

if __name__ == "__main__":
    asyncio.run(main())