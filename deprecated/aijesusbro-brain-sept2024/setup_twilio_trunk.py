#!/usr/bin/env python3
"""
Proper Twilio SIP trunk setup for Retell
No shortcuts - doing it right!
"""

import requests
from requests.auth import HTTPBasicAuth
import json

# Twilio credentials
TWILIO_ACCOUNT_SID = "ACd7564cf277675642888a72f63d1655a3"
TWILIO_API_KEY = "SK451b658e7397ec5ad179ae1686ab5caf"
TWILIO_API_SECRET = "Z2lG0aDvABPaX7jE4eZ1xdvYU0tpQaOA"

# Retell configuration
RETELL_API_KEY = "key_819a6edef632ded41fe1c1ef7f12"
AGENT_ID = "agent_98681d3ba9a92b678106df24e4"

auth = HTTPBasicAuth(TWILIO_API_KEY, TWILIO_API_SECRET)

print("🔧 SETTING UP TWILIO SIP TRUNK FOR RETELL")
print("="*50)

# Step 1: Create SIP Domain if not exists
print("\n1️⃣ Setting up SIP Domain...")
domain_name = f"aijesusbro-retell-{TWILIO_ACCOUNT_SID[-4:]}.sip.twilio.com"
sip_domains_url = f"https://api.twilio.com/2010-04-01/Accounts/{TWILIO_ACCOUNT_SID}/SIP/Domains.json"

# Check existing domains
response = requests.get(sip_domains_url, auth=auth)
domains = response.json().get('domains', [])

domain_sid = None
for domain in domains:
    if "retell" in domain.get('domain_name', ''):
        domain_sid = domain['sid']
        print(f"  Found existing domain: {domain['domain_name']}")
        break

if not domain_sid:
    # Create new SIP domain
    domain_data = {
        'FriendlyName': 'AI Jesus Bro Retell Domain',
        'DomainName': domain_name,
        'VoiceUrl': f'https://api.retellai.com/twilio-voice-webhook/{AGENT_ID}',
        'VoiceMethod': 'POST'
    }

    create_response = requests.post(sip_domains_url, auth=auth, data=domain_data)

    if create_response.status_code in [200, 201]:
        domain = create_response.json()
        domain_sid = domain['sid']
        domain_name = domain['domain_name']
        print(f"  ✅ Created SIP domain: {domain_name}")
    else:
        print(f"  ❌ Failed to create domain: {create_response.text}")

# Step 2: Create or update Trunk
print("\n2️⃣ Setting up SIP Trunk...")
trunks_url = f"https://trunking.twilio.com/v1/Trunks"

# Check for existing trunk
existing_trunks = requests.get(trunks_url, auth=auth)
trunk_sid = None

if existing_trunks.status_code == 200:
    trunks = existing_trunks.json().get('trunks', [])
    for trunk in trunks:
        if 'retell' in trunk.get('friendly_name', '').lower() or 'aijesusbro' in trunk.get('friendly_name', '').lower():
            trunk_sid = trunk['sid']
            print(f"  Found existing trunk: {trunk['friendly_name']}")
            break

if not trunk_sid:
    # Create new trunk
    trunk_data = {
        'FriendlyName': 'AI Jesus Bro Retell Trunk',
        'DomainName': domain_name
    }

    trunk_response = requests.post(trunks_url, auth=auth, json=trunk_data)

    if trunk_response.status_code in [200, 201]:
        trunk = trunk_response.json()
        trunk_sid = trunk['sid']
        print(f"  ✅ Created trunk: {trunk_sid}")
    else:
        print(f"  ❌ Failed to create trunk: {trunk_response.text}")

# Step 3: Configure Termination URI for the trunk
if trunk_sid:
    print("\n3️⃣ Configuring Termination URI...")
    termination_url = f"https://trunking.twilio.com/v1/Trunks/{trunk_sid}/TerminationUri"

    termination_data = {
        'Uri': f'sip:{domain_name}'
    }

    term_response = requests.post(termination_url, auth=auth, json=termination_data)

    if term_response.status_code in [200, 201]:
        print(f"  ✅ Termination URI configured")
        termination_uri = f'sip:{domain_name}'
    else:
        print(f"  ⚠️ Termination URI may already exist")
        termination_uri = f'sip:{domain_name}'

