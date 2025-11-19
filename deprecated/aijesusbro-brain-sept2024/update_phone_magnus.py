#!/usr/bin/env python3
import requests
import json

RETELL_API_KEY = "key_819a6edef632ded41fe1c1ef7f12"
headers = {
    "Authorization": f"Bearer {RETELL_API_KEY}",
    "Content-Type": "application/json"
}

agent_id = "agent_0fa7211ee5b012b7c42c5c4729"  # MAGNUS

# List phone numbers to find the right one
print("📞 Finding phone numbers...")
response = requests.get(
    "https://api.retellai.com/list-phone-numbers",
    headers=headers
)

if response.status_code == 200:
    numbers = response.json()

    # Update the first available number
    for number in numbers:
        if number["phone_number"]:  # Any number will do for demo
            phone_id = number["phone_number_id"]
            phone_num = number["phone_number"]

            print(f"📞 Updating {phone_num} to use MAGNUS...")

            update = requests.patch(
                f"https://api.retellai.com/update-phone-number/{phone_id}",
                headers=headers,
                json={"inbound_agent_id": agent_id}
            )

            if update.status_code in [200, 201]:
                print(f"✅ SUCCESS! {phone_num} now connected to MAGNUS")
                print(f"\n🔥 MAGNUS IS LIVE!")
                print(f"📞 Call {phone_num}")
                print("\n💀 Try saying:")
                print('   "Hi, we\'re a digital marketing agency using AI"')
                print('   "We have ChatGPT integration for our clients"')
                print('   "We do AI-powered social media"')
                break
            else:
                print(f"❌ Failed: {update.text}")
    else:
        print("Available numbers:")
        for n in numbers:
            print(f"  {n['phone_number']} - Current agent: {n.get('inbound_agent_id', 'none')}")
else:
    print(f"❌ Failed to get numbers: {response.text}")