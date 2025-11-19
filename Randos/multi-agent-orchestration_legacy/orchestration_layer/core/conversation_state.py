"""
Platform-agnostic conversation state management
Handles conversation flow, state transitions, and business logic
"""

from enum import Enum
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime

class ConversationState(Enum):
    """Universal conversation states"""
    INITIALIZING = "initializing"
    GREETING = "greeting"
    IDENTIFYING_INTENT = "identifying_intent"
    MAIN_CONVERSATION = "main_conversation"
    COLLECTING_INFORMATION = "collecting_information"
    PROVIDING_SERVICE = "providing_service"
    BOOKING_APPOINTMENT = "booking_appointment"
    PROCESSING_PAYMENT = "processing_payment"
    HANDLING_OBJECTION = "handling_objection"
    ESCALATING = "escalating"
    CONFIRMING = "confirming"
    CLOSING = "closing"
    ENDED = "ended"
    ERROR = "error"

class TransitionTrigger(Enum):
    """Events that trigger state transitions"""
    USER_GREETING = "user_greeting"
    INTENT_IDENTIFIED = "intent_identified"
    INFORMATION_PROVIDED = "information_provided"
    SERVICE_REQUESTED = "service_requested"
    APPOINTMENT_REQUESTED = "appointment_requested"
    PAYMENT_REQUESTED = "payment_requested"
    OBJECTION_RAISED = "objection_raised"
    ESCALATION_NEEDED = "escalation_needed"
    CONFIRMATION_RECEIVED = "confirmation_received"
    CONVERSATION_COMPLETE = "conversation_complete"
    ERROR_OCCURRED = "error_occurred"
    TIMEOUT = "timeout"
    USER_HANGUP = "user_hangup"

@dataclass
class ConversationContext:
    """Context maintained throughout conversation"""
    session_id: str
    user_id: Optional[str] = None
    agent_type: Optional[str] = None
    current_state: ConversationState = ConversationState.INITIALIZING
    previous_state: Optional[ConversationState] = None
    
    # Conversation data
    intent: Optional[str] = None
    sentiment: float = 0.0  # -1.0 to 1.0
    collected_data: Dict[str, Any] = field(default_factory=dict)
    
    # Business data
    appointment_details: Optional[Dict] = None
    payment_details: Optional[Dict] = None
    service_requested: Optional[str] = None
    
    # Metrics
    start_time: datetime = field(default_factory=datetime.now)
    state_transitions: List[Dict] = field(default_factory=list)
    total_duration_seconds: float = 0.0
    
    # Flags
    requires_human: bool = False
    conversion_complete: bool = False
    satisfaction_score: Optional[float] = None

class StateTransitionRule:
    """Defines rules for state transitions"""
    
    def __init__(self, 
                 from_state: ConversationState,
                 trigger: TransitionTrigger,
                 to_state: ConversationState,
                 condition: Optional[Callable[[ConversationContext], bool]] = None,
                 action: Optional[Callable[[ConversationContext], None]] = None):
        self.from_state = from_state
        self.trigger = trigger
        self.to_state = to_state
        self.condition = condition or (lambda ctx: True)
        self.action = action
        
    def can_transition(self, context: ConversationContext) -> bool:
        """Check if transition is valid given context"""
        return (context.current_state == self.from_state and 
                self.condition(context))
    
    def execute(self, context: ConversationContext) -> None:
        """Execute the transition"""
        context.previous_state = context.current_state
        context.current_state = self.to_state
        
        # Record transition
        context.state_transitions.append({
            "from": self.from_state.value,
            "to": self.to_state.value,
            "trigger": self.trigger.value,
            "timestamp": datetime.now().isoformat()
        })
        
        # Execute action if defined
        if self.action:
            self.action(context)

