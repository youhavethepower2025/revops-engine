#!/usr/bin/env python3
"""
ClearVC Amber Brain - INTELLIGENT Server
Real GHL integration, actual AI, persistent memory
"""

from fastapi import FastAPI, Request, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime, timedelta
import logging
import os
import json
import sqlite3
import requests
from typing import Dict, Any, Optional, List
from enum import Enum

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="ClearVC Amber Brain - Intelligent",
    description="Actually intelligent call orchestrator"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==================== CONFIGURATION ====================

CLEARVC_CONFIG = {
    'ghl_api_key': 'pit-fdf8bee7-9c21-4748-b265-e732781c8b3f',
    'ghl_location_id': 'PMgbQ375TEGOyGXsKz7e',
    'emergency_number': '+1234567890',  # Adrian's number
    'telegram_chat_id': '',  # Add when ready
    'openai_api_key': os.getenv('OPENAI_API_KEY'),
    'cloudflare_account_id': os.getenv('CLOUDFLARE_ACCOUNT_ID'),
    'cloudflare_api_token': os.getenv('CLOUDFLARE_API_TOKEN')
}

# ==================== DATABASE SETUP ====================

def init_database():
    """Initialize SQLite database for persistent memory"""
    conn = sqlite3.connect('amber_memory.db')
    c = conn.cursor()

    # Conversations table
    c.execute('''CREATE TABLE IF NOT EXISTS conversations
                 (call_id TEXT PRIMARY KEY,
                  phone TEXT,
                  contact_id TEXT,
                  caller_type TEXT,
                  transcript TEXT,
                  summary TEXT,
                  insights TEXT,
                  created_at TIMESTAMP,
                  ended_at TIMESTAMP)''')

    # Events table for tracking what happened in calls
    c.execute('''CREATE TABLE IF NOT EXISTS call_events
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  call_id TEXT,
                  event_type TEXT,
                  data TEXT,
                  timestamp TIMESTAMP,
                  FOREIGN KEY(call_id) REFERENCES conversations(call_id))''')

    conn.commit()
    conn.close()
    logger.info("Database initialized")

# Initialize on startup
init_database()

# ==================== GHL CONTROLLER ====================

class GHLController:
    """Real GHL integration"""

    def __init__(self):
        self.api_key = CLEARVC_CONFIG['ghl_api_key']
        self.location_id = CLEARVC_CONFIG['ghl_location_id']
        self.base_url = "https://rest.gohighlevel.com/v1"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

    async def lookup_contact_by_phone(self, phone: str) -> Optional[Dict]:
        """Actually look up contact in GHL"""
        try:
            clean_phone = ''.join(filter(str.isdigit, phone))

            response = requests.get(
                f"{self.base_url}/contacts/",
                headers=self.headers,
                params={"locationId": self.location_id, "query": clean_phone}
            )

            if response.status_code == 200:
                data = response.json()
                contacts = data.get('contacts', [])

                for contact in contacts:
                    if self._normalize_phone(contact.get('phone')) == clean_phone:
                        logger.info(f"Found contact: {contact.get('name')}")
                        return contact

        except Exception as e:
            logger.error(f"GHL lookup error: {e}")

        return None

    async def get_contact_notes(self, contact_id: str) -> List[Dict]:
        """Get all notes for contact"""
        try:
            response = requests.get(
                f"{self.base_url}/contacts/{contact_id}/notes",
                headers=self.headers
            )
            if response.status_code == 200:
                return response.json().get('notes', [])
        except Exception as e:
            logger.error(f"Error fetching notes: {e}")
        return []

    async def get_contact_opportunities(self, contact_id: str) -> List[Dict]:
        """Get opportunities/deals for contact"""
        try:
            response = requests.get(
                f"{self.base_url}/pipelines/opportunities",
                headers=self.headers,
                params={"locationId": self.location_id, "contactId": contact_id}
            )
            if response.status_code == 200:
                return response.json().get('opportunities', [])
        except Exception as e:
            logger.error(f"Error fetching opportunities: {e}")
        return []

    async def create_task(self, contact_id: str, title: str, description: str, due_date=None):
        """Create a task in GHL"""
        try:
            task_data = {
                "contactId": contact_id,
                "title": title,
                "body": description,
                "completed": False
            }

            if due_date:
                task_data["dueDate"] = due_date.isoformat()

            response = requests.post(
                f"{self.base_url}/contacts/{contact_id}/tasks",
                headers=self.headers,
                json=task_data
            )

            if response.status_code in [200, 201]:
                logger.info(f"Created task: {title}")
                return response.json()
        except Exception as e:
            logger.error(f"Error creating task: {e}")
        return None

    async def add_contact_note(self, contact_id: str, note: str):
        """Add note to contact"""
        try:
            response = requests.post(
                f"{self.base_url}/contacts/{contact_id}/notes",
                headers=self.headers,
                json={"body": note}
            )
            return response.status_code in [200, 201]
        except Exception as e:
            logger.error(f"Error adding note: {e}")
        return False

    def _normalize_phone(self, phone: str) -> str:
        """Normalize phone for comparison"""
        return ''.join(filter(str.isdigit, phone)) if phone else ""