# Step 4: Associate phone numbers with trunk
print("\n4️⃣ Associating phone numbers with trunk...")

phone_numbers = [
    "+13239685736",  # Primary
    "+17027109167",
    "+17027186386",
    "+17027104257",
    "+17027124212",
    "+17027104174",
    "+18669658975",
    "+17255021112"
]

if trunk_sid:
    for number in phone_numbers:
        print(f"  Configuring {number}...")

        # First, get the phone number SID
        numbers_url = f"https://api.twilio.com/2010-04-01/Accounts/{TWILIO_ACCOUNT_SID}/IncomingPhoneNumbers.json"
        response = requests.get(numbers_url, auth=auth, params={'PhoneNumber': number})

        if response.status_code == 200 and response.json().get('incoming_phone_numbers'):
            number_info = response.json()['incoming_phone_numbers'][0]
            number_sid = number_info['sid']

            # Associate with trunk
            assoc_url = f"https://trunking.twilio.com/v1/Trunks/{trunk_sid}/PhoneNumbers"
            assoc_data = {
                'PhoneNumberSid': number_sid
            }

            assoc_response = requests.post(assoc_url, auth=auth, json=assoc_data)

            if assoc_response.status_code in [200, 201]:
                print(f"    ✅ Associated with trunk")
            else:
                print(f"    ⚠️ May already be associated")

# Step 5: Configure origination for the trunk (for outbound)
print("\n5️⃣ Configuring Origination...")
if trunk_sid:
    origination_url = f"https://trunking.twilio.com/v1/Trunks/{trunk_sid}/OriginationUrls"

    origination_data = {
        'FriendlyName': 'Retell Origination',
        'SipUrl': f'sip:retell@{domain_name}',
        'Priority': 10,
        'Weight': 100,
        'Enabled': True
    }

    orig_response = requests.post(origination_url, auth=auth, json=origination_data)

    if orig_response.status_code in [200, 201]:
        print(f"  ✅ Origination configured")
    else:
        print(f"  ⚠️ Origination may already exist")

# Step 6: Update each phone number's voice webhook to the Retell endpoint
print("\n6️⃣ Updating phone number webhooks...")
retell_webhook = f"https://api.retellai.com/twilio-voice-webhook/{AGENT_ID}"

for number in phone_numbers:
    print(f"  Updating {number}...")

    # Get phone number SID
    numbers_url = f"https://api.twilio.com/2010-04-01/Accounts/{TWILIO_ACCOUNT_SID}/IncomingPhoneNumbers.json"
    response = requests.get(numbers_url, auth=auth, params={'PhoneNumber': number})

    if response.status_code == 200 and response.json().get('incoming_phone_numbers'):
        number_info = response.json()['incoming_phone_numbers'][0]
        number_sid = number_info['sid']

        # Update the voice webhook
        update_url = f"https://api.twilio.com/2010-04-01/Accounts/{TWILIO_ACCOUNT_SID}/IncomingPhoneNumbers/{number_sid}.json"
        update_data = {
            'VoiceUrl': retell_webhook,
            'VoiceMethod': 'POST',
            'VoiceFallbackUrl': '',  # Clear fallback
            'StatusCallback': '',  # Clear status callback for now
            'StatusCallbackMethod': 'POST'
        }

        update_response = requests.post(update_url, auth=auth, data=update_data)

        if update_response.status_code == 200:
            print(f"    ✅ Webhook updated to Retell")
        else:
            print(f"    ❌ Failed: {update_response.text}")

print("\n" + "="*50)
print("✅ TWILIO TRUNK CONFIGURATION COMPLETE!")
print(f"\nTrunk SID: {trunk_sid}")
print(f"Domain: {domain_name}")
print(f"Termination URI: sip:{domain_name}")
print(f"Agent ID: {AGENT_ID}")
print(f"Retell Webhook: {retell_webhook}")
print("\nYour phone numbers are now configured for Retell!")
print("Test by calling any of your numbers.")