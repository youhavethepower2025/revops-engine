#!/usr/bin/env python3
"""
GoHighLevel CRM Controller
Natural language interface for GoHighLevel marketing automation
"""

import requests
import json
from typing import Dict, List, Optional, Any
from datetime import datetime


class GHLController:
    """Controller for GoHighLevel CRM operations"""
    
    def __init__(self, brain):
        self.brain = brain
        self.base_url = "https://api.gohighlevel.com/v1"
        self.credentials = None
        self.headers = {}
        
    def initialize(self) -> bool:
        """Initialize GHL controller with stored credentials"""
        creds = self.brain.retrieve_credential('gohighlevel')
        if creds:
            self.credentials = creds
            self.headers = {
                'Authorization': f"Bearer {creds.get('api_key')}",
                'Content-Type': 'application/json'
            }
            return True
        return False
    
    def setup_credentials(self, api_key: str, location_id: Optional[str] = None) -> Dict:
        """Store GHL API credentials securely"""
        credentials = {
            'api_key': api_key,
            'location_id': location_id,
            'setup_date': datetime.now().isoformat()
        }
        
        success = self.brain.store_credential('gohighlevel', credentials)
        
        if success:
            self.credentials = credentials
            self.headers = {
                'Authorization': f"Bearer {api_key}",
                'Content-Type': 'application/json'
            }
            return {'status': 'success', 'message': 'GHL credentials stored securely'}
        
        return {'status': 'error', 'message': 'Failed to store credentials'}
    
    def natural_language_command(self, command: str) -> Dict:
        """Process natural language commands for GHL"""
        command_lower = command.lower()
        
        # Parse intent from natural language
        if 'create' in command_lower and 'contact' in command_lower:
            return self._handle_create_contact(command)
        elif 'list' in command_lower and 'contact' in command_lower:
            return self.list_contacts()
        elif 'create' in command_lower and 'campaign' in command_lower:
            return self._handle_create_campaign(command)
        elif 'send' in command_lower and ('sms' in command_lower or 'text' in command_lower):
            return self._handle_send_sms(command)
        elif 'create' in command_lower and 'pipeline' in command_lower:
            return self._handle_create_pipeline(command)
        elif 'add' in command_lower and 'tag' in command_lower:
            return self._handle_add_tag(command)
        elif 'schedule' in command_lower and 'appointment' in command_lower:
            return self._handle_schedule_appointment(command)
        elif 'get' in command_lower and 'analytics' in command_lower:
            return self.get_analytics()
        else:
            return {
                'status': 'info',
                'message': 'Available commands',
                'commands': [
                    'Create contact [name] [email] [phone]',
                    'List contacts',
                    'Create campaign [name]',
                    'Send SMS to [contact]',
                    'Create pipeline [name]',
                    'Add tag [tag] to [contact]',
                    'Schedule appointment for [contact]',
                    'Get analytics'
                ]
            }
    
    def _handle_create_contact(self, command: str) -> Dict:
        """Parse and handle create contact command"""
        # Extract contact details from natural language
        # This is a simplified parser - in production, use NLP
        parts = command.split()
        
        contact_data = {
            'firstName': 'New',
            'lastName': 'Contact',
            'email': None,
            'phone': None
        }
        
        # Look for email pattern
        for part in parts:
            if '@' in part:
                contact_data['email'] = part
            elif part.replace('-', '').replace('+', '').isdigit():
                contact_data['phone'] = part
        
        return self.create_contact(contact_data)
    
    def create_contact(self, contact_data: Dict) -> Dict:
        """Create a new contact in GHL"""
        if not self.credentials:
            return {'status': 'error', 'message': 'Not authenticated. Please setup credentials first.'}
        
        try:
            response = requests.post(
                f"{self.base_url}/contacts",
                headers=self.headers,
                json=contact_data
            )
            
            if response.status_code == 201:
                contact = response.json()
                
                # Store in L2 memory
                self.brain.save_campaign({
                    'campaign_id': f"ghl_contact_{contact.get('id')}",
                    'platform': 'gohighlevel',
                    'campaign_name': f"Contact: {contact_data.get('firstName')} {contact_data.get('lastName')}",
                    'status': 'created',
                    'settings': contact_data
                })
                
                return {
                    'status': 'success',
                    'contact_id': contact.get('id'),
                    'message': f"Contact created: {contact_data.get('firstName')} {contact_data.get('lastName')}"
                }
            else:
                return {'status': 'error', 'message': f"Failed to create contact: {response.text}"}
                
        except Exception as e:
            return {'status': 'error', 'message': str(e)}
    
    def list_contacts(self, limit: int = 10) -> Dict:
        """List contacts from GHL"""
        if not self.credentials:
            return {'status': 'error', 'message': 'Not authenticated. Please setup credentials first.'}
        
        try:
            response = requests.get(
                f"{self.base_url}/contacts",
                headers=self.headers,
                params={'limit': limit}
            )
            
            if response.status_code == 200:
                contacts = response.json().get('contacts', [])
                return {
                    'status': 'success',
                    'count': len(contacts),
                    'contacts': [
                        {
                            'id': c.get('id'),
                            'name': f"{c.get('firstName', '')} {c.get('lastName', '')}",
                            'email': c.get('email'),
                            'phone': c.get('phone')
                        }
                        for c in contacts
                    ]
                }
            else:
                return {'status': 'error', 'message': f"Failed to list contacts: {response.text}"}
                
        except Exception as e:
            return {'status': 'error', 'message': str(e)}
    
    def _handle_create_campaign(self, command: str) -> Dict:
        """Parse and handle create campaign command"""
        # Extract campaign name from command
        parts = command.split('campaign')
        campaign_name = parts[1].strip() if len(parts) > 1 else "New Campaign"
        
        return self.create_campaign(campaign_name)
    
    def create_campaign(self, name: str, settings: Dict = None) -> Dict:
        """Create a marketing campaign"""
        if not self.credentials:
            return {'status': 'error', 'message': 'Not authenticated. Please setup credentials first.'}
        
        campaign_data = {
            'name': name,
            'status': 'active',
            'settings': settings or {}
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/campaigns",
                headers=self.headers,
                json=campaign_data
            )
            
            if response.status_code in [200, 201]:
                campaign = response.json()
                
                # Store in L2 memory
                self.brain.save_campaign({
                    'campaign_id': f"ghl_campaign_{campaign.get('id', 'temp')}",
                    'platform': 'gohighlevel',
                    'campaign_name': name,
                    'status': 'active',
                    'settings': campaign_data
                })
                
                return {
                    'status': 'success',
                    'campaign_id': campaign.get('id'),
                    'message': f"Campaign '{name}' created successfully"
                }
            else:
                return {'status': 'error', 'message': f"Failed to create campaign: {response.text}"}
                
        except Exception as e:
            return {'status': 'error', 'message': str(e)}
    
    def _handle_send_sms(self, command: str) -> Dict:
        """Parse and handle send SMS command"""
        # Extract message and recipient from command
        # This is simplified - use NLP in production
        parts = command.lower().split('to')
        
        if len(parts) >= 2:
            message = parts[0].replace('send', '').replace('sms', '').replace('text', '').strip()
            recipient = parts[1].strip()
            
            return self.send_sms(recipient, message)
        
        return {'status': 'error', 'message': 'Could not parse SMS command. Format: Send SMS [message] to [contact]'}
    
    def send_sms(self, contact_id: str, message: str) -> Dict:
        """Send SMS message through GHL"""
        if not self.credentials:
            return {'status': 'error', 'message': 'Not authenticated. Please setup credentials first.'}
        
        sms_data = {
            'contactId': contact_id,
            'message': message,
            'type': 'SMS'
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/conversations/messages",
                headers=self.headers,
                json=sms_data
            )
            
            if response.status_code in [200, 201]:
                # Log to analytics
                self.brain.save_analytics(
                    f"ghl_sms_{contact_id}",
                    'sms_sent',
                    1,
                    {'message_length': len(message)}
                )
                
                return {
                    'status': 'success',
                    'message': f"SMS sent to {contact_id}"
                }
            else:
                return {'status': 'error', 'message': f"Failed to send SMS: {response.text}"}
                
        except Exception as e:
            return {'status': 'error', 'message': str(e)}
    
    def _handle_create_pipeline(self, command: str) -> Dict:
        """Parse and handle create pipeline command"""
        parts = command.split('pipeline')
        pipeline_name = parts[1].strip() if len(parts) > 1 else "New Pipeline"
        
        return self.create_pipeline(pipeline_name)
    
    def create_pipeline(self, name: str, stages: List[str] = None) -> Dict:
        """Create a sales pipeline"""
        if not self.credentials:
            return {'status': 'error', 'message': 'Not authenticated. Please setup credentials first.'}
        
        if not stages:
            stages = ['New Lead', 'Contacted', 'Qualified', 'Proposal', 'Closed Won', 'Closed Lost']
        
        pipeline_data = {
            'name': name,
            'stages': [{'name': stage} for stage in stages]
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/pipelines",
                headers=self.headers,
                json=pipeline_data
            )
            
            if response.status_code in [200, 201]:
                return {
                    'status': 'success',
                    'message': f"Pipeline '{name}' created with {len(stages)} stages"
                }
            else:
                return {'status': 'error', 'message': f"Failed to create pipeline: {response.text}"}
                
        except Exception as e:
            return {'status': 'error', 'message': str(e)}
    
    def _handle_add_tag(self, command: str) -> Dict:
        """Parse and handle add tag command"""
        parts = command.lower().split('to')
        
        if len(parts) >= 2:
            tag_part = parts[0].replace('add', '').replace('tag', '').strip()
            contact_part = parts[1].strip()
            
            return self.add_tag(contact_part, tag_part)
        
        return {'status': 'error', 'message': 'Could not parse tag command. Format: Add tag [tag_name] to [contact]'}
    
    def add_tag(self, contact_id: str, tag: str) -> Dict:
        """Add a tag to a contact"""
        if not self.credentials:
            return {'status': 'error', 'message': 'Not authenticated. Please setup credentials first.'}
        
        try:
            response = requests.post(
                f"{self.base_url}/contacts/{contact_id}/tags",
                headers=self.headers,
                json={'tags': [tag]}
            )
            
            if response.status_code in [200, 201]:
                return {
                    'status': 'success',
                    'message': f"Tag '{tag}' added to contact {contact_id}"
                }
            else:
                return {'status': 'error', 'message': f"Failed to add tag: {response.text}"}
                
        except Exception as e:
            return {'status': 'error', 'message': str(e)}
    
    def _handle_schedule_appointment(self, command: str) -> Dict:
        """Parse and handle schedule appointment command"""
        # Simplified parsing
        return {
            'status': 'info',
            'message': 'To schedule an appointment, please provide:',
            'required': ['contact_id', 'date', 'time', 'duration_minutes']
        }
    
    def get_analytics(self) -> Dict:
        """Get analytics and metrics"""
        if not self.credentials:
            return {'status': 'error', 'message': 'Not authenticated. Please setup credentials first.'}
        
        try:
            # Get various metrics
            metrics = {
                'contacts': 0,
                'campaigns': 0,
                'pipelines': 0,
                'recent_activity': []
            }
            
            # Get contact count
            response = requests.get(
                f"{self.base_url}/contacts",
                headers=self.headers,
                params={'limit': 1}
            )
            if response.status_code == 200:
                metrics['contacts'] = response.json().get('total', 0)
            
            # Get from L2 memory
            campaign_history = self.brain.get_campaign_history('gohighlevel', limit=5)
            metrics['recent_campaigns'] = len(campaign_history)
            metrics['recent_activity'] = [
                {
                    'type': 'campaign',
                    'name': c['campaign_name'],
                    'date': c['updated_at']
                }
                for c in campaign_history
            ]
            
            return {
                'status': 'success',
                'metrics': metrics
            }
            
        except Exception as e:
            return {'status': 'error', 'message': str(e)}
    
    def bulk_import_contacts(self, contacts: List[Dict]) -> Dict:
        """Import multiple contacts at once"""
        if not self.credentials:
            return {'status': 'error', 'message': 'Not authenticated. Please setup credentials first.'}
        
        results = {
            'success': 0,
            'failed': 0,
            'errors': []
        }
        
        for contact in contacts:
            result = self.create_contact(contact)
            if result['status'] == 'success':
                results['success'] += 1
            else:
                results['failed'] += 1
                results['errors'].append(result.get('message'))
        
        return {
            'status': 'success',
            'imported': results['success'],
            'failed': results['failed'],
            'errors': results['errors'][:5]  # Limit error messages
        }