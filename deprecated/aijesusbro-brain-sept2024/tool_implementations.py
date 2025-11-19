"""Tool Implementation Functions for Enhanced Brain"""

import os
import json
import subprocess
import asyncio
import httpx
from datetime import datetime
from typing import Dict, Any, Optional
from pathlib import Path

# Get API configurations
RETELL_API_KEYS = json.loads(os.getenv("RETELL_API_KEYS", '{}'))
GHL_ACCOUNTS = json.loads(os.getenv("GHL_ACCOUNTS", '{}'))
TWILIO_ACCOUNTS = json.loads(os.getenv("TWILIO_ACCOUNTS", '{}'))

# Fallback to single keys
RETELL_API_KEY = RETELL_API_KEYS.get("default", os.getenv("RETELL_API_KEY"))
GHL_API_KEY = list(GHL_ACCOUNTS.values())[0]["api_key"] if GHL_ACCOUNTS else os.getenv("GHL_API_KEY")
GHL_LOCATION_ID = list(GHL_ACCOUNTS.values())[0]["location_id"] if GHL_ACCOUNTS else os.getenv("GHL_LOCATION_ID")

async def execute_enhanced_tool(tool_name: str, args: dict, db_pool) -> dict:
    """Execute enhanced tool implementations"""

    # ============ MEMORY TOOLS (PostgreSQL) ============
    if tool_name == "remember":
        if not db_pool:
            return {"content": [{"type": "text", "text": "Database not connected"}]}
        async with db_pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO memory (key, value, metadata)
                VALUES ($1, $2, $3)
                ON CONFLICT (key) DO UPDATE
                SET value = $2, metadata = $3
            """, args['key'], json.dumps(args['value']), json.dumps(args.get('metadata', {})))
            return {"content": [{"type": "text", "text": f"Remembered: {args['key']}"}]}

    elif tool_name == "recall":
        if not db_pool:
            return {"content": [{"type": "text", "text": "Database not connected"}]}
        async with db_pool.acquire() as conn:
            row = await conn.fetchrow("SELECT value, metadata FROM memory WHERE key = $1", args['key'])
            if row:
                return {"content": [{"type": "text", "text": json.dumps(row['value'])}]}
            else:
                return {"content": [{"type": "text", "text": f"No memory found for key: {args['key']}"}]}

    elif tool_name == "search_memory":
        if not db_pool:
            return {"content": [{"type": "text", "text": "Database not connected"}]}
        async with db_pool.acquire() as conn:
            # Use PostgreSQL's JSONB search capabilities
            rows = await conn.fetch("""
                SELECT key, value FROM memory
                WHERE value::text ILIKE $1
                LIMIT $2
            """, f"%{args['query']}%", args.get('limit', 10))

            results = [{"key": row['key'], "value": row['value']} for row in rows]
            return {"content": [{"type": "text", "text": json.dumps(results)}]}

    # ============ ENHANCED RETELL TOOLS ============
    elif tool_name == "retell_update_agent":
        agent_id = args['agent_id']
        update_data = {k: v for k, v in args.items() if k != 'agent_id' and v is not None}

        async with httpx.AsyncClient() as client:
            response = await client.patch(
                f"https://api.retellai.com/update-agent/{agent_id}",
                headers={"Authorization": f"Bearer {RETELL_API_KEY}"},
                json=update_data
            )
            return {"content": [{"type": "text", "text": json.dumps(response.json())}]}

    elif tool_name == "retell_get_call":
        call_id = args['call_id']
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"https://api.retellai.com/get-call/{call_id}",
                headers={"Authorization": f"Bearer {RETELL_API_KEY}"}
            )
            call_data = response.json()

            # Store in memory for later analysis
            if db_pool:
                async with db_pool.acquire() as conn:
                    await conn.execute("""
                        INSERT INTO memory (key, value, metadata)
                        VALUES ($1, $2, $3)
                        ON CONFLICT (key) DO UPDATE SET value = $2
                    """, f"call_{call_id}", json.dumps(call_data), json.dumps({"type": "call_transcript"}))

            return {"content": [{"type": "text", "text": json.dumps(call_data)}]}

    elif tool_name == "retell_list_calls":
        params = {k: v for k, v in args.items() if v is not None}
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api.retellai.com/list-calls",
                headers={"Authorization": f"Bearer {RETELL_API_KEY}"},
                json=params
            )
            return {"content": [{"type": "text", "text": json.dumps(response.json())}]}

    # ============ ENHANCED GHL TOOLS ============
    elif tool_name == "ghl_search_contact":
        query = args['query']
        location_id = args.get('location_id', GHL_LOCATION_ID)

        async with httpx.AsyncClient() as client:
            # Search by phone, email, or name
            response = await client.get(
                f"https://rest.gohighlevel.com/v1/contacts/search",
                headers={"Authorization": f"Bearer {GHL_API_KEY}"},
                params={"locationId": location_id, "query": query}
            )
            contacts = response.json()

            # If searching by phone and found, store in memory
            if contacts and db_pool:
                async with db_pool.acquire() as conn:
                    await conn.execute("""
                        INSERT INTO memory (key, value, metadata)
                        VALUES ($1, $2, $3)
                        ON CONFLICT (key) DO UPDATE SET value = $2
                    """, f"contact_lookup_{query}", json.dumps(contacts[0]),
                    json.dumps({"type": "contact_lookup", "query": query}))

            return {"content": [{"type": "text", "text": json.dumps(contacts)}]}

    elif tool_name == "ghl_get_contact":
        contact_id = args['contact_id']
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"https://rest.gohighlevel.com/v1/contacts/{contact_id}",
                headers={"Authorization": f"Bearer {GHL_API_KEY}"}
            )
            return {"content": [{"type": "text", "text": json.dumps(response.json())}]}

    elif tool_name == "ghl_update_contact":
        contact_id = args['contact_id']
        update_data = args.get('fields', {})
        if args.get('custom_fields'):
            update_data['customFields'] = args['custom_fields']
        if args.get('tags'):
            update_data['tags'] = args['tags']

        async with httpx.AsyncClient() as client:
            response = await client.put(
                f"https://rest.gohighlevel.com/v1/contacts/{contact_id}",
                headers={"Authorization": f"Bearer {GHL_API_KEY}"},
                json=update_data
            )
            return {"content": [{"type": "text", "text": json.dumps(response.json())}]}

    elif tool_name == "ghl_create_appointment":
        appointment_data = {
            "contactId": args['contact_id'],
            "calendarId": args['calendar_id'],
            "startTime": args['start_time'],
            "endTime": args['end_time'],
            "title": args.get('title', 'Appointment'),
            "status": args.get('status', 'confirmed')
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"https://rest.gohighlevel.com/v1/appointments",
                headers={"Authorization": f"Bearer {GHL_API_KEY}"},
                json=appointment_data
            )
            return {"content": [{"type": "text", "text": json.dumps(response.json())}]}

    elif tool_name == "ghl_get_calendar_slots":
        calendar_id = args['calendar_id']
        params = {
            "calendarId": calendar_id,
            "startDate": args['start_date'],
            "endDate": args['end_date'],
            "timezone": args.get('timezone', 'America/Chicago')
        }

        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://rest.gohighlevel.com/v1/appointments/slots",
                headers={"Authorization": f"Bearer {GHL_API_KEY}"},
                params=params
            )
            return {"content": [{"type": "text", "text": json.dumps(response.json())}]}

    elif tool_name == "ghl_webhook_received":
        # Process and store webhook data
        event_type = args['event_type']
        payload = args['payload']

        if args.get('store_in_memory', True) and db_pool:
            async with db_pool.acquire() as conn:
                await conn.execute("""
                    INSERT INTO memory (key, value, metadata)
                    VALUES ($1, $2, $3)
                """, f"webhook_{event_type}_{payload.get('id', 'unknown')}",
                json.dumps(payload),
                json.dumps({"type": "webhook", "event": event_type, "timestamp": str(datetime.now())}))

        # Process based on event type
        if event_type == "contact.create" or event_type == "contact.update":
            # Could trigger additional actions here
            pass

        return {"content": [{"type": "text", "text": f"Webhook processed: {event_type}"}]}

    # ============ ENHANCED RAILWAY TOOLS ============
    elif tool_name == "railway_set_env_vars":
        project_id = args['project_id']
        variables = args['variables']

        query = """
        mutation SetEnvVars($projectId: String!, $variables: JSON!) {
            deploymentVariablesSet(projectId: $projectId, variables: $variables) {
                success
            }
        }
        """

        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://backboard.railway.app/graphql/v2",
                headers={"Authorization": f"Bearer {os.getenv('RAILWAY_API_TOKEN')}"},
                json={"query": query, "variables": {"projectId": project_id, "variables": variables}}
            )
            return {"content": [{"type": "text", "text": json.dumps(response.json())}]}

    elif tool_name == "railway_get_logs":
        project_id = args['project_id']
        lines = args.get('lines', 100)

        # Use Railway CLI for logs (GraphQL is complex for logs)
        cmd = f"railway logs --project {project_id} --tail {lines}"
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        return {"content": [{"type": "text", "text": result.stdout}]}

    # ============ ENHANCED DOCKER TOOLS ============
    elif tool_name == "docker_logs":
        container = args['container']
        lines = args.get('lines', 100)
        follow = args.get('follow', False)

        cmd = f"docker logs {container} --tail {lines}"
        if follow:
            cmd += " -f"

        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=10)
        return {"content": [{"type": "text", "text": result.stdout + result.stderr}]}

    elif tool_name == "docker_exec":
        container = args['container']
        command = args['command']

        cmd = f"docker exec {container} {command}"
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30)
        return {"content": [{"type": "text", "text": f"Output: {result.stdout}\nErrors: {result.stderr}"}]}

    elif tool_name == "docker_build":
        dockerfile_path = args['dockerfile_path']
        tag = args['tag']
        no_cache = args.get('no_cache', False)

        cmd = f"docker build -f {dockerfile_path} -t {tag}"
        if no_cache:
            cmd += " --no-cache"
        cmd += " ."

        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        return {"content": [{"type": "text", "text": result.stdout}]}

    # ============ MCP MANAGEMENT TOOLS ============
    elif tool_name == "mcp_list_servers":
        # Read Claude Desktop config to see installed servers
        config_path = Path.home() / "Library" / "Application Support" / "Claude" / "claude_desktop_config.json"

        if config_path.exists():
            with open(config_path) as f:
                config = json.load(f)
                servers = config.get("mcpServers", {})
                return {"content": [{"type": "text", "text": json.dumps(servers, indent=2)}]}
        else:
            return {"content": [{"type": "text", "text": "Claude Desktop config not found"}]}

    elif tool_name == "mcp_install_server":
        package = args['package']
        is_global = args.get('global', True)

        cmd = f"npm install {'--global' if is_global else ''} {package}"
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)

        if result.returncode == 0:
            return {"content": [{"type": "text", "text": f"Successfully installed {package}\n{result.stdout}"}]}
        else:
            return {"content": [{"type": "text", "text": f"Failed to install: {result.stderr}"}]}

    elif tool_name == "mcp_configure_server":
        server_name = args['server_name']
        command = args['command']
        server_args = args.get('args', [])
        env = args.get('env', {})

        # Read current config
        config_path = Path.home() / "Library" / "Application Support" / "Claude" / "claude_desktop_config.json"

        if config_path.exists():
            with open(config_path) as f:
                config = json.load(f)
        else:
            config = {"mcpServers": {}}

        # Add new server
        config["mcpServers"][server_name] = {
            "command": command,
            "args": server_args
        }
        if env:
            config["mcpServers"][server_name]["env"] = env

        # Write back
        config_path.parent.mkdir(parents=True, exist_ok=True)
        with open(config_path, 'w') as f:
            json.dump(config, f, indent=2)

        return {"content": [{"type": "text", "text": f"Added {server_name} to Claude Desktop config. Restart Claude to activate."}]}

    elif tool_name == "mcp_restart_server":
        # This would require Claude Desktop API or restart
        return {"content": [{"type": "text", "text": "Please restart Claude Desktop to reload MCP servers"}]}

    # ============ TWILIO SMS ============
    elif tool_name == "twilio_send_sms":
        # Could be direct Twilio or through GHL
        to = args['to']
        body = args['body']
        from_number = args.get('from')

        # If we have GHL, use that
        if GHL_API_KEY:
            # Find contact by phone
            async with httpx.AsyncClient() as client:
                # Search for contact
                search_response = await client.get(
                    f"https://rest.gohighlevel.com/v1/contacts/search",
                    headers={"Authorization": f"Bearer {GHL_API_KEY}"},
                    params={"locationId": GHL_LOCATION_ID, "query": to}
                )
                contacts = search_response.json()

                if contacts:
                    # Send via GHL
                    message_data = {
                        "contactId": contacts[0]['id'],
                        "type": "sms",
                        "message": body
                    }
                    response = await client.post(
                        f"https://rest.gohighlevel.com/v1/conversations/messages",
                        headers={"Authorization": f"Bearer {GHL_API_KEY}"},
                        json=message_data
                    )
                    return {"content": [{"type": "text", "text": "SMS sent via GHL"}]}

        # Otherwise would use Twilio direct
        return {"content": [{"type": "text", "text": "Twilio direct send not implemented yet"}]}

    # ============ DOCKER STATUS & MANAGEMENT ============
    elif tool_name == "docker_status":
        try:
            result = subprocess.run(["docker", "ps", "-a", "--format", "json"],
                                  capture_output=True, text=True)
            if result.returncode == 0:
                return {"content": [{"type": "text", "text": result.stdout}]}
            else:
                return {"content": [{"type": "text", "text": f"Error: {result.stderr}"}]}
        except Exception as e:
            return {"content": [{"type": "text", "text": f"Docker not available: {str(e)}"}]}

    elif tool_name == "docker_compose_up":
        compose_file = args.get('compose_file', 'docker-compose.yml')
        detach = args.get('detach', True)
        cmd = f"docker-compose -f {compose_file} up"
        if detach:
            cmd += " -d"
        try:
            result = subprocess.run(cmd.split(), capture_output=True, text=True, cwd=args.get('path', '.'))
            return {"content": [{"type": "text", "text": result.stdout or "Containers started"}]}
        except Exception as e:
            return {"content": [{"type": "text", "text": f"Error: {str(e)}"}]}

    elif tool_name == "docker_compose_down":
        compose_file = args.get('compose_file', 'docker-compose.yml')
        cmd = f"docker-compose -f {compose_file} down"
        try:
            result = subprocess.run(cmd.split(), capture_output=True, text=True, cwd=args.get('path', '.'))
            return {"content": [{"type": "text", "text": result.stdout or "Containers stopped"}]}
        except Exception as e:
            return {"content": [{"type": "text", "text": f"Error: {str(e)}"}]}

    elif tool_name == "docker_restart":
        container = args['container']
        try:
            result = subprocess.run(["docker", "restart", container], capture_output=True, text=True)
            if result.returncode == 0:
                return {"content": [{"type": "text", "text": f"Container {container} restarted"}]}
            else:
                return {"content": [{"type": "text", "text": f"Error: {result.stderr}"}]}
        except Exception as e:
            return {"content": [{"type": "text", "text": f"Error: {str(e)}"}]}

    elif tool_name == "docker_prune":
        try:
            result = subprocess.run(["docker", "system", "prune", "-af"], capture_output=True, text=True)
            return {"content": [{"type": "text", "text": result.stdout}]}
        except Exception as e:
            return {"content": [{"type": "text", "text": f"Error: {str(e)}"}]}

    # ============ GHL ADDITIONAL TOOLS ============
    elif tool_name == "ghl_create_contact":
        async with httpx.AsyncClient() as client:
            contact_data = {
                "firstName": args.get('first_name'),
                "lastName": args.get('last_name'),
                "email": args.get('email'),
                "phone": args.get('phone'),
                "locationId": GHL_LOCATION_ID
            }
            response = await client.post(
                "https://rest.gohighlevel.com/v1/contacts/",
                headers={"Authorization": f"Bearer {GHL_API_KEY}"},
                json=contact_data
            )
            return {"content": [{"type": "text", "text": f"Created contact: {response.json()}"}]}

    elif tool_name == "ghl_add_note":
        contact_id = args['contact_id']
        note = args['note']
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"https://rest.gohighlevel.com/v1/contacts/{contact_id}/notes/",
                headers={"Authorization": f"Bearer {GHL_API_KEY}"},
                json={"body": note}
            )
            return {"content": [{"type": "text", "text": "Note added"}]}

    elif tool_name == "ghl_create_task":
        async with httpx.AsyncClient() as client:
            task_data = {
                "title": args['title'],
                "body": args.get('body', ''),
                "dueDate": args.get('due_date'),
                "contactId": args.get('contact_id'),
                "assignedTo": args.get('assigned_to')
            }
            response = await client.post(
                "https://rest.gohighlevel.com/v1/contacts/tasks/",
                headers={"Authorization": f"Bearer {GHL_API_KEY}"},
                json=task_data
            )
            return {"content": [{"type": "text", "text": "Task created"}]}

    elif tool_name == "ghl_create_opportunity":
        async with httpx.AsyncClient() as client:
            opp_data = {
                "title": args['title'],
                "contactId": args['contact_id'],
                "status": args.get('status', 'open'),
                "monetaryValue": args.get('value', 0),
                "pipelineId": args.get('pipeline_id'),
                "pipelineStageId": args.get('stage_id')
            }
            response = await client.post(
                "https://rest.gohighlevel.com/v1/pipelines/opportunities/",
                headers={"Authorization": f"Bearer {GHL_API_KEY}"},
                json=opp_data
            )
            return {"content": [{"type": "text", "text": f"Opportunity created: {response.json()}"}]}

    elif tool_name == "ghl_move_opportunity":
        opp_id = args['opportunity_id']
        stage_id = args['stage_id']
        async with httpx.AsyncClient() as client:
            response = await client.put(
                f"https://rest.gohighlevel.com/v1/pipelines/opportunities/{opp_id}",
                headers={"Authorization": f"Bearer {GHL_API_KEY}"},
                json={"pipelineStageId": stage_id}
            )
            return {"content": [{"type": "text", "text": "Opportunity moved"}]}

    elif tool_name == "ghl_trigger_workflow":
        workflow_id = args['workflow_id']
        contact_id = args.get('contact_id')
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"https://rest.gohighlevel.com/v1/workflows/{workflow_id}/trigger",
                headers={"Authorization": f"Bearer {GHL_API_KEY}"},
                json={"contactId": contact_id} if contact_id else {}
            )
            return {"content": [{"type": "text", "text": "Workflow triggered"}]}

    elif tool_name == "ghl_send_message":
        contact_id = args['contact_id']
        message = args['message']
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://rest.gohighlevel.com/v1/conversations/messages",
                headers={"Authorization": f"Bearer {GHL_API_KEY}"},
                json={
                    "type": args.get('type', 'SMS'),
                    "contactId": contact_id,
                    "message": message
                }
            )
            return {"content": [{"type": "text", "text": "Message sent"}]}

    # ============ RAILWAY TOOLS ============
    elif tool_name == "railway_create_project":
        # Import the railway deployment module
        from railway_deployment import RailwayDeploymentEngine

        engine = RailwayDeploymentEngine()
        project_name = args['name']
        client_id = args.get('client_id', project_name.lower().replace(' ', '-'))

        try:
            project_id = await engine.create_project(client_id, project_name)

            # Store in memory for tracking
            if db_pool:
                async with db_pool.acquire() as conn:
                    await conn.execute("""
                        INSERT INTO deployments (project_name, platform, status, config)
                        VALUES ($1, $2, $3, $4)
                    """, project_name, 'railway', 'created', json.dumps({"project_id": project_id}))

            return {"content": [{"type": "text", "text": f"Created Railway project: {project_id}"}]}
        except Exception as e:
            return {"content": [{"type": "text", "text": f"Failed to create project: {str(e)}"}]}

    elif tool_name == "railway_deploy":
        from railway_deployment import RailwayDeploymentEngine

        engine = RailwayDeploymentEngine()
        client_config = {
            "name": args.get('client_name', 'Client'),
            "tier": args.get('tier', 'basic'),
            "ghl_api_key": args.get('ghl_api_key', ''),
            "ghl_location_id": args.get('ghl_location_id', ''),
            "retell_api_key": args.get('retell_api_key', ''),
            "features": args.get('features', ['crm', 'voice'])
        }

        try:
            client_id = args.get('client_id', client_config['name'].lower().replace(' ', '-'))
            deployment = await engine.deploy_client_brain(client_id, client_config)

            # Store deployment info
            if db_pool:
                async with db_pool.acquire() as conn:
                    await conn.execute("""
                        INSERT INTO deployments (project_name, platform, status, config)
                        VALUES ($1, $2, $3, $4)
                    """, client_config['name'], 'railway', 'deployed', json.dumps(deployment))

            return {"content": [{"type": "text", "text": json.dumps(deployment, indent=2)}]}
        except Exception as e:
            return {"content": [{"type": "text", "text": f"Deployment failed: {str(e)}"}]}

    elif tool_name == "railway_add_domain":
        from railway_deployment import RailwayDeploymentEngine

        engine = RailwayDeploymentEngine()
        project_id = args['project_id']
        service_id = args['service_id']
        subdomain = args.get('subdomain', 'brain')

        try:
            domain = await engine.provision_domain(project_id, service_id, subdomain)
            return {"content": [{"type": "text", "text": f"Provisioned domain: {domain}"}]}
        except Exception as e:
            return {"content": [{"type": "text", "text": f"Failed to provision domain: {str(e)}"}]}

    elif tool_name == "railway_add_postgres":
        from railway_deployment import RailwayDeploymentEngine

        engine = RailwayDeploymentEngine()
        project_id = args['project_id']

        try:
            postgres = await engine.add_postgres(project_id)
            return {"content": [{"type": "text", "text": f"Added PostgreSQL: {postgres}"}]}
        except Exception as e:
            return {"content": [{"type": "text", "text": f"Failed to add PostgreSQL: {str(e)}"}]}

    elif tool_name == "railway_get_logs":
        from railway_deployment import RailwayDeploymentEngine

        engine = RailwayDeploymentEngine()
        deployment_id = args.get('deployment_id')
        lines = args.get('lines', 100)

        try:
            logs = await engine.get_deployment_logs(deployment_id, lines)
            return {"content": [{"type": "text", "text": "\n".join(logs) if logs else "No logs available"}]}
        except Exception as e:
            return {"content": [{"type": "text", "text": f"Failed to get logs: {str(e)}"}]}

    elif tool_name == "railway_set_env_vars":
        from railway_deployment import RailwayDeploymentEngine

        engine = RailwayDeploymentEngine()
        project_id = args['project_id']
        service_id = args['service_id']
        variables = args['variables']

        try:
            success = await engine.set_environment_variables(project_id, service_id, variables)
            return {"content": [{"type": "text", "text": f"Environment variables {'set' if success else 'failed to set'}"}]}
        except Exception as e:
            return {"content": [{"type": "text", "text": f"Failed to set env vars: {str(e)}"}]}

    elif tool_name == "railway_restart_service":
        from railway_deployment import RailwayDeploymentEngine

        engine = RailwayDeploymentEngine()
        service_id = args['service_id']

        try:
            success = await engine.restart_service(service_id)
            return {"content": [{"type": "text", "text": f"Service restart: {'successful' if success else 'failed'}"}]}
        except Exception as e:
            return {"content": [{"type": "text", "text": f"Failed to restart service: {str(e)}"}]}

    # ============ RETELL ADDITIONAL TOOLS ============
    elif tool_name == "retell_create_agent":
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api.retellai.com/create-agent",
                headers={"Authorization": f"Bearer {RETELL_API_KEY}"},
                json={
                    "agent_name": args['agent_name'],
                    "voice_id": args.get('voice_id', '11labs-Adrian'),
                    "response_engine": {
                        "type": "retell-llm",
                        "llm_id": args.get('llm_id', 'default')
                    },
                    "prompt": args['prompt'],
                    "webhook_url": args.get('webhook_url')
                }
            )
            if response.status_code == 201:
                agent_data = response.json()
                # Store in memory for reference
                if db_pool:
                    async with db_pool.acquire() as conn:
                        await conn.execute("""
                            INSERT INTO memory (key, value, metadata)
                            VALUES ($1, $2, $3)
                            ON CONFLICT (key) DO UPDATE
                            SET value = $2, metadata = $3
                        """, f"retell_agent_{agent_data.get('agent_id')}",
                            json.dumps(agent_data),
                            json.dumps({"type": "retell_agent", "created_at": str(datetime.now())}))
                return {"content": [{"type": "text", "text": json.dumps(agent_data)}]}
            else:
                return {"content": [{"type": "text", "text": f"Error: {response.text}"}]}

    elif tool_name == "retell_list_agents":
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://api.retellai.com/list-agents",
                headers={"Authorization": f"Bearer {RETELL_API_KEY}"}
            )
            return {"content": [{"type": "text", "text": json.dumps(response.json())}]}

    elif tool_name == "retell_create_phone_call":
        phone_number = args['phone_number']
        agent_id = args['agent_id']
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api.retellai.com/create-phone-call",
                headers={"Authorization": f"Bearer {RETELL_API_KEY}"},
                json={
                    "from_number": args.get('from_number'),
                    "to_number": phone_number,
                    "agent_id": agent_id
                }
            )
            return {"content": [{"type": "text", "text": json.dumps(response.json())}]}

    elif tool_name == "retell_register_phone_number":
        phone_number = args['phone_number']
        agent_id = args.get('agent_id')
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api.retellai.com/register-phone-number",
                headers={"Authorization": f"Bearer {RETELL_API_KEY}"},
                json={
                    "phone_number": phone_number,
                    "agent_id": agent_id
                }
            )
            return {"content": [{"type": "text", "text": json.dumps(response.json())}]}

    # ============ UTILITY TOOLS ============
    elif tool_name == "terminal_execute":
        command = args['command']
        try:
            result = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=30)
            output = result.stdout or result.stderr
            return {"content": [{"type": "text", "text": output[:2000]}]}  # Limit output
        except subprocess.TimeoutExpired:
            return {"content": [{"type": "text", "text": "Command timed out after 30 seconds"}]}
        except Exception as e:
            return {"content": [{"type": "text", "text": f"Error: {str(e)}"}]}

    elif tool_name == "python_execute":
        code = args['code']
        try:
            import io
            import contextlib

            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                exec(code)

            return {"content": [{"type": "text", "text": output.getvalue()[:2000]}]}  # Limit output
        except Exception as e:
            return {"content": [{"type": "text", "text": f"Error: {str(e)}"}]}

    elif tool_name == "deploy_brain":
        # Special tool to deploy brain to Railway
        return {"content": [{"type": "text", "text": "Brain deployment requires setup script"}]}

    else:
        # Return None to let the main brain_server.py handle basic tools
        return None