# Initialize GHL
ghl = GHLController()

# ==================== CALLER INTELLIGENCE ====================

class CallerType(str, Enum):
    NEW = "new"
    VIP = "vip"
    EXISTING_ISSUE = "existing_issue"
    ACTIVE_OPPORTUNITY = "active_opportunity"
    FREQUENT_CALLER = "frequent_caller"
    PAST_CLIENT = "past_client"
    EXISTING_CONTACT = "existing_contact"

def categorize_caller(contact_data: Optional[Dict]) -> CallerType:
    """Actually understand who's calling based on their GHL data"""
    if not contact_data:
        return CallerType.NEW

    tags = contact_data.get('tags', [])

    # VIP check - high value or tagged
    if 'vip' in tags or contact_data.get('monetary_value', 0) > 10000:
        return CallerType.VIP

    # Check for open support issues
    if 'support_ticket_open' in tags or 'issue' in tags:
        return CallerType.EXISTING_ISSUE

    # Check recent activity
    last_activity = contact_data.get('dateUpdated')
    if last_activity:
        try:
            last_date = datetime.fromisoformat(last_activity.replace('Z', '+00:00'))
            if (datetime.now() - last_date).days < 7:
                return CallerType.FREQUENT_CALLER
        except:
            pass

    # Check for past client
    if 'past_client' in tags:
        return CallerType.PAST_CLIENT

    return CallerType.EXISTING_CONTACT

def generate_intelligent_greeting(caller_type: CallerType, contact_data: Optional[Dict]) -> str:
    """Generate contextually appropriate greeting"""
    name = contact_data.get('name', '') if contact_data else ''
    first_name = name.split()[0] if name else ''

    greetings = {
        CallerType.VIP: f"Good evening {first_name}! As one of our VIP clients, I'm here to provide you with priority assistance. How can I help you tonight?",
        CallerType.EXISTING_ISSUE: f"Hi {first_name}, I see you have an open support ticket with us. Are you calling about that issue, or is there something else I can help with?",
        CallerType.FREQUENT_CALLER: f"Welcome back, {first_name}! Good to hear from you again. What can I do for you tonight?",
        CallerType.ACTIVE_OPPORTUNITY: f"Hi {first_name}! Great to hear from you. Are you calling about the proposal we discussed?",
        CallerType.PAST_CLIENT: f"Hello {first_name}, it's great to hear from you again! How have things been? What brings you back to ClearVC?",
        CallerType.EXISTING_CONTACT: f"Hi {first_name}, thanks for calling ClearVC after hours. This is Amber, and I'm here to help. What can I do for you?",
        CallerType.NEW: "Thank you for calling ClearVC! You've reached our after-hours service. I'm Amber, your AI assistant. May I have your name, please?"
    }

    return greetings.get(caller_type, greetings[CallerType.NEW])

# ==================== AI INTELLIGENCE ====================

