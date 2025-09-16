#!/usr/bin/env python3
"""
Real-time Voice Agent
Twilio Media Streams with Cloudflare AI
"""

import asyncio
import json
import base64
import audioop
import logging
from datetime import datetime
from typing import Dict, Optional
import os

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request
from fastapi.responses import Response
import uvicorn
import httpx

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Voice Agent")

# Environment variables
CLOUDFLARE_API_TOKEN = os.getenv("CLOUDFLARE_API_TOKEN", "TyCmFLgySVRZ5RFOvoXXq9gOKbl3HNHaXCp7YIKc")
CLOUDFLARE_ACCOUNT_ID = os.getenv("CLOUDFLARE_ACCOUNT_ID", "bbd9ec5819a97651cc9f481c1c275c3d")
TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID", "[REDACTED]")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN", "e65397c32f16f83469ee9d859308eb6a")
GHL_API_KEY = os.getenv("GHL_API_KEY", "pit-fdf8bee7-9c21-4748-b265-e732781c8b3f")
GHL_LOCATION_ID = os.getenv("GHL_LOCATION_ID", "PMgbQ375TEGOyGXsKz7e")

active_calls: Dict[str, Dict] = {}

class VoiceAgent:
    def __init__(self):
        self.conversation_history = []
        self.audio_buffer = b""
        self.call_sid = None
        
    async def process_audio_chunk(self, audio_data: bytes) -> Optional[str]:
        try:
            pcm_data = audioop.ulaw2lin(audio_data, 2)
            self.audio_buffer += pcm_data
            
            if len(self.audio_buffer) >= 8000:
                transcription = await self.transcribe_with_cloudflare(self.audio_buffer)
                self.audio_buffer = b""
                return transcription
        except Exception as e:
            logger.error(f"Audio processing error: {e}")
        return None
    
    async def transcribe_with_cloudflare(self, audio_data: bytes) -> str:
        try:
            url = f"https://api.cloudflare.com/client/v4/accounts/{CLOUDFLARE_ACCOUNT_ID}/ai/run/@cf/openai/whisper"
            headers = {"Authorization": f"Bearer {CLOUDFLARE_API_TOKEN}"}
            files = {"audio": ("audio.wav", audio_data, "audio/wav")}
            
            async with httpx.AsyncClient(timeout=10) as client:
                response = await client.post(url, headers=headers, files=files)
                
            if response.status_code == 200:
                result = response.json()
                return result.get("result", {}).get("text", "")
            return ""
        except Exception as e:
            logger.error(f"Transcription error: {e}")
            return ""
    
    async def generate_response(self, user_input: str) -> str:
        try:
            self.conversation_history.append({"role": "user", "content": user_input})
            
            messages = [
                {"role": "system", "content": "You are a friendly AI voice assistant. Keep responses short and conversational for phone calls."},
            ] + self.conversation_history[-5:]
            
            url = f"https://api.cloudflare.com/client/v4/accounts/{CLOUDFLARE_ACCOUNT_ID}/ai/run/@cf/qwen/qwen2.5-72b-instruct"
            headers = {"Authorization": f"Bearer {CLOUDFLARE_API_TOKEN}", "Content-Type": "application/json"}
            payload = {"messages": messages, "max_tokens": 150, "temperature": 0.7}
            
            async with httpx.AsyncClient(timeout=15) as client:
                response = await client.post(url, headers=headers, json=payload)
                
            if response.status_code == 200:
                result = response.json()
                ai_response = result.get("result", {}).get("response", "I didn't catch that.")
                self.conversation_history.append({"role": "assistant", "content": ai_response})
                return ai_response
            return "I'm having trouble processing that right now."
        except Exception as e:
            logger.error(f"Response generation error: {e}")
            return "Sorry, I'm experiencing technical difficulties."

