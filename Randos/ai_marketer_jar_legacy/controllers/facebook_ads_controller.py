#!/usr/bin/env python3
"""
Facebook Ads Controller
Natural language interface for Facebook/Instagram advertising
"""

import json
import requests
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta


class FacebookAdsController:
    """Controller for Facebook/Instagram Ads operations"""
    
    def __init__(self, brain):
        self.brain = brain
        self.base_url = "https://graph.facebook.com/v18.0"
        self.credentials = None
        self.access_token = None
        self.ad_account_id = None
        
    def initialize(self) -> bool:
        """Initialize Facebook Ads controller with stored credentials"""
        creds = self.brain.retrieve_credential('facebook_ads')
        if creds:
            self.credentials = creds
            self.access_token = creds.get('access_token')
            self.ad_account_id = creds.get('ad_account_id')
            return True
        return False
    
    def setup_credentials(self, access_token: str, ad_account_id: str, 
                         app_id: Optional[str] = None, app_secret: Optional[str] = None) -> Dict:
        """Store Facebook Ads API credentials securely"""
        credentials = {
            'access_token': access_token,
            'ad_account_id': ad_account_id,
            'app_id': app_id,
            'app_secret': app_secret,
            'setup_date': datetime.now().isoformat()
        }
        
        success = self.brain.store_credential('facebook_ads', credentials)
        
        if success:
            self.credentials = credentials
            self.access_token = access_token
            self.ad_account_id = ad_account_id
            
            # Verify credentials
            if self._verify_credentials():
                return {'status': 'success', 'message': 'Facebook Ads credentials stored securely'}
            else:
                return {'status': 'error', 'message': 'Invalid credentials'}
        
        return {'status': 'error', 'message': 'Failed to store credentials'}
    
    def _verify_credentials(self) -> bool:
        """Verify Facebook Ads credentials"""
        try:
            response = requests.get(
                f"{self.base_url}/me",
                params={'access_token': self.access_token}
            )
            return response.status_code == 200
        except:
            return False
    
    def natural_language_command(self, command: str) -> Dict:
        """Process natural language commands for Facebook Ads"""
        command_lower = command.lower()
        
        # Parse intent from natural language
        if 'create' in command_lower and 'campaign' in command_lower:
            return self._handle_create_campaign(command)
        elif 'create' in command_lower and 'ad' in command_lower:
            return self._handle_create_ad(command)
        elif 'list' in command_lower and 'campaign' in command_lower:
            return self.list_campaigns()
        elif 'pause' in command_lower:
            return self._handle_pause_campaign(command)
        elif 'resume' in command_lower:
            return self._handle_resume_campaign(command)
        elif 'target' in command_lower or 'audience' in command_lower:
            return self._handle_set_targeting(command)
        elif 'budget' in command_lower:
            return self._handle_set_budget(command)
        elif 'boost' in command_lower and 'post' in command_lower:
            return self._handle_boost_post(command)
        elif 'get' in command_lower and ('metrics' in command_lower or 'performance' in command_lower):
            return self.get_campaign_metrics()
        elif 'instagram' in command_lower:
            return self._handle_instagram_ad(command)
        else:
            return {
                'status': 'info',
                'message': 'Available commands',
                'commands': [
                    'Create campaign [name] with budget [amount]',
                    'Create ad for [campaign]',
                    'List campaigns',
                    'Pause campaign [name/id]',
                    'Resume campaign [name/id]',
                    'Target [demographics/interests] for [campaign]',
                    'Set budget [amount] for [campaign]',
                    'Boost post [post_id]',
                    'Get campaign metrics',
                    'Create Instagram ad'
                ]
            }
    
    def _handle_create_campaign(self, command: str) -> Dict:
        """Parse and handle create campaign command"""
        campaign_data = {
            'name': 'New Campaign',
            'objective': 'CONVERSIONS',
            'daily_budget': 50,
            'status': 'PAUSED'
        }
        
        # Extract campaign details from command
        parts = command.split()
        for i, part in enumerate(parts):
            if '$' in part or part.isdigit():
                try:
                    campaign_data['daily_budget'] = float(part.replace('$', '').replace(',', ''))
                except:
                    pass
            elif 'awareness' in part.lower():
                campaign_data['objective'] = 'BRAND_AWARENESS'
            elif 'traffic' in part.lower():
                campaign_data['objective'] = 'LINK_CLICKS'
            elif 'engagement' in part.lower():
                campaign_data['objective'] = 'POST_ENGAGEMENT'
        
        # Extract name
        if 'campaign' in command:
            name_parts = command.split('campaign')[1].split('with')[0].strip()
            if name_parts:
                campaign_data['name'] = name_parts
        
        return self.create_campaign(campaign_data)
    
    def create_campaign(self, campaign_data: Dict) -> Dict:
        """Create a new Facebook Ads campaign"""
        if not self.access_token:
            return {'status': 'error', 'message': 'Not authenticated. Please setup credentials first.'}
        
        try:
            # Create campaign
            campaign_params = {
                'name': campaign_data['name'],
                'objective': campaign_data['objective'],
                'status': campaign_data['status'],
                'special_ad_categories': [],
                'access_token': self.access_token
            }
            
            response = requests.post(
                f"{self.base_url}/act_{self.ad_account_id}/campaigns",
                data=campaign_params
            )
            
            if response.status_code == 200:
                campaign = response.json()
                campaign_id = campaign.get('id')
                
                # Create ad set with budget
                adset_params = {
                    'name': f"{campaign_data['name']} AdSet",
                    'campaign_id': campaign_id,
                    'daily_budget': int(campaign_data['daily_budget'] * 100),  # Convert to cents
                    'billing_event': 'IMPRESSIONS',
                    'optimization_goal': 'REACH',
                    'bid_amount': 2,
                    'targeting': json.dumps({
                        'geo_locations': {'countries': ['US']},
                        'age_min': 18,
                        'age_max': 65
                    }),
                    'status': 'PAUSED',
                    'access_token': self.access_token
                }
                
                adset_response = requests.post(
                    f"{self.base_url}/act_{self.ad_account_id}/adsets",
                    data=adset_params
                )
                
                # Store in L2 memory
                self.brain.save_campaign({
                    'campaign_id': f"facebook_ads_{campaign_id}",
                    'platform': 'facebook_ads',
                    'campaign_name': campaign_data['name'],
                    'status': campaign_data['status'].lower(),
                    'settings': campaign_data,
                    'metrics': {'daily_budget': campaign_data['daily_budget']}
                })
                
                return {
                    'status': 'success',
                    'campaign_id': campaign_id,
                    'message': f"Campaign '{campaign_data['name']}' created with ${campaign_data['daily_budget']}/day budget"
                }
            else:
                error = response.json().get('error', {})
                return {'status': 'error', 'message': error.get('message', 'Failed to create campaign')}
                
        except Exception as e:
            return {'status': 'error', 'message': str(e)}
    
    def list_campaigns(self) -> Dict:
        """List all campaigns"""
        if not self.access_token:
            return {'status': 'error', 'message': 'Not authenticated. Please setup credentials first.'}
        
        try:
            params = {
                'fields': 'id,name,status,objective,daily_budget,lifetime_budget',
                'access_token': self.access_token
            }
            
            response = requests.get(
                f"{self.base_url}/act_{self.ad_account_id}/campaigns",
                params=params
            )
            
            if response.status_code == 200:
                data = response.json()
                campaigns = data.get('data', [])
                
                return {
                    'status': 'success',
                    'count': len(campaigns),
                    'campaigns': [
                        {
                            'id': c.get('id'),
                            'name': c.get('name'),
                            'status': c.get('status'),
                            'objective': c.get('objective'),
                            'daily_budget': c.get('daily_budget', 0) / 100 if c.get('daily_budget') else None,
                            'lifetime_budget': c.get('lifetime_budget', 0) / 100 if c.get('lifetime_budget') else None
                        }
                        for c in campaigns
                    ]
                }
            else:
                return {'status': 'error', 'message': 'Failed to list campaigns'}
                
        except Exception as e:
            return {'status': 'error', 'message': str(e)}
    
    def _handle_pause_campaign(self, command: str) -> Dict:
        """Parse and handle pause campaign command"""
        parts = command.split('campaign')
        if len(parts) > 1:
            campaign_id = parts[1].strip()
            return self.update_campaign_status(campaign_id, 'PAUSED')
        return {'status': 'error', 'message': 'Could not identify campaign'}
    
    def _handle_resume_campaign(self, command: str) -> Dict:
        """Parse and handle resume campaign command"""
        parts = command.split('campaign')
        if len(parts) > 1:
            campaign_id = parts[1].strip()
            return self.update_campaign_status(campaign_id, 'ACTIVE')
        return {'status': 'error', 'message': 'Could not identify campaign'}
    
    def update_campaign_status(self, campaign_id: str, status: str) -> Dict:
        """Update campaign status"""
        if not self.access_token:
            return {'status': 'error', 'message': 'Not authenticated. Please setup credentials first.'}
        
        try:
            params = {
                'status': status,
                'access_token': self.access_token
            }
            
            response = requests.post(
                f"{self.base_url}/{campaign_id}",
                data=params
            )
            
            if response.status_code == 200:
                # Update L2 memory
                self.brain.save_campaign({
                    'campaign_id': f"facebook_ads_{campaign_id}",
                    'platform': 'facebook_ads',
                    'status': status.lower()
                })
                
                return {
                    'status': 'success',
                    'message': f"Campaign {campaign_id} status updated to {status}"
                }
            else:
                return {'status': 'error', 'message': 'Failed to update campaign status'}
                
        except Exception as e:
            return {'status': 'error', 'message': str(e)}
    
    def _handle_set_targeting(self, command: str) -> Dict:
        """Parse and handle targeting command"""
        targeting_data = {
            'geo_locations': {'countries': ['US']},
            'age_min': 18,
            'age_max': 65
        }
        
        command_lower = command.lower()
        
        # Parse age
        if 'young' in command_lower:
            targeting_data['age_min'] = 18
            targeting_data['age_max'] = 34
        elif 'middle age' in command_lower:
            targeting_data['age_min'] = 35
            targeting_data['age_max'] = 54
        elif 'senior' in command_lower:
            targeting_data['age_min'] = 55
            targeting_data['age_max'] = 65
        
        # Parse interests
        interests = []
        if 'fitness' in command_lower:
            interests.append({'id': '6003107902433', 'name': 'Fitness and wellness'})
        if 'technology' in command_lower:
            interests.append({'id': '6003397425735', 'name': 'Technology'})
        if 'fashion' in command_lower:
            interests.append({'id': '6002963432424', 'name': 'Fashion'})
        if 'business' in command_lower:
            interests.append({'id': '6003248297213', 'name': 'Business'})
        
        if interests:
            targeting_data['interests'] = interests
        
        # Parse gender
        if 'women' in command_lower or 'female' in command_lower:
            targeting_data['genders'] = [2]
        elif 'men' in command_lower or 'male' in command_lower:
            targeting_data['genders'] = [1]
        
        return {
            'status': 'success',
            'message': 'Targeting configured',
            'targeting': targeting_data
        }
    
    def _handle_set_budget(self, command: str) -> Dict:
        """Parse and handle budget command"""
        budget = 50  # Default
        campaign_id = None
        
        parts = command.split()
        for part in parts:
            if '$' in part or part.isdigit():
                try:
                    budget = float(part.replace('$', '').replace(',', ''))
                except:
                    pass
        
        if 'for' in command:
            campaign_id = command.split('for')[1].strip()
        
        if campaign_id:
            return self.update_budget(campaign_id, budget)
        
        return {'status': 'error', 'message': 'Please specify campaign ID'}
    
    def update_budget(self, campaign_id: str, daily_budget: float) -> Dict:
        """Update campaign budget"""
        if not self.access_token:
            return {'status': 'error', 'message': 'Not authenticated. Please setup credentials first.'}
        
        try:
            # Get adsets for the campaign
            params = {
                'fields': 'id',
                'access_token': self.access_token
            }
            
            response = requests.get(
                f"{self.base_url}/{campaign_id}/adsets",
                params=params
            )
            
            if response.status_code == 200:
                adsets = response.json().get('data', [])
                
                # Update budget for each adset
                for adset in adsets:
                    update_params = {
                        'daily_budget': int(daily_budget * 100),  # Convert to cents
                        'access_token': self.access_token
                    }
                    
                    requests.post(
                        f"{self.base_url}/{adset['id']}",
                        data=update_params
                    )
                
                # Log to analytics
                self.brain.save_analytics(
                    f"facebook_ads_{campaign_id}",
                    'budget_update',
                    daily_budget,
                    {'action': 'budget_change'}
                )
                
                return {
                    'status': 'success',
                    'message': f"Budget updated to ${daily_budget}/day for campaign {campaign_id}"
                }
            else:
                return {'status': 'error', 'message': 'Failed to update budget'}
                
        except Exception as e:
            return {'status': 'error', 'message': str(e)}
    
    def _handle_create_ad(self, command: str) -> Dict:
        """Parse and handle create ad command"""
        ad_data = {
            'name': 'New Ad',
            'headline': 'Check out our amazing product!',
            'description': 'Limited time offer - Shop now!',
            'call_to_action': 'SHOP_NOW'
        }
        
        # Extract campaign
        if 'for' in command:
            campaign_id = command.split('for')[1].strip()
            return self.create_ad(campaign_id, ad_data)
        
        return {'status': 'error', 'message': 'Please specify campaign: Create ad for [campaign]'}
    
    def create_ad(self, campaign_id: str, ad_data: Dict) -> Dict:
        """Create an ad"""
        if not self.access_token:
            return {'status': 'error', 'message': 'Not authenticated. Please setup credentials first.'}
        
        try:
            # Store ad data in working memory (simplified)
            self.brain.set_working_data(f"facebook_ad_{campaign_id}", ad_data)
            
            # Log to L2
            self.brain.save_campaign({
                'campaign_id': f"facebook_ad_{campaign_id}",
                'platform': 'facebook_ads',
                'campaign_name': ad_data['name'],
                'status': 'created',
                'settings': ad_data
            })
            
            return {
                'status': 'success',
                'message': f"Ad '{ad_data['name']}' created for campaign {campaign_id}",
                'ad_preview': ad_data
            }
            
        except Exception as e:
            return {'status': 'error', 'message': str(e)}
    
    def _handle_boost_post(self, command: str) -> Dict:
        """Parse and handle boost post command"""
        # Extract post ID
        parts = command.split('post')
        if len(parts) > 1:
            post_id = parts[1].strip()
            return self.boost_post(post_id)
        
        return {'status': 'error', 'message': 'Please specify post ID'}
    
    def boost_post(self, post_id: str, budget: float = 20, duration_days: int = 7) -> Dict:
        """Boost an existing post"""
        if not self.access_token:
            return {'status': 'error', 'message': 'Not authenticated. Please setup credentials first.'}
        
        try:
            # Create a campaign for the boosted post
            campaign_data = {
                'name': f'Boosted Post {post_id}',
                'objective': 'POST_ENGAGEMENT',
                'daily_budget': budget,
                'status': 'ACTIVE'
            }
            
            result = self.create_campaign(campaign_data)
            
            if result['status'] == 'success':
                # Store boost info
                self.brain.set_working_data(f"boost_{post_id}", {
                    'post_id': post_id,
                    'campaign_id': result['campaign_id'],
                    'daily_budget': budget,
                    'duration_days': duration_days
                })
                
                return {
                    'status': 'success',
                    'message': f"Post {post_id} boosted with ${budget}/day for {duration_days} days",
                    'campaign_id': result['campaign_id']
                }
            
            return result
            
        except Exception as e:
            return {'status': 'error', 'message': str(e)}
    
    def _handle_instagram_ad(self, command: str) -> Dict:
        """Parse and handle Instagram ad command"""
        ad_data = {
            'platform': 'instagram',
            'placement': 'feed',
            'format': 'single_image'
        }
        
        if 'story' in command.lower():
            ad_data['placement'] = 'story'
        if 'reel' in command.lower():
            ad_data['placement'] = 'reels'
        if 'video' in command.lower():
            ad_data['format'] = 'video'
        
        return {
            'status': 'info',
            'message': 'Instagram ad configuration',
            'config': ad_data,
            'next_steps': 'Create campaign with Instagram placement enabled'
        }
    
    def get_campaign_metrics(self, days: int = 7) -> Dict:
        """Get campaign performance metrics"""
        if not self.access_token:
            return {'status': 'error', 'message': 'Not authenticated. Please setup credentials first.'}
        
        try:
            # Calculate date range
            end_date = datetime.now().strftime('%Y-%m-%d')
            start_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
            
            params = {
                'fields': 'campaign_id,campaign_name,impressions,clicks,ctr,cpc,spend,conversions',
                'time_range': json.dumps({'since': start_date, 'until': end_date}),
                'access_token': self.access_token
            }
            
            response = requests.get(
                f"{self.base_url}/act_{self.ad_account_id}/insights",
                params=params
            )
            
            if response.status_code == 200:
                data = response.json().get('data', [])
                
                total_metrics = {
                    'impressions': 0,
                    'clicks': 0,
                    'spend': 0,
                    'conversions': 0,
                    'campaigns': []
                }
                
                for campaign in data:
                    campaign_metrics = {
                        'id': campaign.get('campaign_id'),
                        'name': campaign.get('campaign_name'),
                        'impressions': int(campaign.get('impressions', 0)),
                        'clicks': int(campaign.get('clicks', 0)),
                        'ctr': float(campaign.get('ctr', 0)),
                        'cpc': float(campaign.get('cpc', 0)),
                        'spend': float(campaign.get('spend', 0)),
                        'conversions': int(campaign.get('conversions', 0))
                    }
                    
                    total_metrics['campaigns'].append(campaign_metrics)
                    total_metrics['impressions'] += campaign_metrics['impressions']
                    total_metrics['clicks'] += campaign_metrics['clicks']
                    total_metrics['spend'] += campaign_metrics['spend']
                    total_metrics['conversions'] += campaign_metrics['conversions']
                
                # Calculate overall metrics
                if total_metrics['impressions'] > 0:
                    total_metrics['overall_ctr'] = (total_metrics['clicks'] / total_metrics['impressions']) * 100
                else:
                    total_metrics['overall_ctr'] = 0
                
                if total_metrics['clicks'] > 0:
                    total_metrics['overall_cpc'] = total_metrics['spend'] / total_metrics['clicks']
                else:
                    total_metrics['overall_cpc'] = 0
                
                # Save to analytics
                for metric in ['impressions', 'clicks', 'spend', 'conversions']:
                    self.brain.save_analytics(
                        'facebook_ads_overall',
                        metric,
                        total_metrics[metric],
                        {'period': f'{days}_days'}
                    )
                
                return {
                    'status': 'success',
                    'period': f"Last {days} days",
                    'metrics': total_metrics
                }
            else:
                return {'status': 'error', 'message': 'Failed to get metrics'}
                
        except Exception as e:
            return {'status': 'error', 'message': str(e)}
    
    def create_lookalike_audience(self, source_audience_id: str, country: str = 'US', ratio: float = 0.01) -> Dict:
        """Create a lookalike audience"""
        if not self.access_token:
            return {'status': 'error', 'message': 'Not authenticated. Please setup credentials first.'}
        
        try:
            params = {
                'name': f'Lookalike {ratio*100}% - {country}',
                'source': source_audience_id,
                'country': country,
                'ratio': ratio,
                'access_token': self.access_token
            }
            
            response = requests.post(
                f"{self.base_url}/act_{self.ad_account_id}/customaudiences",
                data=params
            )
            
            if response.status_code == 200:
                audience = response.json()
                return {
                    'status': 'success',
                    'audience_id': audience.get('id'),
                    'message': f"Lookalike audience created: {params['name']}"
                }
            else:
                return {'status': 'error', 'message': 'Failed to create lookalike audience'}
                
        except Exception as e:
            return {'status': 'error', 'message': str(e)}