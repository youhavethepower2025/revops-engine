"""
Platform-agnostic voice platform interface
Defines the contract that any voice platform adapter must implement
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass
from datetime import datetime

@dataclass
class VoiceAgentConfig:
    """Platform-agnostic voice agent configuration"""
    agent_id: str
    name: str
    description: str
    
    # Voice settings (platform-agnostic)
    voice_gender: str = "neutral"  # male, female, neutral
    voice_age: str = "adult"  # child, teen, adult, senior
    voice_style: str = "professional"  # casual, professional, friendly, authoritative
    speaking_rate: float = 1.0  # 0.5 to 2.0
    pitch: float = 1.0  # 0.5 to 2.0
    energy: float = 0.7  # 0.0 to 1.0
    
    # Conversation settings
    interruption_sensitivity: float = 0.5  # 0.0 to 1.0
    silence_timeout_ms: int = 3000
    max_duration_ms: int = 3600000  # 1 hour
    
    # Business logic references
    agent_type: Optional[str] = None
    personality_profile: Optional[Dict] = None
    capabilities: Optional[Dict] = None
    conversation_flow: Optional[str] = None
    
    # Integration settings
    webhook_url: Optional[str] = None
    event_callbacks: Dict[str, str] = None
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            "agent_id": self.agent_id,
            "name": self.name,
            "description": self.description,
            "voice_settings": {
                "gender": self.voice_gender,
                "age": self.voice_age,
                "style": self.voice_style,
                "speaking_rate": self.speaking_rate,
                "pitch": self.pitch,
                "energy": self.energy
            },
            "conversation_settings": {
                "interruption_sensitivity": self.interruption_sensitivity,
                "silence_timeout_ms": self.silence_timeout_ms,
                "max_duration_ms": self.max_duration_ms
            },
            "business_logic": {
                "agent_type": self.agent_type,
                "personality_profile": self.personality_profile,
                "capabilities": self.capabilities,
                "conversation_flow": self.conversation_flow
            },
            "integrations": {
                "webhook_url": self.webhook_url,
                "event_callbacks": self.event_callbacks or {}
            }
        }

@dataclass
class CallEvent:
    """Platform-agnostic call event"""
    event_type: str  # connected, transcript, ended, error, etc.
    session_id: str
    timestamp: datetime
    data: Dict[str, Any]
    
    def to_dict(self) -> Dict:
        return {
            "event_type": self.event_type,
            "session_id": self.session_id,
            "timestamp": self.timestamp.isoformat(),
            "data": self.data
        }

@dataclass
class CallResponse:
    """Platform-agnostic response to voice platform"""
    action: str  # speak, transfer, end_call, play_audio, etc.
    content: Optional[str] = None
    metadata: Dict[str, Any] = None
    
    def to_dict(self) -> Dict:
        return {
            "action": self.action,
            "content": self.content,
            "metadata": self.metadata or {}
        }

class VoicePlatformInterface(ABC):
    """
    Abstract interface that all voice platform adapters must implement
    This ensures complete platform independence
    """
    
    @abstractmethod
    async def create_agent(self, config: VoiceAgentConfig) -> Dict:
        """Create a new voice agent"""
        pass
    
    @abstractmethod
    async def update_agent(self, agent_id: str, config: VoiceAgentConfig) -> Dict:
        """Update an existing agent"""
        pass
    
    @abstractmethod
    async def delete_agent(self, agent_id: str) -> bool:
        """Delete an agent"""
        pass
    
    @abstractmethod
    async def get_agent(self, agent_id: str) -> Dict:
        """Get agent details"""
        pass
    
    @abstractmethod
    async def list_agents(self) -> List[Dict]:
        """List all agents"""
        pass
    
    @abstractmethod
    async def start_call(self, agent_id: str, phone_number: str, metadata: Dict = None) -> Dict:
        """Initiate an outbound call"""
        pass
    
    @abstractmethod
    async def end_call(self, session_id: str) -> bool:
        """End an active call"""
        pass
    
    @abstractmethod
    async def transfer_call(self, session_id: str, destination: str) -> bool:
        """Transfer call to another number or agent"""
        pass
    
    @abstractmethod
    async def send_message(self, session_id: str, message: str) -> bool:
        """Send a message during active call"""
        pass
    
    @abstractmethod
    async def get_call_status(self, session_id: str) -> Dict:
        """Get current call status"""
        pass
    
    @abstractmethod
    async def get_call_recording(self, session_id: str) -> Optional[bytes]:
        """Get call recording if available"""
        pass
    
    @abstractmethod
    async def get_call_transcript(self, session_id: str) -> Optional[str]:
        """Get call transcript"""
        pass
    
    @abstractmethod
    async def register_webhook(self, event_type: str, url: str) -> bool:
        """Register webhook for events"""
        pass
    
    @abstractmethod
    async def handle_platform_event(self, raw_event: Dict) -> CallEvent:
        """Convert platform-specific event to standard format"""
        pass
    
    @abstractmethod
    async def format_platform_response(self, response: CallResponse) -> Dict:
        """Convert standard response to platform-specific format"""
        pass
    
    @abstractmethod
    async def get_platform_capabilities(self) -> Dict:
        """Get platform-specific capabilities and limitations"""
        pass
    
    @abstractmethod
    async def health_check(self) -> bool:
        """Check if platform connection is healthy"""
        pass

class VoicePlatformAdapter:
    """
    Base adapter class with common functionality
    Specific platform adapters should inherit from this
    """
    
    def __init__(self, platform_interface: VoicePlatformInterface):
        self.platform = platform_interface
        self.event_handlers: Dict[str, Callable] = {}
        self.active_sessions: Dict[str, Dict] = {}
        
    def register_event_handler(self, event_type: str, handler: Callable):
        """Register handler for specific event type"""
        self.event_handlers[event_type] = handler
        
    async def process_event(self, raw_event: Dict) -> Optional[Dict]:
        """Process incoming platform event"""
        
        # Convert to standard format
        event = await self.platform.handle_platform_event(raw_event)
        
        # Track session
        if event.session_id not in self.active_sessions:
            self.active_sessions[event.session_id] = {
                "start_time": datetime.now(),
                "events": []
            }
        
        self.active_sessions[event.session_id]["events"].append(event)
        
        # Call registered handler
        if event.event_type in self.event_handlers:
            handler = self.event_handlers[event.event_type]
            response = await handler(event)
            
            if response:
                # Convert response to platform format
                platform_response = await self.platform.format_platform_response(response)
                return platform_response
        
        return None
    
    async def create_configured_agent(self, 
                                    agent_type: str,
                                    name: str,
                                    custom_config: Dict = None) -> Dict:
        """Create agent with business logic configuration"""
        
        from ..core.agent_types import AgentTemplateLibrary, AgentVertical
        
        # Get template for agent type
        try:
            vertical = AgentVertical(agent_type)
            template = AgentTemplateLibrary.get_template(vertical)
        except ValueError:
            template = AgentTemplateLibrary.get_template(AgentVertical.CUSTOMER_SUPPORT)
        
        # Build configuration
        config = VoiceAgentConfig(
            agent_id=f"{agent_type}_{datetime.now().timestamp()}",
            name=name,
            description=f"{agent_type} voice agent",
            agent_type=agent_type,
            personality_profile=template["personality"].__dict__,
            capabilities=template["capabilities"].to_dict()
        )
        
        # Apply custom configuration
        if custom_config:
            for key, value in custom_config.items():
                if hasattr(config, key):
                    setattr(config, key, value)
        
        # Create agent on platform
        result = await self.platform.create_agent(config)
        
        return result
    
    async def handle_conversation_flow(self, event: CallEvent) -> CallResponse:
        """Handle conversation flow based on business logic"""
        
        from ..core.conversation_state import ConversationFlowManager
        
        # Get or create flow manager
        if not hasattr(self, 'flow_manager'):
            self.flow_manager = ConversationFlowManager()
        
        session_id = event.session_id
        
        # Process event through conversation flow
        if event.event_type == "connected":
            # Start new conversation
            agent_type = event.data.get("agent_type", "customer_support")
            context = self.flow_manager.start_conversation(session_id, agent_type)
            
            # Return greeting
            return CallResponse(
                action="speak",
                content="Hello! How can I assist you today?",
                metadata={"state": context.current_state.value}
            )
        
        elif event.event_type == "transcript":
            # Process user input
            result = self.flow_manager.process_event(
                session_id,
                "user_input",
                {"text": event.data.get("text", "")}
            )
            
            # Generate response based on state
            if result.get("current_state") == "booking_appointment":
                return CallResponse(
                    action="speak",
                    content=result.get("prompt", "Let me help you schedule an appointment."),
                    metadata=result
                )
            elif result.get("requires_human"):
                return CallResponse(
                    action="transfer",
                    content="human_agent",
                    metadata=result
                )
            else:
                return CallResponse(
                    action="speak",
                    content="I understand. Let me help you with that.",
                    metadata=result
                )
        
        elif event.event_type == "ended":
            # Clean up conversation
            metrics = self.flow_manager.end_conversation(session_id)
            
            # Log metrics
            print(f"Call ended. Metrics: {metrics}")
            
            return None
        
        return None
    
    async def get_session_metrics(self, session_id: str) -> Dict:
        """Get metrics for a session"""
        
        if session_id not in self.active_sessions:
            return {"error": "Session not found"}
        
        session = self.active_sessions[session_id]
        
        return {
            "session_id": session_id,
            "duration_seconds": (datetime.now() - session["start_time"]).total_seconds(),
            "total_events": len(session["events"]),
            "event_types": list(set(e.event_type for e in session["events"]))
        }