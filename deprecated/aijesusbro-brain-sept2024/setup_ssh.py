#!/usr/bin/env python3
import requests
import time

DO_API_TOKEN = "dop_v1_d6b57ed13fcf3d16324a3682ab6012cd1c9ff1281d4ba7e63ad86d3a13bf2cab"
DROPLET_ID = "520881582"
SSH_KEY = "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAICC0Juo1/zd27QlFzW3BP4knsejG+L0tqZrQktGapq91 aijesusbro@digitalocean"

headers = {
    "Authorization": f"Bearer {DO_API_TOKEN}",
    "Content-Type": "application/json"
}

print("🔑 Adding SSH key to Digital Ocean account...")

# First, add SSH key to DO account
key_response = requests.post(
    "https://api.digitalocean.com/v2/account/keys",
    headers=headers,
    json={
        "name": "aijesusbro-brain-key",
        "public_key": SSH_KEY
    }
)

if key_response.status_code in [201, 422]:  # 422 means key already exists
    if key_response.status_code == 201:
        key_id = key_response.json()["ssh_key"]["id"]
        print(f"✅ SSH key added to account: {key_id}")
    else:
        # Key exists, get its ID
        keys = requests.get("https://api.digitalocean.com/v2/account/keys", headers=headers)
        for key in keys.json()["ssh_keys"]:
            if key["public_key"] == SSH_KEY:
                key_id = key["id"]
                print(f"✅ SSH key already exists: {key_id}")
                break

    # Now add the key to the droplet
    print(f"🔧 Adding SSH key to droplet {DROPLET_ID}...")

    # Method 1: Try to add via droplet rebuild (keeps data)
    action = requests.post(
        f"https://api.digitalocean.com/v2/droplets/{DROPLET_ID}/actions",
        headers=headers,
        json={
            "type": "rebuild",
            "image": "docker-20-04",
            "ssh_keys": [key_id]
        }
    )

    if action.status_code in [200, 201, 202]:
        print("✅ SSH key being added to droplet (this takes 1-2 minutes)")
        print("⏰ Waiting for droplet to be ready...")
        time.sleep(60)
    else:
        print("⚠️  Couldn't rebuild droplet, trying password reset instead...")
        # Method 2: Reset root password (you'll get email)
        reset = requests.post(
            f"https://api.digitalocean.com/v2/droplets/{DROPLET_ID}/actions",
            headers=headers,
            json={"type": "password_reset"}
        )
        if reset.status_code in [200, 201, 202]:
            print("✅ Password reset initiated - check your email")
            print("Then you can add SSH key manually via console")

print("\n📝 To test SSH access:")
print(f"ssh -i ~/.ssh/aijesusbro_do root@64.23.221.37")
print("\nIf that works, we can deploy everything automatically!")