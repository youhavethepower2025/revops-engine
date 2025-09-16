# AGENT.FORGE ONBOARDING ENGINE
# The Great Journey - From Recruitment to Deployment
#
# From Medellín with love and game theory

import uuid
import asyncio
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum
import asyncpg
from datetime import datetime
import json
import secrets
import re

class OnboardingStage(Enum):
    """The stages of the great journey"""
    WELCOME = "welcome"
    COMPANY_DETAILS = "company_details"
    AGENT_PERSONALITY = "agent_personality"
    KNOWLEDGE_BASE = "knowledge_base"
    WIDGET_CUSTOMIZATION = "widget_customization"
    DEPLOYMENT = "deployment"
    COMPLETED = "completed"

@dataclass
class OnboardingProgress:
    """Progress tracking for the journey"""
    client_id: str
    current_stage: OnboardingStage
    completed_stages: List[OnboardingStage]
    data_collected: Dict[str, Any]
    next_action: str
    completion_percentage: int

class OnboardingEngine:
    """
    The Onboarding Engine of Agent.Forge
    
    Game Theory Optimal Client Acquisition:
    - Minimize time to value
    - Maximize setup success rate
    - Eliminate decision paralysis through guided flow
    - Automate widget generation and deployment
    
    From chaos to deployed intelligence in 7 steps.
    """
    
    def __init__(self, db_pool: asyncpg.Pool):
        self.db = db_pool
        self.stage_configs = self._initialize_stage_configs()
        self.knowledge_templates = self._initialize_knowledge_templates()
    
    def _initialize_stage_configs(self) -> Dict[OnboardingStage, Dict[str, Any]]:
        """Configuration for each onboarding stage"""
        return {
            OnboardingStage.WELCOME: {
                "title": "Welcome to Agent.Forge",
                "description": "Let's deploy your first intelligent agent",
                "fields": [],
                "next_stage": OnboardingStage.COMPANY_DETAILS,
                "auto_advance": True
            },
            OnboardingStage.COMPANY_DETAILS: {
                "title": "Company Information",
                "description": "Tell us about your business",
                "fields": [
                    {"name": "company_name", "type": "text", "required": True, "label": "Company Name"},
                    {"name": "website_url", "type": "url", "required": False, "label": "Website URL"},
                    {"name": "industry", "type": "select", "required": False, "label": "Industry",
                     "options": ["Technology", "Healthcare", "Finance", "E-commerce", "Education", "Other"]},
                    {"name": "company_size", "type": "select", "required": False, "label": "Company Size",
                     "options": ["1-10", "11-50", "51-200", "201-1000", "1000+"]}
                ],
                "next_stage": OnboardingStage.AGENT_PERSONALITY
            },
            OnboardingStage.AGENT_PERSONALITY: {
                "title": "Agent Personality",
                "description": "Design your agent's communication style",
                "fields": [
                    {"name": "agent_name", "type": "text", "required": True, "label": "Agent Name"},
                    {"name": "tone", "type": "select", "required": True, "label": "Communication Tone",
                     "options": ["Professional", "Friendly", "Casual", "Enthusiastic", "Helpful"]},
                    {"name": "personality_traits", "type": "multiselect", "required": False, "label": "Personality Traits",
                     "options": ["Knowledgeable", "Patient", "Quick", "Detailed", "Concise", "Empathetic"]},
                    {"name": "greeting_style", "type": "textarea", "required": False, "label": "Custom Greeting (Optional)"}
                ],
                "next_stage": OnboardingStage.KNOWLEDGE_BASE
            },
            OnboardingStage.KNOWLEDGE_BASE: {
                "title": "Knowledge Base Setup",
                "description": "What should your agent know about?",
                "fields": [
                    {"name": "business_description", "type": "textarea", "required": True, 
                     "label": "Business Description"},
                    {"name": "key_products", "type": "textarea", "required": False, 
                     "label": "Key Products/Services"},
                    {"name": "pricing_info", "type": "textarea", "required": False, 
                     "label": "Pricing Information"},
                    {"name": "support_info", "type": "textarea", "required": False, 
                     "label": "Support & Contact Information"},
                    {"name": "faqs", "type": "textarea", "required": False, 
                     "label": "Common Questions & Answers"}
                ],
                "next_stage": OnboardingStage.WIDGET_CUSTOMIZATION
            },
            OnboardingStage.WIDGET_CUSTOMIZATION: {
                "title": "Widget Customization",
                "description": "Customize your chat widget appearance",
                "fields": [
                    {"name": "widget_position", "type": "select", "required": True, "label": "Widget Position",
                     "options": ["bottom-right", "bottom-left", "top-right", "top-left"]},
                    {"name": "primary_color", "type": "color", "required": False, "label": "Primary Color", 
                     "default": "#007bff"},
                    {"name": "widget_text", "type": "text", "required": False, "label": "Widget Button Text", 
                     "default": "Chat with us"},
                    {"name": "welcome_message", "type": "text", "required": False, "label": "Welcome Message"}
                ],
                "next_stage": OnboardingStage.DEPLOYMENT
            },
            OnboardingStage.DEPLOYMENT: {
                "title": "Deployment Instructions",
                "description": "Get your widget code and go live",
                "fields": [],
                "next_stage": OnboardingStage.COMPLETED,
                "auto_advance": False
            }
        }
    
    def _initialize_knowledge_templates(self) -> Dict[str, str]:
        """Pre-built knowledge entry templates"""
        return {
            "business_description": {
                "title": "About Our Company",
                "intent_type": "general",
                "priority": 10
            },
            "key_products": {
                "title": "Our Products and Services",
                "intent_type": "product_inquiry",
                "priority": 9
            },
            "pricing_info": {
                "title": "Pricing Information",
                "intent_type": "pricing",
                "priority": 8
            },
            "support_info": {
                "title": "Support and Contact",
                "intent_type": "support",
                "priority": 7
            },
            "faqs": {
                "title": "Frequently Asked Questions",
                "intent_type": "general",
                "priority": 6
            }
        }
    
    async def start_onboarding(self, team_id: str, user_id: str) -> OnboardingProgress:
        """Start a new onboarding journey"""
        
        client_id = str(uuid.uuid4())
        
        async with self.db.acquire() as conn:
            # Create initial client record
            await conn.execute(
                """
                INSERT INTO clients (id, team_id, name, widget_id, active, created_at)
                VALUES ($1, $2, 'New Client', $3, false, $4)
                """,
                client_id, team_id, f"widget_{secrets.token_urlsafe(8)}", datetime.utcnow()
            )
            
            # Create onboarding progress record
            await conn.execute(
                """
                INSERT INTO onboarding_progress 
                (client_id, current_stage, completed_stages, data_collected, created_at, updated_at)
                VALUES ($1, $2, $3, $4, $5, $5)
                """,
                client_id, OnboardingStage.WELCOME.value, json.dumps([]),
                json.dumps({}), datetime.utcnow()
            )
        
        return await self.get_progress(client_id)
    
    async def get_progress(self, client_id: str) -> OnboardingProgress:
        """Get current onboarding progress"""
        
        async with self.db.acquire() as conn:
            progress = await conn.fetchrow(
                """
                SELECT current_stage, completed_stages, data_collected
                FROM onboarding_progress
                WHERE client_id = $1
                """,
                client_id
            )
            
            if not progress:
                raise ValueError(f"No onboarding progress found for client {client_id}")
            
            current_stage = OnboardingStage(progress['current_stage'])
            completed_stages = [
                OnboardingStage(stage) for stage in json.loads(progress['completed_stages'])
            ]
            data_collected = json.loads(progress['data_collected'])
            
            # Calculate completion percentage
            total_stages = len(OnboardingStage) - 1  # Exclude COMPLETED
            completion_percentage = int((len(completed_stages) / total_stages) * 100)
            
            # Determine next action
            stage_config = self.stage_configs[current_stage]
            if current_stage == OnboardingStage.COMPLETED:
                next_action = "Onboarding completed"
            else:
                next_action = stage_config.get("description", "Continue setup")
        
        return OnboardingProgress(
            client_id=client_id,
            current_stage=current_stage,
            completed_stages=completed_stages,
            data_collected=data_collected,
            next_action=next_action,
            completion_percentage=completion_percentage
        )
    
    async def submit_stage_data(
        self, 
        client_id: str, 
        stage_data: Dict[str, Any]
    ) -> OnboardingProgress:
        """Submit data for current stage and advance"""
        
        progress = await self.get_progress(client_id)
        current_stage = progress.current_stage
        
        # Validate stage data
        self._validate_stage_data(current_stage, stage_data)
        
        async with self.db.acquire() as conn:
            # Update collected data
            updated_data = {**progress.data_collected, **stage_data}
            
            # Mark current stage as completed
            completed_stages = progress.completed_stages + [current_stage]
            
            # Determine next stage
            next_stage = self.stage_configs[current_stage]["next_stage"]
            
            # Update progress
            await conn.execute(
                """
                UPDATE onboarding_progress 
                SET current_stage = $1, completed_stages = $2, data_collected = $3, updated_at = $4
                WHERE client_id = $5
                """,
                next_stage.value, 
                json.dumps([stage.value for stage in completed_stages]),
                json.dumps(updated_data),
                datetime.utcnow(),
                client_id
            )
            
            # Handle stage-specific processing
            await self._process_stage_completion(client_id, current_stage, stage_data, conn)
        
        return await self.get_progress(client_id)
    
    def _validate_stage_data(self, stage: OnboardingStage, data: Dict[str, Any]):
        """Validate submitted data for a stage"""
        stage_config = self.stage_configs[stage]
        
        for field in stage_config.get("fields", []):
            field_name = field["name"]
            
            if field["required"] and not data.get(field_name):
                raise ValueError(f"Required field '{field_name}' is missing")
            
            if field["type"] == "email" and data.get(field_name):
                email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
                if not re.match(email_pattern, data[field_name]):
                    raise ValueError(f"Invalid email format for '{field_name}'")
            
            if field["type"] == "url" and data.get(field_name):
                url_pattern = r'^https?://[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}.*$'
                if not re.match(url_pattern, data[field_name]):
                    raise ValueError(f"Invalid URL format for '{field_name}'")
    
    async def _process_stage_completion(
        self, 
        client_id: str, 
        completed_stage: OnboardingStage, 
        stage_data: Dict[str, Any],
        conn: asyncpg.Connection
    ):
        """Handle stage-specific processing after completion"""
        
        if completed_stage == OnboardingStage.COMPANY_DETAILS:
            await self._process_company_details(client_id, stage_data, conn)
        
        elif completed_stage == OnboardingStage.AGENT_PERSONALITY:
            await self._process_agent_personality(client_id, stage_data, conn)
        
        elif completed_stage == OnboardingStage.KNOWLEDGE_BASE:
            await self._process_knowledge_base(client_id, stage_data, conn)
        
        elif completed_stage == OnboardingStage.WIDGET_CUSTOMIZATION:
            await self._process_widget_customization(client_id, stage_data, conn)
        
        elif completed_stage == OnboardingStage.DEPLOYMENT:
            await self._process_deployment(client_id, stage_data, conn)
    
    async def _process_company_details(
        self, 
        client_id: str, 
        data: Dict[str, Any], 
        conn: asyncpg.Connection
    ):
        """Process company details stage"""
        # Update client with company information
        await conn.execute(
            """
            UPDATE clients 
            SET name = $1, website_url = $2, industry = $3, company_size = $4, updated_at = $5
            WHERE id = $6
            """,
            data.get('company_name', 'Unnamed Company'),
            data.get('website_url'),
            data.get('industry'),
            data.get('company_size'),
            datetime.utcnow(),
            client_id
        )
    
    async def _process_agent_personality(
        self, 
        client_id: str, 
        data: Dict[str, Any], 
        conn: asyncpg.Connection
    ):
        """Process agent personality stage"""
        # Create agent with personality
        agent_id = str(uuid.uuid4())
        
        personality_traits = data.get('personality_traits', [])
        if isinstance(personality_traits, list):
            personality_desc = f"A {data.get('tone', 'professional')} agent with traits: {', '.join(personality_traits)}"
        else:
            personality_desc = f"A {data.get('tone', 'professional')} agent"
        
        instructions = self._generate_agent_instructions(data)
        
        await conn.execute(
            """
            INSERT INTO agents (id, client_id, name, personality, instructions, 
                               model, temperature, max_tokens, active, created_at)
            VALUES ($1, $2, $3, $4, $5, 'gpt-3.5-turbo', 0.7, 500, true, $6)
            """,
            agent_id, client_id, data.get('agent_name', 'Assistant'),
            personality_desc, instructions, datetime.utcnow()
        )
    
    def _generate_agent_instructions(self, data: Dict[str, Any]) -> str:
        """Generate agent instructions based on personality data"""
        tone = data.get('tone', 'professional').lower()
        traits = data.get('personality_traits', [])
        greeting = data.get('greeting_style', '')
        
        instructions = f"You are a {tone} AI assistant. "
        
        if traits:
            trait_instructions = {
                'knowledgeable': "Provide detailed, well-informed responses.",
                'patient': "Take time to explain things clearly.",
                'quick': "Keep responses concise and to the point.",
                'detailed': "Provide comprehensive explanations.",
                'concise': "Be brief and direct in your responses.",
                'empathetic': "Show understanding and care for user concerns."
            }
            
            trait_text = " ".join([
                trait_instructions.get(trait.lower(), f"Be {trait.lower()}.")
                for trait in traits
            ])
            instructions += trait_text
        
        if greeting:
            instructions += f" Use this greeting style: {greeting}"
        
        instructions += " Always be helpful and represent the company professionally."
        
        return instructions
    
    async def _process_knowledge_base(
        self, 
        client_id: str, 
        data: Dict[str, Any], 
        conn: asyncpg.Connection
    ):
        """Process knowledge base setup"""
        for field_name, content in data.items():
            if content and field_name in self.knowledge_templates:
                template = self.knowledge_templates[field_name]
                
                # Extract keywords from content
                keywords = self._extract_keywords(content)
                
                knowledge_id = str(uuid.uuid4())
                await conn.execute(
                    """
                    INSERT INTO knowledge_entries (id, client_id, title, content, content_type,
                                                  intent_type, keywords, priority, active, created_at)
                    VALUES ($1, $2, $3, $4, 'text', $5, $6, $7, true, $8)
                    """,
                    knowledge_id, client_id, template["title"], content,
                    template["intent_type"], keywords, template["priority"], datetime.utcnow()
                )
    
    def _extract_keywords(self, content: str) -> str:
        """Extract keywords from content for intent matching"""
        # Simple keyword extraction - can be enhanced
        words = re.findall(r'\b[a-zA-Z]{3,}\b', content.lower())
        
        # Remove common words
        stop_words = {'the', 'and', 'for', 'are', 'but', 'not', 'you', 'all', 'can', 'had', 'her', 'was', 'one', 'our', 'out', 'day', 'get', 'has', 'him', 'his', 'how', 'man', 'new', 'now', 'old', 'see', 'two', 'who', 'boy', 'did', 'its', 'let', 'put', 'say', 'she', 'too', 'use'}
        
        keywords = [word for word in set(words) if word not in stop_words]
        
        # Return top 10 keywords
        return ', '.join(keywords[:10])
    
    async def _process_widget_customization(
        self, 
        client_id: str, 
        data: Dict[str, Any], 
        conn: asyncpg.Connection
    ):
        """Process widget customization"""
        # Store widget configuration
        widget_config = {
            'position': data.get('widget_position', 'bottom-right'),
            'primary_color': data.get('primary_color', '#007bff'),
            'widget_text': data.get('widget_text', 'Chat with us'),
            'welcome_message': data.get('welcome_message', 'Hello! How can I help you today?')
        }
        
        await conn.execute(
            """
            UPDATE clients 
            SET widget_config = $1, updated_at = $2
            WHERE id = $3
            """,
            json.dumps(widget_config), datetime.utcnow(), client_id
        )
    
    async def _process_deployment(
        self, 
        client_id: str, 
        data: Dict[str, Any], 
        conn: asyncpg.Connection
    ):
        """Process deployment stage - activate client"""
        await conn.execute(
            """
            UPDATE clients 
            SET active = true, deployed_at = $1, updated_at = $1
            WHERE id = $2
            """,
            datetime.utcnow(), client_id
        )
    
    async def generate_widget_code(self, client_id: str) -> Dict[str, str]:
        """Generate widget implementation code"""
        async with self.db.acquire() as conn:
            client = await conn.fetchrow(
                "SELECT widget_id, widget_config FROM clients WHERE id = $1",
                client_id
            )
            
            if not client:
                raise ValueError(f"Client {client_id} not found")
            
            widget_config = json.loads(client['widget_config'] or '{}')
            widget_id = client['widget_id']
            
            # Generate embed code
            embed_code = f'''
<!-- Agent.Forge Widget - Add this to your website -->
<script>
  window.AgentForgeConfig = {{
    widgetId: '{widget_id}',
    position: '{widget_config.get("position", "bottom-right")}',
    primaryColor: '{widget_config.get("primary_color", "#007bff")}',
    widgetText: '{widget_config.get("widget_text", "Chat with us")}',
    welcomeMessage: '{widget_config.get("welcome_message", "Hello! How can I help you today?")}',
    apiUrl: 'https://api.agent.forge'
  }};
</script>
<script src="https://cdn.agent.forge/widget.js" async></script>
'''
            
            # Generate test HTML page
            test_page = f'''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Widget Test Page</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            margin: 40px;
            line-height: 1.6;
        }}
        .container {{
            max-width: 800px;
            margin: 0 auto;
        }}
        .widget-info {{
            background: #f4f4f4;
            padding: 20px;
            border-radius: 5px;
            margin: 20px 0;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>Agent.Forge Widget Test</h1>
        <p>This is a test page to verify your widget is working correctly.</p>
        
        <div class="widget-info">
            <h3>Widget Configuration:</h3>
            <ul>
                <li><strong>Position:</strong> {widget_config.get("position", "bottom-right")}</li>
                <li><strong>Button Text:</strong> {widget_config.get("widget_text", "Chat with us")}</li>
                <li><strong>Welcome Message:</strong> {widget_config.get("welcome_message", "Hello!")}</li>
            </ul>
        </div>
        
        <p>The chat widget should appear in the {widget_config.get("position", "bottom-right")} corner of your screen.</p>
    </div>
    
    {embed_code}
</body>
</html>
'''
            
            return {
                "widget_id": widget_id,
                "embed_code": embed_code.strip(),
                "test_page": test_page.strip(),
                "widget_url": f"https://cdn.agent.forge/widget.js?id={widget_id}",
                "configuration": widget_config
            }
    
    async def get_onboarding_stats(self, team_id: str) -> Dict[str, Any]:
        """Get onboarding statistics for a team"""
        async with self.db.acquire() as conn:
            stats = await conn.fetchrow(
                """
                SELECT 
                    COUNT(*) as total_onboardings,
                    COUNT(CASE WHEN current_stage = 'completed' THEN 1 END) as completed,
                    COUNT(CASE WHEN current_stage != 'completed' THEN 1 END) as in_progress,
                    AVG(CASE WHEN current_stage = 'completed' THEN 
                        EXTRACT(EPOCH FROM (updated_at - created_at))/3600 
                    END) as avg_completion_hours
                FROM onboarding_progress op
                JOIN clients c ON op.client_id = c.id
                WHERE c.team_id = $1
                """,
                team_id
            )
            
            stage_distribution = await conn.fetch(
                """
                SELECT current_stage, COUNT(*) as count
                FROM onboarding_progress op
                JOIN clients c ON op.client_id = c.id
                WHERE c.team_id = $1
                GROUP BY current_stage
                """,
                team_id
            )
            
            return {
                "total_onboardings": stats['total_onboardings'] or 0,
                "completed": stats['completed'] or 0,
                "in_progress": stats['in_progress'] or 0,
                "completion_rate": (stats['completed'] / stats['total_onboardings'] * 100) if stats['total_onboardings'] else 0,
                "avg_completion_hours": round(stats['avg_completion_hours'] or 0, 2),
                "stage_distribution": {
                    row['current_stage']: row['count'] 
                    for row in stage_distribution
                }
            }

# The Onboarding Engine Factory
async def create_onboarding_engine(db_pool: asyncpg.Pool) -> OnboardingEngine:
    """Create and initialize the onboarding engine"""
    return OnboardingEngine(db_pool)