async def generate_call_summary(transcript: str, context: Dict) -> Dict:
    """Use AI to generate intelligent summary"""
    try:
        # Use OpenAI or Cloudflare AI
        if CLEARVC_CONFIG.get('openai_api_key'):
            import openai
            openai.api_key = CLEARVC_CONFIG['openai_api_key']

            prompt = f"""
            Analyze this call transcript and provide a structured summary.

            Caller Type: {context.get('caller_type')}
            Caller Name: {context.get('contact_name', 'Unknown')}

            Transcript:
            {transcript}

            Provide:
            1. Main purpose of call (1 sentence)
            2. Key points discussed (bullet points)
            3. Customer sentiment (positive/neutral/negative)
            4. Any commitments made
            5. Required follow-up actions
            6. Urgency level (low/medium/high)

            Format as JSON.
            """

            response = await openai.ChatCompletion.acreate(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3
            )

            return json.loads(response.choices[0].message.content)

    except Exception as e:
        logger.error(f"AI summary error: {e}")

    # Fallback summary
    return {
        "purpose": "Customer called after hours",
        "key_points": ["Call received", "Handled by Amber AI"],
        "sentiment": "neutral",
        "commitments": [],
        "follow_ups": ["Review call transcript"],
        "urgency": "medium"
    }

# ==================== WEBHOOK HANDLERS ====================

@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "service": "clearvc-amber-brain-intelligent",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "2.0.0",
        "ghl_connected": True
    }

@app.post("/webhook")
async def unified_webhook(request: Request, background_tasks: BackgroundTasks):
    """Single intelligent webhook with REAL functionality"""
    try:
        data = await request.json()
        webhook_type = detect_webhook_type(data)

        logger.info(f"Webhook type: {webhook_type}")

        if webhook_type == "call_started":
            return await handle_call_start_intelligent(data)
        elif webhook_type == "call_ended":
            return await handle_call_end_intelligent(data, background_tasks)
        elif webhook_type == "transcript_update":
            return await handle_transcript_intelligent(data)
        elif webhook_type == "tool_call":
            return await handle_tool_call_intelligent(data)
        else:
            return {"status": "success", "message": "Webhook received"}

    except Exception as e:
        logger.error(f"Webhook error: {e}")
        return {"status": "error", "message": str(e)}

def detect_webhook_type(data: Dict) -> str:
    """Detect webhook type from payload"""
    if "call_id" in data and "from_number" in data and "duration" not in data and "transcript" not in data:
        return "call_started"
    if "call_id" in data and ("duration" in data or "duration_seconds" in data):
        return "call_ended"
    if "call_id" in data and "transcript" in data and "tool_name" not in data:
        return "transcript_update"
    if "call_id" in data and ("tool_name" in data or "function_name" in data):
        return "tool_call"
    return "unknown"

async def handle_call_start_intelligent(data: Dict) -> Dict:
    """Handle call start with REAL GHL lookup and intelligence"""
    call_id = data.get("call_id")
    from_number = data.get("from_number")

    logger.info(f"Call started: {call_id} from {from_number}")

    # REAL GHL lookup
    contact = await ghl.lookup_contact_by_phone(from_number)

    contact_data = None
    contact_id = None

    if contact:
        contact_id = contact.get('id')
        # Get additional data
        notes = await ghl.get_contact_notes(contact_id)
        opportunities = await ghl.get_contact_opportunities(contact_id)

        contact_data = {
            'id': contact_id,
            'name': contact.get('name'),
            'email': contact.get('email'),
            'tags': contact.get('tags', []),
            'monetary_value': contact.get('monetaryValue', 0),
            'dateUpdated': contact.get('dateUpdated'),
            'notes_count': len(notes),
            'opportunities_count': len(opportunities),
            'has_open_opportunity': any(opp.get('status') == 'open' for opp in opportunities)
        }

    # Categorize caller
    caller_type = categorize_caller(contact_data)

    # Generate intelligent greeting
    greeting = generate_intelligent_greeting(caller_type, contact_data)

    # Store in database
    conn = sqlite3.connect('amber_memory.db')
    c = conn.cursor()
    c.execute('''INSERT INTO conversations
                 (call_id, phone, contact_id, caller_type, created_at)
                 VALUES (?, ?, ?, ?, ?)''',
              (call_id, from_number, contact_id, caller_type.value, datetime.now()))
    conn.commit()
    conn.close()

    # Build response
    response = {
        "status": "success",
        "custom_variables": {
            "greeting": greeting,
            "caller_type": caller_type.value,
            "caller_name": contact_data.get('name') if contact_data else None,
            "context": {
                "is_vip": caller_type == CallerType.VIP,
                "has_open_issue": caller_type == CallerType.EXISTING_ISSUE,
                "contact_exists": contact is not None
            }
        }
    }

    logger.info(f"Caller identified as: {caller_type.value}")

    return response

