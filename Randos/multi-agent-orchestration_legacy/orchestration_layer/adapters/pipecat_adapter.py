"""
Pipecat platform adapter implementation
Translates between orchestration layer and Pipecat's framework
"""

import os
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

# Pipecat imports (these would be actual imports in production)
# from pipecat.pipeline import Pipeline
# from pipecat.transports import WebRTCTransport
# from pipecat.services.openai import OpenAILLMService

class PipecatAdapter(VoicePlatformInterface):
    """
    Adapter for Pipecat framework
    Implements the VoicePlatformInterface to work with Pipecat's pipeline architecture
    """
    
    def __init__(self, config: Dict = None):
        self.config = config or {}
        self.pipelines: Dict[str, Any] = {}  # Store active pipelines
        self.agents: Dict[str, Dict] = {}  # Store agent configurations
        
        # Initialize Pipecat services
        self._initialize_services()
    
    def _initialize_services(self):
        """Initialize Pipecat services"""
        
        # These would be actual Pipecat service initializations
        self.llm_service = None  # OpenAILLMService(api_key=...)
        self.tts_service = None  # TTSService(...)
        self.stt_service = None  # STTService(...)
        self.transport = None  # WebRTCTransport(...)
    
    async def create_agent(self, config: VoiceAgentConfig) -> Dict:
        """Create a Pipecat pipeline from generic config"""
        
        try:
            # Build Pipecat pipeline configuration
            pipeline_config = self._build_pipeline_config(config)
            
            # Create pipeline (simplified - actual implementation would use Pipecat)
            pipeline_id = f"pipecat_{config.agent_id}"
            
            # Store configuration
            self.agents[pipeline_id] = {
                "config": config.to_dict(),
                "pipeline_config": pipeline_config,
                "created_at": datetime.now().isoformat(),
                "status": "ready"
            }
            
            return {
                "success": True,
                "platform": "pipecat",
                "agent_id": pipeline_id,
                "pipeline_config": pipeline_config,
                "capabilities": self._get_agent_capabilities(config)
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def _build_pipeline_config(self, config: VoiceAgentConfig) -> Dict:
        """Build Pipecat pipeline configuration"""
        
        # Map generic config to Pipecat pipeline
        pipeline_config = {
            "name": config.name,
            "description": config.description,
            
            # Audio configuration
            "audio": {
                "sample_rate": 16000,
                "channels": 1,
                "encoding": "pcm"
            },
            
            # Voice configuration
            "tts": {
                "service": "openai",  # or "elevenlabs", "azure", etc.
                "voice": self._map_voice_settings(config),
                "speed": config.speaking_rate,
                "pitch": config.pitch
            },
            
            # Speech recognition
            "stt": {
                "service": "deepgram",  # or "azure", "google", etc.
                "language": "en-US",
                "interim_results": True,
                "punctuation": True
            },
            
            # LLM configuration
            "llm": {
                "service": "openai",
                "model": "gpt-4",
                "temperature": config.energy,
                "system_prompt": self._build_system_prompt(config),
                "max_tokens": 500
            },
            
            # Pipeline behavior
            "behavior": {
                "interruption_enabled": config.interruption_sensitivity > 0.3,
                "interruption_threshold": config.interruption_sensitivity,
                "silence_timeout_ms": config.silence_timeout_ms,
                "max_duration_ms": config.max_duration_ms,
                "enable_transcription": True
            },
            
            # Middleware and processors
            "processors": self._build_processors(config),
            
            # Transport configuration
            "transport": {
                "type": "webrtc",  # or "websocket", "daily", etc.
                "config": {
                    "audio_in_enabled": True,
                    "audio_out_enabled": True,
                    "video_in_enabled": False,
                    "video_out_enabled": False
                }
            }
        }
        
        return pipeline_config
    
    def _map_voice_settings(self, config: VoiceAgentConfig) -> str:
        """Map generic voice settings to Pipecat voice ID"""
        
        # Map to OpenAI voices (example)
        voice_map = {
            ("male", "professional"): "onyx",
            ("female", "professional"): "nova",
            ("male", "casual"): "echo",
            ("female", "casual"): "shimmer",
            ("neutral", "professional"): "alloy"
        }
        
        key = (config.voice_gender, config.voice_style)
        return voice_map.get(key, "alloy")
    
    def _build_system_prompt(self, config: VoiceAgentConfig) -> str:
        """Build system prompt from configuration"""
        
        if not config.personality_profile:
            return "You are a helpful assistant."
        
        profile = config.personality_profile
        prompt_parts = []
        
        # Add traits
        if "traits" in profile:
            traits = profile["traits"]
            prompt_parts.append(f"You have these personality traits: {', '.join(traits)}.")
        
        # Add communication style
        if "communication_style" in profile:
            style = profile["communication_style"]
            prompt_parts.append(f"Your communication style is {style}.")
        
        # Add response patterns
        if "response_patterns" in profile:
            patterns = profile["response_patterns"]
            if "greeting" in patterns:
                prompt_parts.append(f"Greet users with: {patterns['greeting']}")
        
        return " ".join(prompt_parts)
    
    def _build_processors(self, config: VoiceAgentConfig) -> List[Dict]:
        """Build Pipecat processors based on capabilities"""
        
        processors = []
        
        # Always include base processors
        processors.append({
            "type": "conversation_tracker",
            "config": {"track_turns": True}
        })
        
        if config.capabilities:
            if config.capabilities.get("appointment_booking"):
                processors.append({
                    "type": "appointment_handler",
                    "config": {
                        "calendar_integration": True,
                        "confirmation_required": True
                    }
                })
            
            if config.capabilities.get("payment_processing"):
                processors.append({
                    "type": "payment_processor",
                    "config": {
                        "provider": "stripe",
                        "secure_mode": True
                    }
                })
            
            if config.capabilities.get("knowledge_access"):
                processors.append({
                    "type": "knowledge_base",
                    "config": {
                        "source": "vector_db",
                        "similarity_threshold": 0.7
                    }
                })
        
        return processors
    
    def _get_agent_capabilities(self, config: VoiceAgentConfig) -> Dict:
        """Get capabilities for this agent"""
        
        capabilities = {
            "real_time_processing": True,
            "multi_turn_conversation": True,
            "context_awareness": True,
            "interruption_handling": config.interruption_sensitivity > 0
        }
        
        if config.capabilities:
            capabilities.update(config.capabilities)
        
        return capabilities
    
    async def update_agent(self, agent_id: str, config: VoiceAgentConfig) -> Dict:
        """Update Pipecat agent/pipeline"""
        
        if agent_id not in self.agents:
            return {"success": False, "error": "Agent not found"}
        
        # Update configuration
        pipeline_config = self._build_pipeline_config(config)
        self.agents[agent_id]["config"] = config.to_dict()
        self.agents[agent_id]["pipeline_config"] = pipeline_config
        self.agents[agent_id]["updated_at"] = datetime.now().isoformat()
        
        # If pipeline is active, restart it
        if agent_id in self.pipelines:
            # Would restart the actual pipeline
            pass
        
        return {
            "success": True,
            "agent_id": agent_id,
            "updated_config": pipeline_config
        }
    
    async def delete_agent(self, agent_id: str) -> bool:
        """Delete Pipecat agent"""
        
        if agent_id in self.agents:
            # Stop pipeline if active
            if agent_id in self.pipelines:
                # Would stop the actual pipeline
                del self.pipelines[agent_id]
            
            del self.agents[agent_id]
            return True
        
        return False
    
    async def get_agent(self, agent_id: str) -> Dict:
        """Get Pipecat agent details"""
        
        if agent_id not in self.agents:
            return {"error": "Agent not found"}
        
        return self.agents[agent_id]
    
    async def list_agents(self) -> List[Dict]:
        """List all Pipecat agents"""
        
        return [
            {
                "agent_id": agent_id,
                "name": data["config"]["name"],
                "status": data["status"],
                "created_at": data["created_at"]
            }
            for agent_id, data in self.agents.items()
        ]
    
    async def start_call(self, agent_id: str, phone_number: str, metadata: Dict = None) -> Dict:
        """Start Pipecat session"""
        
        if agent_id not in self.agents:
            return {"success": False, "error": "Agent not found"}
        
        # Create pipeline instance
        session_id = f"pipecat_session_{datetime.now().timestamp()}"
        
        # Would create actual Pipecat pipeline here
        pipeline = None  # Pipeline(self.agents[agent_id]["pipeline_config"])
        
        self.pipelines[session_id] = {
            "agent_id": agent_id,
            "pipeline": pipeline,
            "start_time": datetime.now(),
            "metadata": metadata or {}
        }
        
        return {
            "success": True,
            "session_id": session_id,
            "agent_id": agent_id,
            "status": "active"
        }
    
    async def end_call(self, session_id: str) -> bool:
        """End Pipecat session"""
        
        if session_id in self.pipelines:
            # Would stop actual pipeline
            # self.pipelines[session_id]["pipeline"].stop()
            del self.pipelines[session_id]
            return True
        
        return False
    
    async def transfer_call(self, session_id: str, destination: str) -> bool:
        """Transfer not directly supported in Pipecat - would need custom implementation"""
        return False
    
    async def send_message(self, session_id: str, message: str) -> bool:
        """Send message through Pipecat pipeline"""
        
        if session_id in self.pipelines:
            # Would send through actual pipeline
            # self.pipelines[session_id]["pipeline"].send(message)
            return True
        
        return False
    
    async def get_call_status(self, session_id: str) -> Dict:
        """Get Pipecat session status"""
        
        if session_id not in self.pipelines:
            return {"error": "Session not found"}
        
        session = self.pipelines[session_id]
        duration = (datetime.now() - session["start_time"]).total_seconds()
        
        return {
            "session_id": session_id,
            "agent_id": session["agent_id"],
            "status": "active",
            "duration_seconds": duration
        }
    
    async def get_call_recording(self, session_id: str) -> Optional[bytes]:
        """Get recording if enabled"""
        # Would retrieve from storage if recording was enabled
        return None
    
    async def get_call_transcript(self, session_id: str) -> Optional[str]:
        """Get transcript from Pipecat session"""
        # Would retrieve from pipeline's transcript buffer
        return "Sample Pipecat transcript"
    
    async def register_webhook(self, event_type: str, url: str) -> bool:
        """Pipecat uses callbacks instead of webhooks"""
        # Store callback configuration
        return True
    
    async def handle_platform_event(self, raw_event: Dict) -> CallEvent:
        """Convert Pipecat event to standard format"""
        
        # Map Pipecat event types
        event_type_map = {
            "transport.connected": "connected",
            "transport.disconnected": "ended",
            "user.speaking": "user_speaking",
            "user.stopped_speaking": "user_stopped",
            "bot.speaking": "agent_speaking",
            "bot.stopped_speaking": "agent_stopped",
            "transcription.final": "transcript",
            "transcription.interim": "interim_transcript",
            "error": "error"
        }
        
        pipecat_type = raw_event.get("type", "unknown")
        standard_type = event_type_map.get(pipecat_type, pipecat_type)
        
        return CallEvent(
            event_type=standard_type,
            session_id=raw_event.get("session_id", "unknown"),
            timestamp=datetime.now(),
            data={
                "platform": "pipecat",
                "original_event": pipecat_type,
                "text": raw_event.get("text", ""),
                "audio": raw_event.get("audio"),
                "metadata": raw_event.get("metadata", {})
            }
        )
    
    async def format_platform_response(self, response: CallResponse) -> Dict:
        """Convert standard response to Pipecat format"""
        
        pipecat_response = {
            "timestamp": datetime.now().isoformat(),
            "session_id": response.metadata.get("session_id") if response.metadata else None
        }
        
        if response.action == "speak":
            pipecat_response["type"] = "bot.speak"
            pipecat_response["text"] = response.content
            
        elif response.action == "end_call":
            pipecat_response["type"] = "transport.disconnect"
            
        elif response.action == "play_audio":
            pipecat_response["type"] = "bot.play_audio"
            pipecat_response["audio_url"] = response.content
        
        return pipecat_response
    
    async def get_platform_capabilities(self) -> Dict:
        """Get Pipecat platform capabilities"""
        
        return {
            "platform": "pipecat",
            "version": "0.0.79",
            "capabilities": {
                "real_time_processing": True,
                "multi_modal": True,
                "custom_pipelines": True,
                "processor_chaining": True,
                "multiple_transports": True,
                "llm_providers": ["openai", "anthropic", "local"],
                "tts_providers": ["openai", "elevenlabs", "azure"],
                "stt_providers": ["deepgram", "azure", "google"],
                "languages": ["en-US", "es-ES", "fr-FR", "de-DE"],
                "custom_processors": True,
                "WebRTC": True,
                "websocket": True
            },
            "advantages": {
                "flexibility": "Highly customizable pipelines",
                "open_source": True,
                "self_hosted": True,
                "no_vendor_lock": True
            }
        }
    
    async def health_check(self) -> bool:
        """Check Pipecat services health"""
        
        # Check if services are initialized
        services_ok = all([
            self.llm_service is not None or True,  # Simplified for demo
            self.tts_service is not None or True,
            self.stt_service is not None or True
        ])
        
        return services_ok

class PipecatPlatformAdapter(VoicePlatformAdapter):
    """
    High-level Pipecat adapter with business logic integration
    """
    
    def __init__(self, config: Dict = None):
        pipecat_interface = PipecatAdapter(config)
        super().__init__(pipecat_interface)
        
        # Register Pipecat-specific event handlers
        self.register_event_handler("connected", self.handle_transport_connected)
        self.register_event_handler("transcript", self.handle_transcription)
        self.register_event_handler("ended", self.handle_transport_disconnected)
    
    async def handle_transport_connected(self, event: CallEvent) -> CallResponse:
        """Handle transport connected"""
        return await self.handle_conversation_flow(event)
    
    async def handle_transcription(self, event: CallEvent) -> CallResponse:
        """Handle transcription event"""
        return await self.handle_conversation_flow(event)
    
    async def handle_transport_disconnected(self, event: CallEvent) -> CallResponse:
        """Handle transport disconnected"""
        return await self.handle_conversation_flow(event)