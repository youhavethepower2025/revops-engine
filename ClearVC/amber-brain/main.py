"""
ClearVC Amber Brain - Intelligent Call Orchestrator
Handles Retell webhooks and orchestrates with GHL
"""

from fastapi import FastAPI, HTTPException, Request, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
import logging
from datetime import datetime
import json
import os
from dotenv import load_dotenv

from brain import AmberBrain
from models import db, CallSession, Contact, CallEvent
from webhooks import RetellWebhookHandler
from ghl_controller import GHLController

load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize FastAPI
app = FastAPI(
    title="ClearVC Amber Brain",
    description="Intelligent orchestrator for after-hours calls",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure this properly in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize components
brain = AmberBrain()
webhook_handler = RetellWebhookHandler(brain)
ghl = GHLController()

# Health check
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "services": {
            "database": await brain.check_db_health(),
            "redis": await brain.check_redis_health(),
            "ghl": await ghl.check_connection()
        }
    }

# Retell Webhook Endpoints
@app.post("/webhooks/retell/call-started")
async def handle_call_start(request: Request, background_tasks: BackgroundTasks):
    """Handle call start from Retell"""
    try:
        data = await request.json()
        logger.info(f"Call started: {data}")

        # Process call start
        result = await webhook_handler.handle_call_start(data)

        # Background task to prepare context
        background_tasks.add_task(brain.prepare_call_context, data.get('call_id'))

        return result
    except Exception as e:
        logger.error(f"Error handling call start: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/webhooks/retell/call-ended")
async def handle_call_end(request: Request, background_tasks: BackgroundTasks):
    """Handle call end from Retell"""
    try:
        data = await request.json()
        logger.info(f"Call ended: {data}")

        # Process call end
        result = await webhook_handler.handle_call_end(data)

        # Background tasks for post-call processing
        background_tasks.add_task(brain.generate_call_summary, data.get('call_id'))
        background_tasks.add_task(brain.update_ghl_contact, data.get('call_id'))
        background_tasks.add_task(brain.create_follow_ups, data.get('call_id'))

        return result
    except Exception as e:
        logger.error(f"Error handling call end: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/webhooks/retell/transcript-update")
async def handle_transcript_update(request: Request):
    """Handle real-time transcript updates from Retell"""
    try:
        data = await request.json()

        # Process transcript in real-time
        insights = await brain.process_transcript_chunk(
            call_id=data.get('call_id'),
            transcript=data.get('transcript')
        )

        # Return any real-time guidance
        return {
            "status": "processed",
            "insights": insights
        }
    except Exception as e:
        logger.error(f"Error processing transcript: {e}")
        return {"status": "error", "message": str(e)}

@app.post("/webhooks/retell/tool-call")
async def handle_tool_call(request: Request):
    """Handle tool calls from Retell during conversation"""
    try:
        data = await request.json()
        call_id = data.get('call_id')
        tool_name = data.get('tool_name')
        parameters = data.get('parameters', {})

        logger.info(f"Tool call: {tool_name} for call {call_id}")

        # Route to appropriate handler
        result = await brain.handle_tool_call(call_id, tool_name, parameters)

        return {
            "status": "success",
            "result": result
        }
    except Exception as e:
        logger.error(f"Error handling tool call: {e}")
        return {
            "status": "error",
            "message": str(e),
            "fallback": "Let me help you with that..."
        }

# Admin Endpoints
@app.get("/calls")
async def list_calls(limit: int = 50, offset: int = 0):
    """List recent calls"""
    calls = await brain.get_recent_calls(limit, offset)
    return {"calls": calls, "total": len(calls)}

@app.get("/calls/{call_id}")
async def get_call_details(call_id: str):
    """Get detailed information about a specific call"""
    call = await brain.get_call_details(call_id)
    if not call:
        raise HTTPException(status_code=404, detail="Call not found")
    return call

@app.get("/contacts/{phone}")
async def get_contact(phone: str):
    """Get contact information by phone number"""
    contact = await brain.get_contact_by_phone(phone)
    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")
    return contact

@app.post("/brain/train")
async def train_brain(request: Request):
    """Train the brain with new patterns or data"""
    try:
        data = await request.json()
        training_type = data.get('type')
        training_data = data.get('data')

        result = await brain.train(training_type, training_data)

        return {
            "status": "success",
            "message": f"Brain trained with {training_type}",
            "result": result
        }
    except Exception as e:
        logger.error(f"Error training brain: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Startup and Shutdown
@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    logger.info("Starting Amber Brain...")

    # Initialize database
    await db.init()

    # Initialize brain memory
    await brain.initialize()

    # Test GHL connection
    if await ghl.check_connection():
        logger.info("GHL connection successful")
    else:
        logger.warning("GHL connection failed - will retry")

    logger.info("Amber Brain started successfully")

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    logger.info("Shutting down Amber Brain...")
    await brain.cleanup()
    await db.close()
    logger.info("Amber Brain shutdown complete")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )