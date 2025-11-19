"""
Platform-Agnostic Voice AI Orchestration Layer
Your intellectual property, completely independent of any specific platform
"""

from .orchestrator import UnifiedOrchestrator, PlatformType

# Core business logic
from .core.agent_types import AgentVertical, AgentTemplateLibrary, PersonalityProfile
from .core.conversation_state import (
    ConversationState,
    ConversationFlowManager,
    ConversationContext,
    TransitionTrigger
)

# Business engines
from .engines.business_engine import (
    MarketSegment,
    CustomerProfile,
    PricingStrategy,
    RevenueOptimizer
)
from .engines.sales_automation import (
    LeadSource,
    LeadStage,
    Lead,
    LeadScoringEngine,
    SalesAutomationWorkflow
)

# Platform interfaces
from .interfaces.voice_platform_interface import (
    VoiceAgentConfig,
    CallEvent,
    CallResponse,
    VoicePlatformInterface,
    VoicePlatformAdapter
)

__version__ = "1.0.0"
__author__ = "Your Company"

__all__ = [
    # Main orchestrator
    "UnifiedOrchestrator",
    "PlatformType",
    
    # Agent types
    "AgentVertical",
    "AgentTemplateLibrary",
    "PersonalityProfile",
    
    # Conversation management
    "ConversationState",
    "ConversationFlowManager",
    "ConversationContext",
    "TransitionTrigger",
    
    # Business logic
    "MarketSegment",
    "CustomerProfile",
    "PricingStrategy",
    "RevenueOptimizer",
    
    # Sales automation
    "LeadSource",
    "LeadStage",
    "Lead",
    "LeadScoringEngine",
    "SalesAutomationWorkflow",
    
    # Platform interfaces
    "VoiceAgentConfig",
    "CallEvent",
    "CallResponse",
    "VoicePlatformInterface",
    "VoicePlatformAdapter"
]