@app.post("/webhook/voice")
async def handle_voice_webhook(request: Request):
    form_data = await request.form()
    call_sid = form_data.get("CallSid")
    from_number = form_data.get("From")
    to_number = form_data.get("To")
    
    logger.info(f"Incoming call: {call_sid} from {from_number} to {to_number}")
    
    active_calls[call_sid] = {
        "agent": VoiceAgent(),
        "from": from_number,
        "to": to_number,
        "start_time": datetime.now(),
        "transcript": []
    }
    active_calls[call_sid]["agent"].call_sid = call_sid
    
    host = request.headers.get("host", "localhost:8000")
    
    twiml = f'''<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say>Hello! I'm your AI assistant. How can I help you today?</Say>
    <Start>
        <Stream url="wss://{host}/websocket/media-stream" />
    </Start>
    <Pause length="30" />
</Response>'''
    
    return Response(content=twiml, media_type="application/xml")

@app.websocket("/websocket/media-stream")
async def media_stream_handler(websocket: WebSocket):
    await websocket.accept()
    call_sid = None
    agent = None
    
    try:
        while True:
            message = await websocket.receive_text()
            data = json.loads(message)
            event_type = data.get("event")
            
            if event_type == "start":
                start_data = data.get("start", {})
                call_sid = start_data.get("callSid")
                if call_sid and call_sid in active_calls:
                    agent = active_calls[call_sid]["agent"]
                    logger.info(f"Media stream started for call {call_sid}")
                    
            elif event_type == "media" and agent:
                media_data = data.get("media", {})
                payload = media_data.get("payload")
                
                if payload:
                    audio_data = base64.b64decode(payload)
                    transcription = await agent.process_audio_chunk(audio_data)
                    
                    if transcription and transcription.strip():
                        logger.info(f"User said: {transcription}")
                        
                        active_calls[call_sid]["transcript"].append({
                            "speaker": "user",
                            "text": transcription,
                            "timestamp": datetime.now().isoformat()
                        })
                        
                        ai_response = await agent.generate_response(transcription)
                        logger.info(f"AI responds: {ai_response}")
                        
                        active_calls[call_sid]["transcript"].append({
                            "speaker": "ai",
                            "text": ai_response,
                            "timestamp": datetime.now().isoformat()
                        })
                        
            elif event_type == "stop":
                logger.info(f"Media stream ended for call {call_sid}")
                if call_sid and call_sid in active_calls:
                    await send_transcript_to_ghl(call_sid)
                    del active_calls[call_sid]
                break
                
    except WebSocketDisconnect:
        logger.info("WebSocket disconnected")
        if call_sid and call_sid in active_calls:
            await send_transcript_to_ghl(call_sid)
            del active_calls[call_sid]
    except Exception as e:
        logger.error(f"WebSocket error: {e}")

async def send_transcript_to_ghl(call_sid: str):
    try:
        if call_sid not in active_calls:
            return
            
        call_data = active_calls[call_sid]
        phone_number = call_data["from"]
        transcript = call_data["transcript"]
        
        transcript_text = "\n".join([
            f"{item['speaker'].upper()}: {item['text']}"
            for item in transcript
        ])
        
        headers = {"Authorization": f"Bearer {GHL_API_KEY}", "Content-Type": "application/json"}
        
        contact_payload = {
            "phone": phone_number,
            "locationId": GHL_LOCATION_ID,
            "tags": ["voice-agent-call"]
        }
        
        async with httpx.AsyncClient(timeout=10) as client:
            contact_response = await client.post(
                "https://services.leadconnectorhq.com/contacts/",
                headers=headers,
                json=contact_payload
            )
            
            if contact_response.status_code in [200, 201]:
                contact_data = contact_response.json()
                contact_id = contact_data.get("contact", {}).get("id")
                
                if contact_id:
                    note_payload = {
                        "body": f"AI Voice Agent Call\n\nDuration: {datetime.now() - call_data['start_time']}\n\n{transcript_text}",
                        "userId": contact_id
                    }
                    
                    await client.post(
                        f"https://services.leadconnectorhq.com/contacts/{contact_id}/notes",
                        headers=headers,
                        json=note_payload
                    )
                    
                    logger.info(f"Transcript sent to GHL for {phone_number}")
                
    except Exception as e:
        logger.error(f"GHL webhook error: {e}")

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "active_calls": len(active_calls),
        "framework": "FastAPI + Cloudflare AI"
    }

@app.get("/")
async def root():
    return {
        "service": "Voice Agent",
        "version": "1.0.0",
        "description": "Real-time voice agent with Twilio and Cloudflare AI"
    }

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)