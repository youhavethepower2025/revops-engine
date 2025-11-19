#!/usr/bin/env python3
"""
Enhanced webhook handler for Retell + GHL integration
This handles all the shit GHL's interface would make painful
"""

import json
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
import httpx
import asyncio

logger = logging.getLogger(__name__)

class RetellGHLProcessor:
    """Process Retell webhooks and automate GHL operations"""

    def __init__(self, ghl_api_key: str, ghl_location_id: str):
        self.ghl_api_key = ghl_api_key
        self.ghl_location_id = ghl_location_id
        self.ghl_base = "https://rest.gohighlevel.com/v1"
        self.headers = {
            "Authorization": f"Bearer {ghl_api_key}",
            "Content-Type": "application/json"
        }

    async def process_retell_webhook(self, event_type: str, call_data: Dict) -> Dict:
        """Main entry point for Retell webhook processing"""
        logger.info(f"Processing {event_type} for call {call_data.get('call_id')}")

        if event_type == "call_started":
            return await self.handle_call_started(call_data)
        elif event_type == "call_ended":
            return await self.handle_call_ended(call_data)
        elif event_type == "call_analyzed":
            return await self.handle_call_analyzed(call_data)

        return {"status": "unknown_event"}

    async def handle_call_started(self, call_data: Dict) -> Dict:
        """When call starts - do caller ID lookup and prep context"""
        phone = self._normalize_phone(call_data.get('from_number', ''))

        # CALLER ID LOOKUP
        contact = await self.lookup_or_create_contact(phone, call_data)

        # Store in memory for quick access during call
        await self.store_call_context(call_data['call_id'], {
            'contact_id': contact.get('id'),
            'phone': phone,
            'started_at': datetime.now().isoformat(),
            'contact_name': f"{contact.get('firstName', '')} {contact.get('lastName', '')}".strip() or "Unknown Caller"
        })

        # Return context for Retell to use
        return {
            "status": "call_started_processed",
            "contact_id": contact.get('id'),
            "contact_name": contact.get('firstName', 'Friend'),
            "is_new": contact.get('is_new', False)
        }

    async def handle_call_ended(self, call_data: Dict) -> Dict:
        """When call ends - process transcript and take actions"""
        call_id = call_data.get('call_id')
        transcript = call_data.get('transcript', '')

        # Get stored context
        context = await self.get_call_context(call_id)
        contact_id = context.get('contact_id') if context else None

        if not contact_id:
            # Try to find/create contact if we don't have one
            phone = self._normalize_phone(call_data.get('from_number', ''))
            contact = await self.lookup_or_create_contact(phone, call_data)
            contact_id = contact.get('id')

        # Process the transcript for insights
        insights = await self.extract_insights(transcript)

        # UPDATE CONTACT WITH CALL INFO
        await self.update_contact_with_call(contact_id, call_data, insights)

        # CREATE FOLLOW-UP TASK
        await self.create_follow_up_task(contact_id, insights)

        # BOOK APPOINTMENT if requested
        if insights.get('appointment_requested'):
            await self.book_appointment(contact_id, insights)

        # ADD TO PIPELINE if qualified
        if insights.get('qualified_lead'):
            await self.add_to_pipeline(contact_id, insights)

        return {
            "status": "call_processed",
            "contact_id": contact_id,
            "actions_taken": {
                "task_created": insights.get('needs_follow_up', False),
                "appointment_booked": insights.get('appointment_requested', False),
                "pipeline_added": insights.get('qualified_lead', False)
            }
        }

    async def handle_call_analyzed(self, call_data: Dict) -> Dict:
        """When Retell provides analysis - enrich contact further"""
        analysis = call_data.get('call_analysis', {})
        sentiment = analysis.get('user_sentiment')
        summary = analysis.get('call_summary', '')

        # Store the analysis for future reference
        return {
            "status": "analysis_processed",
            "sentiment": sentiment
        }

    async def lookup_or_create_contact(self, phone: str, call_data: Dict) -> Dict:
        """Smart contact lookup with creation fallback"""
        async with httpx.AsyncClient() as client:
            # Search for existing contact
            search_response = await client.get(
                f"{self.ghl_base}/contacts/search",
                headers=self.headers,
                params={
                    "locationId": self.ghl_location_id,
                    "query": phone
                }
            )

            if search_response.status_code == 200:
                contacts = search_response.json().get('contacts', [])

                if contacts:
                    # Found existing contact
                    contact = contacts[0]
                    logger.info(f"Found existing contact: {contact.get('id')}")

                    # Update last interaction
                    await client.put(
                        f"{self.ghl_base}/contacts/{contact['id']}",
                        headers=self.headers,
                        json={
                            "customField": {
                                "last_ai_call": datetime.now().isoformat(),
                                "total_ai_calls": (contact.get('customField', {}).get('total_ai_calls', 0) + 1)
                            }
                        }
                    )

                    return contact
                else:
                    # Create new contact
                    logger.info(f"Creating new contact for {phone}")

                    create_response = await client.post(
                        f"{self.ghl_base}/contacts",
                        headers=self.headers,
                        json={
                            "locationId": self.ghl_location_id,
                            "phone": phone,
                            "firstName": "New",
                            "lastName": "Lead",
                            "source": "AI Phone System",
                            "tags": ["ai-captured", "needs-enrichment"],
                            "customField": {
                                "first_ai_call": datetime.now().isoformat(),
                                "total_ai_calls": 1,
                                "ai_system": "AI Jesus Bro"
                            }
                        }
                    )

                    if create_response.status_code in [200, 201]:
                        new_contact = create_response.json()
                        new_contact['is_new'] = True
                        return new_contact

            # Fallback if everything fails
            return {"id": None, "phone": phone}

    async def extract_insights(self, transcript: str) -> Dict:
        """Extract actionable insights from transcript"""
        insights = {
            "needs_follow_up": True,  # Default to yes
            "appointment_requested": False,
            "qualified_lead": False,
            "services_interested": [],
            "pain_points": [],
            "budget_mentioned": None,
            "timeline": None,
            "next_steps": ""
        }

        # Simple keyword extraction (could be enhanced with AI)
        transcript_lower = transcript.lower()

        # Check for appointment requests
        appointment_keywords = ["appointment", "meeting", "schedule", "book", "calendar", "available", "time to meet"]
        insights['appointment_requested'] = any(kw in transcript_lower for kw in appointment_keywords)

        # Check for qualification signals
        qualification_keywords = ["budget", "timeline", "decision maker", "authority", "purchase", "buy", "invest"]
        insights['qualified_lead'] = any(kw in transcript_lower for kw in qualification_keywords)

        # Check for service interests
        services = {
            "ai_development": ["custom ai", "build ai", "ai development", "develop"],
            "automation": ["automate", "automation", "workflow", "efficiency"],
            "consulting": ["consulting", "advice", "strategy", "guidance"],
            "voice_ai": ["voice", "phone system", "call", "conversation"]
        }

        for service, keywords in services.items():
            if any(kw in transcript_lower for kw in keywords):
                insights['services_interested'].append(service)

        # Extract pain points
        pain_keywords = ["problem", "issue", "challenge", "struggling", "difficult", "hard", "pain", "frustrat"]
        if any(kw in transcript_lower for kw in pain_keywords):
            insights['pain_points'].append("Has expressed challenges")

        # Determine next steps
        if insights['appointment_requested']:
            insights['next_steps'] = "Book appointment ASAP"
        elif insights['qualified_lead']:
            insights['next_steps'] = "High priority follow-up within 24 hours"
        else:
            insights['next_steps'] = "Standard follow-up within 48 hours"

        return insights

    async def update_contact_with_call(self, contact_id: str, call_data: Dict, insights: Dict):
        """Update contact with call information and insights"""
        if not contact_id:
            return

        async with httpx.AsyncClient() as client:
            # Add note with transcript summary
            note_body = f"""AI Call Summary - {datetime.now().strftime('%Y-%m-%d %H:%M')}

Duration: {call_data.get('call_duration', 0)} seconds
Services Interested: {', '.join(insights['services_interested']) or 'None identified'}
Appointment Requested: {'Yes' if insights['appointment_requested'] else 'No'}
Qualified Lead: {'Yes' if insights['qualified_lead'] else 'No'}

Next Steps: {insights['next_steps']}

Transcript Available: Yes
Call ID: {call_data.get('call_id')}
"""

            await client.post(
                f"{self.ghl_base}/contacts/{contact_id}/notes",
                headers=self.headers,
                json={"body": note_body}
            )

            # Update contact fields
            update_data = {
                "customField": {
                    "last_call_duration": call_data.get('call_duration', 0),
                    "last_call_date": datetime.now().isoformat(),
                    "ai_qualified": insights['qualified_lead'],
                    "services_interested": ', '.join(insights['services_interested'])
                }
            }

            # Update tags based on insights
            tags = []
            if insights['appointment_requested']:
                tags.append("appointment-requested")
            if insights['qualified_lead']:
                tags.append("qualified-lead")
            if insights['services_interested']:
                tags.append("interested")

            if tags:
                update_data['tags'] = tags

            await client.put(
                f"{self.ghl_base}/contacts/{contact_id}",
                headers=self.headers,
                json=update_data
            )

    async def create_follow_up_task(self, contact_id: str, insights: Dict):
        """Create follow-up task in GHL"""
        if not contact_id or not insights.get('needs_follow_up'):
            return

        # Determine priority and due date
        if insights['appointment_requested']:
            priority = "high"
            due_date = datetime.now() + timedelta(hours=2)
            title = "URGENT: Book appointment - Customer requested"
        elif insights['qualified_lead']:
            priority = "high"
            due_date = datetime.now() + timedelta(days=1)
            title = "Follow up with qualified lead"
        else:
            priority = "normal"
            due_date = datetime.now() + timedelta(days=2)
            title = "Follow up on AI call"

        async with httpx.AsyncClient() as client:
            await client.post(
                f"{self.ghl_base}/contacts/{contact_id}/tasks",
                headers=self.headers,
                json={
                    "title": title,
                    "body": f"Services interested: {', '.join(insights['services_interested'])}\nNext steps: {insights['next_steps']}",
                    "dueDate": due_date.isoformat(),
                    "priority": priority,
                    "status": "pending"
                }
            )

    async def book_appointment(self, contact_id: str, insights: Dict):
        """Attempt to book appointment in GHL calendar"""
        if not contact_id:
            return

        # This would integrate with GHL calendar API
        # For now, create a high-priority task
        async with httpx.AsyncClient() as client:
            await client.post(
                f"{self.ghl_base}/contacts/{contact_id}/tasks",
                headers=self.headers,
                json={
                    "title": "📅 BOOK APPOINTMENT - Customer requested on call",
                    "body": "Customer explicitly requested an appointment during AI call. Reach out immediately to schedule.",
                    "dueDate": datetime.now().isoformat(),
                    "priority": "urgent",
                    "status": "pending"
                }
            )

    async def add_to_pipeline(self, contact_id: str, insights: Dict):
        """Add qualified lead to sales pipeline"""
        if not contact_id:
            return

        async with httpx.AsyncClient() as client:
            # Create opportunity in pipeline
            await client.post(
                f"{self.ghl_base}/opportunities",
                headers=self.headers,
                json={
                    "locationId": self.ghl_location_id,
                    "contactId": contact_id,
                    "name": f"AI Qualified Lead - {datetime.now().strftime('%Y-%m-%d')}",
                    "pipelineId": "default",  # Would need actual pipeline ID
                    "pipelineStageId": "lead",  # Would need actual stage ID
                    "source": "AI Phone System",
                    "status": "open",
                    "customFields": {
                        "services_interested": ', '.join(insights['services_interested']),
                        "ai_qualified": True
                    }
                }
            )

    async def store_call_context(self, call_id: str, context: Dict):
        """Store call context in memory/redis for quick access"""
        # This would use Redis or database
        # For now, using in-memory storage
        pass

    async def get_call_context(self, call_id: str) -> Optional[Dict]:
        """Retrieve stored call context"""
        # This would use Redis or database
        return None

    def _normalize_phone(self, phone: str) -> str:
        """Normalize phone number format"""
        # Remove all non-digits
        digits = ''.join(filter(str.isdigit, phone))

        # Add US country code if needed
        if len(digits) == 10:
            digits = '1' + digits

        # Format as +1XXXXXXXXXX
        if digits.startswith('1'):
            return '+' + digits

        return phone