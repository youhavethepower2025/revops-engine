"""
Retell platform adapter implementation
Translates between orchestration layer and Retell's specific API
"""

import os
import json
import asyncio
from typing import Dict, List, Optional, Any
from datetime import datetime

from ..interfaces.voice_platform_interface import (
    VoicePlatformInterface,
    VoiceAgentConfig,
    CallEvent,
    CallResponse,
    VoicePlatformAdapter
)

class RetellAdapter(VoicePlatformInterface):
    """
    Adapter for Retell AI platform
    Implements the VoicePlatformInterface to work with Retell's API
    """
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("RETELL_API_KEY")
        self.base_url = "https://api.retell.ai/v1"
        
        # Map our generic voice settings to Retell's voice IDs
        self.voice_mapping = {
            ("male", "adult", "professional"): "josh-Q6q1YRgpzzr9voqHL10b",
            ("female", "adult", "professional"): "sarah-T6q1YRgpzzr9voqHL10c",
            ("male", "adult", "casual"): "mike-R6q1YRgpzzr9voqHL10d",
            ("female", "adult", "casual"): "emma-S6q1YRgpzzr9voqHL10e",
            ("neutral", "adult", "professional"): "alex-U6q1YRgpzzr9voqHL10f"
        }
        
    async def create_agent(self, config: VoiceAgentConfig) -> Dict:
        """Create a Retell agent from generic config"""
        
        # Convert to Retell format
        retell_config = self._convert_to_retell_format(config)
        
        # Call Retell API (simplified - in real implementation use aiohttp)
        try:
            # This would be an actual API call
            agent_data = {
                "agent_id": f"retell_{config.agent_id}",
                "phone_number": "+14155551234",  # Retell assigns this
                "webhook_url": config.webhook_url,
                "status": "created"
            }
            
            return {
                "success": True,
                "platform": "retell",
                "agent_id": agent_data["agent_id"],
                "phone_number": agent_data["phone_number"],
                "config": retell_config
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def _convert_to_retell_format(self, config: VoiceAgentConfig) -> Dict:
        """Convert generic config to Retell-specific format"""
        
        # Map voice settings to Retell voice ID
        voice_key = (config.voice_gender, config.voice_age, config.voice_style)
        voice_id = self.voice_mapping.get(voice_key, "alex-U6q1YRgpzzr9voqHL10f")
        
        # Build system prompt from personality profile
        system_prompt = self._build_system_prompt(config)
        
        # Convert to Retell format
        retell_config = {
            "agent_name": config.name,
            "voice_id": voice_id,
            "language": "en-US",
            "voice_speed": config.speaking_rate,
            "voice_temperature": config.energy,
            "response_speed": 2000,  # Retell-specific
            "llm_websocket_url": config.webhook_url,
            "enable_backchannel": True,
            "backchannel_frequency": config.interruption_sensitivity,
            "area_code": "415",
            "responsiveness": config.interruption_sensitivity,
            "interruption_threshold": 100 * (1 - config.interruption_sensitivity),
            "end_call_after_silence_ms": config.silence_timeout_ms,
            "max_call_duration_ms": config.max_duration_ms,
            "general_prompt": system_prompt,
            "general_tools": self._build_retell_tools(config),
            "states": self._build_retell_states(config)
        }
        
        return retell_config
    
    def _build_system_prompt(self, config: VoiceAgentConfig) -> str:
        """Build Retell system prompt from personality profile"""
        
        if not config.personality_profile:
            return "You are a helpful assistant."
        
        profile = config.personality_profile
        traits = profile.get("traits", [])
        style = profile.get("communication_style", "professional")
        
        prompt = f"You are a {style} assistant with these traits: {', '.join(traits)}. "
        
        if profile.get("response_patterns"):
            patterns = profile["response_patterns"]
            if "greeting" in patterns:
                prompt += f"Start conversations with: {patterns['greeting']} "
        
        return prompt
    
    def _build_retell_tools(self, config: VoiceAgentConfig) -> List[Dict]:
        """Build Retell tools configuration"""
        
        tools = []
        
        if config.capabilities:
            if config.capabilities.get("appointment_booking"):
                tools.append({
                    "type": "book_appointment",
                    "name": "Book Appointment",
                    "description": "Schedule an appointment",
                    "parameters": {
                        "date": "string",
                        "time": "string",
                        "service": "string"
                    }
                })
            
            if config.capabilities.get("payment_processing"):
                tools.append({
                    "type": "process_payment",
                    "name": "Process Payment",
                    "description": "Handle payment",
                    "parameters": {
                        "amount": "number",
                        "method": "string"
                    }
                })
        
        return tools
    
    def _build_retell_states(self, config: VoiceAgentConfig) -> List[Dict]:
        """Build Retell conversation states"""
        
        # Basic state machine for Retell
        states = [
            {
                "name": "greeting",
                "prompt": "Hello! How can I help you today?",
                "transitions": [
                    {"trigger": "user_responds", "target": "main"}
                ]
            },
            {
                "name": "main",
                "prompt": self._build_system_prompt(config),
                "transitions": [
                    {"trigger": "appointment_request", "target": "booking"},
                    {"trigger": "payment_request", "target": "payment"},
                    {"trigger": "end_request", "target": "closing"}
                ]
            },
            {
                "name": "closing",
                "prompt": "Thank you for calling. Have a great day!",
                "transitions": []
            }
        ]
        
        return states
    
    async def update_agent(self, agent_id: str, config: VoiceAgentConfig) -> Dict:
        """Update Retell agent"""
        
        retell_config = self._convert_to_retell_format(config)
        
        # API call would go here
        return {
            "success": True,
            "agent_id": agent_id,
            "updated_config": retell_config
        }
    
    async def delete_agent(self, agent_id: str) -> bool:
        """Delete Retell agent"""
        # API call would go here
        return True
    
    async def get_agent(self, agent_id: str) -> Dict:
        """Get Retell agent details"""
        # API call would go here
        return {
            "agent_id": agent_id,
            "platform": "retell",
            "status": "active"
        }
    
    async def list_agents(self) -> List[Dict]:
        """List all Retell agents"""
        # API call would go here
        return []
    
    async def start_call(self, agent_id: str, phone_number: str, metadata: Dict = None) -> Dict:
        """Start outbound call via Retell"""
        
        # API call would go here
        session_id = f"retell_call_{datetime.now().timestamp()}"
        
        return {
            "success": True,
            "session_id": session_id,
            "agent_id": agent_id,
            "phone_number": phone_number,
            "status": "dialing"
        }
    
    async def end_call(self, session_id: str) -> bool:
        """End Retell call"""
        # API call would go here
        return True
    
    async def transfer_call(self, session_id: str, destination: str) -> bool:
        """Transfer Retell call"""
        # API call would go here
        return True
    
    async def send_message(self, session_id: str, message: str) -> bool:
        """Send message during Retell call"""
        # API call would go here
        return True
    
    async def get_call_status(self, session_id: str) -> Dict:
        """Get Retell call status"""
        return {
            "session_id": session_id,
            "status": "active",
            "duration_seconds": 120
        }
    
    async def get_call_recording(self, session_id: str) -> Optional[bytes]:
        """Get Retell call recording"""
        # API call would return actual recording
        return None
    
    async def get_call_transcript(self, session_id: str) -> Optional[str]:
        """Get Retell call transcript"""
        # API call would return actual transcript
        return "Sample transcript from Retell"
    
    async def register_webhook(self, event_type: str, url: str) -> bool:
        """Register Retell webhook"""
        # API call would go here
        return True
    
    async def handle_platform_event(self, raw_event: Dict) -> CallEvent:
        """Convert Retell event to standard format"""
        
        # Map Retell event types to standard types
        event_type_map = {
            "call_started": "connected",
            "call_ended": "ended",
            "user_transcript": "transcript",
            "agent_response": "agent_spoke",
            "call_transferred": "transferred",
            "error": "error"
        }
        
        retell_type = raw_event.get("event", "unknown")
        standard_type = event_type_map.get(retell_type, retell_type)
        
        return CallEvent(
            event_type=standard_type,
            session_id=raw_event.get("call_id", "unknown"),
            timestamp=datetime.now(),
            data={
                "platform": "retell",
                "original_event": retell_type,
                "text": raw_event.get("transcript", ""),
                "metadata": raw_event.get("metadata", {})
            }
        )
    
    async def format_platform_response(self, response: CallResponse) -> Dict:
        """Convert standard response to Retell format"""
        
        retell_response = {
            "response_id": datetime.now().timestamp(),
            "content": response.content
        }
        
        if response.action == "speak":
            retell_response["type"] = "response"
            retell_response["text"] = response.content
            
        elif response.action == "transfer":
            retell_response["type"] = "transfer"
            retell_response["transfer_to"] = response.content
            
        elif response.action == "end_call":
            retell_response["type"] = "end_call"
            
        return retell_response
    
    async def get_platform_capabilities(self) -> Dict:
        """Get Retell platform capabilities"""
        
        return {
            "platform": "retell",
            "version": "1.0",
            "capabilities": {
                "outbound_calling": True,
                "inbound_calling": True,
                "call_transfer": True,
                "call_recording": True,
                "real_time_transcription": True,
                "custom_voices": False,
                "voice_cloning": True,
                "languages": ["en-US"],
                "max_call_duration_minutes": 60,
                "webhooks": True,
                "websocket": True
            },
            "pricing": {
                "per_minute": 0.12,
                "minimum_charge": 0.02
            }
        }
    
    async def health_check(self) -> bool:
        """Check Retell API health"""
        # Would make actual API call
        return True

class RetellPlatformAdapter(VoicePlatformAdapter):
    """
    High-level Retell adapter with business logic integration
    """
    
    def __init__(self, api_key: Optional[str] = None):
        retell_interface = RetellAdapter(api_key)
        super().__init__(retell_interface)
        
        # Register default event handlers
        self.register_event_handler("connected", self.handle_call_connected)
        self.register_event_handler("transcript", self.handle_transcript)
        self.register_event_handler("ended", self.handle_call_ended)
    
    async def handle_call_connected(self, event: CallEvent) -> CallResponse:
        """Handle call connected event"""
        return await self.handle_conversation_flow(event)
    
    async def handle_transcript(self, event: CallEvent) -> CallResponse:
        """Handle user transcript"""
        return await self.handle_conversation_flow(event)
    
    async def handle_call_ended(self, event: CallEvent) -> CallResponse:
        """Handle call ended"""
        return await self.handle_conversation_flow(event)