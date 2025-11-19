"""
Main Orchestrator - Platform-Agnostic Voice AI System
This is your intellectual property, completely independent of any specific platform
"""

import os
import asyncio
from typing import Dict, List, Optional, Any
from datetime import datetime
from enum import Enum

# Core business logic imports
from .core.agent_types import AgentVertical, AgentTemplateLibrary
from .core.conversation_state import ConversationFlowManager, ConversationState
from .engines.business_engine import (
    MarketSegment, 
    CustomerProfile, 
    PricingStrategy, 
    RevenueOptimizer
)
from .engines.sales_automation import (
    LeadSource,
    Lead,
    LeadScoringEngine,
    SalesAutomationWorkflow
)

# Platform interfaces
from .interfaces.voice_platform_interface import (
    VoiceAgentConfig,
    CallEvent,
    CallResponse,
    VoicePlatformAdapter
)

class PlatformType(Enum):
    """Supported voice platforms"""
    RETELL = "retell"
    PIPECAT = "pipecat"
    CUSTOM = "custom"
    MOCK = "mock"  # For testing

class UnifiedOrchestrator:
    """
    Main orchestrator that manages all business logic
    Platform-agnostic and portable
    """
    
    def __init__(self, platform: PlatformType = PlatformType.MOCK):
        # Initialize business engines
        self.conversation_manager = ConversationFlowManager()
        self.pricing_engine = PricingStrategy()
        self.revenue_optimizer = RevenueOptimizer()
        self.lead_scorer = LeadScoringEngine()
        self.sales_workflow = SalesAutomationWorkflow()
        
        # Initialize platform adapter
        self.platform_adapter = self._initialize_platform(platform)
        
        # Track active agents and sessions
        self.active_agents: Dict[str, Dict] = {}
        self.active_sessions: Dict[str, Dict] = {}
        
        # Business metrics
        self.metrics = {
            "total_calls": 0,
            "total_revenue": 0,
            "conversion_rate": 0,
            "average_call_duration": 0,
            "customer_satisfaction": 0
        }
    
    def _initialize_platform(self, platform: PlatformType) -> VoicePlatformAdapter:
        """Initialize the appropriate platform adapter"""
        
        if platform == PlatformType.RETELL:
            from .adapters.retell_adapter import RetellPlatformAdapter
            return RetellPlatformAdapter()
            
        elif platform == PlatformType.PIPECAT:
            from .adapters.pipecat_adapter import PipecatPlatformAdapter
            return PipecatPlatformAdapter()
            
        else:
            # Mock adapter for testing
            from .adapters.mock_adapter import MockPlatformAdapter
            return MockPlatformAdapter()
    
    async def create_agent(self,
                          vertical: AgentVertical,
                          name: str,
                          customer_profile: Optional[CustomerProfile] = None) -> Dict:
        """
        Create a voice agent for a specific vertical
        This method contains your business logic
        """
        
        # Get the appropriate template
        template = AgentTemplateLibrary.get_template(vertical)
        
        # Calculate optimal pricing if customer profile provided
        pricing = None
        if customer_profile:
            value_created = customer_profile.current_pain_cost * 1.5
            pricing = self.pricing_engine.calculate_optimal_price(
                customer_profile, 
                value_created
            )
        
        # Build agent configuration
        config = VoiceAgentConfig(
            agent_id=f"{vertical.value}_{datetime.now().timestamp()}",
            name=name,
            description=f"{vertical.value} voice agent",
            agent_type=vertical.value,
            personality_profile=template["personality"].__dict__,
            capabilities=template["capabilities"].to_dict(),
            
            # Voice settings based on vertical
            voice_gender=self._get_voice_gender(vertical),
            voice_style=self._get_voice_style(vertical),
            speaking_rate=self._get_speaking_rate(vertical),
            energy=template["personality"].emotional_intelligence
        )
        
        # Create agent on platform
        result = await self.platform_adapter.create_configured_agent(
            vertical.value,
            name,
            config.to_dict()
        )
        
        if result.get("success"):
            # Store agent with business metadata
            self.active_agents[result["agent_id"]] = {
                "vertical": vertical.value,
                "template": template,
                "config": config.to_dict(),
                "pricing": pricing,
                "customer_profile": customer_profile.__dict__ if customer_profile else None,
                "created_at": datetime.now().isoformat(),
                "platform_data": result
            }
        
        return result
    
    def _get_voice_gender(self, vertical: AgentVertical) -> str:
        """Determine voice gender based on vertical"""
        female_preferred = [
            AgentVertical.WELLNESS_COACH,
            AgentVertical.MEDICAL_RECEPTIONIST,
            AgentVertical.THERAPIST_INTAKE
        ]
        
        male_preferred = [
            AgentVertical.BUSINESS_ADVISOR,
            AgentVertical.FINANCIAL_CONSULTANT
        ]
        
        if vertical in female_preferred:
            return "female"
        elif vertical in male_preferred:
            return "male"
        else:
            return "neutral"
    
    def _get_voice_style(self, vertical: AgentVertical) -> str:
        """Determine voice style based on vertical"""
        professional = [
            AgentVertical.MEDICAL_RECEPTIONIST,
            AgentVertical.FINANCIAL_CONSULTANT,
            AgentVertical.LEGAL_ASSISTANT,
            AgentVertical.BUSINESS_ADVISOR
        ]
        
        if vertical in professional:
            return "professional"
        else:
            return "friendly"
    
    def _get_speaking_rate(self, vertical: AgentVertical) -> float:
        """Determine speaking rate based on vertical"""
        slower = [
            AgentVertical.SPIRITUAL_GUIDE,
            AgentVertical.THERAPIST_INTAKE,
            AgentVertical.EDUCATION_TUTOR
        ]
        
        if vertical in slower:
            return 0.9
        else:
            return 1.0
    
    async def process_lead(self,
                          company_name: str,
                          contact_name: str,
                          title: str,
                          source: LeadSource,
                          pain_points: List[str] = None) -> Dict:
        """
        Process a new lead through the sales automation system
        """
        
        # Create lead
        lead = Lead(
            lead_id=f"lead_{datetime.now().timestamp()}",
            source=source,
            company_name=company_name,
            contact_name=contact_name,
            title=title,
            pain_points=pain_points or []
        )
        
        # Score and process through workflow
        result = self.sales_workflow.process_lead(lead)
        
        # If high priority, create specialized agent
        if lead.priority in ["high", "urgent"]:
            # Determine best vertical for this lead
            vertical = self._determine_vertical_for_lead(lead)
            
            # Create customer profile
            profile = CustomerProfile(
                segment=self._map_to_market_segment(lead),
                company_size=lead.company_size or "11-50",
                current_pain_cost=50000,  # Estimate
                decision_maker=lead.title,
                sales_cycle_days=30,
                implementation_complexity="moderate",
                churn_risk=0.2,
                lifetime_value=100000,
                acquisition_cost=5000,
                profit_margin=0.7,
                expansion_potential=2.0
            )
            
            # Create personalized agent
            agent_result = await self.create_agent(
                vertical,
                f"Agent for {company_name}",
                profile
            )
            
            result["personalized_agent"] = agent_result
        
        return result
    
    def _determine_vertical_for_lead(self, lead: Lead) -> AgentVertical:
        """Determine best agent vertical for lead"""
        
        # Simple mapping based on pain points
        if any("appointment" in p.lower() for p in lead.pain_points):
            return AgentVertical.APPOINTMENT_SCHEDULER
        elif any("sales" in p.lower() for p in lead.pain_points):
            return AgentVertical.SALES_REPRESENTATIVE
        elif any("support" in p.lower() for p in lead.pain_points):
            return AgentVertical.CUSTOMER_SUPPORT
        else:
            return AgentVertical.BUSINESS_ADVISOR
    
    def _map_to_market_segment(self, lead: Lead) -> MarketSegment:
        """Map lead to market segment"""
        
        # Simple mapping based on company/industry
        if lead.industry:
            industry_lower = lead.industry.lower()
            if "health" in industry_lower or "medical" in industry_lower:
                return MarketSegment.HEALTHCARE
            elif "real estate" in industry_lower:
                return MarketSegment.REAL_ESTATE
            elif "finance" in industry_lower or "bank" in industry_lower:
                return MarketSegment.FINANCIAL
        
        # Default based on company size
        if lead.company_size in ["1-10", "11-50"]:
            return MarketSegment.LOCAL_BUSINESS
        else:
            return MarketSegment.ENTERPRISE_REPLACEMENT
    
    async def handle_call_event(self, session_id: str, event: CallEvent) -> Optional[Dict]:
        """
        Handle incoming call events from any platform
        This is where your business logic processes events
        """
        
        # Track session
        if session_id not in self.active_sessions:
            self.active_sessions[session_id] = {
                "start_time": datetime.now(),
                "events": [],
                "metrics": {}
            }
        
        self.active_sessions[session_id]["events"].append(event)
        
        # Process through conversation manager
        if event.event_type == "connected":
            # Start conversation
            agent_type = event.data.get("agent_type", "customer_support")
            context = self.conversation_manager.start_conversation(session_id, agent_type)
            
            # Get greeting from template
            if agent_type in self.active_agents:
                template = self.active_agents[agent_type].get("template")
                if template and "personality" in template:
                    greeting = template["personality"].response_patterns.get("greeting")
                    
                    return {
                        "response": CallResponse(
                            action="speak",
                            content=greeting,
                            metadata={"state": context.current_state.value}
                        )
                    }
        
        elif event.event_type == "transcript":
            # Process user input through conversation flow
            result = self.conversation_manager.process_event(
                session_id,
                "user_input",
                {"text": event.data.get("text", "")}
            )
            
            # Generate appropriate response
            return self._generate_response_from_state(result)
        
        elif event.event_type == "ended":
            # Calculate call metrics
            metrics = self._calculate_call_metrics(session_id)
            
            # Update business metrics
            self._update_business_metrics(metrics)
            
            # Clean up
            if session_id in self.active_sessions:
                del self.active_sessions[session_id]
            
            return {"metrics": metrics}
        
        return None
    
    def _generate_response_from_state(self, state_result: Dict) -> Dict:
        """Generate response based on conversation state"""
        
        current_state = state_result.get("current_state")
        
        if current_state == "booking_appointment":
            return {
                "response": CallResponse(
                    action="speak",
                    content="I'd be happy to schedule an appointment for you. What date and time work best?",
                    metadata=state_result
                )
            }
        
        elif current_state == "processing_payment":
            return {
                "response": CallResponse(
                    action="speak",
                    content="I can process your payment securely. Please confirm the amount.",
                    metadata=state_result
                )
            }
        
        elif state_result.get("requires_human"):
            return {
                "response": CallResponse(
                    action="transfer",
                    content="human_agent",
                    metadata=state_result
                )
            }
        
        else:
            return {
                "response": CallResponse(
                    action="speak",
                    content="I understand. How else can I help you?",
                    metadata=state_result
                )
            }
    
    def _calculate_call_metrics(self, session_id: str) -> Dict:
        """Calculate metrics for a call"""
        
        if session_id not in self.active_sessions:
            return {}
        
        session = self.active_sessions[session_id]
        duration = (datetime.now() - session["start_time"]).total_seconds()
        
        return {
            "session_id": session_id,
            "duration_seconds": duration,
            "total_events": len(session["events"]),
            "cost": duration * 0.002,  # $0.12/minute
            "revenue_generated": 0,  # Would calculate based on conversions
            "satisfaction_score": 0  # Would calculate from sentiment
        }
    
    def _update_business_metrics(self, call_metrics: Dict):
        """Update overall business metrics"""
        
        self.metrics["total_calls"] += 1
        
        if "duration_seconds" in call_metrics:
            # Update average duration
            current_avg = self.metrics["average_call_duration"]
            total_calls = self.metrics["total_calls"]
            new_avg = ((current_avg * (total_calls - 1)) + call_metrics["duration_seconds"]) / total_calls
            self.metrics["average_call_duration"] = new_avg
    
    def get_business_metrics(self) -> Dict:
        """Get current business metrics"""
        return self.metrics
    
    def get_agent_performance(self, agent_id: str) -> Dict:
        """Get performance metrics for an agent"""
        
        if agent_id not in self.active_agents:
            return {"error": "Agent not found"}
        
        agent = self.active_agents[agent_id]
        
        # Calculate performance (would be based on actual call data)
        return {
            "agent_id": agent_id,
            "vertical": agent["vertical"],
            "total_calls": 0,  # Would track
            "conversion_rate": 0,  # Would calculate
            "average_satisfaction": 0,  # Would calculate
            "revenue_generated": 0,  # Would track
            "created_at": agent["created_at"]
        }

