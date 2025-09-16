#!/usr/bin/env python3
"""
SPECTRUM Gateway - The communication bridge for agents to talk to SPECTRUM.

This is the stateless gateway that converts agent communication into 
SPECTRUM's POST /v1/process_turn protocol. Agents hit this gateway,
it translates to SPECTRUM, and returns responses.
"""

import os
import uuid
import asyncio
import logging
from typing import Dict, Any, Optional
from datetime import datetime

import httpx
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
import uvicorn

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AgentMessage(BaseModel):
    """Input model for agents talking to the gateway."""
    agent_id: str = Field(..., description="Agent identifier")
    customer_id: str = Field(..., description="Customer identifier") 
    message: str = Field(..., description="The agent's message")
    session_id: Optional[str] = Field(None, description="Session ID (auto-generated if not provided)")


class GatewayResponse(BaseModel):
    """Response model from the gateway."""
    session_id: str
    agent_response: str
    success: bool
    error: Optional[str] = None


class SpectrumGateway:
    """The SPECTRUM gateway that converts agent communication to SPECTRUM protocol."""
    
    def __init__(self):
        # SPECTRUM engine endpoint
        self.spectrum_host = os.getenv('SPECTRUM_HOST', 'localhost')
        self.spectrum_port = os.getenv('SPECTRUM_PORT', '8000')
        self.spectrum_base_url = f"http://{self.spectrum_host}:{self.spectrum_port}"
        
        # HTTP client for talking to SPECTRUM
        self.http_client = httpx.AsyncClient(timeout=30.0)
        
        logger.info(f"SPECTRUM Gateway initialized - targeting {self.spectrum_base_url}")

    async def process_agent_message(self, agent_msg: AgentMessage) -> GatewayResponse:
        """
        Convert agent message to SPECTRUM protocol and get response.
        
        This is the core translation layer:
        Agent Input → SPECTRUM POST /v1/process_turn → Agent Response
        """
        try:
            # Generate session ID if not provided
            session_id = agent_msg.session_id or f"session_{uuid.uuid4().hex[:8]}"
            
            # Build SPECTRUM request payload
            spectrum_payload = {
                "session_id": session_id,
                "agent_id": agent_msg.agent_id,
                "customer_id": agent_msg.customer_id,
                "user_message": agent_msg.message
            }
            
            logger.info(f"Converting agent message to SPECTRUM protocol: {agent_msg.agent_id}")
            
            # Call SPECTRUM engine
            spectrum_url = f"{self.spectrum_base_url}/v1/process_turn"
            response = await self.http_client.post(
                spectrum_url,
                json=spectrum_payload,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code != 200:
                error_msg = f"SPECTRUM engine error: {response.status_code} - {response.text}"
                logger.error(error_msg)
                return GatewayResponse(
                    session_id=session_id,
                    agent_response="",
                    success=False,
                    error=error_msg
                )
            
            # Extract SPECTRUM response
            spectrum_data = response.json()
            agent_response = spectrum_data.get("agent_response", "No response from SPECTRUM")
            
            logger.info(f"SPECTRUM response received for session {session_id}")
            
            return GatewayResponse(
                session_id=session_id,
                agent_response=agent_response,
                success=True
            )
            
        except httpx.ConnectError:
            error_msg = f"Cannot connect to SPECTRUM engine at {self.spectrum_base_url}"
            logger.error(error_msg)
            return GatewayResponse(
                session_id=agent_msg.session_id or "unknown",
                agent_response="",
                success=False,
                error=error_msg
            )
        except Exception as e:
            error_msg = f"Gateway error: {str(e)}"
            logger.error(error_msg)
            return GatewayResponse(
                session_id=agent_msg.session_id or "unknown", 
                agent_response="",
                success=False,
                error=error_msg
            )

    async def health_check(self) -> Dict[str, Any]:
        """Check if SPECTRUM engine is reachable."""
        try:
            response = await self.http_client.get(f"{self.spectrum_base_url}/")
            return {
                "gateway_status": "healthy",
                "spectrum_status": "connected" if response.status_code == 200 else "error",
                "spectrum_url": self.spectrum_base_url
            }
        except:
            return {
                "gateway_status": "healthy",
                "spectrum_status": "disconnected",
                "spectrum_url": self.spectrum_base_url
            }


# Initialize the gateway
gateway = SpectrumGateway()

# Create FastAPI app
app = FastAPI(
    title="SPECTRUM Gateway",
    description="The communication bridge for agents to talk to SPECTRUM",
    version="1.0.0"
)


@app.get("/")
async def root():
    """Gateway health check."""
    health = await gateway.health_check()
    return {
        "service": "SPECTRUM Gateway",
        "status": "active",
        **health
    }


@app.post("/chat", response_model=GatewayResponse)
async def agent_chat(message: AgentMessage):
    """
    Main endpoint for agents to communicate through SPECTRUM.
    
    Agents send messages here, gateway translates to SPECTRUM protocol,
    and returns SPECTRUM's response.
    """
    logger.info(f"Agent {message.agent_id} sending message via gateway")
    
    response = await gateway.process_agent_message(message)
    
    if not response.success:
        raise HTTPException(status_code=500, detail=response.error)
    
    return response


@app.get("/health")
async def health():
    """Detailed health check including SPECTRUM connectivity."""
    return await gateway.health_check()


if __name__ == "__main__":
    # Load configuration
    host = os.getenv("GATEWAY_HOST", "0.0.0.0")
    port = int(os.getenv("GATEWAY_PORT", "8001"))
    
    print(f"""
🚀 SPECTRUM Gateway Starting...

Gateway: http://{host}:{port}
SPECTRUM Engine: {gateway.spectrum_base_url}

Agents can now talk to SPECTRUM via:
POST http://{host}:{port}/chat

Example payload:
{{
    "agent_id": "my_agent",
    "customer_id": "customer_123", 
    "message": "Hello SPECTRUM"
}}
    """)
    
    uvicorn.run(
        "spectrum_gateway:app",
        host=host,
        port=port,
        reload=os.getenv("RELOAD", "false").lower() == "true"
    )