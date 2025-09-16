#!/usr/bin/env python3
"""
ClearVC Brain v1 - The AI Communications Hub
Handles VAPI webhooks, processes conversations, and sends professional emails.
"""

import os
import json
import smtplib
import logging
from datetime import datetime
from typing import Dict, Any, Optional
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders

from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel
import requests
from openai import OpenAI

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

app = FastAPI(
    title="ClearVC Brain",
    description="AI Communications Hub for ClearVC - Processes calls and sends insights",
    version="1.0.0"
)

class VapiWebhook(BaseModel):
    """Model for VAPI webhook payload"""
    type: str
    call_id: str
    timestamp: str
    data: Dict[str, Any]

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
        response = client.chat.completions.create(
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

def send_gmail(to_email: str, subject: str, body: str, attachment_path: Optional[str] = None):
    """Send email via Gmail SMTP"""

    try:
        gmail_user = os.getenv('GMAIL_USER')
        gmail_password = os.getenv('GMAIL_APP_PASSWORD')  # Use App Password

        msg = MIMEMultipart('alternative')
        msg['From'] = gmail_user
        msg['To'] = to_email
        msg['Subject'] = subject

        # Add HTML body
        msg.attach(MIMEText(body, 'html'))

        # Add attachment if provided
        if attachment_path and os.path.exists(attachment_path):
            with open(attachment_path, "rb") as attachment:
                part = MIMEBase('application', 'octet-stream')
                part.set_payload(attachment.read())
                encoders.encode_base64(part)
                part.add_header(
                    'Content-Disposition',
                    f'attachment; filename= {os.path.basename(attachment_path)}'
                )
                msg.attach(part)

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

def push_to_ghl(contact_data: Dict[str, Any]) -> bool:
    """Push lead data to GoHighLevel CRM"""

    try:
        ghl_api_key = os.getenv('GHL_API_KEY')
        ghl_location_id = os.getenv('GHL_LOCATION_ID')

        if not ghl_api_key or not ghl_location_id:
            logger.warning("GHL credentials not configured, skipping CRM push")
            return False

        headers = {
            'Authorization': f'Bearer {ghl_api_key}',
            'Content-Type': 'application/json'
        }

        ghl_payload = {
            "firstName": contact_data.get('first_name', ''),
            "lastName": contact_data.get('last_name', ''),
            "phone": contact_data.get('phone', ''),
            "email": contact_data.get('email', ''),
            "source": "ClearVC AI Phone System",
            "tags": ["AI Generated", f"Score-{contact_data.get('lead_score', 0)}"],
            "customFields": {
                "lead_score": str(contact_data.get('lead_score', 0)),
                "urgency_level": contact_data.get('urgency_level', 'Medium'),
                "call_transcript": contact_data.get('transcript', '')[:1000]  # Truncate if too long
            }
        }

        response = requests.post(
            f"https://services.leadconnectorhq.com/locations/{ghl_location_id}/contacts",
            headers=headers,
            json=ghl_payload,
            timeout=10
        )

        if response.status_code in [200, 201]:
            logger.info("✅ Contact pushed to GHL successfully")
            return True
        else:
            logger.error(f"❌ GHL API error: {response.status_code} - {response.text}")
            return False

    except Exception as e:
        logger.error(f"❌ Failed to push to GHL: {e}")
        return False

@app.get("/")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "ClearVC Brain v1",
        "timestamp": datetime.now().isoformat()
    }

@app.post("/vapi/webhook")
async def handle_vapi_webhook(request: Request):
    """Handle VAPI webhook - the money shot endpoint"""

    try:
        payload = await request.json()
        logger.info(f"🎯 Received VAPI webhook: {payload.get('type', 'unknown')}")

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

        # Extract AI insights
        logger.info("🧠 Analyzing call with AI...")
        insights = extract_lead_insights(transcript)

        # Create professional email
        logger.info("📧 Generating professional email...")
        email_body = create_professional_email(call_data, insights)

        # Send email to ClearVC team
        recipient_email = os.getenv('CLEARVC_EMAIL', 'adrian@clearvc.co.uk')  # Default to Adrian
        subject = f"🔥 ClearVC AI: Hot Lead Analysis - Score {insights['lead_score']}/10"

        email_sent = send_gmail(recipient_email, subject, email_body)

        # Prepare GHL data
        ghl_data = {
            'phone': call_data.get('customer', {}).get('number', ''),
            'first_name': 'ClearVC',  # We'll need to extract this from transcript later
            'last_name': 'Prospect',
            'lead_score': insights['lead_score'],
            'urgency_level': insights['urgency_level'],
            'transcript': transcript
        }

        # Push to GHL
        ghl_success = push_to_ghl(ghl_data)

        logger.info(f"✅ Call {call_id} processed - Email: {email_sent}, GHL: {ghl_success}")

        return {
            "status": "success",
            "call_id": call_id,
            "lead_score": insights['lead_score'],
            "email_sent": email_sent,
            "ghl_pushed": ghl_success,
            "processed_at": datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"❌ Error processing webhook: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/test/email")
async def test_email():
    """Test endpoint to verify email sending works"""

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
        "transcript": "This is a test call transcript. The prospect is very interested in our AI solutions and has budget available.",
        "customer": {"number": "+44 7700 123456"},
        "duration": "4:32"
    }

    email_body = create_professional_email(test_call_data, test_insights)
    recipient = os.getenv('CLEARVC_EMAIL', 'your-email@gmail.com')

    success = send_gmail(recipient, "🧪 ClearVC AI Test: System Working Perfectly", email_body)

    return {
        "test_email_sent": success,
        "recipient": recipient,
        "timestamp": datetime.now().isoformat()
    }

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)