# Example usage
async def main():
    """Example of using the platform-agnostic orchestrator"""
    
    # Initialize with Pipecat (can easily switch to Retell or custom)
    orchestrator = UnifiedOrchestrator(platform=PlatformType.PIPECAT)
    
    # Create a wellness coach agent
    print("Creating wellness coach agent...")
    agent_result = await orchestrator.create_agent(
        vertical=AgentVertical.WELLNESS_COACH,
        name="Sarah - Wellness Guide"
    )
    print(f"Agent created: {agent_result}")
    
    # Process a high-value lead
    print("\nProcessing new lead...")
    lead_result = await orchestrator.process_lead(
        company_name="Tech Startup Inc",
        contact_name="John Smith",
        title="CEO",
        source=LeadSource.INBOUND_WEBSITE,
        pain_points=["need 24/7 customer support", "reduce support costs"]
    )
    print(f"Lead processed: {lead_result}")
    
    # Simulate call event
    print("\nSimulating call event...")
    event = CallEvent(
        event_type="connected",
        session_id="test_session_123",
        timestamp=datetime.now(),
        data={"agent_type": "wellness_coach"}
    )
    
    response = await orchestrator.handle_call_event("test_session_123", event)
    print(f"Response: {response}")
    
    # Get business metrics
    print("\nBusiness metrics:")
    metrics = orchestrator.get_business_metrics()
    print(metrics)

if __name__ == "__main__":
    asyncio.run(main())