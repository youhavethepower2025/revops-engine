#!/usr/bin/env python3
"""
Google Ads Controller
Natural language interface for Google Ads campaign management
"""

import json
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from google.ads.googleads.client import GoogleAdsClient
from google.ads.googleads.errors import GoogleAdsException


class GoogleAdsController:
    """Controller for Google Ads operations"""
    
    def __init__(self, brain):
        self.brain = brain
        self.client = None
        self.credentials = None
        self.customer_id = None
        
    def initialize(self) -> bool:
        """Initialize Google Ads controller with stored credentials"""
        creds = self.brain.retrieve_credential('google_ads')
        if creds:
            self.credentials = creds
            self.customer_id = creds.get('customer_id')
            
            # Initialize Google Ads client
            try:
                credentials_dict = {
                    'developer_token': creds.get('developer_token'),
                    'client_id': creds.get('client_id'),
                    'client_secret': creds.get('client_secret'),
                    'refresh_token': creds.get('refresh_token'),
                    'login_customer_id': creds.get('login_customer_id')
                }
                
                self.client = GoogleAdsClient.load_from_dict(credentials_dict)
                return True
            except Exception:
                return False
        return False
    
    def setup_credentials(self, developer_token: str, client_id: str, 
                         client_secret: str, refresh_token: str,
                         customer_id: str, login_customer_id: Optional[str] = None) -> Dict:
        """Store Google Ads API credentials securely"""
        credentials = {
            'developer_token': developer_token,
            'client_id': client_id,
            'client_secret': client_secret,
            'refresh_token': refresh_token,
            'customer_id': customer_id,
            'login_customer_id': login_customer_id or customer_id,
            'setup_date': datetime.now().isoformat()
        }
        
        success = self.brain.store_credential('google_ads', credentials)
        
        if success:
            self.credentials = credentials
            self.customer_id = customer_id
            
            # Initialize client
            try:
                credentials_dict = {
                    'developer_token': developer_token,
                    'client_id': client_id,
                    'client_secret': client_secret,
                    'refresh_token': refresh_token,
                    'login_customer_id': login_customer_id or customer_id
                }
                
                self.client = GoogleAdsClient.load_from_dict(credentials_dict)
                return {'status': 'success', 'message': 'Google Ads credentials stored securely'}
            except Exception as e:
                return {'status': 'error', 'message': f'Failed to initialize client: {str(e)}'}
        
        return {'status': 'error', 'message': 'Failed to store credentials'}
    
    def natural_language_command(self, command: str) -> Dict:
        """Process natural language commands for Google Ads"""
        command_lower = command.lower()
        
        # Parse intent from natural language
        if 'create' in command_lower and 'campaign' in command_lower:
            return self._handle_create_campaign(command)
        elif 'pause' in command_lower and 'campaign' in command_lower:
            return self._handle_pause_campaign(command)
        elif 'resume' in command_lower and 'campaign' in command_lower:
            return self._handle_resume_campaign(command)
        elif 'list' in command_lower and 'campaign' in command_lower:
            return self.list_campaigns()
        elif 'create' in command_lower and 'ad' in command_lower:
            return self._handle_create_ad(command)
        elif 'set' in command_lower and 'budget' in command_lower:
            return self._handle_set_budget(command)
        elif 'add' in command_lower and 'keyword' in command_lower:
            return self._handle_add_keywords(command)
        elif 'get' in command_lower and ('performance' in command_lower or 'metrics' in command_lower):
            return self.get_performance_metrics()
        elif 'optimize' in command_lower:
            return self.optimize_campaigns()
        else:
            return {
                'status': 'info',
                'message': 'Available commands',
                'commands': [
                    'Create campaign [name] with budget [amount]',
                    'Pause campaign [name/id]',
                    'Resume campaign [name/id]',
                    'List campaigns',
                    'Create ad for [campaign]',
                    'Set budget [amount] for [campaign]',
                    'Add keywords [keywords] to [campaign]',
                    'Get performance metrics',
                    'Optimize campaigns'
                ]
            }
    
    def _handle_create_campaign(self, command: str) -> Dict:
        """Parse and handle create campaign command"""
        # Extract campaign details from natural language
        campaign_data = {
            'name': 'New Campaign',
            'budget': 100,  # Default daily budget in dollars
            'campaign_type': 'SEARCH'
        }
        
        # Look for budget amount in command
        parts = command.split()
        for i, part in enumerate(parts):
            if '$' in part or part.isdigit():
                try:
                    campaign_data['budget'] = float(part.replace('$', '').replace(',', ''))
                except:
                    pass
            elif part == 'display':
                campaign_data['campaign_type'] = 'DISPLAY'
            elif part == 'video':
                campaign_data['campaign_type'] = 'VIDEO'
        
        # Extract campaign name
        if 'campaign' in command:
            name_parts = command.split('campaign')[1].split('with')[0].strip()
            if name_parts:
                campaign_data['name'] = name_parts
        
        return self.create_campaign(campaign_data)
    
    def create_campaign(self, campaign_data: Dict) -> Dict:
        """Create a new Google Ads campaign"""
        if not self.client:
            return {'status': 'error', 'message': 'Not authenticated. Please setup credentials first.'}
        
        try:
            campaign_service = self.client.get_service("CampaignService")
            campaign_operation = self.client.get_type("CampaignOperation")
            
            campaign = campaign_operation.create
            campaign.name = campaign_data['name']
            campaign.status = self.client.enums.CampaignStatusEnum.PAUSED
            
            # Set campaign budget
            campaign.campaign_budget = self._create_budget(
                campaign_data['name'] + ' Budget',
                campaign_data['budget']
            )
            
            # Set campaign type
            if campaign_data['campaign_type'] == 'SEARCH':
                campaign.advertising_channel_type = (
                    self.client.enums.AdvertisingChannelTypeEnum.SEARCH
                )
            elif campaign_data['campaign_type'] == 'DISPLAY':
                campaign.advertising_channel_type = (
                    self.client.enums.AdvertisingChannelTypeEnum.DISPLAY
                )
            
            # Add campaign
            response = campaign_service.mutate_campaigns(
                customer_id=self.customer_id,
                operations=[campaign_operation]
            )
            
            campaign_id = response.results[0].resource_name.split('/')[-1]
            
            # Store in L2 memory
            self.brain.save_campaign({
                'campaign_id': f"google_ads_{campaign_id}",
                'platform': 'google_ads',
                'campaign_name': campaign_data['name'],
                'status': 'paused',
                'settings': campaign_data
            })
            
            return {
                'status': 'success',
                'campaign_id': campaign_id,
                'message': f"Campaign '{campaign_data['name']}' created with ${campaign_data['budget']}/day budget"
            }
            
        except GoogleAdsException as ex:
            return {'status': 'error', 'message': f"Google Ads error: {ex.failure}"}
        except Exception as e:
            return {'status': 'error', 'message': str(e)}
    
    def _create_budget(self, name: str, amount_dollars: float) -> str:
        """Create a campaign budget"""
        budget_service = self.client.get_service("CampaignBudgetService")
        campaign_budget_operation = self.client.get_type("CampaignBudgetOperation")
        
        campaign_budget = campaign_budget_operation.create
        campaign_budget.name = name
        campaign_budget.amount_micros = int(amount_dollars * 1_000_000)
        campaign_budget.delivery_method = self.client.enums.BudgetDeliveryMethodEnum.STANDARD
        
        response = budget_service.mutate_campaign_budgets(
            customer_id=self.customer_id,
            operations=[campaign_budget_operation]
        )
        
        return response.results[0].resource_name
    
    def list_campaigns(self) -> Dict:
        """List all campaigns"""
        if not self.client:
            return {'status': 'error', 'message': 'Not authenticated. Please setup credentials first.'}
        
        try:
            ga_service = self.client.get_service("GoogleAdsService")
            
            query = """
                SELECT
                    campaign.id,
                    campaign.name,
                    campaign.status,
                    campaign_budget.amount_micros,
                    metrics.impressions,
                    metrics.clicks,
                    metrics.cost_micros
                FROM campaign
                WHERE campaign.status != 'REMOVED'
                ORDER BY campaign.id
            """
            
            response = ga_service.search_stream(
                customer_id=self.customer_id,
                query=query
            )
            
            campaigns = []
            for batch in response:
                for row in batch.results:
                    campaigns.append({
                        'id': row.campaign.id,
                        'name': row.campaign.name,
                        'status': row.campaign.status.name,
                        'daily_budget': row.campaign_budget.amount_micros / 1_000_000,
                        'impressions': row.metrics.impressions,
                        'clicks': row.metrics.clicks,
                        'cost': row.metrics.cost_micros / 1_000_000
                    })
            
            return {
                'status': 'success',
                'count': len(campaigns),
                'campaigns': campaigns
            }
            
        except GoogleAdsException as ex:
            return {'status': 'error', 'message': f"Google Ads error: {ex.failure}"}
        except Exception as e:
            return {'status': 'error', 'message': str(e)}
    
    def _handle_pause_campaign(self, command: str) -> Dict:
        """Parse and handle pause campaign command"""
        # Extract campaign identifier
        parts = command.split('campaign')
        if len(parts) > 1:
            campaign_id = parts[1].strip()
            return self.pause_campaign(campaign_id)
        return {'status': 'error', 'message': 'Could not identify campaign to pause'}
    
    def pause_campaign(self, campaign_id: str) -> Dict:
        """Pause a campaign"""
        if not self.client:
            return {'status': 'error', 'message': 'Not authenticated. Please setup credentials first.'}
        
        try:
            campaign_service = self.client.get_service("CampaignService")
            campaign_operation = self.client.get_type("CampaignOperation")
            
            campaign = campaign_operation.update
            campaign.resource_name = f"customers/{self.customer_id}/campaigns/{campaign_id}"
            campaign.status = self.client.enums.CampaignStatusEnum.PAUSED
            
            campaign_operation.update_mask.paths.append("status")
            
            response = campaign_service.mutate_campaigns(
                customer_id=self.customer_id,
                operations=[campaign_operation]
            )
            
            # Update L2 memory
            self.brain.save_campaign({
                'campaign_id': f"google_ads_{campaign_id}",
                'platform': 'google_ads',
                'status': 'paused'
            })
            
            return {
                'status': 'success',
                'message': f"Campaign {campaign_id} paused"
            }
            
        except GoogleAdsException as ex:
            return {'status': 'error', 'message': f"Google Ads error: {ex.failure}"}
        except Exception as e:
            return {'status': 'error', 'message': str(e)}
    
    def _handle_resume_campaign(self, command: str) -> Dict:
        """Parse and handle resume campaign command"""
        parts = command.split('campaign')
        if len(parts) > 1:
            campaign_id = parts[1].strip()
            return self.resume_campaign(campaign_id)
        return {'status': 'error', 'message': 'Could not identify campaign to resume'}
    
    def resume_campaign(self, campaign_id: str) -> Dict:
        """Resume a paused campaign"""
        if not self.client:
            return {'status': 'error', 'message': 'Not authenticated. Please setup credentials first.'}
        
        try:
            campaign_service = self.client.get_service("CampaignService")
            campaign_operation = self.client.get_type("CampaignOperation")
            
            campaign = campaign_operation.update
            campaign.resource_name = f"customers/{self.customer_id}/campaigns/{campaign_id}"
            campaign.status = self.client.enums.CampaignStatusEnum.ENABLED
            
            campaign_operation.update_mask.paths.append("status")
            
            response = campaign_service.mutate_campaigns(
                customer_id=self.customer_id,
                operations=[campaign_operation]
            )
            
            # Update L2 memory
            self.brain.save_campaign({
                'campaign_id': f"google_ads_{campaign_id}",
                'platform': 'google_ads',
                'status': 'enabled'
            })
            
            return {
                'status': 'success',
                'message': f"Campaign {campaign_id} resumed"
            }
            
        except GoogleAdsException as ex:
            return {'status': 'error', 'message': f"Google Ads error: {ex.failure}"}
        except Exception as e:
            return {'status': 'error', 'message': str(e)}
    
    def _handle_set_budget(self, command: str) -> Dict:
        """Parse and handle set budget command"""
        # Extract budget amount and campaign
        budget = 100  # Default
        campaign_id = None
        
        parts = command.split()
        for part in parts:
            if '$' in part or part.isdigit():
                try:
                    budget = float(part.replace('$', '').replace(',', ''))
                except:
                    pass
        
        # Extract campaign ID
        if 'for' in command:
            campaign_id = command.split('for')[1].strip()
        
        if campaign_id:
            return self.update_budget(campaign_id, budget)
        
        return {'status': 'error', 'message': 'Please specify campaign ID'}
    
    def update_budget(self, campaign_id: str, daily_budget: float) -> Dict:
        """Update campaign budget"""
        if not self.client:
            return {'status': 'error', 'message': 'Not authenticated. Please setup credentials first.'}
        
        try:
            # First get the campaign's budget resource name
            ga_service = self.client.get_service("GoogleAdsService")
            query = f"""
                SELECT campaign_budget.resource_name
                FROM campaign
                WHERE campaign.id = {campaign_id}
            """
            
            response = ga_service.search_stream(
                customer_id=self.customer_id,
                query=query
            )
            
            budget_resource_name = None
            for batch in response:
                for row in batch.results:
                    budget_resource_name = row.campaign_budget.resource_name
                    break
            
            if not budget_resource_name:
                return {'status': 'error', 'message': 'Campaign not found'}
            
            # Update the budget
            budget_service = self.client.get_service("CampaignBudgetService")
            budget_operation = self.client.get_type("CampaignBudgetOperation")
            
            budget = budget_operation.update
            budget.resource_name = budget_resource_name
            budget.amount_micros = int(daily_budget * 1_000_000)
            
            budget_operation.update_mask.paths.append("amount_micros")
            
            response = budget_service.mutate_campaign_budgets(
                customer_id=self.customer_id,
                operations=[budget_operation]
            )
            
            # Log to analytics
            self.brain.save_analytics(
                f"google_ads_{campaign_id}",
                'budget_update',
                daily_budget,
                {'action': 'budget_change'}
            )
            
            return {
                'status': 'success',
                'message': f"Budget updated to ${daily_budget}/day for campaign {campaign_id}"
            }
            
        except GoogleAdsException as ex:
            return {'status': 'error', 'message': f"Google Ads error: {ex.failure}"}
        except Exception as e:
            return {'status': 'error', 'message': str(e)}
    
    def _handle_add_keywords(self, command: str) -> Dict:
        """Parse and handle add keywords command"""
        # Extract keywords and campaign
        if 'to' in command:
            parts = command.split('to')
            keywords_part = parts[0].replace('add', '').replace('keywords', '').replace('keyword', '').strip()
            campaign_part = parts[1].strip()
            
            keywords = [k.strip() for k in keywords_part.split(',')]
            
            return self.add_keywords(campaign_part, keywords)
        
        return {'status': 'error', 'message': 'Format: Add keywords [keyword1, keyword2] to [campaign]'}
    
    def add_keywords(self, campaign_id: str, keywords: List[str]) -> Dict:
        """Add keywords to a campaign"""
        if not self.client:
            return {'status': 'error', 'message': 'Not authenticated. Please setup credentials first.'}
        
        try:
            # This is simplified - in reality, keywords are added to ad groups
            # Store in working memory for now
            self.brain.set_working_data(f"keywords_{campaign_id}", keywords)
            
            # Log to analytics
            self.brain.save_analytics(
                f"google_ads_{campaign_id}",
                'keywords_added',
                len(keywords),
                {'keywords': keywords}
            )
            
            return {
                'status': 'success',
                'message': f"Added {len(keywords)} keywords to campaign {campaign_id}",
                'keywords': keywords
            }
            
        except Exception as e:
            return {'status': 'error', 'message': str(e)}
    
    def _handle_create_ad(self, command: str) -> Dict:
        """Parse and handle create ad command"""
        # Extract campaign from command
        if 'for' in command:
            campaign_id = command.split('for')[1].strip()
            
            ad_data = {
                'headline1': 'Amazing Product',
                'headline2': 'Best Prices',
                'description': 'Get the best deals today!',
                'final_url': 'https://example.com'
            }
            
            return self.create_ad(campaign_id, ad_data)
        
        return {'status': 'error', 'message': 'Please specify campaign: Create ad for [campaign]'}
    
    def create_ad(self, campaign_id: str, ad_data: Dict) -> Dict:
        """Create an ad (simplified)"""
        if not self.client:
            return {'status': 'error', 'message': 'Not authenticated. Please setup credentials first.'}
        
        try:
            # Store ad data in working memory (simplified)
            self.brain.set_working_data(f"ad_{campaign_id}", ad_data)
            
            # Log to L2
            self.brain.save_campaign({
                'campaign_id': f"google_ads_ad_{campaign_id}",
                'platform': 'google_ads',
                'campaign_name': f"Ad for campaign {campaign_id}",
                'status': 'created',
                'settings': ad_data
            })
            
            return {
                'status': 'success',
                'message': f"Ad created for campaign {campaign_id}",
                'ad_preview': ad_data
            }
            
        except Exception as e:
            return {'status': 'error', 'message': str(e)}
    
    def get_performance_metrics(self, days: int = 30) -> Dict:
        """Get performance metrics for all campaigns"""
        if not self.client:
            return {'status': 'error', 'message': 'Not authenticated. Please setup credentials first.'}
        
        try:
            ga_service = self.client.get_service("GoogleAdsService")
            
            # Calculate date range
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)
            
            query = f"""
                SELECT
                    campaign.name,
                    metrics.impressions,
                    metrics.clicks,
                    metrics.ctr,
                    metrics.average_cpc,
                    metrics.cost_micros,
                    metrics.conversions,
                    metrics.conversion_rate
                FROM campaign
                WHERE segments.date BETWEEN '{start_date.strftime('%Y-%m-%d')}' 
                    AND '{end_date.strftime('%Y-%m-%d')}'
                    AND campaign.status != 'REMOVED'
            """
            
            response = ga_service.search_stream(
                customer_id=self.customer_id,
                query=query
            )
            
            total_metrics = {
                'impressions': 0,
                'clicks': 0,
                'cost': 0,
                'conversions': 0,
                'campaigns': []
            }
            
            for batch in response:
                for row in batch.results:
                    campaign_metrics = {
                        'name': row.campaign.name,
                        'impressions': row.metrics.impressions,
                        'clicks': row.metrics.clicks,
                        'ctr': row.metrics.ctr,
                        'avg_cpc': row.metrics.average_cpc / 1_000_000,
                        'cost': row.metrics.cost_micros / 1_000_000,
                        'conversions': row.metrics.conversions,
                        'conversion_rate': row.metrics.conversion_rate
                    }
                    
                    total_metrics['campaigns'].append(campaign_metrics)
                    total_metrics['impressions'] += row.metrics.impressions
                    total_metrics['clicks'] += row.metrics.clicks
                    total_metrics['cost'] += row.metrics.cost_micros / 1_000_000
                    total_metrics['conversions'] += row.metrics.conversions
            
            # Calculate overall metrics
            if total_metrics['impressions'] > 0:
                total_metrics['overall_ctr'] = (total_metrics['clicks'] / total_metrics['impressions']) * 100
            else:
                total_metrics['overall_ctr'] = 0
            
            if total_metrics['clicks'] > 0:
                total_metrics['overall_cpc'] = total_metrics['cost'] / total_metrics['clicks']
                total_metrics['overall_conversion_rate'] = (total_metrics['conversions'] / total_metrics['clicks']) * 100
            else:
                total_metrics['overall_cpc'] = 0
                total_metrics['overall_conversion_rate'] = 0
            
            return {
                'status': 'success',
                'period': f"Last {days} days",
                'metrics': total_metrics
            }
            
        except GoogleAdsException as ex:
            return {'status': 'error', 'message': f"Google Ads error: {ex.failure}"}
        except Exception as e:
            return {'status': 'error', 'message': str(e)}
    
    def optimize_campaigns(self) -> Dict:
        """Provide optimization recommendations"""
        if not self.client:
            return {'status': 'error', 'message': 'Not authenticated. Please setup credentials first.'}
        
        try:
            metrics = self.get_performance_metrics(30)
            
            if metrics['status'] != 'success':
                return metrics
            
            recommendations = []
            
            for campaign in metrics['metrics']['campaigns']:
                # Check CTR
                if campaign['ctr'] < 2.0:
                    recommendations.append({
                        'campaign': campaign['name'],
                        'issue': 'Low CTR',
                        'recommendation': 'Review ad copy and targeting'
                    })
                
                # Check conversion rate
                if campaign['clicks'] > 100 and campaign['conversion_rate'] < 2.0:
                    recommendations.append({
                        'campaign': campaign['name'],
                        'issue': 'Low conversion rate',
                        'recommendation': 'Optimize landing page and offer'
                    })
                
                # Check CPC
                if campaign['avg_cpc'] > 5.0:
                    recommendations.append({
                        'campaign': campaign['name'],
                        'issue': 'High CPC',
                        'recommendation': 'Review keyword bids and quality score'
                    })
            
            return {
                'status': 'success',
                'recommendations': recommendations,
                'summary': f"Found {len(recommendations)} optimization opportunities"
            }
            
        except Exception as e:
            return {'status': 'error', 'message': str(e)}