#!/usr/bin/env python3
"""AI Jesus Bro Brain - Production Server"""

import os
import json
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import uvicorn
import httpx
from datetime import datetime

app = FastAPI(title="AI Jesus Bro Brain")

# Config
GHL_API_KEY = os.getenv("GHL_API_KEY")
GHL_LOCATION_ID = os.getenv("GHL_LOCATION_ID")
RETELL_API_KEY = os.getenv("RETELL_API_KEY")
GHL_BASE = "https://rest.gohighlevel.com/v1"

@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "version": "2.0.0",
        "droplet": "64.23.221.37",
        "timestamp": datetime.now().isoformat()
    }

@app.post("/webhooks/retell")
async def retell_webhook(request: Request):
    """Handle Retell webhooks with GHL automation"""
    try:
        data = await request.json()
        event_type = data.get("event")

        if event_type == "call_started":
            phone = data.get("from_number", "")
            print(f"📞 Call started from {phone}")

            # Caller ID lookup in GHL
            async with httpx.AsyncClient() as client:
                search = await client.get(
                    f"{GHL_BASE}/contacts/search",
                    headers={"Authorization": f"Bearer {GHL_API_KEY}"},
                    params={"locationId": GHL_LOCATION_ID, "query": phone}
                )

                if search.status_code == 200:
                    contacts = search.json().get("contacts", [])
                    if contacts:
                        contact = contacts[0]
                        print(f"✅ Found: {contact.get('firstName')} {contact.get('lastName')}")
                    else:
                        # Create new contact
                        create = await client.post(
                            f"{GHL_BASE}/contacts",
                            headers={"Authorization": f"Bearer {GHL_API_KEY}"},
                            json={
                                "locationId": GHL_LOCATION_ID,
                                "phone": phone,
                                "firstName": "New",
                                "lastName": "Lead",
                                "source": "AI Phone System",
                                "tags": ["ai-captured", "auto-created"]
                            }
                        )
                        if create.status_code in [200, 201]:
                            print(f"✅ Created contact for {phone}")

        elif event_type == "call_ended":
            # Process transcript and create tasks
            call_id = data.get("call_id")
            transcript = data.get("transcript", "")

            if "appointment" in transcript.lower() or "meeting" in transcript.lower():
                print("📅 Appointment requested - creating urgent task")
                # TODO: Create task in GHL

        return JSONResponse({"status": "processed", "event": event_type})

    except Exception as e:
        print(f"❌ Error: {e}")
        return JSONResponse({"status": "error", "message": str(e)}, status_code=500)

@app.post("/webhooks/ghl")
async def ghl_webhook(request: Request):
    """Handle GHL webhooks"""
    data = await request.json()
    print(f"GHL Event: {data.get('event_type', 'unknown')}")
    return JSONResponse({"status": "processed"})

@app.post("/sse")
async def sse_endpoint(request: Request):
    """MCP endpoint for Claude"""
    data = await request.json()
    method = data.get("method")

    if method == "tools/call":
        tool_name = data.get("params", {}).get("name")
        return JSONResponse({
            "jsonrpc": "2.0",
            "result": {"status": "ok", "tool": tool_name},
            "id": data.get("id", 1)
        })

    return JSONResponse({
        "jsonrpc": "2.0",
        "result": {"status": "ok"},
        "id": data.get("id", 1)
    })

if __name__ == "__main__":
    print("🧠 AI Jesus Bro Brain Starting...")
    print(f"GHL Location: {GHL_LOCATION_ID}")
    print(f"Retell Configured: {'Yes' if RETELL_API_KEY else 'No'}")
    uvicorn.run(app, host="0.0.0.0", port=8080)