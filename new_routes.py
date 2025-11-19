import redis
from fastapi import APIRouter, Request, Form, HTTPException
from fastapi.responses import StreamingResponse, HTMLResponse, RedirectResponse
import json
import asyncio
import logging
import os
import time
from urllib.parse import urlencode

# --- Redis Client Initialization ---
# Assuming Redis is accessible at redis://redis:6380 within the Docker network
# or redis://localhost:6380 if running locally outside Docker Compose
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6380))
redis_client = redis.StrictRedis(host=REDIS_HOST, port=REDIS_PORT, db=0, decode_responses=True)

# --- Minimal, From-Scratch OAuth 2.1 Implementation ---

# This is the client ID that Claude Desktop will use.
CLIENT_ID = "claude-desktop"
REDIRECT_URI = "https://claude.ai/oauth/callback"

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/authorize")
async def oauth_authorize(request: Request, client_id: str, redirect_uri: str, scope: str, state: str, response_type: str):
    """
    This is the /authorize endpoint.
    It checks the client_id and redirect_uri, and if they are valid,
    it generates an authorization code and redirects the user back to the
    redirect_uri with the code and state.
    """
    if client_id != CLIENT_ID:
        raise HTTPException(status_code=400, detail="Invalid client_id")
    if redirect_uri != REDIRECT_URI:
        raise HTTPException(status_code=400, detail="Invalid redirect_uri")
    if response_type != "code":
        raise HTTPException(status_code=400, detail="Invalid response_type")

    # Generate a simple authorization code
    auth_code = os.urandom(16).hex()
    
    # Store the code in Redis with an expiration (e.g., 10 minutes)
    # The value stored is a JSON string of the code's details
    code_data = {
        "client_id": client_id,
        "redirect_uri": redirect_uri, # Store the redirect_uri for validation at /token
        "scope": scope,
        "state": state
    }
    redis_client.setex(f"auth_code:{auth_code}", 600, json.dumps(code_data)) # 600 seconds = 10 minutes

    # Redirect back to the client with the code
    params = {
        "code": auth_code,
        "state": state
    }
    return RedirectResponse(url=f"{redirect_uri}?{urlencode(params)}")

@router.post("/token")
async def oauth_token(
    request: Request,
    grant_type: str = Form(...),
    code: str = Form(...),
    redirect_uri: str = Form(...),
    client_id: str = Form(...)
):
    """
    This is the /token endpoint.
    It exchanges an authorization code for an access token.
    """
    if grant_type != "authorization_code":
        raise HTTPException(status_code=400, detail="Invalid grant_type")
    if client_id != CLIENT_ID:
        raise HTTPException(status_code=400, detail="Invalid client_id")
    if redirect_uri != REDIRECT_URI: # Validate redirect_uri again
        raise HTTPException(status_code=400, detail="Invalid redirect_uri")

    # Retrieve and delete the authorization code from Redis
    code_json = redis_client.get(f"auth_code:{code}")
    if not code_json:
        raise HTTPException(status_code=400, detail="Invalid or expired authorization code")
    
    auth_code_data = json.loads(code_json)
    redis_client.delete(f"auth_code:{code}") # Code is single-use

    # Validate client_id and redirect_uri from stored code data
    if auth_code_data["client_id"] != client_id:
        raise HTTPException(status_code=400, detail="Mismatched client_id")
    if auth_code_data["redirect_uri"] != redirect_uri:
        raise HTTPException(status_code=400, detail="Mismatched redirect_uri")

    # The code is valid, so we can issue an access token.
    access_token = os.urandom(32).hex()
    
    # Store the token in Redis with an expiration (e.g., 1 hour)
    token_data = {
        "client_id": client_id,
        "scope": auth_code_data["scope"]
    }
    redis_client.setex(f"access_token:{access_token}", 3600, json.dumps(token_data)) # 3600 seconds = 1 hour

    # Return the access token
    return {
        "access_token": access_token,
        "token_type": "Bearer",
        "expires_in": 3600,
        "scope": auth_code_data["scope"]
    }

# --- MCP Endpoint ---

from app.mcp.tool_registry import registry

