#!/usr/bin/env python3
import requests
import json

RETELL_API_KEY = "key_819a6edef632ded41fe1c1ef7f12"
headers = {
    "Authorization": f"Bearer {RETELL_API_KEY}",
    "Content-Type": "application/json"
}

agent_id = "agent_0fa7211ee5b012b7c42c5c4729"  # MAGNUS

# Import a 702 number from Twilio
phone_to_import = "+17027186386"  # One of your 702 numbers

print(f"📞 Importing {phone_to_import} to Retell...")

import_response = requests.post(
    "https://api.retellai.com/import-phone-number",
    headers=headers,
    json={
        "phone_number": phone_to_import,
        "termination_uri": "sip:aijesusbro-retell-55a3.sip.twilio.com",
        "inbound_agent_id": agent_id
    }
)

if import_response.status_code in [200, 201]:
    print(f"✅ SUCCESS! {phone_to_import} imported and connected to MAGNUS")
    print(f"\n🔥 MAGNUS IS LIVE ON {phone_to_import}!")
    print("\n💀 Call that number and try saying:")
    print('   "Hi, we\'re a digital marketing agency using AI"')
    print('   "We offer ChatGPT integration"')
    print('   "We do AI-powered campaigns"')
    print('\nWatch MAGNUS intellectually destroy the caller!')
else:
    print(f"Response: {import_response.status_code}")
    print(f"Error: {import_response.text}")