#!/usr/bin/env python3
import requests
from requests.auth import HTTPBasicAuth

TWILIO_ACCOUNT_SID = "ACd7564cf277675642888a72f63d1655a3"
TWILIO_AUTH_TOKEN = "e65397c32f16f83469ee9d859308eb6a"

# Test account access
url = f"https://api.twilio.com/2010-04-01/Accounts/{TWILIO_ACCOUNT_SID}.json"
response = requests.get(url, auth=HTTPBasicAuth(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN))

print(f"Status: {response.status_code}")
if response.status_code == 200:
    data = response.json()
    print(f"Account Name: {data.get('friendly_name')}")
    print(f"Status: {data.get('status')}")

    # Now check phone numbers
    numbers_url = f"https://api.twilio.com/2010-04-01/Accounts/{TWILIO_ACCOUNT_SID}/IncomingPhoneNumbers.json"
    numbers_response = requests.get(numbers_url, auth=HTTPBasicAuth(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN))

    if numbers_response.status_code == 200:
        numbers_data = numbers_response.json()
        print(f"\nPhone Numbers Found: {len(numbers_data.get('incoming_phone_numbers', []))}")
        for number in numbers_data.get('incoming_phone_numbers', []):
            print(f"  - {number['phone_number']} (SID: {number['sid'][:10]}...)")
            if number['phone_number'] == '+13239685736':
                print(f"    ✅ PRIMARY NUMBER FOUND - Free from Vapi!")
                print(f"    Current Voice URL: {number.get('voice_url', 'None')}")
else:
    print(f"Error: {response.text}")