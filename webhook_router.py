"""
Master Webhook Router for All Retell Agents
Routes to appropriate brain based on agent_id
"""

from fastapi import FastAPI, Request, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
import httpx
import logging
import os
import json
from typing import Dict, Any, Optional
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Master Retell Webhook Router",
    description="Routes Retell webhooks to appropriate brain services"
)

# Add CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Agent routing configuration
# Map Retell agent IDs to their brain services
AGENT_ROUTES = {
    # ClearVC agents
    "clearvc_amber": "http://clearvc-brain:8000",
    "clearvc_main": "http://clearvc-brain:8000",

    # Your other agents
    "spectrum": "http://mcp-brain:8080",

    # Add more as needed
    # "rebecca": "http://rebecca-brain:8002",
    # "ai_marketer": "http://marketer-brain:8003",
}

# Default route for unknown agents
DEFAULT_BRAIN = "http://mcp-brain:8080"

@app.get("/health")
async def health_check():
    """Master router health check"""
    return {
        "status": "healthy",
        "service": "master_webhook_router",
        "timestamp": datetime.utcnow().isoformat(),
        "configured_agents": list(AGENT_ROUTES.keys())
    }

@app.post("/webhooks/retell/{event_type}")
async def route_retell_webhook(
    event_type: str,
    request: Request,
    background_tasks: BackgroundTasks
):
    """
    Master routing for all Retell webhooks
    Routes based on agent_id in payload
    """
    try:
        # Parse the incoming webhook
        payload = await request.json()

        # Log incoming webhook
        logger.info(f"Received {event_type} webhook for agent: {payload.get('agent_id')}")

        # Extract agent_id to determine routing
        agent_id = payload.get("agent_id")

        # Determine target brain
        if agent_id in AGENT_ROUTES:
            target_url = AGENT_ROUTES[agent_id]
            logger.info(f"Routing to configured brain: {target_url}")
        else:
            # Check if it's a ClearVC agent by name pattern
            if agent_id and "clearvc" in agent_id.lower():
                target_url = AGENT_ROUTES.get("clearvc_amber", DEFAULT_BRAIN)
                logger.info(f"Routing ClearVC agent to: {target_url}")
            else:
                target_url = DEFAULT_BRAIN
                logger.warning(f"Unknown agent {agent_id}, routing to default: {target_url}")

        # Forward the webhook to the appropriate brain
        async with httpx.AsyncClient(timeout=30.0) as client:
            # Build the full target URL
            full_url = f"{target_url}/webhooks/retell/{event_type}"

            # Forward the request
            response = await client.post(
                full_url,
                json=payload,
                headers={
                    "Content-Type": "application/json",
                    "X-Forwarded-For": request.client.host if request.client else "unknown",
                    "X-Original-Agent": agent_id or "unknown"
                }
            )

            # Log the result
            if response.status_code == 200:
                logger.info(f"Successfully routed {event_type} for {agent_id}")
            else:
                logger.error(f"Brain returned {response.status_code} for {event_type}")

            # Return the brain's response
            return response.json()

    except httpx.RequestError as e:
        logger.error(f"Failed to forward webhook: {e}")
        # Return a safe fallback response for Retell
        if event_type == "call-started":
            return {
                "status": "success",
                "custom_variables": {
                    "greeting": "Thank you for calling. How may I help you today?"
                }
            }
        elif event_type == "tool-call":
            return {
                "success": False,
                "result": "I'm having trouble processing that request. Please try again."
            }
        else:
            raise HTTPException(status_code=502, detail="Service temporarily unavailable")

    except Exception as e:
        logger.error(f"Unexpected error in router: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/agents")
async def list_configured_agents():
    """List all configured agents and their routing"""
    agents = []
    for agent_id, target in AGENT_ROUTES.items():
        # Check if the brain is healthy
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                health_response = await client.get(f"{target}/health")
                status = "online" if health_response.status_code == 200 else "offline"
        except:
            status = "unreachable"

        agents.append({
            "agent_id": agent_id,
            "target_brain": target,
            "status": status
        })

    return {
        "agents": agents,
        "default_brain": DEFAULT_BRAIN,
        "total_configured": len(agents)
    }

@app.post("/test/webhook")
async def test_webhook(agent_id: str, event_type: str = "call-started"):
    """Test webhook routing for a specific agent"""
    test_payload = {
        "agent_id": agent_id,
        "call_id": f"test_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
        "from_number": "+1234567890",
        "test": True
    }

    # Determine routing
    target = AGENT_ROUTES.get(agent_id, DEFAULT_BRAIN)

    return {
        "agent_id": agent_id,
        "would_route_to": target,
        "test_payload": test_payload,
        "event_type": event_type
    }

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", "8090"))
    uvicorn.run(app, host="0.0.0.0", port=port)