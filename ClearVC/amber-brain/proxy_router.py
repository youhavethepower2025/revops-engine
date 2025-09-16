"""
Proxy Router for ClearVC Amber Brain
Routes Retell webhooks through your MCP infrastructure
"""

from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
import httpx
import logging
import os
from typing import Dict, Any

app = FastAPI(title="ClearVC Webhook Router")
logger = logging.getLogger(__name__)

# Configuration
CLEARVC_BRAIN_URL = os.getenv("CLEARVC_BRAIN_URL", "http://localhost:8001")  # ClearVC runs on 8001
CLEARVC_AGENT_ID = os.getenv("CLEARVC_AGENT_ID", "clearvc_amber")  # Set this to the actual Retell agent ID

# Route mapping for different clients
AGENT_ROUTING = {
    "clearvc_amber": CLEARVC_BRAIN_URL,
    # Add more agents here as needed for other clients
}

@app.post("/webhooks/retell/{event_type}")
async def route_webhook(event_type: str, request: Request):
    """
    Route Retell webhooks to appropriate brain based on agent_id
    """
    try:
        # Get the payload
        payload = await request.json()

        # Determine which brain to route to
        agent_id = payload.get("agent_id")

        if not agent_id:
            logger.warning("No agent_id in webhook payload")
            # Default to ClearVC for now
            target_url = CLEARVC_BRAIN_URL
        else:
            target_url = AGENT_ROUTING.get(agent_id)

            if not target_url:
                logger.error(f"Unknown agent_id: {agent_id}")
                raise HTTPException(status_code=404, detail=f"No handler for agent {agent_id}")

        # Forward the webhook
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{target_url}/webhooks/retell/{event_type}",
                json=payload,
                headers=dict(request.headers),
                timeout=30.0
            )

            # Return the response from the target brain
            return JSONResponse(
                content=response.json(),
                status_code=response.status_code
            )

    except httpx.RequestError as e:
        logger.error(f"Error forwarding webhook: {e}")
        raise HTTPException(status_code=502, detail="Error forwarding webhook")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "clearvc_router"}

@app.get("/agents")
async def list_agents():
    """List configured agents and their targets"""
    return {
        "agents": [
            {
                "agent_id": agent_id,
                "target": target,
                "status": "active"
            }
            for agent_id, target in AGENT_ROUTING.items()
        ]
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)