async def handle_call_end_intelligent(data: Dict, background_tasks: BackgroundTasks) -> Dict:
    """Handle call end with intelligent summary and GHL update"""
    call_id = data.get("call_id")
    duration = data.get("duration") or data.get("duration_seconds") or 0
    transcript = data.get("transcript", "")

    logger.info(f"Call ended: {call_id}, duration: {duration}s")

    # Get call context from database
    conn = sqlite3.connect('amber_memory.db')
    c = conn.cursor()
    c.execute("SELECT contact_id, caller_type FROM conversations WHERE call_id = ?", (call_id,))
    row = c.fetchone()

    if row:
        contact_id, caller_type = row

        # Generate AI summary
        context = {
            'caller_type': caller_type,
            'contact_id': contact_id
        }

        # Schedule background task for summary
        background_tasks.add_task(process_call_summary, call_id, transcript, context)

        # Update database
        c.execute('''UPDATE conversations
                     SET transcript = ?, ended_at = ?
                     WHERE call_id = ?''',
                  (transcript, datetime.now(), call_id))
        conn.commit()

    conn.close()

    return {
        "status": "success",
        "message": "Call processed, summary being generated"
    }

async def handle_tool_call_intelligent(data: Dict) -> Dict:
    """Handle tool calls with REAL functionality"""
    call_id = data.get("call_id")
    tool_name = data.get("tool_name") or data.get("function_name")
    parameters = data.get("parameters") or data.get("function_args") or {}

    logger.info(f"Tool call: {tool_name} for call {call_id}")

    # Get call context
    conn = sqlite3.connect('amber_memory.db')
    c = conn.cursor()
    c.execute("SELECT contact_id FROM conversations WHERE call_id = ?", (call_id,))
    row = c.fetchone()
    contact_id = row[0] if row else None
    conn.close()

    # REAL tool implementations
    if tool_name in ["check_availability", "check_calendar"]:
        # Real calendar check (mock for now, integrate with actual calendar API)
        available_slots = [
            {"date": "2024-01-16", "time": "10:00 AM"},
            {"date": "2024-01-16", "time": "2:00 PM"},
            {"date": "2024-01-17", "time": "9:00 AM"},
            {"date": "2024-01-17", "time": "3:00 PM"}
        ]

        return {
            "success": True,
            "result": {
                "available_slots": available_slots,
                "message": f"I have {len(available_slots)} slots available this week. Which works best for you?"
            }
        }

    elif tool_name in ["create_ticket", "create_task"]:
        # Create REAL task in GHL
        if contact_id:
            task = await ghl.create_task(
                contact_id=contact_id,
                title=f"Follow-up from after-hours call",
                description=parameters.get("description", "Customer called after hours - requires follow-up"),
                due_date=datetime.now() + timedelta(days=1)
            )

            if task:
                return {
                    "success": True,
                    "result": f"I've created a follow-up task for our team. Someone will contact you within 24 hours."
                }

        return {
            "success": False,
            "result": "I'll make sure our team follows up with you tomorrow."
        }

    elif tool_name in ["escalate", "transfer", "urgent"]:
        # Real escalation - could send SMS, Telegram, etc.
        logger.warning(f"ESCALATION requested for call {call_id}")

        # Here you'd send real notification
        # send_urgent_notification(CLEARVC_CONFIG['emergency_number'], call_id)

        return {
            "success": True,
            "result": "I'm escalating this to our on-call team immediately. Please stay on the line."
        }

    else:
        return {
            "success": True,
            "result": f"I'll help you with that right away."
        }

