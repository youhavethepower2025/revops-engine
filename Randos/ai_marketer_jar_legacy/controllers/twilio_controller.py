#!/usr/bin/env python3
"""
Twilio Controller
Natural language interface for SMS marketing campaigns
"""

import json
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from twilio.rest import Client
from twilio.base.exceptions import TwilioRestException


class TwilioController:
    """Controller for Twilio SMS operations"""
    
    def __init__(self, brain):
        self.brain = brain
        self.client = None
        self.credentials = None
        self.from_number = None
        
    def initialize(self) -> bool:
        """Initialize Twilio controller with stored credentials"""
        creds = self.brain.retrieve_credential('twilio')
        if creds:
            self.credentials = creds
            try:
                self.client = Client(
                    creds.get('account_sid'),
                    creds.get('auth_token')
                )
                self.from_number = creds.get('from_number')
                return True
            except:
                return False
        return False
    
    def setup_credentials(self, account_sid: str, auth_token: str, 
                         from_number: str, messaging_service_sid: Optional[str] = None) -> Dict:
        """Store Twilio API credentials securely"""
        credentials = {
            'account_sid': account_sid,
            'auth_token': auth_token,
            'from_number': from_number,
            'messaging_service_sid': messaging_service_sid,
            'setup_date': datetime.now().isoformat()
        }
        
        # Verify credentials
        try:
            test_client = Client(account_sid, auth_token)
            test_client.api.accounts(account_sid).fetch()
        except Exception as e:
            return {'status': 'error', 'message': f'Invalid credentials: {str(e)}'}
        
        success = self.brain.store_credential('twilio', credentials)
        
        if success:
            self.credentials = credentials
            self.client = Client(account_sid, auth_token)
            self.from_number = from_number
            return {'status': 'success', 'message': 'Twilio credentials stored securely'}
        
        return {'status': 'error', 'message': 'Failed to store credentials'}
    
    def natural_language_command(self, command: str) -> Dict:
        """Process natural language commands for Twilio SMS"""
        command_lower = command.lower()
        
        # Parse intent from natural language
        if 'send' in command_lower and ('sms' in command_lower or 'text' in command_lower or 'message' in command_lower):
            return self._handle_send_sms(command)
        elif 'broadcast' in command_lower or 'bulk' in command_lower:
            return self._handle_broadcast_sms(command)
        elif 'schedule' in command_lower:
            return self._handle_schedule_sms(command)
        elif 'create' in command_lower and 'campaign' in command_lower:
            return self._handle_create_campaign(command)
        elif 'list' in command_lower and 'campaign' in command_lower:
            return self.list_campaigns()
        elif 'stop' in command_lower or 'cancel' in command_lower:
            return self._handle_stop_campaign(command)
        elif 'add' in command_lower and 'contact' in command_lower:
            return self._handle_add_contact(command)
        elif 'remove' in command_lower and 'contact' in command_lower:
            return self._handle_remove_contact(command)
        elif 'get' in command_lower and ('metrics' in command_lower or 'stats' in command_lower):
            return self.get_campaign_metrics()
        elif 'template' in command_lower:
            return self._handle_template_management(command)
        else:
            return {
                'status': 'info',
                'message': 'Available commands',
                'commands': [
                    'Send SMS [message] to [number]',
                    'Broadcast SMS [message] to [list/segment]',
                    'Schedule SMS [message] for [time]',
                    'Create campaign [name]',
                    'List campaigns',
                    'Stop campaign [name/id]',
                    'Add contact [number] to [list]',
                    'Remove contact [number]',
                    'Get campaign metrics',
                    'Create template [name]'
                ]
            }
    
    def _handle_send_sms(self, command: str) -> Dict:
        """Parse and handle send SMS command"""
        # Extract message and recipient
        if 'to' in command.lower():
            parts = command.lower().split('to')
            message_part = parts[0].replace('send', '').replace('sms', '').replace('text', '').replace('message', '').strip()
            recipient_part = parts[1].strip()
            
            # Clean up phone number
            recipient = ''.join(filter(str.isdigit, recipient_part))
            if not recipient.startswith('+'):
                recipient = '+1' + recipient  # Default to US
            
            return self.send_sms(recipient, message_part)
        
        return {'status': 'error', 'message': 'Format: Send SMS [message] to [number]'}
    
    def send_sms(self, to_number: str, message: str) -> Dict:
        """Send a single SMS message"""
        if not self.client:
            return {'status': 'error', 'message': 'Not authenticated. Please setup credentials first.'}
        
        try:
            message_obj = self.client.messages.create(
                body=message,
                from_=self.from_number,
                to=to_number
            )
            
            # Store in L2 memory
            self.brain.save_campaign({
                'campaign_id': f"twilio_sms_{message_obj.sid}",
                'platform': 'twilio',
                'campaign_name': f"SMS to {to_number}",
                'status': 'sent',
                'settings': {
                    'to': to_number,
                    'message': message,
                    'sid': message_obj.sid
                }
            })
            
            # Log analytics
            self.brain.save_analytics(
                f"twilio_sms_{to_number}",
                'sms_sent',
                1,
                {'message_length': len(message), 'sid': message_obj.sid}
            )
            
            return {
                'status': 'success',
                'message_sid': message_obj.sid,
                'message': f"SMS sent to {to_number}",
                'status_callback': message_obj.status
            }
            
        except TwilioRestException as e:
            return {'status': 'error', 'message': f"Twilio error: {e.msg}"}
        except Exception as e:
            return {'status': 'error', 'message': str(e)}
    
    def _handle_broadcast_sms(self, command: str) -> Dict:
        """Parse and handle broadcast SMS command"""
        # Extract message and recipients
        if 'to' in command.lower():
            parts = command.lower().split('to')
            message_part = parts[0].replace('broadcast', '').replace('bulk', '').replace('sms', '').strip()
            recipients_part = parts[1].strip()
            
            # Get recipients from working memory or parse
            recipients = self.brain.get_working_data(f"contact_list_{recipients_part}")
            if not recipients:
                # Try to parse as comma-separated numbers
                recipients = [r.strip() for r in recipients_part.split(',')]
            
            return self.broadcast_sms(recipients, message_part)
        
        return {'status': 'error', 'message': 'Format: Broadcast SMS [message] to [list]'}
    
    def broadcast_sms(self, recipients: List[str], message: str) -> Dict:
        """Send SMS to multiple recipients"""
        if not self.client:
            return {'status': 'error', 'message': 'Not authenticated. Please setup credentials first.'}
        
        results = {
            'success': 0,
            'failed': 0,
            'message_sids': [],
            'errors': []
        }
        
        campaign_id = f"twilio_broadcast_{datetime.now().timestamp()}"
        
        for recipient in recipients:
            # Clean up phone number
            if not recipient.startswith('+'):
                recipient = '+1' + recipient  # Default to US
            
            try:
                message_obj = self.client.messages.create(
                    body=message,
                    from_=self.from_number,
                    to=recipient
                )
                results['success'] += 1
                results['message_sids'].append(message_obj.sid)
                
            except TwilioRestException as e:
                results['failed'] += 1
                results['errors'].append(f"{recipient}: {e.msg}")
        
        # Store campaign in L2 memory
        self.brain.save_campaign({
            'campaign_id': campaign_id,
            'platform': 'twilio',
            'campaign_name': f"Broadcast to {len(recipients)} recipients",
            'status': 'completed',
            'metrics': {
                'recipients': len(recipients),
                'success': results['success'],
                'failed': results['failed']
            },
            'settings': {
                'message': message,
                'recipients_count': len(recipients)
            }
        })
        
        # Log analytics
        self.brain.save_analytics(
            campaign_id,
            'broadcast_sent',
            results['success'],
            {'total_recipients': len(recipients), 'failed': results['failed']}
        )
        
        return {
            'status': 'success',
            'campaign_id': campaign_id,
            'sent': results['success'],
            'failed': results['failed'],
            'message': f"Broadcast sent to {results['success']} of {len(recipients)} recipients"
        }
    
    def _handle_schedule_sms(self, command: str) -> Dict:
        """Parse and handle schedule SMS command"""
        # Store scheduling info in working memory
        schedule_data = {
            'message': '',
            'recipients': [],
            'scheduled_time': None
        }
        
        # Extract time
        if 'at' in command.lower():
            time_part = command.lower().split('at')[1].strip()
            schedule_data['scheduled_time'] = time_part
        elif 'in' in command.lower():
            delay_part = command.lower().split('in')[1].strip()
            # Parse delay (e.g., "5 minutes", "1 hour")
            if 'minute' in delay_part:
                minutes = int(''.join(filter(str.isdigit, delay_part)))
                schedule_data['scheduled_time'] = (datetime.now() + timedelta(minutes=minutes)).isoformat()
            elif 'hour' in delay_part:
                hours = int(''.join(filter(str.isdigit, delay_part)))
                schedule_data['scheduled_time'] = (datetime.now() + timedelta(hours=hours)).isoformat()
        
        # Store in working memory
        schedule_id = f"schedule_{datetime.now().timestamp()}"
        self.brain.set_working_data(schedule_id, schedule_data)
        
        return {
            'status': 'success',
            'schedule_id': schedule_id,
            'message': f"SMS scheduled for {schedule_data['scheduled_time']}",
            'note': 'Scheduled messages are stored in working memory. Implement cron/scheduler for production.'
        }
    
    def _handle_create_campaign(self, command: str) -> Dict:
        """Parse and handle create campaign command"""
        # Extract campaign name
        parts = command.split('campaign')
        campaign_name = parts[1].strip() if len(parts) > 1 else f"Campaign {datetime.now().strftime('%Y%m%d')}"
        
        return self.create_campaign(campaign_name)
    
    def create_campaign(self, name: str, settings: Dict = None) -> Dict:
        """Create an SMS campaign"""
        if not self.client:
            return {'status': 'error', 'message': 'Not authenticated. Please setup credentials first.'}
        
        campaign_id = f"twilio_campaign_{datetime.now().timestamp()}"
        
        campaign_data = {
            'campaign_id': campaign_id,
            'platform': 'twilio',
            'campaign_name': name,
            'status': 'draft',
            'settings': settings or {
                'message_template': '',
                'recipients': [],
                'schedule': None,
                'personalization': False
            }
        }
        
        # Store in L2 memory
        self.brain.save_campaign(campaign_data)
        
        # Store in working memory for quick access
        self.brain.set_working_data(f"campaign_{campaign_id}", campaign_data)
        
        return {
            'status': 'success',
            'campaign_id': campaign_id,
            'message': f"Campaign '{name}' created",
            'next_steps': [
                'Add recipients to campaign',
                'Set message template',
                'Schedule or send campaign'
            ]
        }
    
    def list_campaigns(self) -> Dict:
        """List SMS campaigns"""
        # Get from L2 memory
        campaigns = self.brain.get_campaign_history('twilio', limit=20)
        
        return {
            'status': 'success',
            'count': len(campaigns),
            'campaigns': [
                {
                    'id': c['campaign_id'],
                    'name': c['campaign_name'],
                    'status': c['status'],
                    'created': c['created_at'],
                    'metrics': c.get('metrics', {})
                }
                for c in campaigns
            ]
        }
    
    def _handle_stop_campaign(self, command: str) -> Dict:
        """Parse and handle stop campaign command"""
        # Extract campaign identifier
        parts = command.split('campaign')
        if len(parts) > 1:
            campaign_id = parts[1].strip()
            return self.stop_campaign(campaign_id)
        
        return {'status': 'error', 'message': 'Please specify campaign ID'}
    
    def stop_campaign(self, campaign_id: str) -> Dict:
        """Stop/cancel a campaign"""
        # Update campaign status in L2
        self.brain.save_campaign({
            'campaign_id': campaign_id,
            'platform': 'twilio',
            'status': 'stopped'
        })
        
        # Clear from working memory
        self.brain.set_working_data(f"campaign_{campaign_id}", None)
        
        return {
            'status': 'success',
            'message': f"Campaign {campaign_id} stopped"
        }
    
    def _handle_add_contact(self, command: str) -> Dict:
        """Parse and handle add contact command"""
        # Extract phone number and list
        if 'to' in command.lower():
            parts = command.lower().split('to')
            contact_part = parts[0].replace('add', '').replace('contact', '').strip()
            list_part = parts[1].strip()
            
            # Clean phone number
            contact = ''.join(filter(str.isdigit, contact_part))
            if not contact.startswith('+'):
                contact = '+1' + contact
            
            return self.add_contact(contact, list_part)
        
        return {'status': 'error', 'message': 'Format: Add contact [number] to [list]'}
    
    def add_contact(self, phone_number: str, list_name: str) -> Dict:
        """Add a contact to a list"""
        # Get or create contact list in working memory
        list_key = f"contact_list_{list_name}"
        contacts = self.brain.get_working_data(list_key) or []
        
        if phone_number not in contacts:
            contacts.append(phone_number)
            self.brain.set_working_data(list_key, contacts)
            
            # Log to analytics
            self.brain.save_analytics(
                f"twilio_list_{list_name}",
                'contact_added',
                1,
                {'phone': phone_number}
            )
            
            return {
                'status': 'success',
                'message': f"Contact {phone_number} added to list '{list_name}'",
                'list_size': len(contacts)
            }
        
        return {
            'status': 'info',
            'message': f"Contact {phone_number} already in list '{list_name}'",
            'list_size': len(contacts)
        }
    
    def _handle_remove_contact(self, command: str) -> Dict:
        """Parse and handle remove contact command"""
        # Extract phone number
        parts = command.lower().split('contact')
        if len(parts) > 1:
            contact_part = parts[1].strip()
            
            # Clean phone number
            contact = ''.join(filter(str.isdigit, contact_part))
            if not contact.startswith('+'):
                contact = '+1' + contact
            
            return self.remove_contact(contact)
        
        return {'status': 'error', 'message': 'Please specify contact number'}
    
    def remove_contact(self, phone_number: str) -> Dict:
        """Remove a contact from all lists"""
        removed_from = []
        
        # Check all contact lists in working memory
        # In production, this would query a proper database
        for i in range(10):  # Check first 10 potential lists
            for list_name in ['marketing', 'customers', 'leads', 'vip', f'list_{i}']:
                list_key = f"contact_list_{list_name}"
                contacts = self.brain.get_working_data(list_key)
                
                if contacts and phone_number in contacts:
                    contacts.remove(phone_number)
                    self.brain.set_working_data(list_key, contacts)
                    removed_from.append(list_name)
        
        if removed_from:
            return {
                'status': 'success',
                'message': f"Contact {phone_number} removed from lists: {', '.join(removed_from)}"
            }
        
        return {
            'status': 'info',
            'message': f"Contact {phone_number} not found in any lists"
        }
    
    def get_campaign_metrics(self) -> Dict:
        """Get SMS campaign metrics"""
        if not self.client:
            return {'status': 'error', 'message': 'Not authenticated. Please setup credentials first.'}
        
        try:
            # Get message statistics from Twilio
            messages = self.client.messages.list(limit=100)
            
            metrics = {
                'total_sent': 0,
                'delivered': 0,
                'failed': 0,
                'queued': 0,
                'cost': 0.0
            }
            
            for message in messages:
                metrics['total_sent'] += 1
                
                if message.status == 'delivered':
                    metrics['delivered'] += 1
                elif message.status == 'failed':
                    metrics['failed'] += 1
                elif message.status == 'queued':
                    metrics['queued'] += 1
                
                if message.price:
                    metrics['cost'] += abs(float(message.price))
            
            # Calculate delivery rate
            if metrics['total_sent'] > 0:
                metrics['delivery_rate'] = (metrics['delivered'] / metrics['total_sent']) * 100
            else:
                metrics['delivery_rate'] = 0
            
            # Get campaign history from L2
            campaign_history = self.brain.get_campaign_history('twilio', limit=10)
            
            return {
                'status': 'success',
                'metrics': metrics,
                'recent_campaigns': len(campaign_history),
                'message': f"Delivered {metrics['delivered']} of {metrics['total_sent']} messages ({metrics['delivery_rate']:.1f}% delivery rate)"
            }
            
        except Exception as e:
            return {'status': 'error', 'message': str(e)}
    
    def _handle_template_management(self, command: str) -> Dict:
        """Parse and handle template commands"""
        if 'create' in command.lower():
            # Extract template name
            parts = command.split('template')
            template_name = parts[1].strip() if len(parts) > 1 else 'New Template'
            
            return self.create_template(template_name)
        elif 'list' in command.lower():
            return self.list_templates()
        
        return {'status': 'error', 'message': 'Available template commands: Create template [name], List templates'}
    
    def create_template(self, name: str, content: str = "") -> Dict:
        """Create an SMS template"""
        template_id = f"template_{datetime.now().timestamp()}"
        
        template_data = {
            'id': template_id,
            'name': name,
            'content': content or "Hi {{name}}, your {{product}} is ready for pickup!",
            'variables': ['name', 'product'],
            'created_at': datetime.now().isoformat()
        }
        
        # Store in working memory
        self.brain.set_working_data(f"sms_template_{template_id}", template_data)
        
        # Also store a list of template IDs
        templates = self.brain.get_working_data('sms_templates') or []
        templates.append(template_id)
        self.brain.set_working_data('sms_templates', templates)
        
        return {
            'status': 'success',
            'template_id': template_id,
            'message': f"Template '{name}' created",
            'template': template_data
        }
    
    def list_templates(self) -> Dict:
        """List all SMS templates"""
        template_ids = self.brain.get_working_data('sms_templates') or []
        
        templates = []
        for tid in template_ids:
            template = self.brain.get_working_data(f"sms_template_{tid}")
            if template:
                templates.append(template)
        
        return {
            'status': 'success',
            'count': len(templates),
            'templates': templates
        }
    
    def send_with_template(self, template_id: str, recipient: str, variables: Dict) -> Dict:
        """Send SMS using a template"""
        if not self.client:
            return {'status': 'error', 'message': 'Not authenticated. Please setup credentials first.'}
        
        # Get template
        template = self.brain.get_working_data(f"sms_template_{template_id}")
        if not template:
            return {'status': 'error', 'message': 'Template not found'}
        
        # Replace variables in template
        message = template['content']
        for var, value in variables.items():
            message = message.replace(f"{{{{{var}}}}}", str(value))
        
        # Send SMS
        return self.send_sms(recipient, message)
    
    def get_phone_number_info(self, phone_number: str) -> Dict:
        """Look up information about a phone number"""
        if not self.client:
            return {'status': 'error', 'message': 'Not authenticated. Please setup credentials first.'}
        
        try:
            phone_number_info = self.client.lookups.v1.phone_numbers(phone_number).fetch(
                type=['carrier', 'caller-name']
            )
            
            return {
                'status': 'success',
                'phone_number': phone_number_info.phone_number,
                'carrier': phone_number_info.carrier,
                'caller_name': phone_number_info.caller_name,
                'country_code': phone_number_info.country_code,
                'national_format': phone_number_info.national_format
            }
            
        except Exception as e:
            return {'status': 'error', 'message': str(e)}