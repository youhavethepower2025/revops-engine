"""
AmberBrain - The Core Intelligence Layer
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional
from enum import Enum

import openai
from langchain.memory import ConversationSummaryBufferMemory
from langchain_openai import ChatOpenAI
import redis.asyncio as redis

from models import db, CallSession, Contact, CallEvent, CallerType
from ghl_controller import GHLController
from ai_engine import AIEngine

logger = logging.getLogger(__name__)

class AmberBrain:
    """
    The core intelligence orchestrator for ClearVC
    Manages context, memory, and decision-making
    """

    def __init__(self):
        self.ghl = GHLController()
        self.ai = AIEngine()
        self.redis_client = None
        self.conversations = {}  # Active conversations in memory
        self.initialized = False

    async def initialize(self):
        """Initialize brain components"""
        try:
            # Initialize Redis for real-time state
            self.redis_client = await redis.from_url(
                "redis://redis:6379",
                decode_responses=True
            )

            # Test Redis connection
            await self.redis_client.ping()

            # Initialize AI engine
            await self.ai.initialize()

            self.initialized = True
            logger.info("Brain initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize brain: {e}")
            raise

    async def handle_call_start(self, call_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process call start - identify caller and prepare context
        """
        phone = call_data.get('from_number')
        call_id = call_data.get('call_id')

        logger.info(f"Processing call start for {phone}")

        # Check if caller exists in GHL
        ghl_contact = await self.ghl.lookup_contact_by_phone(phone)

        if ghl_contact:
            # Existing contact - pull full context
            contact_data = await self._extract_contact_data(ghl_contact)
            caller_type = self._determine_caller_type(contact_data)
            strategy = await self._generate_conversation_strategy(contact_data, caller_type)
        else:
            # New caller - discovery mode
            contact_data = None
            caller_type = CallerType.NEW
            strategy = {
                'approach': 'discovery',
                'goals': ['capture_name', 'understand_need', 'book_callback'],
                'tone': 'welcoming_professional',
                'key_questions': [
                    "May I have your name?",
                    "How can ClearVC help you today?",
                    "What's the best time for us to call you back?"
                ]
            }

        # Store conversation in memory and Redis
        conversation_context = {
            'phone': phone,
            'contact_data': contact_data,
            'caller_type': caller_type.value if isinstance(caller_type, Enum) else caller_type,
            'strategy': strategy,
            'started_at': datetime.utcnow().isoformat(),
            'events': []
        }

        self.conversations[call_id] = conversation_context

        # Store in Redis for distributed access
        await self.redis_client.set(
            f"call:{call_id}",
            json.dumps(conversation_context),
            ex=7200  # 2 hour expiry
        )

        # Store in database
        session = await CallSession.create(
            call_id=call_id,
            phone_number=phone,
            caller_type=caller_type,
            started_at=datetime.utcnow()
        )

        # Return context for Retell
        return {
            'call_id': call_id,
            'caller_type': caller_type.value if isinstance(caller_type, Enum) else caller_type,
            'caller_name': contact_data.get('name') if contact_data else None,
            'greeting': self._get_custom_greeting(caller_type, contact_data),
            'conversation_hints': strategy.get('key_questions', []),
            'escalation_available': caller_type in [CallerType.VIP, CallerType.EXISTING_ISSUE]
        }

    async def _extract_contact_data(self, ghl_contact: Dict) -> Dict[str, Any]:
        """Extract comprehensive contact data from GHL"""
        contact_id = ghl_contact.get('id')

        # Fetch additional data in parallel
        tasks = [
            self.ghl.get_contact_notes(contact_id),
            self.ghl.get_contact_opportunities(contact_id),
            self.ghl.get_contact_tasks(contact_id)
        ]

        notes, opportunities, tasks = await asyncio.gather(*tasks, return_exceptions=True)

        return {
            'id': contact_id,
            'name': ghl_contact.get('name'),
            'email': ghl_contact.get('email'),
            'tags': ghl_contact.get('tags', []),
            'custom_fields': ghl_contact.get('customFields', {}),
            'notes': notes if not isinstance(notes, Exception) else [],
            'opportunities': opportunities if not isinstance(opportunities, Exception) else [],
            'tasks': tasks if not isinstance(tasks, Exception) else [],
            'last_interaction': ghl_contact.get('dateUpdated'),
            'total_value': self._calculate_total_value(opportunities)
        }

    def _determine_caller_type(self, contact_data: Dict) -> CallerType:
        """Analyze contact data to determine caller type"""
        tags = contact_data.get('tags', [])
        opportunities = contact_data.get('opportunities', [])
        tasks = contact_data.get('tasks', [])

        # VIP check
        if 'vip' in tags or contact_data.get('total_value', 0) > 10000:
            return CallerType.VIP

        # Support issue check
        if any(task.get('title', '').lower().startswith('support') for task in tasks):
            return CallerType.EXISTING_ISSUE

        # Active opportunity check
        if any(opp.get('status') == 'open' for opp in opportunities):
            return CallerType.ACTIVE_OPPORTUNITY

        # Past client check
        if 'past_client' in tags or any(opp.get('status') == 'won' for opp in opportunities):
            return CallerType.PAST_CLIENT

        return CallerType.EXISTING_CONTACT

    async def _generate_conversation_strategy(
        self,
        contact_data: Dict,
        caller_type: CallerType
    ) -> Dict[str, Any]:
        """Use AI to generate dynamic conversation strategy"""
        prompt = f"""
        Generate a conversation strategy for an after-hours call.

        Caller Type: {caller_type.value}
        Contact Name: {contact_data.get('name', 'Unknown')}
        Previous Interactions: {len(contact_data.get('notes', []))} notes
        Open Opportunities: {len([o for o in contact_data.get('opportunities', []) if o.get('status') == 'open'])}
        Tags: {', '.join(contact_data.get('tags', []))}

        Provide:
        1. Primary objective for this call
        2. Key talking points
        3. Tone and approach
        4. Questions to ask
        5. Ideal outcome

        Format as JSON.
        """

        strategy = await self.ai.generate_json(prompt)
        return strategy

    def _get_custom_greeting(self, caller_type: CallerType, contact_data: Optional[Dict]) -> str:
        """Generate appropriate greeting based on caller type"""
        if caller_type == CallerType.VIP and contact_data:
            name = contact_data.get('name', 'there')
            return f"Good evening {name}! I recognize you as one of our VIP clients. How can I assist you tonight?"
        elif caller_type == CallerType.EXISTING_ISSUE:
            return "Hello! I see you have an open support ticket with us. Are you calling about that issue?"
        elif caller_type == CallerType.ACTIVE_OPPORTUNITY and contact_data:
            name = contact_data.get('name', 'there')
            return f"Hi {name}! Great to hear from you. Are you calling about the proposal we discussed?"
        elif caller_type == CallerType.NEW:
            return "Thank you for calling ClearVC! You've reached our after-hours service. I'm Amber, and I'm here to help. May I have your name?"
        else:
            return "Thank you for calling ClearVC! This is Amber, handling our after-hours service. How can I help you tonight?"

    def _calculate_total_value(self, opportunities: List[Dict]) -> float:
        """Calculate total value from opportunities"""
        if not opportunities or isinstance(opportunities, Exception):
            return 0.0

        total = 0.0
        for opp in opportunities:
            if opp.get('status') == 'won':
                total += float(opp.get('monetaryValue', 0))
        return total

    async def handle_tool_call(
        self,
        call_id: str,
        tool_name: str,
        parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Handle tool calls from Retell during conversation"""
        conversation = self.conversations.get(call_id)

        if not conversation:
            # Try to load from Redis
            redis_data = await self.redis_client.get(f"call:{call_id}")
            if redis_data:
                conversation = json.loads(redis_data)
                self.conversations[call_id] = conversation
            else:
                return {"error": "Conversation not found"}

        # Log the tool call event
        event = {
            'timestamp': datetime.utcnow().isoformat(),
            'type': 'tool_call',
            'tool': tool_name,
            'parameters': parameters
        }
        conversation['events'].append(event)

        # Route to appropriate handler
        if tool_name == 'escalate_to_human':
            return await self._handle_escalation(conversation)
        elif tool_name == 'check_availability':
            return await self._handle_availability_check(parameters)
        elif tool_name == 'book_appointment':
            return await self._handle_appointment_booking(conversation, parameters)
        elif tool_name == 'capture_information':
            return await self._handle_information_capture(conversation, parameters)
        else:
            return {"error": f"Unknown tool: {tool_name}"}

    async def _handle_escalation(self, conversation: Dict) -> Dict[str, Any]:
        """Handle escalation to human"""
        # Send urgent notification
        await self.send_urgent_notification(conversation)

        return {
            'message': "I'm connecting you with our team lead right away. They'll be with you shortly.",
            'action': 'escalate',
            'urgency': 'high'
        }

    async def _handle_availability_check(self, parameters: Dict) -> Dict[str, Any]:
        """Check real availability"""
        # This would integrate with actual calendar system
        # For now, return mock availability
        return {
            'available_slots': [
                {'date': '2024-01-15', 'time': '10:00 AM'},
                {'date': '2024-01-15', 'time': '2:00 PM'},
                {'date': '2024-01-16', 'time': '11:00 AM'}
            ],
            'message': "I have a few slots available. Which works best for you?"
        }

    async def _handle_appointment_booking(
        self,
        conversation: Dict,
        parameters: Dict
    ) -> Dict[str, Any]:
        """Book an appointment"""
        # Create appointment in GHL
        contact_data = conversation.get('contact_data')

        if contact_data:
            await self.ghl.create_appointment(
                contact_id=contact_data['id'],
                date=parameters.get('date'),
                time=parameters.get('time'),
                type=parameters.get('type', 'Follow-up Call')
            )

        return {
            'message': f"Perfect! I've scheduled your appointment for {parameters.get('date')} at {parameters.get('time')}. You'll receive a confirmation email shortly.",
            'success': True
        }

    async def _handle_information_capture(
        self,
        conversation: Dict,
        parameters: Dict
    ) -> Dict[str, Any]:
        """Capture and store information"""
        # Update conversation context
        if 'captured_info' not in conversation:
            conversation['captured_info'] = {}

        conversation['captured_info'].update(parameters)

        # Update in Redis
        await self.redis_client.set(
            f"call:{conversation.get('call_id')}",
            json.dumps(conversation),
            ex=7200
        )

        return {
            'message': "Got it, I've noted that information.",
            'captured': True
        }

    async def process_transcript_chunk(
        self,
        call_id: str,
        transcript: str
    ) -> Dict[str, Any]:
        """Process transcript in real-time for insights"""
        # Analyze transcript for key patterns
        insights = await self.ai.analyze_transcript(transcript)

        # Store insights
        if call_id in self.conversations:
            if 'insights' not in self.conversations[call_id]:
                self.conversations[call_id]['insights'] = []
            self.conversations[call_id]['insights'].append(insights)

        return insights

    async def handle_call_end(self, call_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process call end - generate summary and update systems"""
        call_id = call_data.get('call_id')
        conversation = self.conversations.get(call_id)

        if not conversation:
            logger.warning(f"No conversation found for call {call_id}")
            return {"status": "no_context"}

        # Generate comprehensive summary
        summary = await self.ai.generate_call_summary(
            transcript=call_data.get('transcript', ''),
            context=conversation
        )

        # Update or create contact in GHL
        await self._update_or_create_contact(conversation, summary)

        # Create follow-up tasks
        await self._create_follow_up_tasks(conversation, summary)

        # Send notifications
        await self._send_call_summary(conversation, summary)

        # Store final state in database
        await CallSession.update(
            call_id=call_id,
            ended_at=datetime.utcnow(),
            summary=summary,
            transcript=call_data.get('transcript')
        )

        # Clean up memory
        del self.conversations[call_id]
        await self.redis_client.delete(f"call:{call_id}")

        return {
            "status": "completed",
            "summary": summary
        }

    async def send_urgent_notification(self, conversation: Dict):
        """Send urgent notification for escalation"""
        # Implementation would send to Telegram/Slack/SMS
        logger.info(f"URGENT: Escalation requested for {conversation.get('phone')}")

    async def check_db_health(self) -> bool:
        """Check database health"""
        try:
            await db.execute("SELECT 1")
            return True
        except:
            return False

    async def check_redis_health(self) -> bool:
        """Check Redis health"""
        try:
            await self.redis_client.ping()
            return True
        except:
            return False

    async def cleanup(self):
        """Cleanup resources"""
        if self.redis_client:
            await self.redis_client.close()