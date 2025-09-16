#!/usr/bin/env python3
"""
Deploy ClearVC Amber Brain to Railway using API
No browser login needed - uses Railway API directly
"""

import os
import json
import requests
import subprocess
from typing import Dict, Any, Optional

# Railway API configuration
RAILWAY_API_URL = "https://backboard.railway.app/graphql/v2"

def get_railway_token() -> Optional[str]:
    """Get Railway token from environment or config"""
    # Try environment variable first
    token = os.getenv("RAILWAY_TOKEN")

    if not token:
        # Try to get from Railway CLI config
        config_path = os.path.expanduser("~/.railway/config.json")
        if os.path.exists(config_path):
            with open(config_path, 'r') as f:
                config = json.load(f)
                # Railway stores token in user config
                token = config.get("user", {}).get("token")

    if not token:
        # Try railway token command
        try:
            result = subprocess.run(
                ["railway", "token"],
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                token = result.stdout.strip()
        except:
            pass

    return token

def create_railway_project(token: str, name: str = "clearvc-amber-brain") -> Dict[str, Any]:
    """Create a new Railway project"""

    query = """
    mutation CreateProject($name: String!) {
        projectCreate(input: {
            name: $name
            description: "ClearVC Amber Brain - Intelligent Call Orchestrator"
            isPublic: false
        }) {
            projectId
            name
        }
    }
    """

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    response = requests.post(
        RAILWAY_API_URL,
        json={
            "query": query,
            "variables": {"name": name}
        },
        headers=headers
    )

    if response.status_code == 200:
        data = response.json()
        if "data" in data:
            return data["data"]["projectCreate"]

    print(f"Failed to create project: {response.text}")
    return None

def deploy_service(token: str, project_id: str) -> bool:
    """Deploy the service to Railway"""

    # Create deployment using Railway CLI with token
    env_vars = {
        "RAILWAY_TOKEN": token,
        "RAILWAY_PROJECT_ID": project_id
    }

    commands = [
        # Link to project
        f"railway link {project_id}",

        # Add PostgreSQL
        "railway add --plugin postgresql",

        # Set environment variables
        "railway variables set RETELL_API_KEY=$RETELL_API_KEY",
        "railway variables set GHL_API_KEY=$GHL_API_KEY",
        "railway variables set GHL_LOCATION_ID=$GHL_LOCATION_ID",
        "railway variables set OPENAI_API_KEY=$OPENAI_API_KEY",

        # Deploy
        "railway up --detach"
    ]

    for cmd in commands:
        print(f"Running: {cmd}")
        result = subprocess.run(
            cmd,
            shell=True,
            env={**os.environ, **env_vars},
            cwd="/Users/aijesusbro/AI Projects/ClearVC/amber-brain",
            capture_output=True,
            text=True
        )

        if result.returncode != 0:
            print(f"Command failed: {result.stderr}")
            return False

        print(f"Success: {result.stdout}")

    return True

def get_deployment_url(token: str, project_id: str) -> Optional[str]:
    """Get the deployment URL"""

    query = """
    query GetProjectDomains($projectId: String!) {
        project(id: $projectId) {
            services {
                edges {
                    node {
                        id
                        name
                        domains {
                            serviceDomains {
                                domain
                            }
                        }
                    }
                }
            }
        }
    }
    """

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    response = requests.post(
        RAILWAY_API_URL,
        json={
            "query": query,
            "variables": {"projectId": project_id}
        },
        headers=headers
    )

    if response.status_code == 200:
        data = response.json()
        services = data.get("data", {}).get("project", {}).get("services", {}).get("edges", [])

        for service in services:
            domains = service.get("node", {}).get("domains", {}).get("serviceDomains", [])
            if domains:
                return f"https://{domains[0]['domain']}"

    return None

def main():
    """Main deployment flow"""
    print("🚀 ClearVC Amber Brain - Railway API Deployment")
    print("=" * 50)

    # Get Railway token
    token = get_railway_token()

    if not token:
        print("❌ No Railway token found")
        print("\nTo get a token:")
        print("1. Run: railway login --browserless")
        print("2. Or set RAILWAY_TOKEN environment variable")
        return

    print("✅ Railway token found")

    # Load environment variables for deployment
    env_file = "/Users/aijesusbro/AI Projects/ClearVC/amber-brain/.env"
    if os.path.exists(env_file):
        from dotenv import load_dotenv
        load_dotenv(env_file)
        print("✅ Environment variables loaded")

    # Create project
    print("\n📦 Creating Railway project...")
    project = create_railway_project(token)

    if not project:
        print("❌ Failed to create project")
        return

    project_id = project["projectId"]
    print(f"✅ Project created: {project['name']} ({project_id})")

    # Deploy service
    print("\n🚂 Deploying service...")
    if deploy_service(token, project_id):
        print("✅ Service deployed successfully")

        # Get URL
        print("\n🔗 Getting deployment URL...")
        import time
        time.sleep(10)  # Wait for deployment to initialize

        url = get_deployment_url(token, project_id)
        if url:
            print(f"✅ Deployment URL: {url}")

            # Save URL for Retell update
            with open("deployment_url.txt", "w") as f:
                f.write(url)

            print("\n📝 Webhook URLs for Retell:")
            print(f"  Call Start:  {url}/webhooks/retell/call-started")
            print(f"  Call End:    {url}/webhooks/retell/call-ended")
            print(f"  Transcript:  {url}/webhooks/retell/transcript-update")
            print(f"  Tool Call:   {url}/webhooks/retell/tool-call")
        else:
            print("⚠️  URL not ready yet - check Railway dashboard")
    else:
        print("❌ Deployment failed")

if __name__ == "__main__":
    main()