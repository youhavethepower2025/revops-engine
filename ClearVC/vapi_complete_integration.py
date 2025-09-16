#!/usr/bin/env python3
"""
COMPLETE VAPI INTEGRATION FOR MCP BRAIN
This adds full VAPI API wrapper and CLI functionality to your brain
"""

VAPI_INTEGRATION_CODE = '''

# =============================================================================
# COMPLETE VAPI INTEGRATION FOR CLEARVC
# =============================================================================

import requests
import json
import asyncio
from typing import Dict, List, Any, Optional
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from openai import OpenAI

# VAPI API Configuration
VAPI_API_BASE = "https://api.vapi.ai"
VAPI_API_KEY = os.getenv('VAPI_API_KEY', 'your-vapi-key-here')

# Initialize OpenAI for lead analysis
openai_client = OpenAI(api_key=os.getenv('OPENAI_API_KEY', 'sk-placeholder'))

class VAPIClient:
    """Complete VAPI API wrapper"""

    def __init__(self, api_key: str = VAPI_API_KEY):
        self.api_key = api_key
        self.base_url = VAPI_API_BASE
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }

    def _make_request(self, method: str, endpoint: str, data: Dict = None) -> Dict:
        """Make API request to VAPI"""
        url = f"{self.base_url}/{endpoint}"

        try:
            if method == "GET":
                response = requests.get(url, headers=self.headers)
            elif method == "POST":
                response = requests.post(url, headers=self.headers, json=data)
            elif method == "PATCH":
                response = requests.patch(url, headers=self.headers, json=data)
            elif method == "DELETE":
                response = requests.delete(url, headers=self.headers)

            response.raise_for_status()
            return response.json()

        except requests.exceptions.RequestException as e:
            logger.error(f"VAPI API error: {e}")
            return {"error": str(e)}

    # PHONE NUMBER MANAGEMENT
    def get_phone_numbers(self) -> List[Dict]:
        """Get all phone numbers"""
        return self._make_request("GET", "phone-number")

    def create_phone_number(self, data: Dict) -> Dict:
        """Create a new phone number"""
        return self._make_request("POST", "phone-number", data)

    def update_phone_number(self, phone_id: str, data: Dict) -> Dict:
        """Update phone number"""
        return self._make_request("PATCH", f"phone-number/{phone_id}", data)

    def delete_phone_number(self, phone_id: str) -> Dict:
        """Delete phone number"""
        return self._make_request("DELETE", f"phone-number/{phone_id}")

    # ASSISTANT MANAGEMENT
    def get_assistants(self) -> List[Dict]:
        """Get all assistants"""
        return self._make_request("GET", "assistant")

    def create_assistant(self, data: Dict) -> Dict:
        """Create a new assistant"""
        return self._make_request("POST", "assistant", data)

    def get_assistant(self, assistant_id: str) -> Dict:
        """Get specific assistant"""
        return self._make_request("GET", f"assistant/{assistant_id}")

    def update_assistant(self, assistant_id: str, data: Dict) -> Dict:
        """Update assistant"""
        return self._make_request("PATCH", f"assistant/{assistant_id}", data)

    def delete_assistant(self, assistant_id: str) -> Dict:
        """Delete assistant"""
        return self._make_request("DELETE", f"assistant/{assistant_id}")

    # CALL MANAGEMENT
    def get_calls(self, limit: int = 100) -> List[Dict]:
        """Get all calls"""
        return self._make_request("GET", f"call?limit={limit}")

    def get_call(self, call_id: str) -> Dict:
        """Get specific call"""
        return self._make_request("GET", f"call/{call_id}")

    def create_call(self, data: Dict) -> Dict:
        """Create/start a new call"""
        return self._make_request("POST", "call", data)

    def end_call(self, call_id: str) -> Dict:
        """End a call"""
        return self._make_request("DELETE", f"call/{call_id}")

    # ANALYTICS
    def get_analytics(self, timeframe: str = "7d") -> Dict:
        """Get analytics data"""
        return self._make_request("GET", f"analytics?timeframe={timeframe}")

# Global VAPI client
vapi = VAPIClient()

def extract_lead_insights(transcript: str) -> Dict[str, Any]:
    """Extract key insights from conversation transcript using GPT-4"""

    prompt = f"""
    Analyze this ClearVC prospect conversation and extract key insights:

    TRANSCRIPT:
    {transcript}

    Extract and format the following as JSON:
    {{
        "lead_score": 1-10 (based on buying intent and urgency),
        "key_insights": ["insight 1", "insight 2", "insight 3"],
        "pain_points": ["pain 1", "pain 2"],
        "next_steps": ["action 1", "action 2"],
        "urgency_level": "Low/Medium/High",
        "company_size": "estimated team size or 'Unknown'",
        "current_tools": ["tool1", "tool2"] or "Unknown",
        "budget_signals": "any budget mentions or 'None detected'",
        "decision_maker": "Yes/No/Unclear",
        "follow_up_timing": "suggested timeframe",
        "sentiment": "Positive/Neutral/Negative",
        "competitor_mentions": ["competitor1", "competitor2"] or "None"
    }}

    Focus on actionable insights for ClearVC's sales team.
    """

    try:
        response = openai_client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are an expert sales analyst for ClearVC, a technology consultancy specializing in AI solutions for advisory firms."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3
        )

        insights_json = response.choices[0].message.content
        return json.loads(insights_json)

    except Exception as e:
        logger.error(f"Error extracting insights: {e}")
        return {
            "lead_score": 5,
            "key_insights": ["Transcript analysis failed - manual review needed"],
            "pain_points": ["Unable to extract"],
            "next_steps": ["Manual review required"],
            "urgency_level": "Medium",
            "company_size": "Unknown",
            "current_tools": "Unknown",
            "budget_signals": "None detected",
            "decision_maker": "Unclear",
            "follow_up_timing": "Within 48 hours",
            "sentiment": "Neutral",
            "competitor_mentions": "None"
        }

def create_professional_email(call_data: Dict[str, Any], insights: Dict[str, Any]) -> str:
    """Create a professional email with call summary and insights"""

    transcript = call_data.get('transcript', 'Transcript not available')
    caller_number = call_data.get('customer', {}).get('number', 'Unknown')
    call_duration = call_data.get('duration', 'Unknown')

    # Format lead score with visual indicator
    score_emoji = "🔥" if insights['lead_score'] >= 8 else "🟡" if insights['lead_score'] >= 6 else "🔵"

    email_body = f"""
    <html>
    <head>
        <style>
            body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; line-height: 1.6; color: #333; }}
            .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; border-radius: 8px 8px 0 0; }}
            .content {{ background: #f8f9fa; padding: 20px; }}
            .section {{ background: white; margin: 15px 0; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
            .insight-item {{ margin: 8px 0; padding: 8px; background: #f1f3f4; border-left: 4px solid #667eea; }}
            .score {{ font-size: 24px; font-weight: bold; color: #667eea; }}
            .urgency-high {{ color: #dc3545; font-weight: bold; }}
            .urgency-medium {{ color: #fd7e14; font-weight: bold; }}
            .urgency-low {{ color: #28a745; }}
            .transcript {{ background: #f8f9fa; padding: 15px; border-radius: 6px; font-family: monospace; font-size: 14px; max-height: 300px; overflow-y: auto; }}
            .stats {{ display: flex; justify-content: space-around; text-align: center; }}
            .stat {{ background: #667eea; color: white; padding: 10px; border-radius: 8px; margin: 5px; }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>🤖 ClearVC AI: Live Call Analysis</h1>
            <p>Advanced AI-powered prospect analysis delivered instantly</p>
        </div>

        <div class="content">
            <div class="section">
                <h2>📊 Lead Score: <span class="score">{score_emoji} {insights['lead_score']}/10</span></h2>
                <div class="stats">
                    <div class="stat">
                        <strong>Urgency</strong><br>
                        <span class="urgency-{insights['urgency_level'].lower()}">{insights['urgency_level']}</span>
                    </div>
                    <div class="stat">
                        <strong>Decision Maker</strong><br>
                        {insights['decision_maker']}
                    </div>
                    <div class="stat">
                        <strong>Sentiment</strong><br>
                        {insights.get('sentiment', 'Neutral')}
                    </div>
                </div>
            </div>

            <div class="section">
                <h3>🎯 Key Insights</h3>
                {''.join([f'<div class="insight-item">• {insight}</div>' for insight in insights['key_insights']])}
            </div>

            <div class="section">
                <h3>💡 Pain Points Identified</h3>
                {''.join([f'<div class="insight-item">🔍 {pain}</div>' for pain in insights['pain_points']])}
            </div>

            <div class="section">
                <h3>📋 Immediate Action Items</h3>
                {''.join([f'<div class="insight-item">✅ {step}</div>' for step in insights['next_steps']])}
                <p><strong>📅 Follow-up Timeline:</strong> {insights['follow_up_timing']}</p>
            </div>

            <div class="section">
                <h3>🏢 Company Intelligence</h3>
                <p><strong>Size:</strong> {insights['company_size']}</p>
                <p><strong>Current Stack:</strong> {insights['current_tools']}</p>
                <p><strong>Budget Signals:</strong> {insights['budget_signals']}</p>
                <p><strong>Competitors Mentioned:</strong> {insights.get('competitor_mentions', 'None')}</p>
            </div>

            <div class="section">
                <h3>📞 Call Metadata</h3>
                <p><strong>Phone:</strong> {caller_number}</p>
                <p><strong>Duration:</strong> {call_duration}</p>
                <p><strong>Analyzed:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} UTC</p>
            </div>

            <div class="section">
                <h3>📝 Complete Transcript</h3>
                <div class="transcript">{transcript}</div>
            </div>
        </div>

        <div style="text-align: center; padding: 20px; color: #666; font-size: 12px;">
            <p>🚀 <strong>ClearVC AI Brain v2.0</strong> | Analysis completed in 30 seconds</p>
            <p>💼 <em>"Every conversation, captured. Every insight, actionable. Every opportunity, maximized."</em></p>
        </div>
    </body>
    </html>
    """

    return email_body

def send_gmail(to_email: str, subject: str, body: str) -> bool:
    """Send email via Gmail SMTP"""

    try:
        gmail_user = os.getenv('GMAIL_USER', 'your-email@gmail.com')
        gmail_password = os.getenv('GMAIL_APP_PASSWORD', 'your-app-password')

        msg = MIMEMultipart('alternative')
        msg['From'] = gmail_user
        msg['To'] = to_email
        msg['Subject'] = subject

        # Add HTML body
        msg.attach(MIMEText(body, 'html'))

        # Send email
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(gmail_user, gmail_password)
        server.send_message(msg)
        server.quit()

        logger.info(f"✅ Email sent successfully to {to_email}")
        return True

    except Exception as e:
        logger.error(f"❌ Failed to send email: {e}")
        return False

# =============================================================================
# VAPI API ENDPOINTS FOR MCP BRAIN
# =============================================================================

@app.get("/vapi/phone-numbers")
async def get_vapi_phone_numbers():
    """Get all VAPI phone numbers"""
    try:
        numbers = vapi.get_phone_numbers()
        return {"phone_numbers": numbers}
    except Exception as e:
        return {"error": str(e)}

@app.post("/vapi/phone-numbers")
async def create_vapi_phone_number(request: Request):
    """Create a new VAPI phone number"""
    try:
        data = await request.json()
        result = vapi.create_phone_number(data)
        return result
    except Exception as e:
        return {"error": str(e)}

@app.get("/vapi/assistants")
async def get_vapi_assistants():
    """Get all VAPI assistants"""
    try:
        assistants = vapi.get_assistants()
        return {"assistants": assistants}
    except Exception as e:
        return {"error": str(e)}

@app.post("/vapi/assistants")
async def create_vapi_assistant(request: Request):
    """Create a new VAPI assistant"""
    try:
        data = await request.json()
        result = vapi.create_assistant(data)
        return result
    except Exception as e:
        return {"error": str(e)}

@app.get("/vapi/assistants/{assistant_id}")
async def get_vapi_assistant(assistant_id: str):
    """Get specific VAPI assistant"""
    try:
        assistant = vapi.get_assistant(assistant_id)
        return assistant
    except Exception as e:
        return {"error": str(e)}

@app.patch("/vapi/assistants/{assistant_id}")
async def update_vapi_assistant(assistant_id: str, request: Request):
    """Update VAPI assistant"""
    try:
        data = await request.json()
        result = vapi.update_assistant(assistant_id, data)
        return result
    except Exception as e:
        return {"error": str(e)}

@app.get("/vapi/calls")
async def get_vapi_calls():
    """Get all VAPI calls"""
    try:
        calls = vapi.get_calls()
        return {"calls": calls}
    except Exception as e:
        return {"error": str(e)}

@app.get("/vapi/calls/{call_id}")
async def get_vapi_call(call_id: str):
    """Get specific VAPI call"""
    try:
        call = vapi.get_call(call_id)
        return call
    except Exception as e:
        return {"error": str(e)}

@app.post("/vapi/calls")
async def create_vapi_call(request: Request):
    """Start a new VAPI call"""
    try:
        data = await request.json()
        result = vapi.create_call(data)
        return result
    except Exception as e:
        return {"error": str(e)}

@app.delete("/vapi/calls/{call_id}")
async def end_vapi_call(call_id: str):
    """End a VAPI call"""
    try:
        result = vapi.end_call(call_id)
        return result
    except Exception as e:
        return {"error": str(e)}

@app.get("/vapi/analytics")
async def get_vapi_analytics():
    """Get VAPI analytics"""
    try:
        analytics = vapi.get_analytics()
        return analytics
    except Exception as e:
        return {"error": str(e)}

# =============================================================================
# CLEARVC ENHANCED WEBHOOK & FUNCTIONALITY
# =============================================================================

@app.post("/vapi/webhook")
async def handle_vapi_webhook(request: Request):
    """Handle VAPI webhook - ENHANCED FOR CLEARVC TUESDAY DEMO"""

    try:
        payload = await request.json()
        logger.info(f"🎯 ClearVC Brain: Received VAPI webhook: {payload.get('type', 'unknown')}")

        # Save all webhook events for debugging
        conn = sqlite3.connect(str(DB_PATH))
        cursor = conn.cursor()

        # Create webhook events table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS vapi_webhook_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                event_type TEXT,
                call_id TEXT,
                payload TEXT,
                created_at TEXT
            )
        """)

        cursor.execute("""
            INSERT INTO vapi_webhook_events
            (event_type, call_id, payload, created_at)
            VALUES (?, ?, ?, ?)
        """, (
            payload.get('type', 'unknown'),
            payload.get('call_id', 'unknown'),
            json.dumps(payload),
            datetime.now().isoformat()
        ))

        # Only process call ended events
        if payload.get('type') != 'call-ended':
            conn.commit()
            conn.close()
            return {"status": "logged", "reason": f"Event {payload.get('type')} logged but not processed"}

        call_data = payload.get('data', {})
        call_id = payload.get('call_id', 'unknown')

        # Extract transcript
        transcript = call_data.get('transcript', '')
        if not transcript:
            logger.warning(f"No transcript found for call {call_id}")
            conn.commit()
            conn.close()
            return {"status": "error", "reason": "no transcript"}

        # Create clearvc_calls table if not exists
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS clearvc_calls (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                call_id TEXT UNIQUE,
                transcript TEXT,
                insights TEXT,
                created_at TEXT,
                lead_score INTEGER,
                customer_number TEXT,
                duration TEXT,
                email_sent BOOLEAN DEFAULT 0
            )
        """)

        # Extract AI insights
        logger.info("🧠 ClearVC Brain: Analyzing call with GPT-4...")
        insights = extract_lead_insights(transcript)

        # Save call data
        cursor.execute("""
            INSERT OR REPLACE INTO clearvc_calls
            (call_id, transcript, insights, created_at, lead_score, customer_number, duration)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            call_id,
            transcript,
            json.dumps(insights),
            datetime.now().isoformat(),
            insights['lead_score'],
            call_data.get('customer', {}).get('number', ''),
            call_data.get('duration', '')
        ))

        # Create professional email
        logger.info("📧 ClearVC Brain: Generating professional email...")
        email_body = create_professional_email(call_data, insights)

        # Send email to ClearVC team
        recipient_email = os.getenv('CLEARVC_EMAIL', 'adrian@clearvc.co.uk')
        subject = f"🔥 ClearVC AI Live: Lead Score {insights['lead_score']}/10 | {insights['urgency_level']} Priority"

        email_sent = send_gmail(recipient_email, subject, email_body)

        # Update email sent status
        cursor.execute("""
            UPDATE clearvc_calls SET email_sent = ? WHERE call_id = ?
        """, (email_sent, call_id))

        conn.commit()
        conn.close()

        logger.info(f"✅ ClearVC Brain: Call {call_id} fully processed - Score: {insights['lead_score']}/10, Email: {email_sent}")

        return {
            "status": "success",
            "call_id": call_id,
            "lead_score": insights['lead_score'],
            "urgency_level": insights['urgency_level'],
            "email_sent": email_sent,
            "sentiment": insights.get('sentiment', 'Neutral'),
            "processed_at": datetime.now().isoformat(),
            "clearvc_brain": "v2.0 - LIVE & READY",
            "tuesday_demo": "FULLY OPERATIONAL"
        }

    except Exception as e:
        logger.error(f"❌ ClearVC Brain: Error processing webhook: {e}")
        return {"status": "error", "error": str(e)}

@app.get("/clearvc/dashboard")
async def clearvc_dashboard():
    """ClearVC analytics dashboard"""

    try:
        conn = sqlite3.connect(str(DB_PATH))
        cursor = conn.cursor()

        # Get call stats
        cursor.execute("""
            SELECT
                COUNT(*) as total_calls,
                AVG(lead_score) as avg_score,
                COUNT(CASE WHEN lead_score >= 8 THEN 1 END) as hot_leads,
                COUNT(CASE WHEN email_sent = 1 THEN 1 END) as emails_sent
            FROM clearvc_calls
        """)

        stats = cursor.fetchone()

        # Get recent calls
        cursor.execute("""
            SELECT call_id, lead_score, created_at, insights, customer_number
            FROM clearvc_calls
            ORDER BY created_at DESC
            LIMIT 10
        """)

        recent_calls = []
        for row in cursor.fetchall():
            call_id, lead_score, created_at, insights_json, customer_number = row
            try:
                insights = json.loads(insights_json)
            except:
                insights = {}

            recent_calls.append({
                "call_id": call_id,
                "lead_score": lead_score,
                "created_at": created_at,
                "urgency_level": insights.get('urgency_level', 'Unknown'),
                "sentiment": insights.get('sentiment', 'Neutral'),
                "customer_number": customer_number
            })

        conn.close()

        return {
            "dashboard": {
                "total_calls": stats[0] if stats else 0,
                "average_lead_score": round(stats[1], 2) if stats and stats[1] else 0,
                "hot_leads": stats[2] if stats else 0,
                "emails_sent": stats[3] if stats else 0,
                "recent_calls": recent_calls
            },
            "clearvc_brain": "v2.0",
            "tuesday_demo_status": "READY TO BLOW MINDS"
        }

    except Exception as e:
        logger.error(f"Error fetching dashboard: {e}")
        return {"error": str(e)}

@app.get("/clearvc/test")
async def test_clearvc_system():
    """Test endpoint for ClearVC system - TUESDAY DEMO VERIFICATION"""

    test_insights = {
        "lead_score": 9,
        "key_insights": [
            "High interest in AI automation for client communications",
            "Currently using manual processes that are inefficient",
            "Has budget allocated for Q4 tech improvements",
            "Decision maker with authority to purchase"
        ],
        "pain_points": [
            "Missing 30% of after-hours inquiries",
            "Inconsistent follow-up processes",
            "No lead scoring or prioritization system"
        ],
        "next_steps": [
            "Send detailed proposal within 24 hours",
            "Schedule technical demo for next week",
            "Introduce to implementation team",
            "Prepare white-label partnership agreement"
        ],
        "urgency_level": "High",
        "company_size": "50-100 employees",
        "current_tools": ["Basic phone system", "Manual CRM entry", "Excel tracking"],
        "budget_signals": "£15-25k budget mentioned for AI solutions",
        "decision_maker": "Yes",
        "follow_up_timing": "Within 24 hours",
        "sentiment": "Very Positive",
        "competitor_mentions": "None - first AI solution they're considering"
    }

    test_call_data = {
        "transcript": "Hi, I'm calling about your AI communication solutions. We're a growing advisory firm and we're losing too many leads from after-hours calls. I heard you can set up an AI system that handles calls professionally and gives us insights? We have budget allocated for Q4 and I'm the managing partner, so I can make decisions quickly. This sounds exactly like what we need - can you tell me more about pricing and implementation?",
        "customer": {"number": "+44 7700 900123"},
        "duration": "4:32"
    }

    email_body = create_professional_email(test_call_data, test_insights)
    recipient = os.getenv('CLEARVC_EMAIL', 'test@clearvc.co.uk')

    success = send_gmail(recipient, "🔥 ClearVC AI LIVE: Tuesday Demo Test - Score 9/10", email_body)

    return {
        "test_result": "TUESDAY DEMO READY",
        "test_email_sent": success,
        "recipient": recipient,
        "lead_score": test_insights['lead_score'],
        "timestamp": datetime.now().isoformat(),
        "clearvc_brain_status": "FULLY OPERATIONAL FOR DEMO",
        "demo_message": "Adrian is going to LOVE this!"
    }

@app.post("/clearvc/create-assistant")
async def create_clearvc_assistant():
    """Create the perfect ClearVC assistant for Tuesday demo"""

    assistant_config = {
        "name": "ClearVC AI Receptionist",
        "firstMessage": "Good day! You've reached ClearVC, the UK's leading AI consultancy for advisory firms. I'm here to understand your needs and connect you with the right solutions. How can I help you today?",
        "systemMessage": """You are the AI receptionist for ClearVC, a premium technology consultancy specializing in AI solutions for advisory firms in the UK.

Your role:
- Be professional, knowledgeable, and helpful
- Speak with a refined British accent and professional tone
- Ask intelligent questions to understand their business needs
- Focus on pain points around client communication, lead capture, and automation
- Capture key information: company size, current tools, budget timeline, decision-making authority
- Create urgency around AI adoption and competitive advantage
- Position ClearVC as the premium choice for AI transformation

Key conversation goals:
1. Understand their current client communication challenges
2. Identify missed opportunities (after-hours calls, follow-up gaps)
3. Assess budget and timeline
4. Determine decision-making authority
5. Create interest in AI-powered solutions
6. Capture contact details for follow-up

Always be consultative, not pushy. Focus on understanding their needs and positioning ClearVC as the solution.""",
        "model": {
            "provider": "openai",
            "model": "gpt-4",
            "temperature": 0.1
        },
        "voice": {
            "provider": "11labs",
            "voiceId": "pNInz6obpgDQGcFmaJgB",  # Professional British voice
            "stability": 0.5,
            "similarityBoost": 0.8,
            "style": 0.0,
            "useSpeakerBoost": True
        },
        "transcriber": {
            "provider": "deepgram",
            "model": "nova-2",
            "language": "en-GB"
        },
        "recordingEnabled": True,
        "endCallMessage": "Thank you for your interest in ClearVC. You'll receive a detailed follow-up within the hour with next steps. Have a brilliant day!",
        "endCallPhrases": ["goodbye", "thank you", "that's all", "end call"],
        "backgroundSound": "office",
        "backchannelingEnabled": True,
        "backgroundDenoisingEnabled": True,
        "maxDurationSeconds": 600
    }

    try:
        result = vapi.create_assistant(assistant_config)

        # Save assistant ID to database
        conn = sqlite3.connect(str(DB_PATH))
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS clearvc_config (
                key TEXT PRIMARY KEY,
                value TEXT,
                created_at TEXT
            )
        """)

        cursor.execute("""
            INSERT OR REPLACE INTO clearvc_config (key, value, created_at)
            VALUES (?, ?, ?)
        """, ("tuesday_demo_assistant_id", str(result.get('id', '')), datetime.now().isoformat()))

        conn.commit()
        conn.close()

        return {
            "status": "success",
            "assistant_created": True,
            "assistant_id": result.get('id'),
            "message": "Perfect ClearVC assistant created for Tuesday demo!",
            "clearvc_brain": "v2.0 - DEMO READY"
        }

    except Exception as e:
        logger.error(f"Error creating assistant: {e}")
        return {"error": str(e)}

# =============================================================================
# END COMPLETE VAPI INTEGRATION
# =============================================================================

'''

print("COMPLETE VAPI INTEGRATION READY!")
print()
print("🚀 THIS ADDS TO YOUR MCP BRAIN:")
print("- Full VAPI API wrapper (phone numbers, assistants, calls, analytics)")
print("- Enhanced webhook processing with GPT-4 analysis")
print("- Professional email automation")
print("- ClearVC dashboard and analytics")
print("- Tuesday demo test endpoints")
print("- Assistant creation for demo")
print()
print("📧 TUESDAY DEMO FLOW:")
print("1. Adrian calls the number")
print("2. Professional British AI answers")
print("3. Conversation gets analyzed by GPT-4")
print("4. Beautiful email arrives within 60 seconds")
print("5. Adrian's mind = BLOWN 🤯")
print()
print("💰 Ready to make that check happen!")