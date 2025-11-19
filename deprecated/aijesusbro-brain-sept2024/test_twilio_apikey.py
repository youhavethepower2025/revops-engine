#!/usr/bin/env python3
import requests
from requests.auth import HTTPBasicAuth

# Using API Key instead of auth token
TWILIO_ACCOUNT_SID = "ACd7564cf277675642888a72f63d1655a3"
TWILIO_API_KEY_SID = "SK445dfd1ff0b605e82ca5462484b044f8"
TWILIO_API_KEY_SECRET = "UPDATE_ME"  # Need the secret that goes with this key

# For standard auth (if the other credentials are actually correct)
TWILIO_AUTH_TOKEN = "e65397c32f16f83469ee9d859308eb6a"

print("Testing with standard auth token first...")
url = f"https://api.twilio.com/2010-04-01/Accounts/{TWILIO_ACCOUNT_SID}.json"
response = requests.get(url, auth=HTTPBasicAuth(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN))

if response.status_code == 200:
    print("✅ Standard auth working!")
    data = response.json()
    print(f"Account: {data.get('friendly_name')}")

    # Get phone numbers
    numbers_url = f"https://api.twilio.com/2010-04-01/Accounts/{TWILIO_ACCOUNT_SID}/IncomingPhoneNumbers.json"
    numbers_response = requests.get(numbers_url, auth=HTTPBasicAuth(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN))

    if numbers_response.status_code == 200:
        numbers_data = numbers_response.json()
        print(f"\nPhone Numbers: {len(numbers_data.get('incoming_phone_numbers', []))}")
        for number in numbers_data.get('incoming_phone_numbers', [])[:10]:
            print(f"  - {number['phone_number']}")
else:
    print(f"❌ Auth failed: {response.status_code}")
    print("Response:", response.text[:200])

print("\nNote: For API Key auth, we need the SECRET that goes with SK445dfd1ff0b605e82ca5462484b044f8")
print("It should be a long string shown when you created the API key")