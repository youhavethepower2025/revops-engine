#!/usr/bin/env python3
"""
Deploy ClearVC to YOUR Railway project using API
"""

import requests
import os
import sys
from pathlib import Path

# Railway configuration
RAILWAY_API = "https://backboard.railway.app/graphql/v2"
RAILWAY_PROJECT_ID = "440f92bc-1b30-4e4e-b1c2-157f4cddf2e5"

# Load credentials
creds_file = Path("/Users/aijesusbro/AI Projects/mcp_credentials.env")
if creds_file.exists():
    with open(creds_file) as f:
        for line in f:
            if "RAILWAY_TOKEN=" in line:
                RAILWAY_TOKEN = line.split("=", 1)[1].strip()
                break

def api_request(query, variables=None):
    """Make Railway GraphQL request"""
    headers = {
        "Authorization": f"Bearer {RAILWAY_TOKEN}",
        "Content-Type": "application/json"
    }

    resp = requests.post(
        RAILWAY_API,
        json={"query": query, "variables": variables or {}},
        headers=headers
    )

    if resp.status_code != 200:
        print(f"❌ API Error: {resp.status_code}")
        print(resp.text)
        return None

    data = resp.json()
    if "errors" in data:
        print(f"❌ GraphQL Error: {data['errors']}")
        return None

    return data.get("data")

def get_or_create_service():
    """Get existing ClearVC service or create new one"""

    # Check for existing service
    query = """
    query GetServices($projectId: String!) {
        project(id: $projectId) {
            services {
                edges {
                    node {
                        id
                        name
                    }
                }
            }
        }
    }
    """

    data = api_request(query, {"projectId": RAILWAY_PROJECT_ID})

    if data and data["project"]["services"]["edges"]:
        for edge in data["project"]["services"]["edges"]:
            if "clearvc" in edge["node"]["name"].lower():
                service_id = edge["node"]["id"]
                print(f"✅ Found existing service: {edge['node']['name']}")
                return service_id

    # Create new service
    create_query = """
    mutation CreateService($projectId: String!) {
        serviceCreate(
            projectId: $projectId
            input: {
                name: "clearvc-amber-brain"
            }
        ) {
            id
            name
        }
    }
    """

    data = api_request(create_query, {"projectId": RAILWAY_PROJECT_ID})

    if data:
        service = data["serviceCreate"]
        print(f"✅ Created service: {service['name']}")
        return service["id"]

    return None

def set_env_variables(service_id):
    """Set environment variables for the service"""

    # Get environment ID
    env_query = """
    query GetEnvironments($projectId: String!) {
        project(id: $projectId) {
            environments {
                edges {
                    node {
                        id
                        name
                    }
                }
            }
        }
    }
    """

    data = api_request(env_query, {"projectId": RAILWAY_PROJECT_ID})

    if not data:
        print("❌ Failed to get environments")
        return False

    env_id = data["project"]["environments"]["edges"][0]["node"]["id"]

    # Set variables
    vars_query = """
    mutation SetVariables($projectId: String!, $environmentId: String!, $serviceId: String!, $variables: VariableCollectionInput!) {
        variableCollectionUpsert(
            projectId: $projectId
            environmentId: $environmentId
            serviceId: $serviceId
            input: $variables
        )
    }
    """

    # Load environment variables from .env if exists
    env_file = Path("/Users/aijesusbro/AI Projects/ClearVC/amber-brain/.env")
    variables = {}

    if env_file.exists():
        with open(env_file) as f:
            for line in f:
                if "=" in line and not line.startswith("#"):
                    key, value = line.strip().split("=", 1)
                    variables[key] = value.strip('"')

    # Add required variables
    variables.update({
        "PORT": "8000",
        "ENVIRONMENT": "production"
    })

    result = api_request(vars_query, {
        "projectId": RAILWAY_PROJECT_ID,
        "environmentId": env_id,
        "serviceId": service_id,
        "variables": {"variables": variables}
    })

    if result:
        print(f"✅ Set {len(variables)} environment variables")
        return True

    return False