class ConversationStateMachine:
    """Platform-agnostic state machine for conversations"""
    
    def __init__(self):
        self.rules: List[StateTransitionRule] = []
        self._build_standard_rules()
        
    def _build_standard_rules(self):
        """Build standard transition rules"""
        
        # Initialization to greeting
        self.add_rule(
            ConversationState.INITIALIZING,
            TransitionTrigger.USER_GREETING,
            ConversationState.GREETING
        )
        
        # Greeting to intent identification
        self.add_rule(
            ConversationState.GREETING,
            TransitionTrigger.INTENT_IDENTIFIED,
            ConversationState.IDENTIFYING_INTENT
        )
        
        # Intent to main conversation
        self.add_rule(
            ConversationState.IDENTIFYING_INTENT,
            TransitionTrigger.INTENT_IDENTIFIED,
            ConversationState.MAIN_CONVERSATION
        )
        
        # Main conversation branches
        self.add_rule(
            ConversationState.MAIN_CONVERSATION,
            TransitionTrigger.APPOINTMENT_REQUESTED,
            ConversationState.BOOKING_APPOINTMENT,
            condition=lambda ctx: ctx.agent_type in ["medical_receptionist", "wellness_coach"]
        )
        
        self.add_rule(
            ConversationState.MAIN_CONVERSATION,
            TransitionTrigger.PAYMENT_REQUESTED,
            ConversationState.PROCESSING_PAYMENT,
            condition=lambda ctx: ctx.collected_data.get("payment_authorized", False)
        )
        
        self.add_rule(
            ConversationState.MAIN_CONVERSATION,
            TransitionTrigger.ESCALATION_NEEDED,
            ConversationState.ESCALATING,
            action=lambda ctx: setattr(ctx, "requires_human", True)
        )
        
        # Appointment booking flow
        self.add_rule(
            ConversationState.BOOKING_APPOINTMENT,
            TransitionTrigger.CONFIRMATION_RECEIVED,
            ConversationState.CONFIRMING,
            action=lambda ctx: setattr(ctx, "conversion_complete", True)
        )
        
        # Payment processing flow
        self.add_rule(
            ConversationState.PROCESSING_PAYMENT,
            TransitionTrigger.CONFIRMATION_RECEIVED,
            ConversationState.CONFIRMING,
            action=lambda ctx: setattr(ctx, "conversion_complete", True)
        )
        
        # Objection handling
        self.add_rule(
            ConversationState.MAIN_CONVERSATION,
            TransitionTrigger.OBJECTION_RAISED,
            ConversationState.HANDLING_OBJECTION
        )
        
        self.add_rule(
            ConversationState.HANDLING_OBJECTION,
            TransitionTrigger.OBJECTION_RAISED,
            ConversationState.MAIN_CONVERSATION,
            condition=lambda ctx: ctx.sentiment > -0.5  # If sentiment improves
        )
        
        # Closing flows
        self.add_rule(
            ConversationState.CONFIRMING,
            TransitionTrigger.CONVERSATION_COMPLETE,
            ConversationState.CLOSING
        )
        
        self.add_rule(
            ConversationState.CLOSING,
            TransitionTrigger.USER_HANGUP,
            ConversationState.ENDED
        )
        
        # Error handling
        for state in ConversationState:
            if state not in [ConversationState.ERROR, ConversationState.ENDED]:
                self.add_rule(
                    state,
                    TransitionTrigger.ERROR_OCCURRED,
                    ConversationState.ERROR
                )
        
    def add_rule(self, 
                 from_state: ConversationState,
                 trigger: TransitionTrigger,
                 to_state: ConversationState,
                 condition: Optional[Callable] = None,
                 action: Optional[Callable] = None):
        """Add a transition rule"""
        self.rules.append(StateTransitionRule(
            from_state, trigger, to_state, condition, action
        ))
        
    def process_trigger(self, 
                       context: ConversationContext,
                       trigger: TransitionTrigger) -> bool:
        """Process a trigger and update state if applicable"""
        
        for rule in self.rules:
            if (rule.from_state == context.current_state and 
                rule.trigger == trigger and 
                rule.can_transition(context)):
                
                rule.execute(context)
                return True
                
        return False
    
    def get_valid_triggers(self, context: ConversationContext) -> List[TransitionTrigger]:
        """Get all valid triggers from current state"""
        valid_triggers = []
        
        for rule in self.rules:
            if (rule.from_state == context.current_state and 
                rule.can_transition(context)):
                valid_triggers.append(rule.trigger)
                
        return valid_triggers

