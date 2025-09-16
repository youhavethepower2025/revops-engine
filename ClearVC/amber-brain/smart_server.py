#!/usr/bin/env python3
"""
ClearVC Amber Brain - Smart Single Endpoint
One webhook to rule them all
"""

from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
import logging
import os
from typing import Dict, Any

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="ClearVC Amber Brain",
    description="Intelligent call orchestrator with unified webhook"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Store conversations in memory
conversations = {}

@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "service": "clearvc-amber-brain",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0"
    }

@app.post("/webhook")
async def unified_webhook(request: Request):
    """
    Single intelligent webhook endpoint
    Automatically detects and routes based on payload content
    """
    try:
        data = await request.json()

        # Detect webhook type from payload structure
        webhook_type = detect_webhook_type(data)

        logger.info(f"Detected webhook type: {webhook_type}")
        logger.info(f"Payload keys: {data.keys()}")

        # Route to appropriate handler
        if webhook_type == "call_started":
            return handle_call_start(data)
        elif webhook_type == "call_ended":
            return handle_call_end(data)
        elif webhook_type == "transcript_update":
            return handle_transcript(data)
        elif webhook_type == "tool_call":
            return handle_tool_call(data)
        else:
            logger.warning(f"Unknown webhook type. Data: {data}")
            # Default response that won't break Retell
            return {
                "status": "success",
                "message": "Webhook received"
            }

    except Exception as e:
        logger.error(f"Webhook error: {e}")
        return {
            "status": "error",
            "message": str(e)
        }

def detect_webhook_type(data: Dict[str, Any]) -> str:
    """
    Intelligently detect webhook type from payload structure
    """
    # Check for specific fields that indicate webhook type

    # Call started usually has: call_id, from_number, agent_id, and no duration
    if "call_id" in data and "from_number" in data and "duration" not in data and "transcript" not in data:
        return "call_started"

    # Call ended has: call_id, duration, end_reason
    if "call_id" in data and ("duration" in data or "duration_seconds" in data or "end_reason" in data):
        return "call_ended"

    # Transcript update has: call_id, transcript (and maybe speaker)
    if "call_id" in data and "transcript" in data and "tool_name" not in data:
        return "transcript_update"

    # Tool/function call has: call_id, tool_name or function_name
    if "call_id" in data and ("tool_name" in data or "function_name" in data):
        return "tool_call"

    # Check for other patterns
    if "event_type" in data:
        return data["event_type"]

    if "type" in data:
        return data["type"]

    return "unknown"

def handle_call_start(data: Dict[str, Any]) -> Dict[str, Any]:
    """Handle call start event"""
    call_id = data.get("call_id")
    from_number = data.get("from_number")

    logger.info(f"Call started: {call_id} from {from_number}")

    # Store conversation
    conversations[call_id] = {
        "phone": from_number,
        "started": datetime.utcnow().isoformat(),
        "events": [],
        "agent_id": data.get("agent_id")
    }

    # Return Retell-compatible response
    return {
        "status": "success",
        "custom_variables": {
            "greeting": "Thank you for calling ClearVC! This is Amber, your after-hours assistant. How can I help you tonight?",
            "caller_type": "new",
            "context": {
                "business_hours": False,
                "service": "after_hours"
            }
        }
    }

def handle_call_end(data: Dict[str, Any]) -> Dict[str, Any]:
    """Handle call end event"""
    call_id = data.get("call_id")
    duration = data.get("duration") or data.get("duration_seconds") or 0

    logger.info(f"Call ended: {call_id}, duration: {duration}s")

    if call_id in conversations:
        conversations[call_id]["ended"] = datetime.utcnow().isoformat()
        conversations[call_id]["duration"] = duration

    return {
        "status": "success",
        "summary": {
            "call_id": call_id,
            "duration": duration,
            "processed": True
        }
    }

def handle_transcript(data: Dict[str, Any]) -> Dict[str, Any]:
    """Handle transcript update"""
    call_id = data.get("call_id")
    transcript = data.get("transcript", "")

    logger.info(f"Transcript for {call_id}: {transcript[:100]}...")

    if call_id in conversations:
        conversations[call_id]["events"].append({
            "type": "transcript",
            "content": transcript,
            "timestamp": datetime.utcnow().isoformat()
        })

    # Analyze transcript for insights
    insights = analyze_transcript(transcript)

    return {
        "status": "processed",
        "insights": insights
    }

def handle_tool_call(data: Dict[str, Any]) -> Dict[str, Any]:
    """Handle tool/function call"""
    call_id = data.get("call_id")
    tool_name = data.get("tool_name") or data.get("function_name")
    parameters = data.get("parameters") or data.get("function_args") or {}

    logger.info(f"Tool call in {call_id}: {tool_name}")

    # Handle different tools
    if tool_name in ["check_availability", "check_calendar", "schedule"]:
        return {
            "success": True,
            "result": {
                "available_slots": [
                    {"date": "2024-01-16", "time": "10:00 AM"},
                    {"date": "2024-01-16", "time": "2:00 PM"},
                    {"date": "2024-01-17", "time": "11:00 AM"}
                ],
                "message": "I found several available slots. Which works best for you?"
            }
        }

    elif tool_name in ["escalate", "transfer", "human"]:
        return {
            "success": True,
            "result": "I'll connect you with our team right away. Please hold for just a moment."
        }

    else:
        return {
            "success": True,
            "result": f"I'll help you with {tool_name}"
        }

def analyze_transcript(transcript: str) -> Dict[str, Any]:
    """Simple transcript analysis"""
    transcript_lower = transcript.lower()

    # Detect sentiment
    if any(word in transcript_lower for word in ["angry", "frustrated", "upset", "terrible"]):
        sentiment = "negative"
        urgency = "high"
    elif any(word in transcript_lower for word in ["happy", "great", "excellent", "perfect"]):
        sentiment = "positive"
        urgency = "low"
    else:
        sentiment = "neutral"
        urgency = "normal"

    # Detect intent
    if any(word in transcript_lower for word in ["appointment", "schedule", "meeting", "book"]):
        intent = "scheduling"
    elif any(word in transcript_lower for word in ["problem", "issue", "broken", "help"]):
        intent = "support"
    elif any(word in transcript_lower for word in ["price", "cost", "quote", "buy"]):
        intent = "sales"
    else:
        intent = "general"

    return {
        "sentiment": sentiment,
        "urgency": urgency,
        "intent": intent
    }

@app.get("/")
async def root():
    return {
        "service": "ClearVC Amber Brain",
        "status": "running",
        "endpoints": {
            "health": "/health",
            "webhook": "/webhook (unified intelligent endpoint)"
        },
        "message": "One endpoint to handle all Retell webhooks intelligently"
    }

@app.get("/conversations")
async def get_conversations():
    """Debug endpoint to see stored conversations"""
    return conversations

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", "8000"))
    uvicorn.run(app, host="0.0.0.0", port=port)