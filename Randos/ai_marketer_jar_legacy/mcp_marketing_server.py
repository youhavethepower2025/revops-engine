#!/usr/bin/env python3
"""
AI MARKETER JAR - MCP Server
Secure marketing tools interface with no system access
"""

import asyncio
import json
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime

from mcp.server import Server
from mcp.server.stdio import stdio_server
import mcp.types as types

from brain import MarketingBrain
from controllers.ghl_controller import GHLController
from controllers.google_ads_controller import GoogleAdsController
from controllers.facebook_ads_controller import FacebookAdsController
from controllers.twilio_controller import TwilioController


class MarketingMCPServer:
    """MCP Server that only exposes marketing tools - no system access"""
    
    def __init__(self):
        self.server = Server("ai-marketer-jar")
        
        # Initialize the brain and controllers
        self.brain = MarketingBrain(data_dir="./data")
        self.ghl = GHLController(self.brain)
        self.google_ads = GoogleAdsController(self.brain)
        self.facebook_ads = FacebookAdsController(self.brain)
        self.twilio = TwilioController(self.brain)
        
        # Initialize all controllers
        self.ghl.initialize()
        self.google_ads.initialize()
        self.facebook_ads.initialize()
        self.twilio.initialize()
        
        self.setup_handlers()
    
    def setup_handlers(self):
        """Setup MCP protocol handlers - ONLY marketing tools"""
        
        @self.server.list_tools()
        async def list_tools() -> List[types.Tool]:
            return [
                # Credential Management (write-only to L3)
                types.Tool(
                    name="setup_credentials",
                    description="Setup API credentials for a marketing platform (GoHighLevel, Google Ads, Facebook Ads, or Twilio)",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "platform": {
                                "type": "string",
                                "enum": ["gohighlevel", "google_ads", "facebook_ads", "twilio"]
                            },
                            "credentials": {
                                "type": "object",
                                "description": "Platform-specific credentials object"
                            }
                        },
                        "required": ["platform", "credentials"]
                    }
                ),
                
                # Natural Language Marketing Commands
                types.Tool(
                    name="marketing_command",
                    description="Execute natural language marketing commands across all platforms",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "platform": {
                                "type": "string",
                                "enum": ["gohighlevel", "google_ads", "facebook_ads", "twilio", "auto"]
                            },
                            "command": {
                                "type": "string",
                                "description": "Natural language command (e.g., 'Create campaign with $100 budget')"
                            }
                        },
                        "required": ["command"]
                    }
                ),
                
                # Campaign Management
                types.Tool(
                    name="create_campaign",
                    description="Create a marketing campaign on any platform",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "platform": {
                                "type": "string",
                                "enum": ["gohighlevel", "google_ads", "facebook_ads", "twilio"]
                            },
                            "campaign_name": {"type": "string"},
                            "budget": {"type": "number"},
                            "settings": {"type": "object"}
                        },
                        "required": ["platform", "campaign_name"]
                    }
                ),
                
                types.Tool(
                    name="list_campaigns",
                    description="List campaigns from a platform or all platforms",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "platform": {
                                "type": "string",
                                "enum": ["gohighlevel", "google_ads", "facebook_ads", "twilio", "all"]
                            }
                        }
                    }
                ),
                
                # SMS Operations
                types.Tool(
                    name="send_sms",
                    description="Send SMS message via Twilio",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "to": {"type": "string"},
                            "message": {"type": "string"}
                        },
                        "required": ["to", "message"]
                    }
                ),
                
                types.Tool(
                    name="broadcast_sms",
                    description="Send SMS to multiple recipients",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "recipients": {
                                "type": "array",
                                "items": {"type": "string"}
                            },
                            "message": {"type": "string"}
                        },
                        "required": ["recipients", "message"]
                    }
                ),
                
                # Analytics and Metrics
                types.Tool(
                    name="get_metrics",
                    description="Get performance metrics from marketing platforms",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "platform": {
                                "type": "string",
                                "enum": ["gohighlevel", "google_ads", "facebook_ads", "twilio", "all"]
                            },
                            "days": {
                                "type": "number",
                                "default": 7
                            }
                        }
                    }
                ),
                
                # Contact Management
                types.Tool(
                    name="manage_contacts",
                    description="Add, remove, or list marketing contacts",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "action": {
                                "type": "string",
                                "enum": ["add", "remove", "list"]
                            },
                            "platform": {
                                "type": "string",
                                "enum": ["gohighlevel", "twilio"]
                            },
                            "contact_data": {"type": "object"}
                        },
                        "required": ["action", "platform"]
                    }
                ),
                
                # Memory Statistics (read-only, no credential access)
                types.Tool(
                    name="get_memory_stats",
                    description="Get statistics about memory usage (no credential access)",
                    inputSchema={
                        "type": "object",
                        "properties": {}
                    }
                ),
                
                # Campaign History
                types.Tool(
                    name="get_campaign_history",
                    description="Get campaign history from memory",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "platform": {"type": "string"},
                            "limit": {
                                "type": "number",
                                "default": 10
                            }
                        }
                    }
                ),
                
                # ============ SPECTRUM BRAIN TOOLS ============
                # Memory Operations
                types.Tool(
                    name="brain_store_memory",
                    description="Store data in the brain's persistent memory with tags for retrieval",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "key": {"type": "string"},
                            "content": {"type": "string"},
                            "tags": {
                                "type": "array",
                                "items": {"type": "string"}
                            }
                        },
                        "required": ["key", "content"]
                    }
                ),
                
                types.Tool(
                    name="brain_retrieve_memory",
                    description="Retrieve specific memory by key",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "key": {"type": "string"}
                        },
                        "required": ["key"]
                    }
                ),
                
                types.Tool(
                    name="brain_search_memories",
                    description="Search memories by tags or content",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "tags": {
                                "type": "array",
                                "items": {"type": "string"}
                            },
                            "content_search": {"type": "string"},
                            "limit": {"type": "number", "default": 10}
                        }
                    }
                ),
                
                types.Tool(
                    name="brain_list_memories",
                    description="List all stored memories with their metadata",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "limit": {"type": "number", "default": 20}
                        }
                    }
                ),
                
                # Execution Tools
                types.Tool(
                    name="brain_run_terminal",
                    description="Execute terminal commands with full system access",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "command": {"type": "string"},
                            "working_dir": {"type": "string"}
                        },
                        "required": ["command"]
                    }
                ),
                
                types.Tool(
                    name="brain_run_python",
                    description="Execute Python code with access to all libraries",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "code": {"type": "string"},
                            "variables": {"type": "object"}
                        },
                        "required": ["code"]
                    }
                ),
                
                # File Operations
                types.Tool(
                    name="brain_read_file",
                    description="Read file contents from filesystem",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "file_path": {"type": "string"}
                        },
                        "required": ["file_path"]
                    }
                ),
                
                types.Tool(
                    name="brain_write_file",
                    description="Write content to file on filesystem",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "file_path": {"type": "string"},
                            "content": {"type": "string"}
                        },
                        "required": ["file_path", "content"]
                    }
                ),
                
                types.Tool(
                    name="brain_list_directory",
                    description="List contents of a directory",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "directory_path": {"type": "string"}
                        },
                        "required": ["directory_path"]
                    }
                ),
                
                # Process Management
                types.Tool(
                    name="brain_manage_process",
                    description="Start, stop, or monitor system processes",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "action": {
                                "type": "string",
                                "enum": ["start", "stop", "status", "list"]
                            },
                            "process_name": {"type": "string"},
                            "command": {"type": "string"}
                        },
                        "required": ["action"]
                    }
                ),
                
                # The CRITICAL tool - Self-modification via Aider
                types.Tool(
                    name="brain_aider_architect", 
                    description="Use Aider AI to modify your own code architecture and capabilities",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "modification_request": {"type": "string"},
                            "target_files": {
                                "type": "array",
                                "items": {"type": "string"}
                            },
                            "model": {
                                "type": "string",
                                "default": "@cf/qwen/qwen2.5-32b-instruct"
                            }
                        },
                        "required": ["modification_request"]
                    }
                )
            ]
        
        @self.server.call_tool()
        async def call_tool(name: str, arguments: Dict[str, Any]) -> List[types.TextContent]:
            try:
                result = await self.handle_tool(name, arguments)
                return [types.TextContent(type="text", text=json.dumps(result, indent=2))]
            except Exception as e:
                return [types.TextContent(type="text", text=json.dumps({
                    "status": "error",
                    "message": str(e)
                }, indent=2))]
    
    async def handle_tool(self, name: str, args: Dict[str, Any]) -> Any:
        """Route tool calls to appropriate handlers - NO SYSTEM ACCESS"""
        
        if name == "setup_credentials":
            return await self.setup_credentials(args["platform"], args["credentials"])
        
        elif name == "marketing_command":
            platform = args.get("platform", "auto")
            command = args["command"]
            return await self.execute_marketing_command(platform, command)
        
        elif name == "create_campaign":
            return await self.create_campaign(
                args["platform"],
                args["campaign_name"],
                args.get("budget"),
                args.get("settings", {})
            )
        
        elif name == "list_campaigns":
            platform = args.get("platform", "all")
            return await self.list_campaigns(platform)
        
        elif name == "send_sms":
            return await self.send_sms(args["to"], args["message"])
        
        elif name == "broadcast_sms":
            return await self.broadcast_sms(args["recipients"], args["message"])
        
        elif name == "get_metrics":
            platform = args.get("platform", "all")
            days = args.get("days", 7)
            return await self.get_metrics(platform, days)
        
        elif name == "manage_contacts":
            return await self.manage_contacts(
                args["action"],
                args["platform"],
                args.get("contact_data", {})
            )
        
        elif name == "get_memory_stats":
            return self.brain.get_memory_stats()
        
        elif name == "get_campaign_history":
            return self.brain.get_campaign_history(
                args.get("platform"),
                args.get("limit", 10)
            )
        
        # ============ BRAIN TOOL HANDLERS ============
        elif name == "brain_store_memory":
            return await self.brain_store_memory(args["key"], args["content"], args.get("tags", []))
            
        elif name == "brain_retrieve_memory":
            return await self.brain_retrieve_memory(args["key"])
            
        elif name == "brain_search_memories":
            return await self.brain_search_memories(
                args.get("tags"), 
                args.get("content_search"), 
                args.get("limit", 10)
            )
            
        elif name == "brain_list_memories":
            return await self.brain_list_memories(args.get("limit", 20))
            
        elif name == "brain_run_terminal":
            return await self.brain_run_terminal(args["command"], args.get("working_dir"))
            
        elif name == "brain_run_python":
            return await self.brain_run_python(args["code"], args.get("variables", {}))
            
        elif name == "brain_read_file":
            return await self.brain_read_file(args["file_path"])
            
        elif name == "brain_write_file":
            return await self.brain_write_file(args["file_path"], args["content"])
            
        elif name == "brain_list_directory":
            return await self.brain_list_directory(args["directory_path"])
            
        elif name == "brain_manage_process":
            return await self.brain_manage_process(
                args["action"], 
                args.get("process_name"), 
                args.get("command")
            )
            
        elif name == "brain_aider_architect":
            return await self.brain_aider_architect(
                args["modification_request"],
                args.get("target_files", []),
                args.get("model", "@cf/qwen/qwen2.5-32b-instruct")
            )
        
        else:
            raise ValueError(f"Unknown tool: {name}")
    
    async def setup_credentials(self, platform: str, credentials: Dict) -> Dict:
        """Setup credentials for a marketing platform"""
        
        if platform == "gohighlevel":
            return self.ghl.setup_credentials(
                credentials.get("api_key"),
                credentials.get("location_id")
            )
        
        elif platform == "google_ads":
            return self.google_ads.setup_credentials(
                credentials.get("developer_token"),
                credentials.get("client_id"),
                credentials.get("client_secret"),
                credentials.get("refresh_token"),
                credentials.get("customer_id"),
                credentials.get("login_customer_id")
            )
        
        elif platform == "facebook_ads":
            return self.facebook_ads.setup_credentials(
                credentials.get("access_token"),
                credentials.get("ad_account_id"),
                credentials.get("app_id"),
                credentials.get("app_secret")
            )
        
        elif platform == "twilio":
            return self.twilio.setup_credentials(
                credentials.get("account_sid"),
                credentials.get("auth_token"),
                credentials.get("from_number"),
                credentials.get("messaging_service_sid")
            )
        
        else:
            return {"status": "error", "message": f"Unknown platform: {platform}"}
    
    async def execute_marketing_command(self, platform: str, command: str) -> Dict:
        """Execute natural language marketing command"""
        
        # Auto-detect platform from command if not specified
        if platform == "auto":
            command_lower = command.lower()
            if "ghl" in command_lower or "gohighlevel" in command_lower or "pipeline" in command_lower:
                platform = "gohighlevel"
            elif "google" in command_lower or "adwords" in command_lower:
                platform = "google_ads"
            elif "facebook" in command_lower or "instagram" in command_lower or "fb" in command_lower:
                platform = "facebook_ads"
            elif "sms" in command_lower or "text" in command_lower or "twilio" in command_lower:
                platform = "twilio"
            else:
                # Default to GHL for CRM operations
                platform = "gohighlevel"
        
        # Route to appropriate controller
        if platform == "gohighlevel":
            return self.ghl.natural_language_command(command)
        elif platform == "google_ads":
            return self.google_ads.natural_language_command(command)
        elif platform == "facebook_ads":
            return self.facebook_ads.natural_language_command(command)
        elif platform == "twilio":
            return self.twilio.natural_language_command(command)
        else:
            return {"status": "error", "message": f"Unknown platform: {platform}"}
    
    async def create_campaign(self, platform: str, name: str, budget: Optional[float], settings: Dict) -> Dict:
        """Create a campaign on specified platform"""
        
        campaign_data = {
            "name": name,
            "budget": budget,
            **settings
        }
        
        if platform == "gohighlevel":
            return self.ghl.create_campaign(name, settings)
        elif platform == "google_ads":
            campaign_data["daily_budget"] = budget or 100
            return self.google_ads.create_campaign(campaign_data)
        elif platform == "facebook_ads":
            campaign_data["daily_budget"] = budget or 50
            return self.facebook_ads.create_campaign(campaign_data)
        elif platform == "twilio":
            return self.twilio.create_campaign(name, settings)
        else:
            return {"status": "error", "message": f"Unknown platform: {platform}"}
    
    async def list_campaigns(self, platform: str) -> Dict:
        """List campaigns from specified platform(s)"""
        
        if platform == "all":
            all_campaigns = []
            
            # Get campaigns from each platform
            for p, controller in [
                ("gohighlevel", self.ghl),
                ("google_ads", self.google_ads),
                ("facebook_ads", self.facebook_ads),
                ("twilio", self.twilio)
            ]:
                try:
                    result = controller.list_campaigns()
                    if result.get("status") == "success":
                        campaigns = result.get("campaigns", [])
                        for c in campaigns:
                            c["platform"] = p
                        all_campaigns.extend(campaigns)
                except:
                    pass
            
            return {
                "status": "success",
                "count": len(all_campaigns),
                "campaigns": all_campaigns
            }
        
        else:
            if platform == "gohighlevel":
                return self.ghl.list_campaigns()
            elif platform == "google_ads":
                return self.google_ads.list_campaigns()
            elif platform == "facebook_ads":
                return self.facebook_ads.list_campaigns()
            elif platform == "twilio":
                return self.twilio.list_campaigns()
            else:
                return {"status": "error", "message": f"Unknown platform: {platform}"}
    
    async def send_sms(self, to: str, message: str) -> Dict:
        """Send SMS via Twilio"""
        return self.twilio.send_sms(to, message)
    
    async def broadcast_sms(self, recipients: List[str], message: str) -> Dict:
        """Broadcast SMS to multiple recipients"""
        return self.twilio.broadcast_sms(recipients, message)
    
    async def get_metrics(self, platform: str, days: int) -> Dict:
        """Get metrics from specified platform(s)"""
        
        if platform == "all":
            all_metrics = {}
            
            # Get metrics from each platform
            for p, controller in [
                ("gohighlevel", self.ghl),
                ("google_ads", self.google_ads),
                ("facebook_ads", self.facebook_ads),
                ("twilio", self.twilio)
            ]:
                try:
                    if p == "gohighlevel":
                        result = controller.get_analytics()
                    elif p == "google_ads":
                        result = controller.get_performance_metrics(days)
                    elif p == "facebook_ads":
                        result = controller.get_campaign_metrics(days)
                    elif p == "twilio":
                        result = controller.get_campaign_metrics()
                    
                    if result.get("status") == "success":
                        all_metrics[p] = result.get("metrics", {})
                except:
                    all_metrics[p] = {"error": "Not configured"}
            
            return {
                "status": "success",
                "metrics": all_metrics
            }
        
        else:
            if platform == "gohighlevel":
                return self.ghl.get_analytics()
            elif platform == "google_ads":
                return self.google_ads.get_performance_metrics(days)
            elif platform == "facebook_ads":
                return self.facebook_ads.get_campaign_metrics(days)
            elif platform == "twilio":
                return self.twilio.get_campaign_metrics()
            else:
                return {"status": "error", "message": f"Unknown platform: {platform}"}
    
    async def manage_contacts(self, action: str, platform: str, contact_data: Dict) -> Dict:
        """Manage contacts on specified platform"""
        
        if platform == "gohighlevel":
            if action == "add":
                return self.ghl.create_contact(contact_data)
            elif action == "list":
                return self.ghl.list_contacts()
            else:
                return {"status": "error", "message": f"Action {action} not supported for GHL"}
        
        elif platform == "twilio":
            if action == "add":
                return self.twilio.add_contact(
                    contact_data.get("phone_number"),
                    contact_data.get("list_name", "default")
                )
            elif action == "remove":
                return self.twilio.remove_contact(contact_data.get("phone_number"))
            elif action == "list":
                return {"status": "info", "message": "Use list_campaigns to see contact lists"}
            else:
                return {"status": "error", "message": f"Unknown action: {action}"}
        
        else:
            return {"status": "error", "message": f"Contact management not supported for {platform}"}
    
    # ============ BRAIN TOOL IMPLEMENTATIONS ============
    async def brain_store_memory(self, key: str, content: str, tags: List[str] = None) -> Dict:
        """Store data in brain's persistent memory"""
        import json
        import os
        from datetime import datetime
        
        # Use the existing L2 memory for brain storage
        cursor = self.brain.l2_conn.cursor()
        
        # Create a brain memories table if it doesn't exist
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS brain_memories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                key TEXT UNIQUE NOT NULL,
                content TEXT NOT NULL,
                tags TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        cursor.execute("""
            INSERT OR REPLACE INTO brain_memories (key, content, tags, updated_at)
            VALUES (?, ?, ?, ?)
        """, (key, content, json.dumps(tags or []), datetime.now().isoformat()))
        
        self.brain.l2_conn.commit()
        return {"status": "success", "key": key, "tags": tags}
    
    async def brain_retrieve_memory(self, key: str) -> Dict:
        """Retrieve specific memory by key"""
        import json
        
        cursor = self.brain.l2_conn.cursor()
        cursor.execute("SELECT content, tags, created_at FROM brain_memories WHERE key = ?", (key,))
        row = cursor.fetchone()
        
        if row:
            return {
                "key": key,
                "content": row["content"],
                "tags": json.loads(row["tags"]),
                "created_at": row["created_at"]
            }
        else:
            return {"status": "not_found", "key": key}
    
    async def brain_search_memories(self, tags: List[str] = None, content_search: str = None, limit: int = 10) -> Dict:
        """Search memories by tags or content"""
        import json
        
        cursor = self.brain.l2_conn.cursor()
        
        query = "SELECT key, content, tags, created_at FROM brain_memories WHERE 1=1"
        params = []
        
        if tags:
            # Search for any of the provided tags
            tag_conditions = " OR ".join(["tags LIKE ?" for _ in tags])
            query += f" AND ({tag_conditions})"
            params.extend([f'%"{tag}"%' for tag in tags])
        
        if content_search:
            query += " AND content LIKE ?"
            params.append(f"%{content_search}%")
        
        query += " ORDER BY updated_at DESC LIMIT ?"
        params.append(limit)
        
        cursor.execute(query, params)
        memories = []
        
        for row in cursor.fetchall():
            memories.append({
                "key": row["key"],
                "content": row["content"],
                "tags": json.loads(row["tags"]),
                "created_at": row["created_at"]
            })
        
        return {"memories": memories, "count": len(memories)}
    
    async def brain_list_memories(self, limit: int = 20) -> Dict:
        """List all stored memories"""
        import json
        
        cursor = self.brain.l2_conn.cursor()
        cursor.execute("""
            SELECT key, content, tags, created_at 
            FROM brain_memories 
            ORDER BY updated_at DESC 
            LIMIT ?
        """, (limit,))
        
        memories = []
        for row in cursor.fetchall():
            memories.append({
                "key": row["key"],
                "content": row["content"][:200] + "..." if len(row["content"]) > 200 else row["content"],
                "tags": json.loads(row["tags"]),
                "created_at": row["created_at"]
            })
        
        return {"memories": memories, "total": len(memories)}
    
    async def brain_run_terminal(self, command: str, working_dir: str = None) -> Dict:
        """Execute terminal command"""
        import subprocess
        import os
        
        try:
            # Set working directory
            if working_dir:
                original_dir = os.getcwd()
                os.chdir(working_dir)
            
            # Execute command
            result = subprocess.run(
                command, 
                shell=True, 
                capture_output=True, 
                text=True, 
                timeout=60
            )
            
            # Restore directory
            if working_dir:
                os.chdir(original_dir)
            
            return {
                "status": "success",
                "stdout": result.stdout,
                "stderr": result.stderr,
                "return_code": result.returncode,
                "command": command
            }
            
        except subprocess.TimeoutExpired:
            return {"status": "error", "message": "Command timed out"}
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    async def brain_run_python(self, code: str, variables: Dict = None) -> Dict:
        """Execute Python code"""
        import sys
        from io import StringIO
        
        try:
            # Capture stdout
            old_stdout = sys.stdout
            sys.stdout = StringIO()
            
            # Create execution namespace
            namespace = {"__builtins__": __builtins__}
            if variables:
                namespace.update(variables)
            
            # Execute code
            exec(code, namespace)
            
            # Get output
            output = sys.stdout.getvalue()
            sys.stdout = old_stdout
            
            # Return results (excluding builtins)
            result_vars = {k: v for k, v in namespace.items() if not k.startswith('__')}
            
            return {
                "status": "success",
                "output": output,
                "variables": str(result_vars),
                "code": code
            }
            
        except Exception as e:
            sys.stdout = old_stdout
            return {"status": "error", "message": str(e), "code": code}
    
    async def brain_read_file(self, file_path: str) -> Dict:
        """Read file contents"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            return {
                "status": "success",
                "file_path": file_path,
                "content": content,
                "size": len(content)
            }
            
        except Exception as e:
            return {"status": "error", "message": str(e), "file_path": file_path}
    
    async def brain_write_file(self, file_path: str, content: str) -> Dict:
        """Write content to file"""
        try:
            import os
            
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            return {
                "status": "success",
                "file_path": file_path,
                "bytes_written": len(content.encode('utf-8'))
            }
            
        except Exception as e:
            return {"status": "error", "message": str(e), "file_path": file_path}
    
    async def brain_list_directory(self, directory_path: str) -> Dict:
        """List directory contents"""
        try:
            import os
            
            items = []
            for item in os.listdir(directory_path):
                item_path = os.path.join(directory_path, item)
                items.append({
                    "name": item,
                    "is_file": os.path.isfile(item_path),
                    "is_directory": os.path.isdir(item_path),
                    "size": os.path.getsize(item_path) if os.path.isfile(item_path) else None
                })
            
            return {
                "status": "success",
                "directory": directory_path,
                "items": items,
                "count": len(items)
            }
            
        except Exception as e:
            return {"status": "error", "message": str(e), "directory": directory_path}
    
    async def brain_manage_process(self, action: str, process_name: str = None, command: str = None) -> Dict:
        """Manage system processes"""
        import subprocess
        import psutil
        
        try:
            if action == "list":
                processes = []
                for proc in psutil.process_iter(['pid', 'name', 'status']):
                    try:
                        processes.append(proc.info)
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        pass
                
                return {"status": "success", "processes": processes[:20]}  # Limit to 20
            
            elif action == "start" and command:
                proc = subprocess.Popen(command, shell=True)
                return {"status": "success", "pid": proc.pid, "command": command}
            
            elif action == "status" and process_name:
                matching_procs = []
                for proc in psutil.process_iter(['pid', 'name', 'status']):
                    try:
                        if process_name.lower() in proc.info['name'].lower():
                            matching_procs.append(proc.info)
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        pass
                
                return {"status": "success", "processes": matching_procs}
            
            else:
                return {"status": "error", "message": f"Invalid action or missing parameters"}
                
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    async def brain_aider_architect(self, modification_request: str, target_files: List[str] = None, model: str = "@cf/qwen/qwen2.5-32b-instruct") -> Dict:
        """Use Aider to modify code architecture - THE CRITICAL SELF-MODIFICATION TOOL"""
        import subprocess
        import os
        
        try:
            # Set up Cloudflare AI endpoint for Aider
            env = os.environ.copy()
            
            # Get Cloudflare credentials from brain's L3 storage
            cf_creds = self.brain.retrieve_credential("cloudflare")
            if not cf_creds:
                return {"status": "error", "message": "Cloudflare credentials not found. Store them first with setup_credentials."}
            
            # Configure Aider for Cloudflare Workers AI
            env["OPENAI_API_KEY"] = cf_creds["api_token"]
            env["OPENAI_BASE_URL"] = f"https://api.cloudflare.com/client/v4/accounts/{cf_creds['account_id']}/ai/v1"
            
            # Build aider command
            cmd = ["aider", "--model", model, "--message", modification_request]
            
            if target_files:
                cmd.extend(target_files)
            else:
                # Default to current directory
                cmd.append(".")
            
            # Execute Aider
            result = subprocess.run(
                cmd,
                cwd=os.path.dirname(os.path.abspath(__file__)),
                capture_output=True,
                text=True,
                env=env,
                timeout=300  # 5 minute timeout
            )
            
            # Store the modification in brain memory
            await self.brain_store_memory(
                f"aider_modification_{datetime.now().isoformat()}",
                f"Request: {modification_request}\nResult: {result.stdout}\nErrors: {result.stderr}",
                ["self-modification", "aider", "evolution"]
            )
            
            return {
                "status": "success" if result.returncode == 0 else "error",
                "modification_request": modification_request,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "return_code": result.returncode,
                "model_used": model,
                "files_modified": target_files or ["auto-detected"]
            }
            
        except subprocess.TimeoutExpired:
            return {"status": "error", "message": "Aider modification timed out"}
        except Exception as e:
            return {"status": "error", "message": f"Aider error: {str(e)}"}
    
    async def run(self):
        """Run the MCP server"""
        async with stdio_server() as (read_stream, write_stream):
            await self.server.run(read_stream, write_stream, None)


async def main():
    """Main entry point"""
    server = MarketingMCPServer()
    await server.run()


if __name__ == "__main__":
    asyncio.run(main())