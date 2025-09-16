#!/usr/bin/env python3
"""
Deploy ClearVC to Railway using their API
"""

import requests
import json
import os
import time

# Your Railway token
RAILWAY_TOKEN = "440f92bc-1b30-4e4e-b1c2-157f4cddf2e5"
RAILWAY_API = "https://backboard.railway.app/graphql/v2"

def graphql_request(query, variables=None):
    """Make a GraphQL request to Railway API"""
    headers = {
        "Authorization": f"Bearer {RAILWAY_TOKEN}",
        "Content-Type": "application/json"
    }

    response = requests.post(
        RAILWAY_API,
        json={"query": query, "variables": variables or {}},
        headers=headers
    )

    print(f"Response status: {response.status_code}")

    if response.status_code != 200:
        print(f"Error: {response.text}")
        return None

    data = response.json()

    if "errors" in data:
        print(f"GraphQL errors: {data['errors']}")

    return data.get("data")

def create_project():
    """Create a new Railway project"""
    query = """
    mutation CreateProject {
        projectCreate(input: {
            name: "clearvc-amber-brain"
            description: "ClearVC Intelligent Call Orchestrator"
            isPublic: false
        }) {
            id
            name
        }
    }
    """

    print("Creating Railway project...")
    data = graphql_request(query)

    if data and "projectCreate" in data:
        project = data["projectCreate"]
        print(f"✅ Created project: {project['name']} (ID: {project['id']})")
        return project["id"]

    return None

def create_service(project_id):
    """Create a service in the project"""
    query = """
    mutation CreateService($projectId: String!, $name: String!) {
        serviceCreate(
            projectId: $projectId
            input: {
                name: $name
                source: {}
            }
        ) {
            id
            name
        }
    }
    """

    print("\nCreating service...")
    data = graphql_request(query, {"projectId": project_id, "name": "amber-brain"})

    if data and "serviceCreate" in data:
        service = data["serviceCreate"]
        print(f"✅ Created service: {service['name']} (ID: {service['id']})")
        return service["id"]

    return None

def get_environments(project_id):
    """Get project environments"""
    query = """
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

    data = graphql_request(query, {"projectId": project_id})

    if data and "project" in data:
        environments = data["project"]["environments"]["edges"]
        if environments:
            env = environments[0]["node"]
            print(f"Found environment: {env['name']} (ID: {env['id']})")
            return env["id"]

    return None

def set_environment_variables(project_id, environment_id, service_id):
    """Set environment variables for the service"""
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
        "PORT": "8000",
        "ENVIRONMENT": "production",
        "DEBUG": "false"
    }

    print("\nSetting environment variables...")
    data = graphql_request(query, {
        "projectId": project_id,
        "environmentId": environment_id,
        "serviceId": service_id,
        "variables": {"variables": variables}
    })

    if data:
        print(f"✅ Environment variables set")
        return True

    return False

def deploy_from_github(project_id, service_id, environment_id):
    """Deploy from GitHub (or trigger deployment)"""
    query = """
    mutation Deploy($projectId: String!, $serviceId: String!, $environmentId: String!) {
        deploymentTrigger(
            projectId: $projectId
            serviceId: $serviceId
            environmentId: $environmentId
        ) {
            id
            status
        }
    }
    """

    print("\nTriggering deployment...")
    data = graphql_request(query, {
        "projectId": project_id,
        "serviceId": service_id,
        "environmentId": environment_id
    })

    if data and "deploymentTrigger" in data:
        deployment = data["deploymentTrigger"]
        print(f"✅ Deployment triggered: {deployment['id']}")
        return deployment["id"]

    return None

def get_service_domain(project_id, service_id, environment_id):
    """Get or generate domain for the service"""
    # First try to generate a domain
    gen_query = """
    mutation GenerateDomain($projectId: String!, $serviceId: String!, $environmentId: String!) {
        serviceDomainCreate(
            projectId: $projectId
            serviceId: $serviceId
            environmentId: $environmentId
        ) {
            domain
        }
    }
    """

    print("\nGenerating domain...")
    data = graphql_request(gen_query, {
        "projectId": project_id,
        "serviceId": service_id,
        "environmentId": environment_id
    })

    if data and "serviceDomainCreate" in data:
        domain = data["serviceDomainCreate"]["domain"]
        return f"https://{domain}"

    # If generation fails, try to get existing domain
    get_query = """
    query GetDomain($serviceId: String!) {
        service(id: $serviceId) {
            domains {
                serviceDomains {
                    domain
                }
            }
        }
    }
    """

    data = graphql_request(get_query, {"serviceId": service_id})

    if data and "service" in data:
        domains = data["service"]["domains"]["serviceDomains"]
        if domains:
            return f"https://{domains[0]['domain']}"

    return None

def main():
    print("🚀 Deploying ClearVC to Railway")
    print("=" * 50)

    # Create project
    project_id = create_project()
    if not project_id:
        print("❌ Failed to create project")
        return

    # Create service
    service_id = create_service(project_id)
    if not service_id:
        print("❌ Failed to create service")
        return

    # Get environment
    environment_id = get_environments(project_id)
    if not environment_id:
        print("❌ Failed to get environment")
        return

    # Set environment variables
    set_environment_variables(project_id, environment_id, service_id)

    # Deploy
    deployment_id = deploy_from_github(project_id, service_id, environment_id)

    if deployment_id:
        print("\n⏳ Deployment in progress...")
        print(f"   View at: https://railway.app/project/{project_id}")

        # Wait a bit
        time.sleep(5)

        # Get domain
        domain = get_service_domain(project_id, service_id, environment_id)

        if domain:
            print(f"\n✅ Service URL: {domain}")
            print(f"\n📍 Single Webhook URL for Retell:")
            print(f"   {domain}/webhook")
            print(f"\n   (This one endpoint handles all webhook types intelligently)")

            # Save for later use
            with open("railway_deployment.json", "w") as f:
                json.dump({
                    "project_id": project_id,
                    "service_id": service_id,
                    "environment_id": environment_id,
                    "url": domain,
                    "webhook": f"{domain}/webhook"
                }, f, indent=2)

            print(f"\n✅ Deployment info saved to railway_deployment.json")
        else:
            print("⚠️  Domain pending - check Railway dashboard")

if __name__ == "__main__":
    main()