class ConversationFlowManager:
    """Manages conversation flow logic"""
    
    def __init__(self):
        self.state_machine = ConversationStateMachine()
        self.contexts: Dict[str, ConversationContext] = {}
        
    def start_conversation(self, session_id: str, agent_type: str) -> ConversationContext:
        """Start a new conversation"""
        context = ConversationContext(
            session_id=session_id,
            agent_type=agent_type,
            current_state=ConversationState.INITIALIZING
        )
        
        self.contexts[session_id] = context
        return context
        
    def process_event(self, session_id: str, event_type: str, data: Dict = None) -> Dict:
        """Process a conversation event"""
        
        if session_id not in self.contexts:
            return {"error": "Session not found"}
            
        context = self.contexts[session_id]
        
        # Map event to trigger
        trigger = self._map_event_to_trigger(event_type, data, context)
        
        if trigger:
            # Update context with event data
            self._update_context(context, event_type, data)
            
            # Process state transition
            transitioned = self.state_machine.process_trigger(context, trigger)
            
            # Generate response based on new state
            response = self._generate_response(context, transitioned)
            
            return response
        else:
            return {
                "error": "Invalid event",
                "current_state": context.current_state.value
            }
    
    def _map_event_to_trigger(self, 
                             event_type: str, 
                             data: Dict,
                             context: ConversationContext) -> Optional[TransitionTrigger]:
        """Map platform events to triggers"""
        
        event_trigger_map = {
            "user_connected": TransitionTrigger.USER_GREETING,
            "intent_detected": TransitionTrigger.INTENT_IDENTIFIED,
            "appointment_request": TransitionTrigger.APPOINTMENT_REQUESTED,
            "payment_request": TransitionTrigger.PAYMENT_REQUESTED,
            "objection": TransitionTrigger.OBJECTION_RAISED,
            "escalate": TransitionTrigger.ESCALATION_NEEDED,
            "confirm": TransitionTrigger.CONFIRMATION_RECEIVED,
            "end_call": TransitionTrigger.CONVERSATION_COMPLETE,
            "error": TransitionTrigger.ERROR_OCCURRED
        }
        
        return event_trigger_map.get(event_type)
    
    def _update_context(self, context: ConversationContext, event_type: str, data: Dict):
        """Update context based on event data"""
        
        if data:
            # Update intent
            if "intent" in data:
                context.intent = data["intent"]
                
            # Update sentiment
            if "sentiment" in data:
                context.sentiment = data["sentiment"]
                
            # Collect data
            if "collected_data" in data:
                context.collected_data.update(data["collected_data"])
                
            # Update business data
            if "appointment" in data:
                context.appointment_details = data["appointment"]
                
            if "payment" in data:
                context.payment_details = data["payment"]
                
    def _generate_response(self, context: ConversationContext, transitioned: bool) -> Dict:
        """Generate response based on current state"""
        
        response = {
            "session_id": context.session_id,
            "current_state": context.current_state.value,
            "transitioned": transitioned,
            "valid_actions": [t.value for t in self.state_machine.get_valid_triggers(context)],
            "requires_human": context.requires_human,
            "conversion_complete": context.conversion_complete
        }
        
        # Add state-specific response data
        if context.current_state == ConversationState.BOOKING_APPOINTMENT:
            response["prompt"] = "What date and time would work best for you?"
            response["required_fields"] = ["date", "time", "service"]
            
        elif context.current_state == ConversationState.PROCESSING_PAYMENT:
            response["prompt"] = "I can process your payment now. The total is..."
            response["required_fields"] = ["amount", "method"]
            
        elif context.current_state == ConversationState.ESCALATING:
            response["prompt"] = "Let me connect you with a specialist who can better assist you."
            response["action"] = "transfer_to_human"
            
        return response
    
    def end_conversation(self, session_id: str) -> Dict:
        """End a conversation and return metrics"""
        
        if session_id not in self.contexts:
            return {"error": "Session not found"}
            
        context = self.contexts[session_id]
        
        # Calculate metrics
        context.total_duration_seconds = (datetime.now() - context.start_time).total_seconds()
        
        metrics = {
            "session_id": session_id,
            "duration_seconds": context.total_duration_seconds,
            "total_transitions": len(context.state_transitions),
            "conversion_complete": context.conversion_complete,
            "required_human": context.requires_human,
            "final_sentiment": context.sentiment,
            "collected_data_fields": list(context.collected_data.keys()),
            "state_path": [t["to"] for t in context.state_transitions]
        }
        
        # Clean up
        del self.contexts[session_id]
        
        return metrics