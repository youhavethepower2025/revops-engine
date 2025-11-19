# 3. DigitalOcean Integration Guide

## Authentication

To interact with the DigitalOcean API, you need a Personal Access Token (PAT). You can generate a PAT from the DigitalOcean control panel.

**Important:** Treat your PAT like a password. Store it securely and do not expose it in client-side code.

### Using the PAT

All API requests must include the PAT in an `Authorization` header as a Bearer token.

`Authorization: Bearer YOUR_DIGITALOCEAN_PAT`

### Python Example

Here is a Python example of how to make an authenticated request to the DigitalOcean API:

```python
import os
import requests

# It is recommended to store your PAT as an environment variable
DO_PAT = os.getenv("DIGITALOCEAN_TOKEN")

headers = {
    "Authorization": f"Bearer {DO_PAT}",
    "Content-Type": "application/json",
}

response = requests.get("https://api.digitalocean.com/v2/droplets", headers=headers)

if response.status_code == 200:
    droplets = response.json()["droplets"]
    for droplet in droplets:
        print(f"Droplet: {droplet['name']}")
else:
    print(f"Error: {response.status_code} - {response.text}")
```

## Quick Start: Create a Droplet

This example shows how to create a new Droplet using the API.

1.  **Endpoint:** `POST /v2/droplets`
2.  **Request Body:**

    ```json
    {
      "name": "My-New-Droplet",
      "region": "nyc3",
      "size": "s-1vcpu-1gb",
      "image": "ubuntu-20-04-x64",
      "ssh_keys": ["YOUR_SSH_KEY_FINGERPRINT"],
      "user_data": "#!/bin/bash\napt-get update -y\napt-get install -y nginx"
    }
    ```

3.  **Response:** A successful request will return a JSON object with details about the new Droplet.

## Core Workflows

### Listing Droplets

*   **Endpoint:** `GET /v2/droplets`
*   **Description:** Retrieves a list of all Droplets in your account.

### Deleting a Droplet

*   **Endpoint:** `DELETE /v2/droplets/{droplet_id}`
*   **Description:** Deletes a Droplet by its ID.

## Error Handling

*   **401 Unauthorized:** Your PAT is invalid or missing.
*   **404 Not Found:** The requested resource does not exist.
*   **422 Unprocessable Entity:** The request body is malformed or contains invalid parameters.
*   **500 Internal Server Error:** An error occurred on DigitalOcean's end.
