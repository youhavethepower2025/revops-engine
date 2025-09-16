"""
Retell Webhook Handler
Processes webhooks from Retell AI voice platform
"""

import logging
from typing import Dict, Any, Optional
from datetime import datetime
import json

logger = logging.getLogger(__name__)

class RetellWebhookHandler:
    """
    Handler for Retell AI webhook events
    """

    def __init__(self, brain):
        self.brain = brain

    async def handle_call_start(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process call start webhook from Retell
        """
        try:
            # Extract relevant data from Retell webhook
            call_id = data.get('call_id')
            from_number = data.get('from_number') or data.get('from', {}).get('number')
            to_number = data.get('to_number') or data.get('to', {}).get('number')
            agent_id = data.get('agent_id')

            logger.info(f"Processing call start: {call_id} from {from_number}")

            # Process through brain
            context = await self.brain.handle_call_start({
                'call_id': call_id,
                'from_number': from_number,
                'to_number': to_number,
                'agent_id': agent_id,
                'timestamp': datetime.utcnow().isoformat()
            })

            # Return Retell-compatible response
            return {
                "status": "success",
                "context": context,
                "custom_variables": {
                    "caller_name": context.get('caller_name'),
                    "caller_type": context.get('caller_type'),
                    "greeting": context.get('greeting')
                }
            }
        except Exception as e:
            logger.error(f"Error handling call start: {e}")
            return {
                "status": "error",
                "message": str(e),
                "custom_variables": {
                    "greeting": "Thank you for calling ClearVC. How can I help you today?"
                }
            }

    async def handle_call_end(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process call end webhook from Retell
        """
        try:
            call_id = data.get('call_id')
            duration = data.get('duration_seconds', 0)
            transcript = data.get('transcript', '')
            recording_url = data.get('recording_url')
            end_reason = data.get('end_reason', 'completed')

            logger.info(f"Processing call end: {call_id}, duration: {duration}s")

            # Process through brain
            result = await self.brain.handle_call_end({
                'call_id': call_id,
                'duration_seconds': duration,
                'transcript': transcript,
                'recording_url': recording_url,
                'end_reason': end_reason,
                'timestamp': datetime.utcnow().isoformat()
            })

            return {
                "status": "success",
                "summary": result.get('summary'),
                "follow_ups_created": result.get('follow_ups_created', False)
            }
        except Exception as e:
            logger.error(f"Error handling call end: {e}")
            return {
                "status": "error",
                "message": str(e)
            }

    async def handle_function_call(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle function/tool calls from Retell during conversation
        """
        try:
            call_id = data.get('call_id')
            function_name = data.get('function_name')
            function_args = data.get('function_args', {})

            logger.info(f"Function call: {function_name} for call {call_id}")

            # Map Retell functions to brain tool calls
            tool_mapping = {
                'schedule_appointment': 'book_appointment',
                'check_calendar': 'check_availability',
                'escalate': 'escalate_to_human',
                'capture_info': 'capture_information',
                'send_email': 'queue_email',
                'create_ticket': 'create_support_ticket'
            }

            tool_name = tool_mapping.get(function_name, function_name)

            # Process through brain
            result = await self.brain.handle_tool_call(
                call_id=call_id,
                tool_name=tool_name,
                parameters=function_args
            )

            # Return Retell-compatible response
            return {
                "success": not result.get('error'),
                "result": result.get('message') or result.get('result'),
                "data": result
            }
        except Exception as e:
            logger.error(f"Error handling function call: {e}")
            return {
                "success": False,
                "result": "I apologize, but I couldn't complete that action. Let me try another way to help you.",
                "error": str(e)
            }

    async def handle_transcript_update(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle real-time transcript updates
        """
        try:
            call_id = data.get('call_id')
            transcript = data.get('transcript', '')
            speaker = data.get('speaker', 'unknown')
            timestamp = data.get('timestamp')

            # Process for real-time insights
            insights = await self.brain.process_transcript_chunk(
                call_id=call_id,
                transcript=transcript
            )

            # Check if escalation is needed
            if insights.get('urgency') == 'critical':
                await self.brain.send_urgent_notification({
                    'call_id': call_id,
                    'reason': 'Critical urgency detected',
                    'transcript': transcript
                })

            return {
                "status": "processed",
                "insights": insights
            }
        except Exception as e:
            logger.error(f"Error handling transcript update: {e}")
            return {
                "status": "error",
                "message": str(e)
            }

    async def handle_custom_event(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle custom events from Retell
        """
        try:
            event_type = data.get('event_type')
            call_id = data.get('call_id')
            event_data = data.get('data', {})

            logger.info(f"Custom event: {event_type} for call {call_id}")

            # Route based on event type
            if event_type == 'sentiment_change':
                # Handle sentiment changes
                if event_data.get('sentiment') == 'negative':
                    # Consider escalation
                    escalation_check = await self.brain.ai.check_escalation_needed(
                        transcript=event_data.get('transcript', ''),
                        context={'call_id': call_id}
                    )

                    if escalation_check.get('needs_escalation'):
                        await self.brain.send_urgent_notification({
                            'call_id': call_id,
                            'reason': escalation_check.get('reason'),
                            'urgency': escalation_check.get('urgency')
                        })

            elif event_type == 'intent_detected':
                # Handle specific intents
                intent = event_data.get('intent')
                if intent == 'purchase_intent':
                    # Flag as hot lead
                    await self.brain.ghl.add_contact_tag(
                        contact_id=event_data.get('contact_id'),
                        tag='hot_lead'
                    )

            return {
                "status": "processed",
                "event_type": event_type
            }
        except Exception as e:
            logger.error(f"Error handling custom event: {e}")
            return {
                "status": "error",
                "message": str(e)
            }

    async def validate_webhook_signature(self, signature: str, payload: bytes) -> bool:
        """
        Validate webhook signature from Retell
        """
        # Implement signature validation based on Retell's security requirements
        # This is a placeholder - implement actual validation
        return True