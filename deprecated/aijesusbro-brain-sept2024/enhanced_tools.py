"""Enhanced MCP Brain Tools - Maximum Power Edition"""

def get_enhanced_tools():
    """Return the complete enhanced tool arsenal"""
    return [
        # ============ RETELL.AI ENHANCED ============
        {
            "name": "retell_create_agent",
            "description": "Create a new Retell.ai voice agent",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "agent_name": {"type": "string"},
                    "prompt": {"type": "string"},
                    "voice_id": {"type": "string", "default": "11labs-Adrian"},
                    "webhook_url": {"type": "string"},
                    "llm_id": {"type": "string", "description": "Retell LLM ID"},
                    "account": {"type": "string", "description": "Which Retell account to use"}
                },
                "required": ["agent_name", "prompt"]
            }
        },
        {
            "name": "retell_update_agent",
            "description": "Update an existing agent's configuration",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "agent_id": {"type": "string"},
                    "prompt": {"type": "string"},
                    "voice_id": {"type": "string"},
                    "webhook_url": {"type": "string"}
                },
                "required": ["agent_id"]
            }
        },
        {
            "name": "retell_list_agents",
            "description": "List all Retell.ai agents",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "account": {"type": "string", "description": "Which account to list from"}
                }
            }
        },
        {
            "name": "retell_get_call",
            "description": "Get call details including transcript and recording",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "call_id": {"type": "string"}
                },
                "required": ["call_id"]
            }
        },
        {
            "name": "retell_list_calls",
            "description": "List recent calls with filtering",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "agent_id": {"type": "string"},
                    "limit": {"type": "number", "default": 10},
                    "status": {"type": "string", "enum": ["completed", "failed", "in-progress"]}
                }
            }
        },
        {
            "name": "retell_create_phone_call",
            "description": "Initiate an outbound call",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "agent_id": {"type": "string"},
                    "to_number": {"type": "string"},
                    "from_number": {"type": "string"},
                    "metadata": {"type": "object"},
                    "retell_llm_dynamic_variables": {"type": "object", "description": "Dynamic vars for prompt"}
                },
                "required": ["agent_id", "to_number"]
            }
        },
        {
            "name": "retell_register_phone_number",
            "description": "Register a phone number for inbound calls",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "phone_number": {"type": "string"},
                    "agent_id": {"type": "string"},
                    "webhook_url": {"type": "string"}
                },
                "required": ["phone_number", "agent_id"]
            }
        },

        # ============ GOHIGHLEVEL MAXIMUM ============
        {
            "name": "ghl_search_contact",
            "description": "Search contacts by phone, email, or name",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Phone, email, or name"},
                    "location_id": {"type": "string", "description": "Optional specific location"}
                },
                "required": ["query"]
            }
        },
        {
            "name": "ghl_get_contact",
            "description": "Get full contact details by ID",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "contact_id": {"type": "string"}
                },
                "required": ["contact_id"]
            }
        },
        {
            "name": "ghl_update_contact",
            "description": "Update contact information and custom fields",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "contact_id": {"type": "string"},
                    "fields": {"type": "object", "description": "Fields to update"},
                    "custom_fields": {"type": "object", "description": "Custom field values"},
                    "tags": {"type": "array", "items": {"type": "string"}}
                },
                "required": ["contact_id", "fields"]
            }
        },
        {
            "name": "ghl_create_contact",
            "description": "Create a new contact",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "email": {"type": "string"},
                    "phone": {"type": "string"},
                    "firstName": {"type": "string"},
                    "lastName": {"type": "string"},
                    "tags": {"type": "array", "items": {"type": "string"}},
                    "source": {"type": "string"},
                    "customFields": {"type": "object"}
                },
                "required": ["phone"]  # Phone is usually more important for voice
            }
        },
        {
            "name": "ghl_create_appointment",
            "description": "Book a calendar appointment",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "contact_id": {"type": "string"},
                    "calendar_id": {"type": "string"},
                    "start_time": {"type": "string", "description": "ISO datetime"},
                    "end_time": {"type": "string", "description": "ISO datetime"},
                    "title": {"type": "string"},
                    "status": {"type": "string", "default": "confirmed"}
                },
                "required": ["contact_id", "calendar_id", "start_time", "end_time"]
            }
        },
        {
            "name": "ghl_get_calendar_slots",
            "description": "Get available calendar slots",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "calendar_id": {"type": "string"},
                    "start_date": {"type": "string"},
                    "end_date": {"type": "string"},
                    "timezone": {"type": "string", "default": "America/Chicago"}
                },
                "required": ["calendar_id", "start_date", "end_date"]
            }
        },
        {
            "name": "ghl_create_task",
            "description": "Create a task/follow-up",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "contact_id": {"type": "string"},
                    "title": {"type": "string"},
                    "description": {"type": "string"},
                    "due_date": {"type": "string"},
                    "assigned_to": {"type": "string"}
                },
                "required": ["contact_id", "title"]
            }
        },
        {
            "name": "ghl_add_note",
            "description": "Add a note to a contact",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "contact_id": {"type": "string"},
                    "note": {"type": "string"}
                },
                "required": ["contact_id", "note"]
            }
        },
        {
            "name": "ghl_create_opportunity",
            "description": "Create a sales opportunity",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "contact_id": {"type": "string"},
                    "name": {"type": "string"},
                    "pipeline_id": {"type": "string"},
                    "stage_id": {"type": "string"},
                    "value": {"type": "number"},
                    "status": {"type": "string", "default": "open"}
                },
                "required": ["contact_id", "name", "pipeline_id", "stage_id"]
            }
        },
        {
            "name": "ghl_move_opportunity",
            "description": "Move opportunity to different stage",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "opportunity_id": {"type": "string"},
                    "stage_id": {"type": "string"}
                },
                "required": ["opportunity_id", "stage_id"]
            }
        },
        {
            "name": "ghl_trigger_workflow",
            "description": "Trigger a workflow for a contact",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "contact_id": {"type": "string"},
                    "workflow_id": {"type": "string"}
                },
                "required": ["contact_id", "workflow_id"]
            }
        },
        {
            "name": "ghl_send_message",
            "description": "Send SMS/Email via GoHighLevel",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "contact_id": {"type": "string"},
                    "type": {"type": "string", "enum": ["sms", "email"]},
                    "message": {"type": "string"},
                    "subject": {"type": "string", "description": "For email only"},
                    "template_id": {"type": "string", "description": "Use template instead"}
                },
                "required": ["contact_id", "type", "message"]
            }
        },
        {
            "name": "ghl_webhook_received",
            "description": "Process incoming GHL webhook and store data",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "event_type": {"type": "string"},
                    "payload": {"type": "object"},
                    "store_in_memory": {"type": "boolean", "default": True}
                },
                "required": ["event_type", "payload"]
            }
        },

        # ============ RAILWAY ENHANCED ============
        {
            "name": "railway_create_project",
            "description": "Create a new Railway project",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "description": {"type": "string"},
                    "repo_url": {"type": "string"},
                    "is_private": {"type": "boolean", "default": True}
                },
                "required": ["name"]
            }
        },
        {
            "name": "railway_deploy",
            "description": "Deploy to Railway project",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "project_id": {"type": "string"},
                    "environment": {"type": "object"},
                    "start_command": {"type": "string"},
                    "branch": {"type": "string", "default": "main"}
                },
                "required": ["project_id"]
            }
        },
        {
            "name": "railway_set_env_vars",
            "description": "Set environment variables in Railway",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "project_id": {"type": "string"},
                    "service_id": {"type": "string"},
                    "variables": {"type": "object"}
                },
                "required": ["project_id", "variables"]
            }
        },
        {
            "name": "railway_get_logs",
            "description": "Get deployment logs from Railway",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "project_id": {"type": "string"},
                    "service_id": {"type": "string"},
                    "lines": {"type": "number", "default": 100}
                },
                "required": ["project_id"]
            }
        },
        {
            "name": "railway_restart_service",
            "description": "Restart a Railway service",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "project_id": {"type": "string"},
                    "service_id": {"type": "string"}
                },
                "required": ["project_id", "service_id"]
            }
        },
        {
            "name": "railway_add_domain",
            "description": "Add custom domain to Railway service",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "project_id": {"type": "string"},
                    "service_id": {"type": "string"},
                    "domain": {"type": "string"}
                },
                "required": ["project_id", "service_id", "domain"]
            }
        },
        {
            "name": "railway_add_postgres",
            "description": "Add PostgreSQL to Railway project",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "project_id": {"type": "string"},
                    "database_name": {"type": "string", "default": "railway"}
                },
                "required": ["project_id"]
            }
        },

        # ============ DOCKER MAXIMUM ============
        {
            "name": "docker_compose_up",
            "description": "Start Docker Compose services",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "project_path": {"type": "string"},
                    "service": {"type": "string"},
                    "detached": {"type": "boolean", "default": True},
                    "build": {"type": "boolean", "default": False}
                },
                "required": ["project_path"]
            }
        },
        {
            "name": "docker_compose_down",
            "description": "Stop Docker Compose services",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "project_path": {"type": "string"},
                    "remove_volumes": {"type": "boolean", "default": False}
                },
                "required": ["project_path"]
            }
        },
        {
            "name": "docker_build",
            "description": "Build Docker image",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "dockerfile_path": {"type": "string"},
                    "tag": {"type": "string"},
                    "no_cache": {"type": "boolean", "default": False}
                },
                "required": ["dockerfile_path", "tag"]
            }
        },
        {
            "name": "docker_logs",
            "description": "Get container logs",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "container": {"type": "string"},
                    "lines": {"type": "number", "default": 100},
                    "follow": {"type": "boolean", "default": False}
                },
                "required": ["container"]
            }
        },
        {
            "name": "docker_exec",
            "description": "Execute command in container",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "container": {"type": "string"},
                    "command": {"type": "string"},
                    "interactive": {"type": "boolean", "default": False}
                },
                "required": ["container", "command"]
            }
        },
        {
            "name": "docker_status",
            "description": "Get all container statuses",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "all": {"type": "boolean", "default": False}
                }
            }
        },
        {
            "name": "docker_restart",
            "description": "Restart container",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "container": {"type": "string"}
                },
                "required": ["container"]
            }
        },
        {
            "name": "docker_prune",
            "description": "Clean up unused Docker resources",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "volumes": {"type": "boolean", "default": False},
                    "images": {"type": "boolean", "default": False},
                    "all": {"type": "boolean", "default": False}
                }
            }
        },

        # ============ TWILIO (via GHL or Direct) ============
        {
            "name": "twilio_send_sms",
            "description": "Send SMS via Twilio (direct or through GHL)",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "to": {"type": "string"},
                    "from": {"type": "string"},
                    "body": {"type": "string"},
                    "media_url": {"type": "string"},
                    "account": {"type": "string", "description": "Which Twilio account"}
                },
                "required": ["to", "body"]
            }
        },

        # ============ MCP-SPECIFIC TOOLS ============
        {
            "name": "mcp_list_servers",
            "description": "List all available MCP servers in the system",
            "inputSchema": {
                "type": "object",
                "properties": {}
            }
        },
        {
            "name": "mcp_install_server",
            "description": "Install a new MCP server from npm or GitHub",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "package": {"type": "string", "description": "npm package or GitHub URL"},
                    "global": {"type": "boolean", "default": True}
                },
                "required": ["package"]
            }
        },
        {
            "name": "mcp_configure_server",
            "description": "Add MCP server to Claude Desktop config",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "server_name": {"type": "string"},
                    "command": {"type": "string"},
                    "args": {"type": "array", "items": {"type": "string"}},
                    "env": {"type": "object"}
                },
                "required": ["server_name", "command"]
            }
        },
        {
            "name": "mcp_restart_server",
            "description": "Restart an MCP server connection",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "server_name": {"type": "string"}
                },
                "required": ["server_name"]
            }
        },

        # ============ EXISTING CORE TOOLS ============
        {
            "name": "remember",
            "description": "Store data in PostgreSQL with metadata",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "key": {"type": "string"},
                    "value": {"type": ["string", "object", "array"]},
                    "metadata": {"type": "object"}
                },
                "required": ["key", "value"]
            }
        },
        {
            "name": "recall",
            "description": "Retrieve data from PostgreSQL",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "key": {"type": "string"}
                },
                "required": ["key"]
            }
        },
        {
            "name": "search_memory",
            "description": "Search memory with PostgreSQL full-text search",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "query": {"type": "string"},
                    "limit": {"type": "number", "default": 10}
                },
                "required": ["query"]
            }
        },
        {
            "name": "terminal_execute",
            "description": "Execute any terminal command",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "command": {"type": "string"},
                    "working_dir": {"type": "string"},
                    "timeout": {"type": "number", "default": 30}
                },
                "required": ["command"]
            }
        },
        {
            "name": "python_execute",
            "description": "Execute Python code directly",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "code": {"type": "string"},
                    "capture_output": {"type": "boolean", "default": True}
                },
                "required": ["code"]
            }
        },
        {
            "name": "deploy_brain",
            "description": "Deploy complete brain instance for a client",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "client_name": {"type": "string"},
                    "platform": {"type": "string", "enum": ["railway", "docker"]},
                    "voice_agent_prompt": {"type": "string"},
                    "ghl_location_id": {"type": "string"},
                    "retell_api_key": {"type": "string"},
                    "configure_webhooks": {"type": "boolean", "default": True}
                },
                "required": ["client_name", "platform"]
            }
        }
    ]