#!/usr/bin/env python3
"""
Deploy ClearVC to Railway NOW using API
"""

import requests
import json
import base64
import os

# Railway API endpoint
RAILWAY_API = "https://backboard.railway.app/graphql/v2"

# Your Railway token from config
RAILWAY_TOKEN = "rw_Fe26.2**bcbde17e71b9e876208f67254e8f6f299b6b6a36eb6d5dd91c697afb5b3d42a6*48QEzBddzrfVFOwTdOQyYA*Ibid3ab71oEViphbWhRr_J2SiHrOnR8AmglNh7fF2lYk62bYQV0XQa0yePrtwb6azYaruRuHXOETxiyc4HYZsQ*1754804534005*0023d3cf9d9b75b9a883096bc169dd718f1f2a5ddaf0226f03709912f0ea934b*OLwSAFUjN_eG3TcHrefelWbtnYd1calYkqLUxHIcuWY"

# Project ID you provided
PROJECT_ID = "440f92bc-1b30-4e4e-b1c2-157f4cddf2e5"

def railway_request(query, variables=None):
    """Make Railway API request"""
    headers = {
        "Authorization": f"Bearer {RAILWAY_TOKEN}",
        "Content-Type": "application/json"
    }

    response = requests.post(
        RAILWAY_API,
        json={"query": query, "variables": variables or {}},
        headers=headers
    )

    if response.status_code == 200:
        return response.json()
    else:
        print(f"API Error: {response.status_code} - {response.text}")
        return None

def create_service():
    """Create a new service in the project"""
    query = """
    mutation CreateService($projectId: String!) {
        serviceCreate(projectId: $projectId, input: {
            name: "clearvc-amber-brain"
            source: {
                image: "python:3.11-slim"
            }
        }) {
            id
            name
        }
    }
    """

    result = railway_request(query, {"projectId": PROJECT_ID})
    if result and "data" in result:
        service = result["data"]["serviceCreate"]
        print(f"✅ Created service: {service['name']} ({service['id']})")
        return service['id']
    return None

def deploy_code(service_id):
    """Deploy the code to the service"""

    # Read all Python files
    files_to_deploy = {}
    code_dir = "/Users/aijesusbro/AI Projects/ClearVC/amber-brain"

    for filename in os.listdir(code_dir):
        if filename.endswith(('.py', '.txt', '.yml', '.json', '.md', '.toml')) or filename == 'Dockerfile':
            filepath = os.path.join(code_dir, filename)
            with open(filepath, 'r') as f:
                files_to_deploy[filename] = f.read()

    # Create deployment
    query = """
    mutation Deploy($serviceId: String!, $environmentId: String!) {
        deploymentCreate(
            serviceId: $serviceId
            environmentId: $environmentId
            input: {
                meta: {
                    commitMessage: "Deploy ClearVC Amber Brain"
                }
            }
        ) {
            id
            status
        }
    }
    """

    # Get environment ID
    env_query = """
    query GetEnvironment($projectId: String!) {
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

    env_result = railway_request(env_query, {"projectId": PROJECT_ID})
    if env_result and "data" in env_result:
        environments = env_result["data"]["project"]["environments"]["edges"]
        if environments:
            env_id = environments[0]["node"]["id"]

            # Deploy
            deploy_result = railway_request(query, {
                "serviceId": service_id,
                "environmentId": env_id
            })

            if deploy_result and "data" in deploy_result:
                deployment = deploy_result["data"]["deploymentCreate"]
                print(f"✅ Deployment started: {deployment['id']}")
                return deployment['id']

    return None

def set_variables(service_id):
    """Set environment variables"""
    query = """
    mutation SetVariables($projectId: String!, $environmentId: String!, $serviceId: String!, $variables: VariableCollectionInput!) {
        variableCollectionUpsert(
            projectId: $projectId
            environmentId: $environmentId
            serviceId: $serviceId
            input: $variables
        )
    }
    """

    variables = {
        "RETELL_API_KEY": os.getenv("RETELL_API_KEY", "your_retell_key"),
        "GHL_API_KEY": "clearvc_ghl_key",
        "GHL_LOCATION_ID": "clearvc_location",
        "OPENAI_API_KEY": os.getenv("OPENAI_API_KEY", "your_openai_key"),
        "PORT": "8000"
    }

    # Convert to Railway format
    var_input = {
        "variables": json.dumps(variables)
    }

    result = railway_request(query, {
        "projectId": PROJECT_ID,
        "environmentId": "production",
        "serviceId": service_id,
        "variables": var_input
    })

    if result:
        print("✅ Environment variables set")
        return True
    return False

def get_domain(service_id):
    """Get or create domain for service"""
    query = """
    mutation GenerateDomain($projectId: String!, $serviceId: String!) {
        customDomainCreate(
            projectId: $projectId
            serviceId: $serviceId
            input: {
                domain: "clearvc-amber-brain"
            }
        ) {
            domain
            status
        }
    }
    """

    result = railway_request(query, {
        "projectId": PROJECT_ID,
        "serviceId": service_id
    })

    if result and "data" in result:
        domain = result["data"]["customDomainCreate"]["domain"]
        return f"https://{domain}.up.railway.app"

    # Try to get existing domain
    get_query = """
    query GetDomains($projectId: String!, $serviceId: String!) {
        service(id: $serviceId) {
            domains {
                serviceDomains {
                    domain
                }
            }
        }
    }
    """

    result = railway_request(get_query, {
        "projectId": PROJECT_ID,
        "serviceId": service_id
    })

    if result and "data" in result:
        domains = result["data"]["service"]["domains"]["serviceDomains"]
        if domains:
            return f"https://{domains[0]['domain']}"

    return None

def main():
    print("🚀 Deploying ClearVC to Railway via API")
    print("=" * 50)

    # Create service
    service_id = create_service()
    if not service_id:
        print("❌ Failed to create service")
        return

    # Set variables
    set_variables(service_id)

    # Deploy code
    deployment_id = deploy_code(service_id)
    if not deployment_id:
        print("❌ Failed to deploy")
        return

    # Get domain
    domain = get_domain(service_id)
    if domain:
        print(f"\n✅ Deployed to: {domain}")
        print("\n📝 Webhook URLs for Retell:")
        print(f"  Call Start:  {domain}/webhooks/retell/call-started")
        print(f"  Call End:    {domain}/webhooks/retell/call-ended")
        print(f"  Transcript:  {domain}/webhooks/retell/transcript-update")
        print(f"  Tool Call:   {domain}/webhooks/retell/tool-call")

        # Save URL for Retell update
        with open("deployment_url.txt", "w") as f:
            f.write(domain)
    else:
        print("⚠️  Domain not ready yet - check Railway dashboard")

if __name__ == "__main__":
    main()