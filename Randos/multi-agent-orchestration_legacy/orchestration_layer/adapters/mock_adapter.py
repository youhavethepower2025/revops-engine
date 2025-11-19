"""
Mock platform adapter for testing
Simulates a voice platform without external dependencies
"""

from typing import Dict, List, Optional, Any
from datetime import datetime
import random

from ..interfaces.voice_platform_interface import (
    VoicePlatformInterface,
    VoiceAgentConfig,
    CallEvent,
    CallResponse,
    VoicePlatformAdapter
)

class MockAdapter(VoicePlatformInterface):
    """Mock adapter for testing business logic without a real platform"""
    
    def __init__(self):
        self.agents = {}
        self.sessions = {}
        self.call_counter = 0
    
    async def create_agent(self, config: VoiceAgentConfig) -> Dict:
        """Create mock agent"""
        agent_id = f"mock_{config.agent_id}"
        
        self.agents[agent_id] = {
            "config": config.to_dict(),
            "created_at": datetime.now().isoformat(),
            "status": "active",
            "mock_phone": f"+1415555{random.randint(1000, 9999)}"
        }
        
        return {
            "success": True,
            "platform": "mock",
            "agent_id": agent_id,
            "phone_number": self.agents[agent_id]["mock_phone"],
            "test_mode": True
        }
    
    async def update_agent(self, agent_id: str, config: VoiceAgentConfig) -> Dict:
        """Update mock agent"""
        if agent_id in self.agents:
            self.agents[agent_id]["config"] = config.to_dict()
            self.agents[agent_id]["updated_at"] = datetime.now().isoformat()
            return {"success": True, "agent_id": agent_id}
        return {"success": False, "error": "Agent not found"}
    
    async def delete_agent(self, agent_id: str) -> bool:
        """Delete mock agent"""
        if agent_id in self.agents:
            del self.agents[agent_id]
            return True
        return False
    
    async def get_agent(self, agent_id: str) -> Dict:
        """Get mock agent"""
        return self.agents.get(agent_id, {"error": "Agent not found"})
    
    async def list_agents(self) -> List[Dict]:
        """List mock agents"""
        return [
            {"agent_id": aid, "status": data["status"]}
            for aid, data in self.agents.items()
        ]
    
    async def start_call(self, agent_id: str, phone_number: str, metadata: Dict = None) -> Dict:
        """Start mock call"""
        self.call_counter += 1
        session_id = f"mock_session_{self.call_counter}"
        
        self.sessions[session_id] = {
            "agent_id": agent_id,
            "phone_number": phone_number,
            "start_time": datetime.now(),
            "status": "active",
            "metadata": metadata or {}
        }
        
        return {
            "success": True,
            "session_id": session_id,
            "status": "connected",
            "mock_call": True
        }
    
    async def end_call(self, session_id: str) -> bool:
        """End mock call"""
        if session_id in self.sessions:
            self.sessions[session_id]["status"] = "ended"
            self.sessions[session_id]["end_time"] = datetime.now()
            return True
        return False
    
    async def transfer_call(self, session_id: str, destination: str) -> bool:
        """Transfer mock call"""
        if session_id in self.sessions:
            self.sessions[session_id]["transferred_to"] = destination
            return True
        return False
    
    async def send_message(self, session_id: str, message: str) -> bool:
        """Send mock message"""
        if session_id in self.sessions:
            if "messages" not in self.sessions[session_id]:
                self.sessions[session_id]["messages"] = []
            self.sessions[session_id]["messages"].append({
                "timestamp": datetime.now().isoformat(),
                "message": message
            })
            return True
        return False
    
    async def get_call_status(self, session_id: str) -> Dict:
        """Get mock call status"""
        if session_id in self.sessions:
            session = self.sessions[session_id]
            duration = (datetime.now() - session["start_time"]).total_seconds()
            return {
                "session_id": session_id,
                "status": session["status"],
                "duration_seconds": duration
            }
        return {"error": "Session not found"}
    
    async def get_call_recording(self, session_id: str) -> Optional[bytes]:
        """Get mock recording"""
        # Return fake audio data for testing
        return b"MOCK_AUDIO_DATA"
    
    async def get_call_transcript(self, session_id: str) -> Optional[str]:
        """Get mock transcript"""
        return f"Mock transcript for session {session_id}"
    
    async def register_webhook(self, event_type: str, url: str) -> bool:
        """Register mock webhook"""
        return True
    
    async def handle_platform_event(self, raw_event: Dict) -> CallEvent:
        """Handle mock event"""
        return CallEvent(
            event_type=raw_event.get("type", "mock_event"),
            session_id=raw_event.get("session_id", "mock_session"),
            timestamp=datetime.now(),
            data=raw_event
        )
    
    async def format_platform_response(self, response: CallResponse) -> Dict:
        """Format mock response"""
        return {
            "mock_response": True,
            "action": response.action,
            "content": response.content,
            "timestamp": datetime.now().isoformat()
        }
    
    async def get_platform_capabilities(self) -> Dict:
        """Get mock capabilities"""
        return {
            "platform": "mock",
            "test_mode": True,
            "capabilities": {
                "all_features": True,
                "no_costs": True,
                "instant_responses": True
            }
        }
    
    async def health_check(self) -> bool:
        """Mock health check"""
        return True

class MockPlatformAdapter(VoicePlatformAdapter):
    """Mock platform adapter for testing"""
    
    def __init__(self):
        mock_interface = MockAdapter()
        super().__init__(mock_interface)