async def handle_mcp_request(request_data: dict, response_queue: asyncio.Queue):
    method = request_data.get("method")
    params = request_data.get("params", {})
    request_id = request_data.get("id")

    logger.info(f"Processing MCP method: {method}, id: {request_id}")
    response_data = None

    try:
        if method == "initialize":
            response_data = {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {
                    "protocolVersion": "2025-06-18",
                    "capabilities": {
                        "tools": {"listChanged": True},
                        "resources": {},
                        "prompts": {},
                        "logging": {}
                    },
                    "serverInfo": {
                        "name": "medtainer-mcp",
                        "version": "1.3.0" # Version bump
                    }
                }
            }
        elif method == "tools/list":
            enabled_ecosystems = {"gohighlevel", "godaddy", "digitalocean"}
            tools = registry.list_tools()
            filtered_tools = [
                tool for tool in tools
                if tool.get("ecosystem") in enabled_ecosystems
            ]
            response_data = {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {"tools": filtered_tools}
            }
        elif method == "tools/call":
            tool_name = params.get("name")
            tool_args = params.get("arguments", {})
            result = registry.execute(tool_name, tool_args)
            result_dict = result.model_dump()
            response_data = {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": result_dict
            }
        else:
            response_data = {
                "jsonrpc": "2.0",
                "id": request_id,
                "error": {
                    "code": -32601,
                    "message": f"Method not found: {method}"
                }
            }
    except Exception as e:
        logger.error(f"Error handling MCP request: {e}", exc_info=True)
        response_data = {
            "jsonrpc": "2.0",
            "id": request_id,
            "error": {
                "code": -32603,
                "message": str(e)
            }
        }
    
    if response_data:
        await response_queue.put(response_data)

async def read_requests(request: Request, response_queue: asyncio.Queue):
    try:
        async for line in request.stream():
            line = line.decode('utf-8').strip()
            if not line:
                continue

            logger.debug(f"Received raw line: {line}")
            try:
                request_data = json.loads(line)
            except json.JSONDecodeError:
                logger.error(f"Failed to decode JSON: {line}")
                continue

            if "id" in request_data:
                asyncio.create_task(handle_mcp_request(request_data, response_queue))
            else:
                logger.info(f"Received notification: {request_data.get('method')}")

    except Exception as e:
        logger.error(f"Error reading request stream: {e}", exc_info=True)
    finally:
        logger.info("Request stream closed.")
        await response_queue.put(None)

# --- Token Validation Middleware ---
from starlette.middleware.base import BaseHTTPMiddleware

class TokenValidationMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if request.url.path == "/sse":
            auth_header = request.headers.get("Authorization")
            if not auth_header or not auth_header.startswith("Bearer "):
                return HTMLResponse(status_code=401, content="Unauthorized")
            
            token_string = auth_header.split(" ")[1]
            
            # Check if token exists and is not expired in Redis
            token_json = redis_client.get(f"access_token:{token_string}")
            if not token_json:
                return HTMLResponse(status_code=401, content="Invalid or expired Token")
            
            # Optionally, you could parse token_json here if you stored more data
            # token_data = json.loads(token_json)
            # if token_data["client_id"] != CLIENT_ID:
            #     return HTMLResponse(status_code=401, content="Invalid Token Client")
        
        response = await call_next(request)
        return response

# --- Main SSE Endpoint ---

@router.get("/sse")
async def sse_endpoint(request: Request):
    response_queue = asyncio.Queue()

    async def event_generator():
        read_task = asyncio.create_task(read_requests(request, response_queue))
        
        init_notification = {
            "jsonrpc": "2.0",
            "method": "server/initialized",
            "params": {}
        }
        yield json.dumps(init_notification) + '\n'
        logger.info("Sent server/initialized notification.")

        try:
            while True:
                response_data = await response_queue.get()
                if response_data is None:
                    break
                
                response_str = json.dumps(response_data) + '\n'
                logger.debug(f"Sending response: {response_str.strip()}")
                yield response_str
                
        except asyncio.CancelledError:
            logger.info("Event generator cancelled.")
        finally:
            read_task.cancel()
            logger.info("SSE stream closed.")

    return StreamingResponse(event_generator(), media_type="application/x-ndjson")

@router.get("/health")
def health_check() -> dict:
    return {
        "app": "medtainer-mcp",
        "status": "ok",
    }
