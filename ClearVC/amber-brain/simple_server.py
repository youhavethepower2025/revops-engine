#!/usr/bin/env python3
"""
Simple ClearVC Amber Brain Server
Runs without Docker for quick deployment
"""

from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from datetime import datetime
import uvicorn
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="ClearVC Amber Brain")

# Store conversations in memory for now
conversations = {}

@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "service": "clearvc-amber-brain",
        "timestamp": datetime.utcnow().isoformat(),
        "url": "https://clearvc.aijesusbro.com"
    }

@app.post("/webhooks/retell/call-started")
async def call_started(request: Request):
    data = await request.json()
    logger.info(f"Call started: {data}")

    call_id = data.get("call_id")
    from_number = data.get("from_number")

    # Store conversation
    conversations[call_id] = {
        "phone": from_number,
        "started": datetime.utcnow().isoformat(),
        "events": []
    }

    return {
        "status": "success",
        "custom_variables": {
            "greeting": "Thank you for calling ClearVC! You've reached our after-hours service. I'm Amber, and I'm here to help. How can I assist you tonight?",
            "caller_type": "new"
        }
    }

@app.post("/webhooks/retell/call-ended")
async def call_ended(request: Request):
    data = await request.json()
    logger.info(f"Call ended: {data}")

    return {
        "status": "success",
        "summary": "Call processed successfully"
    }

@app.post("/webhooks/retell/transcript-update")
async def transcript_update(request: Request):
    data = await request.json()
    logger.info(f"Transcript update: {data.get('transcript', '')[:100]}")

    return {
        "status": "processed",
        "insights": {
            "sentiment": "neutral",
            "urgency": "normal"
        }
    }

@app.post("/webhooks/retell/tool-call")
async def tool_call(request: Request):
    data = await request.json()
    tool_name = data.get("tool_name")
    logger.info(f"Tool call: {tool_name}")

    if tool_name == "check_availability":
        return {
            "success": True,
            "result": {
                "available_slots": [
                    {"date": "2024-01-16", "time": "10:00 AM"},
                    {"date": "2024-01-16", "time": "2:00 PM"},
                    {"date": "2024-01-17", "time": "11:00 AM"}
                ],
                "message": "I have several slots available. Which works best for you?"
            }
        }

    return {
        "success": True,
        "result": "I'll help you with that."
    }

@app.get("/")
async def root():
    return {
        "service": "ClearVC Amber Brain",
        "status": "running",
        "endpoints": [
            "/health",
            "/webhooks/retell/call-started",
            "/webhooks/retell/call-ended",
            "/webhooks/retell/transcript-update",
            "/webhooks/retell/tool-call"
        ]
    }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001)