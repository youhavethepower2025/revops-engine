#!/usr/bin/env python3
import requests
from requests.auth import HTTPBasicAuth

# NEW WORKING CREDS!
TWILIO_ACCOUNT_SID = "ACd7564cf277675642888a72f63d1655a3"
TWILIO_API_KEY = "SK451b658e7397ec5ad179ae1686ab5caf"
TWILIO_API_SECRET = "Z2lG0aDvABPaX7jE4eZ1xdvYU0tpQaOA"

print("🚀 TESTING NEW API CREDENTIALS!")
print("="*50)

# With API keys, use the API key as username and secret as password
url = f"https://api.twilio.com/2010-04-01/Accounts/{TWILIO_ACCOUNT_SID}.json"
response = requests.get(url, auth=HTTPBasicAuth(TWILIO_API_KEY, TWILIO_API_SECRET))

if response.status_code == 200:
    print("✅ FUCK YES! AUTHENTICATION WORKING!")
    data = response.json()
    print(f"Account Name: {data.get('friendly_name')}")
    print(f"Status: {data.get('status')}")
    print(f"Balance: {data.get('balance')}")

    # Get phone numbers
    numbers_url = f"https://api.twilio.com/2010-04-01/Accounts/{TWILIO_ACCOUNT_SID}/IncomingPhoneNumbers.json"
    numbers_response = requests.get(numbers_url, auth=HTTPBasicAuth(TWILIO_API_KEY, TWILIO_API_SECRET))

    if numbers_response.status_code == 200:
        numbers_data = numbers_response.json()
        print(f"\n📱 PHONE NUMBERS FOUND: {len(numbers_data.get('incoming_phone_numbers', []))}")
        for number in numbers_data.get('incoming_phone_numbers', []):
            print(f"  - {number['phone_number']} (SID: {number['sid'][:20]}...)")
            if number['phone_number'] == '+13239685736':
                print(f"    🎉 PRIMARY NUMBER FOUND - FREE FROM VAPI!")
                print(f"    Voice URL: {number.get('voice_url', 'None')}")
else:
    print(f"❌ Still failed: {response.status_code}")
    print(response.text)