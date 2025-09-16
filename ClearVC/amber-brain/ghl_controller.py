"""
GHL (GoHighLevel) Controller for ClearVC
Handles all interactions with the GHL CRM
"""

import httpx
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

class GHLController:
    """
    Controller for GoHighLevel CRM operations
    """

    def __init__(self):
        self.api_key = os.getenv('GHL_API_KEY')
        self.location_id = os.getenv('GHL_LOCATION_ID')
        self.base_url = "https://rest.gohighlevel.com/v1"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        self.client = httpx.AsyncClient(timeout=30.0)

    async def check_connection(self) -> bool:
        """Test GHL API connection"""
        try:
            response = await self.client.get(
                f"{self.base_url}/locations/{self.location_id}",
                headers=self.headers
            )
            return response.status_code == 200
        except Exception as e:
            logger.error(f"GHL connection check failed: {e}")
            return False

    async def lookup_contact_by_phone(self, phone: str) -> Optional[Dict[str, Any]]:
        """
        Look up a contact by phone number
        """
        try:
            # Clean phone number (remove non-digits)
            clean_phone = ''.join(filter(str.isdigit, phone))

            response = await self.client.get(
                f"{self.base_url}/contacts/",
                headers=self.headers,
                params={
                    "locationId": self.location_id,
                    "query": clean_phone
                }
            )

            if response.status_code == 200:
                data = response.json()
                contacts = data.get('contacts', [])

                # Find exact match
                for contact in contacts:
                    if self._normalize_phone(contact.get('phone')) == clean_phone:
                        return contact

            return None
        except Exception as e:
            logger.error(f"Error looking up contact: {e}")
            return None

    async def create_contact(
        self,
        phone: str,
        name: str = None,
        email: str = None,
        tags: List[str] = None,
        notes: str = None
    ) -> Dict[str, Any]:
        """
        Create a new contact in GHL
        """
        try:
            contact_data = {
                "locationId": self.location_id,
                "phone": phone,
                "tags": tags or ["amber_captured", "after_hours"],
                "source": "Amber Brain"
            }

            if name:
                contact_data["name"] = name
            if email:
                contact_data["email"] = email

            response = await self.client.post(
                f"{self.base_url}/contacts/",
                headers=self.headers,
                json=contact_data
            )

            if response.status_code in [200, 201]:
                contact = response.json()

                # Add initial note if provided
                if notes:
                    await self.add_contact_note(contact['id'], notes)

                return contact
            else:
                logger.error(f"Failed to create contact: {response.text}")
                return {}
        except Exception as e:
            logger.error(f"Error creating contact: {e}")
            return {}

    async def update_contact(
        self,
        contact_id: str,
        **kwargs
    ) -> bool:
        """
        Update an existing contact
        """
        try:
            update_data = {k: v for k, v in kwargs.items() if v is not None}

            response = await self.client.put(
                f"{self.base_url}/contacts/{contact_id}",
                headers=self.headers,
                json=update_data
            )

            return response.status_code == 200
        except Exception as e:
            logger.error(f"Error updating contact: {e}")
            return False

    async def get_contact_notes(self, contact_id: str) -> List[Dict[str, Any]]:
        """
        Get all notes for a contact
        """
        try:
            response = await self.client.get(
                f"{self.base_url}/contacts/{contact_id}/notes",
                headers=self.headers
            )

            if response.status_code == 200:
                return response.json().get('notes', [])
            return []
        except Exception as e:
            logger.error(f"Error fetching notes: {e}")
            return []

    async def add_contact_note(self, contact_id: str, note: str) -> bool:
        """
        Add a note to a contact
        """
        try:
            response = await self.client.post(
                f"{self.base_url}/contacts/{contact_id}/notes",
                headers=self.headers,
                json={
                    "body": note,
                    "userId": self.location_id  # Using location as user ID
                }
            )

            return response.status_code in [200, 201]
        except Exception as e:
            logger.error(f"Error adding note: {e}")
            return False

    async def get_contact_opportunities(self, contact_id: str) -> List[Dict[str, Any]]:
        """
        Get all opportunities for a contact
        """
        try:
            response = await self.client.get(
                f"{self.base_url}/pipelines/opportunities",
                headers=self.headers,
                params={
                    "locationId": self.location_id,
                    "contactId": contact_id
                }
            )

            if response.status_code == 200:
                return response.json().get('opportunities', [])
            return []
        except Exception as e:
            logger.error(f"Error fetching opportunities: {e}")
            return []

    async def create_opportunity(
        self,
        contact_id: str,
        name: str,
        pipeline_id: str = None,
        stage_id: str = None,
        value: float = 0
    ) -> Dict[str, Any]:
        """
        Create a new opportunity
        """
        try:
            opportunity_data = {
                "locationId": self.location_id,
                "contactId": contact_id,
                "name": name,
                "monetaryValue": value,
                "status": "open"
            }

            if pipeline_id:
                opportunity_data["pipelineId"] = pipeline_id
            if stage_id:
                opportunity_data["pipelineStageId"] = stage_id

            response = await self.client.post(
                f"{self.base_url}/pipelines/opportunities",
                headers=self.headers,
                json=opportunity_data
            )

            if response.status_code in [200, 201]:
                return response.json()
            return {}
        except Exception as e:
            logger.error(f"Error creating opportunity: {e}")
            return {}

    async def get_contact_tasks(self, contact_id: str) -> List[Dict[str, Any]]:
        """
        Get all tasks for a contact
        """
        try:
            response = await self.client.get(
                f"{self.base_url}/contacts/{contact_id}/tasks",
                headers=self.headers
            )

            if response.status_code == 200:
                return response.json().get('tasks', [])
            return []
        except Exception as e:
            logger.error(f"Error fetching tasks: {e}")
            return []

    async def create_task(
        self,
        contact_id: str,
        title: str,
        description: str = None,
        due_date: datetime = None
    ) -> Dict[str, Any]:
        """
        Create a task for a contact
        """
        try:
            task_data = {
                "contactId": contact_id,
                "title": title,
                "completed": False
            }

            if description:
                task_data["body"] = description
            if due_date:
                task_data["dueDate"] = due_date.isoformat()

            response = await self.client.post(
                f"{self.base_url}/contacts/{contact_id}/tasks",
                headers=self.headers,
                json=task_data
            )

            if response.status_code in [200, 201]:
                return response.json()
            return {}
        except Exception as e:
            logger.error(f"Error creating task: {e}")
            return {}

    async def create_appointment(
        self,
        contact_id: str,
        date: str,
        time: str,
        type: str = "Phone Call",
        duration: int = 30
    ) -> Dict[str, Any]:
        """
        Create an appointment in GHL calendar
        """
        try:
            # Parse date and time
            appointment_datetime = datetime.strptime(f"{date} {time}", "%Y-%m-%d %H:%M")
            end_datetime = appointment_datetime + timedelta(minutes=duration)

            appointment_data = {
                "locationId": self.location_id,
                "contactId": contact_id,
                "title": f"{type} - Amber Scheduled",
                "appointmentStatus": "confirmed",
                "selectedTimezone": "America/Los_Angeles",  # Adjust as needed
                "selectedSlot": {
                    "startTime": appointment_datetime.isoformat(),
                    "endTime": end_datetime.isoformat()
                }
            }

            response = await self.client.post(
                f"{self.base_url}/calendars/appointments",
                headers=self.headers,
                json=appointment_data
            )

            if response.status_code in [200, 201]:
                return response.json()
            return {}
        except Exception as e:
            logger.error(f"Error creating appointment: {e}")
            return {}

    async def add_contact_tag(self, contact_id: str, tag: str) -> bool:
        """
        Add a tag to a contact
        """
        try:
            # Get current contact to preserve existing tags
            response = await self.client.get(
                f"{self.base_url}/contacts/{contact_id}",
                headers=self.headers
            )

            if response.status_code == 200:
                contact = response.json()
                current_tags = contact.get('tags', [])

                if tag not in current_tags:
                    current_tags.append(tag)

                    # Update contact with new tags
                    return await self.update_contact(contact_id, tags=current_tags)

            return True  # Tag already exists
        except Exception as e:
            logger.error(f"Error adding tag: {e}")
            return False

    async def send_sms(self, contact_id: str, message: str) -> bool:
        """
        Send SMS to a contact
        """
        try:
            response = await self.client.post(
                f"{self.base_url}/conversations/messages",
                headers=self.headers,
                json={
                    "type": "SMS",
                    "contactId": contact_id,
                    "message": message
                }
            )

            return response.status_code in [200, 201]
        except Exception as e:
            logger.error(f"Error sending SMS: {e}")
            return False

    async def trigger_workflow(self, contact_id: str, workflow_id: str) -> bool:
        """
        Trigger a GHL workflow for a contact
        """
        try:
            response = await self.client.post(
                f"{self.base_url}/contacts/{contact_id}/workflow/{workflow_id}",
                headers=self.headers
            )

            return response.status_code in [200, 201]
        except Exception as e:
            logger.error(f"Error triggering workflow: {e}")
            return False

    def _normalize_phone(self, phone: str) -> str:
        """Normalize phone number for comparison"""
        if not phone:
            return ""
        return ''.join(filter(str.isdigit, phone))

    async def close(self):
        """Close HTTP client"""
        await self.client.aclose()