def trigger_deployment(service_id):
    """Trigger a new deployment from GitHub or uploaded code"""

    # Get environment ID
    env_query = """
    query GetEnvironments($projectId: String!) {
        project(id: $projectId) {
            environments {
                edges {
                    node {
                        id
                        name
                    }
                }
            }
        }
    }
    """

    data = api_request(env_query, {"projectId": RAILWAY_PROJECT_ID})
    env_id = data["project"]["environments"]["edges"][0]["node"]["id"]

    # Create deployment
    deploy_query = """
    mutation TriggerDeployment($serviceId: String!, $environmentId: String!) {
        deploymentTrigger(
            serviceId: $serviceId
            environmentId: $environmentId
        ) {
            id
            status
        }
    }
    """

    data = api_request(deploy_query, {
        "serviceId": service_id,
        "environmentId": env_id
    })

    if data:
        deployment = data["deploymentTrigger"]
        print(f"✅ Deployment triggered: {deployment['id']}")
        return deployment["id"]

    return None

def get_service_domain(service_id):
    """Get the public domain for the service"""

    query = """
    query GetServiceDomain($serviceId: String!) {
        service(id: $serviceId) {
            domains {
                serviceDomains {
                    domain
                }
            }
        }
    }
    """

    data = api_request(query, {"serviceId": service_id})

    if data and data["service"]["domains"]["serviceDomains"]:
        domain = data["service"]["domains"]["serviceDomains"][0]["domain"]
        return f"https://{domain}"

    # Generate domain if none exists
    gen_query = """
    mutation GenerateDomain($serviceId: String!, $environmentId: String!) {
        serviceDomainCreate(
            serviceId: $serviceId
            environmentId: $environmentId
        ) {
            domain
        }
    }
    """

    # Get environment ID
    env_data = api_request("""
        query GetEnvironments($projectId: String!) {
            project(id: $projectId) {
                environments {
                    edges {
                        node {
                            id
                        }
                    }
                }
            }
        }
    """, {"projectId": RAILWAY_PROJECT_ID})

    env_id = env_data["project"]["environments"]["edges"][0]["node"]["id"]

    data = api_request(gen_query, {
        "serviceId": service_id,
        "environmentId": env_id
    })

    if data:
        domain = data["serviceDomainCreate"]["domain"]
        return f"https://{domain}"

    return None

def main():
    print("🚀 Deploying ClearVC to Railway")
    print("=" * 50)

    # Get or create service
    service_id = get_or_create_service()
    if not service_id:
        print("❌ Failed to get/create service")
        return

    # Set environment variables
    print("\n📝 Setting environment variables...")
    set_env_variables(service_id)

    # Trigger deployment
    print("\n🚂 Triggering deployment...")
    deployment_id = trigger_deployment(service_id)

    if deployment_id:
        print("\n⏳ Deployment in progress...")
        print("   Check status at: https://railway.app/project/" + RAILWAY_PROJECT_ID)

    # Get domain
    print("\n🔗 Getting service URL...")
    domain = get_service_domain(service_id)

    if domain:
        print(f"\n✅ Service URL: {domain}")
        print("\n📍 Webhook URLs for Retell:")
        print(f"   Call Start:  {domain}/webhooks/retell/call-started")
        print(f"   Call End:    {domain}/webhooks/retell/call-ended")
        print(f"   Transcript:  {domain}/webhooks/retell/transcript-update")
        print(f"   Tool Call:   {domain}/webhooks/retell/tool-call")

        # Save URL
        with open("deployment_url.txt", "w") as f:
            f.write(domain)

        print(f"\n✅ URL saved to deployment_url.txt")
    else:
        print("⚠️  Domain generation pending - check Railway dashboard")

if __name__ == "__main__":
    main()