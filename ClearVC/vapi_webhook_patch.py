#!/usr/bin/env python3
"""
VAPI webhook endpoint addition for the Brain MCP Server
This adds ClearVC-specific functionality to the existing brain
"""

# VAPI webhook functionality to add to the brain
VAPI_WEBHOOK_CODE = '''

# =============================================================================
# CLEARVC VAPI WEBHOOK FUNCTIONALITY
# =============================================================================

import smtplib
import requests
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from openai import OpenAI

# Initialize OpenAI for lead analysis
openai_client = OpenAI(api_key=os.getenv('OPENAI_API_KEY', 'sk-placeholder'))

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
        "follow_up_timing": "suggested timeframe"
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
            "follow_up_timing": "Within 48 hours"
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
        </style>
    </head>
    <body>
        <div class="header">
            <h1>🤖 ClearVC AI: Call Summary & Lead Analysis</h1>
            <p>Advanced AI-powered prospect analysis delivered instantly</p>
        </div>

        <div class="content">
            <div class="section">
                <h2>📊 Lead Score: <span class="score">{score_emoji} {insights['lead_score']}/10</span></h2>
                <p><strong>Urgency Level:</strong> <span class="urgency-{insights['urgency_level'].lower()}">{insights['urgency_level']}</span></p>
                <p><strong>Decision Maker:</strong> {insights['decision_maker']}</p>
                <p><strong>Recommended Follow-up:</strong> {insights['follow_up_timing']}</p>
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
                <h3>📋 Suggested Next Steps</h3>
                {''.join([f'<div class="insight-item">✅ {step}</div>' for step in insights['next_steps']])}
            </div>

            <div class="section">
                <h3>🏢 Company Profile</h3>
                <p><strong>Estimated Size:</strong> {insights['company_size']}</p>
                <p><strong>Current Tools:</strong> {insights['current_tools']}</p>
                <p><strong>Budget Signals:</strong> {insights['budget_signals']}</p>
            </div>

            <div class="section">
                <h3>📞 Call Details</h3>
                <p><strong>Phone Number:</strong> {caller_number}</p>
                <p><strong>Duration:</strong> {call_duration}</p>
                <p><strong>Processed:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} UTC</p>
            </div>

            <div class="section">
                <h3>📝 Full Transcript</h3>
                <div class="transcript">{transcript}</div>
            </div>
        </div>

        <div style="text-align: center; padding: 20px; color: #666; font-size: 12px;">
            <p>🚀 Powered by ClearVC AI Brain v1.0 | This analysis was generated in under 60 seconds</p>
            <p>💼 Ready to scale this across your entire client base?</p>
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

@app.post("/vapi/webhook")
async def handle_vapi_webhook(request: Request):
    """Handle VAPI webhook - the money shot endpoint for Tuesday demo"""

    try:
        payload = await request.json()
        logger.info(f"🎯 ClearVC: Received VAPI webhook: {payload.get('type', 'unknown')}")

        # Only process call ended events
        if payload.get('type') != 'call-ended':
            return {"status": "ignored", "reason": "not a call-ended event"}

        call_data = payload.get('data', {})
        call_id = payload.get('call_id', 'unknown')

        # Extract transcript
        transcript = call_data.get('transcript', '')
        if not transcript:
            logger.warning(f"No transcript found for call {call_id}")
            return {"status": "error", "reason": "no transcript"}

        # Save to brain database
        conn = sqlite3.connect(str(DB_PATH))
        cursor = conn.cursor()

        # Create clearvc_calls table if not exists
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS clearvc_calls (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                call_id TEXT UNIQUE,
                transcript TEXT,
                insights TEXT,
                created_at TEXT,
                lead_score INTEGER
            )
        """)

        # Extract AI insights
        logger.info("🧠 ClearVC: Analyzing call with AI...")
        insights = extract_lead_insights(transcript)

        # Save call data
        cursor.execute("""
            INSERT OR REPLACE INTO clearvc_calls
            (call_id, transcript, insights, created_at, lead_score)
            VALUES (?, ?, ?, ?, ?)
        """, (call_id, transcript, json.dumps(insights), datetime.now().isoformat(), insights['lead_score']))

        conn.commit()
        conn.close()

        # Create professional email
        logger.info("📧 ClearVC: Generating professional email...")
        email_body = create_professional_email(call_data, insights)

        # Send email to ClearVC team
        recipient_email = os.getenv('CLEARVC_EMAIL', 'adrian@clearvc.co.uk')
        subject = f"🔥 ClearVC AI: Hot Lead Analysis - Score {insights['lead_score']}/10"

        email_sent = send_gmail(recipient_email, subject, email_body)

        logger.info(f"✅ ClearVC: Call {call_id} processed - Email: {email_sent}, Score: {insights['lead_score']}/10")

        return {
            "status": "success",
            "call_id": call_id,
            "lead_score": insights['lead_score'],
            "email_sent": email_sent,
            "processed_at": datetime.now().isoformat(),
            "clearvc_brain": "v1.0 - TUESDAY DEMO READY"
        }

    except Exception as e:
        logger.error(f"❌ ClearVC: Error processing webhook: {e}")
        return {"status": "error", "error": str(e)}

@app.get("/clearvc/test")
async def test_clearvc_system():
    """Test endpoint for ClearVC system - use this to verify everything works"""

    test_insights = {
        "lead_score": 9,
        "key_insights": ["High interest in AI solutions", "Current manual processes causing pain", "Budget available Q4"],
        "pain_points": ["Manual data entry", "Inconsistent client follow-up"],
        "next_steps": ["Send proposal", "Schedule technical demo"],
        "urgency_level": "High",
        "company_size": "50-100 employees",
        "current_tools": ["Excel", "Basic CRM"],
        "budget_signals": "£10-20k budget mentioned",
        "decision_maker": "Yes",
        "follow_up_timing": "Within 24 hours"
    }

    test_call_data = {
        "transcript": "This is a test call transcript for ClearVC. The prospect is very interested in our AI solutions and has budget available for Q4 implementation.",
        "customer": {"number": "+44 7700 123456"},
        "duration": "4:32"
    }

    email_body = create_professional_email(test_call_data, test_insights)
    recipient = os.getenv('CLEARVC_EMAIL', 'test@clearvc.co.uk')

    success = send_gmail(recipient, "🧪 ClearVC AI Test: System Working Perfectly", email_body)

    return {
        "test_email_sent": success,
        "recipient": recipient,
        "timestamp": datetime.now().isoformat(),
        "clearvc_brain_status": "READY FOR TUESDAY DEMO"
    }

@app.get("/clearvc/calls")
async def get_clearvc_calls():
    """Get all ClearVC calls for dashboard"""

    try:
        conn = sqlite3.connect(str(DB_PATH))
        cursor = conn.cursor()

        cursor.execute("""
            SELECT call_id, lead_score, created_at, insights
            FROM clearvc_calls
            ORDER BY created_at DESC
            LIMIT 50
        """)

        calls = []
        for row in cursor.fetchall():
            call_id, lead_score, created_at, insights_json = row
            try:
                insights = json.loads(insights_json)
            except:
                insights = {}

            calls.append({
                "call_id": call_id,
                "lead_score": lead_score,
                "created_at": created_at,
                "urgency_level": insights.get('urgency_level', 'Unknown'),
                "decision_maker": insights.get('decision_maker', 'Unknown')
            })

        conn.close()

        return {
            "total_calls": len(calls),
            "calls": calls,
            "clearvc_brain": "v1.0"
        }

    except Exception as e:
        logger.error(f"Error fetching ClearVC calls: {e}")
        return {"error": str(e)}

# =============================================================================
# END CLEARVC FUNCTIONALITY
# =============================================================================

'''

print("VAPI webhook code ready to be added to the brain!")
print("This adds:")
print("- /vapi/webhook endpoint for processing calls")
print("- /clearvc/test endpoint for testing the system")
print("- /clearvc/calls endpoint for viewing call history")
print("- AI analysis with GPT-4")
print("- Professional email generation")
print("- Database storage of call data")