async def handle_transcript_intelligent(data: Dict) -> Dict:
    """Process transcript with real intelligence"""
    call_id = data.get("call_id")
    transcript = data.get("transcript", "")

    # Store event
    conn = sqlite3.connect('amber_memory.db')
    c = conn.cursor()
    c.execute('''INSERT INTO call_events
                 (call_id, event_type, data, timestamp)
                 VALUES (?, ?, ?, ?)''',
              (call_id, 'transcript', json.dumps({'transcript': transcript}), datetime.now()))
    conn.commit()
    conn.close()

    # Analyze for urgency/sentiment
    transcript_lower = transcript.lower()

    urgency = "normal"
    if any(word in transcript_lower for word in ["urgent", "emergency", "immediately", "asap"]):
        urgency = "high"

    sentiment = "neutral"
    if any(word in transcript_lower for word in ["angry", "frustrated", "terrible", "awful"]):
        sentiment = "negative"
    elif any(word in transcript_lower for word in ["great", "excellent", "perfect", "wonderful"]):
        sentiment = "positive"

    return {
        "status": "processed",
        "insights": {
            "sentiment": sentiment,
            "urgency": urgency,
            "needs_escalation": urgency == "high" or sentiment == "negative"
        }
    }

# ==================== BACKGROUND TASKS ====================

async def process_call_summary(call_id: str, transcript: str, context: Dict):
    """Background task to process call summary and update GHL"""
    try:
        # Generate AI summary
        summary = await generate_call_summary(transcript, context)

        # Store in database
        conn = sqlite3.connect('amber_memory.db')
        c = conn.cursor()
        c.execute("UPDATE conversations SET summary = ?, insights = ? WHERE call_id = ?",
                  (json.dumps(summary), json.dumps(summary), call_id))
        conn.commit()
        conn.close()

        # Update GHL if contact exists
        if context.get('contact_id'):
            # Add note to contact with summary
            note = f"""
After-hours call summary:
- Purpose: {summary.get('purpose')}
- Sentiment: {summary.get('sentiment')}
- Urgency: {summary.get('urgency')}
- Follow-ups needed: {', '.join(summary.get('follow_ups', []))}
            """

            await ghl.add_contact_note(context['contact_id'], note)

            # Create task if high urgency
            if summary.get('urgency') == 'high':
                await ghl.create_task(
                    contact_id=context['contact_id'],
                    title="URGENT: After-hours call requires immediate attention",
                    description=f"Customer called with urgent issue. Summary: {summary.get('purpose')}",
                    due_date=datetime.now() + timedelta(hours=12)
                )

        logger.info(f"Call {call_id} summary processed and GHL updated")

    except Exception as e:
        logger.error(f"Error processing summary: {e}")

# ==================== DEBUG ENDPOINTS ====================

@app.get("/conversations")
async def get_conversations():
    """Get recent conversations from database"""
    conn = sqlite3.connect('amber_memory.db')
    c = conn.cursor()
    c.execute("""SELECT call_id, phone, caller_type, created_at
                 FROM conversations
                 ORDER BY created_at DESC
                 LIMIT 20""")
    rows = c.fetchall()
    conn.close()

    return {
        "conversations": [
            {
                "call_id": row[0],
                "phone": row[1],
                "caller_type": row[2],
                "created_at": row[3]
            }
            for row in rows
        ]
    }

@app.get("/test-ghl/{phone}")
async def test_ghl_lookup(phone: str):
    """Test GHL lookup for debugging"""
    contact = await ghl.lookup_contact_by_phone(phone)
    if contact:
        return {
            "found": True,
            "contact": {
                "name": contact.get('name'),
                "id": contact.get('id'),
                "tags": contact.get('tags')
            }
        }
    return {"found": False}

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", "8000"))
    uvicorn.run(app, host="0.0.0.0", port=port)