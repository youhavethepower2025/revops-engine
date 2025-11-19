"""
Platform-agnostic sales automation engine
Handles lead scoring, nurturing, and conversion optimization
"""

from enum import Enum
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any, Callable
from datetime import datetime, timedelta

class LeadSource(Enum):
    """Lead acquisition sources"""
    INBOUND_WEBSITE = "inbound_website"
    OUTBOUND_COLD = "outbound_cold"
    PARTNER_REFERRAL = "partner_referral"
    CONTENT_MARKETING = "content_marketing"
    PAID_ADVERTISING = "paid_advertising"
    EVENT_NETWORKING = "event_networking"
    SOCIAL_MEDIA = "social_media"
    CUSTOMER_REFERRAL = "customer_referral"
    PRODUCT_TRIAL = "product_trial"

class LeadStage(Enum):
    """Sales pipeline stages"""
    RAW_LEAD = "raw_lead"
    MARKETING_QUALIFIED = "mql"
    SALES_QUALIFIED = "sql"
    OPPORTUNITY = "opportunity"
    PROPOSAL = "proposal"
    NEGOTIATION = "negotiation"
    CLOSED_WON = "closed_won"
    CLOSED_LOST = "closed_lost"
    NURTURE = "nurture"

@dataclass
class Lead:
    """Platform-agnostic lead representation"""
    lead_id: str
    source: LeadSource
    stage: LeadStage = LeadStage.RAW_LEAD
    
    # Contact information
    company_name: Optional[str] = None
    contact_name: Optional[str] = None
    title: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    
    # Qualification data
    company_size: Optional[str] = None
    industry: Optional[str] = None
    budget_range: Optional[str] = None
    timeline: Optional[str] = None
    pain_points: List[str] = field(default_factory=list)
    
    # Engagement metrics
    engagement_score: float = 0.0
    interactions: List[Dict] = field(default_factory=list)
    last_contact: Optional[datetime] = None
    
    # Scoring
    lead_score: float = 0.0
    conversion_probability: float = 0.0
    priority: str = "medium"  # low, medium, high, urgent
    
    # Sales data
    assigned_to: Optional[str] = None
    next_action: Optional[str] = None
    next_action_date: Optional[datetime] = None
    
    # Metadata
    created_date: datetime = field(default_factory=datetime.now)
    updated_date: datetime = field(default_factory=datetime.now)
    tags: List[str] = field(default_factory=list)
    notes: List[str] = field(default_factory=list)

class LeadScoringEngine:
    """Intelligent lead scoring system"""
    
    def __init__(self):
        self.scoring_criteria = self._initialize_criteria()
        self.behavioral_signals = self._initialize_signals()
        
    def _initialize_criteria(self) -> Dict:
        """Initialize scoring criteria"""
        return {
            "demographic": {
                "company_size": {
                    "1000+": 25,
                    "201-1000": 20,
                    "51-200": 15,
                    "11-50": 10,
                    "1-10": 5
                },
                "title_authority": {
                    "c_level": ["ceo", "cto", "cfo", "coo", "cmo"],
                    "vp_level": ["vp", "vice president"],
                    "director_level": ["director"],
                    "manager_level": ["manager"],
                    "other": []
                },
                "title_scores": {
                    "c_level": 25,
                    "vp_level": 20,
                    "director_level": 15,
                    "manager_level": 10,
                    "other": 5
                }
            },
            "behavioral": {
                "website_visits": 2,  # Points per visit
                "content_downloads": 5,  # Points per download
                "demo_request": 20,
                "pricing_page_view": 15,
                "email_open": 1,
                "email_click": 3,
                "meeting_scheduled": 25,
                "proposal_reviewed": 30
            },
            "fit": {
                "budget_match": {
                    "exact": 20,
                    "above": 15,
                    "slightly_below": 10,
                    "significantly_below": 0
                },
                "timeline": {
                    "immediate": 20,
                    "this_quarter": 15,
                    "this_year": 10,
                    "next_year": 5,
                    "no_timeline": 0
                },
                "pain_severity": {
                    "critical": 25,
                    "high": 20,
                    "medium": 10,
                    "low": 5,
                    "none": 0
                }
            },
            "negative_signals": {
                "competitor_mentioned": -10,
                "budget_concerns": -15,
                "no_response_days": -1,  # Per day
                "unsubscribed": -50,
                "wrong_industry": -20
            }
        }
    
    def _initialize_signals(self) -> Dict:
        """Initialize behavioral signal patterns"""
        return {
            "high_intent": [
                "viewed_pricing",
                "downloaded_case_study",
                "attended_webinar",
                "requested_demo",
                "asked_technical_questions"
            ],
            "medium_intent": [
                "subscribed_newsletter",
                "followed_social_media",
                "viewed_features",
                "downloaded_whitepaper"
            ],
            "low_intent": [
                "single_page_visit",
                "bounced_quickly",
                "no_engagement"
            ]
        }
    
    def score_lead(self, lead: Lead) -> float:
        """Calculate comprehensive lead score"""
        
        score = 0
        
        # Demographic scoring
        score += self._score_demographics(lead)
        
        # Behavioral scoring
        score += self._score_behavior(lead)
        
        # Fit scoring
        score += self._score_fit(lead)
        
        # Apply negative signals
        score += self._apply_negative_signals(lead)
        
        # Normalize to 0-100
        normalized_score = max(0, min(100, score))
        
        # Update lead
        lead.lead_score = normalized_score
        lead.priority = self._determine_priority(normalized_score)
        lead.conversion_probability = self._calculate_conversion_probability(normalized_score, lead)
        
        return normalized_score
    
    def _score_demographics(self, lead: Lead) -> float:
        """Score based on demographic data"""
        score = 0
        
        # Company size
        if lead.company_size:
            size_scores = self.scoring_criteria["demographic"]["company_size"]
            score += size_scores.get(lead.company_size, 0)
        
        # Title authority
        if lead.title:
            title_lower = lead.title.lower()
            title_criteria = self.scoring_criteria["demographic"]["title_authority"]
            title_scores = self.scoring_criteria["demographic"]["title_scores"]
            
            for level, keywords in title_criteria.items():
                if any(keyword in title_lower for keyword in keywords):
                    score += title_scores[level]
                    break
        
        return score
    
    def _score_behavior(self, lead: Lead) -> float:
        """Score based on behavioral data"""
        score = 0
        
        behavioral_scores = self.scoring_criteria["behavioral"]
        
        # Count interactions
        for interaction in lead.interactions:
            action = interaction.get("action")
            if action in behavioral_scores:
                score += behavioral_scores[action]
        
        # Engagement recency bonus
        if lead.last_contact:
            days_since_contact = (datetime.now() - lead.last_contact).days
            if days_since_contact < 3:
                score += 10
            elif days_since_contact < 7:
                score += 5
            elif days_since_contact < 14:
                score += 2
        
        return score
    
    def _score_fit(self, lead: Lead) -> float:
        """Score based on solution fit"""
        score = 0
        
        fit_criteria = self.scoring_criteria["fit"]
        
        # Budget fit
        if lead.budget_range:
            # Simplified budget matching
            score += fit_criteria["budget_match"]["exact"]
        
        # Timeline fit
        if lead.timeline:
            timeline_scores = fit_criteria["timeline"]
            score += timeline_scores.get(lead.timeline, 0)
        
        # Pain point severity
        if lead.pain_points:
            # More pain points = higher severity
            if len(lead.pain_points) >= 3:
                score += fit_criteria["pain_severity"]["critical"]
            elif len(lead.pain_points) >= 2:
                score += fit_criteria["pain_severity"]["high"]
            elif len(lead.pain_points) >= 1:
                score += fit_criteria["pain_severity"]["medium"]
        
        return score
    
    def _apply_negative_signals(self, lead: Lead) -> float:
        """Apply negative scoring signals"""
        score = 0
        
        negative_signals = self.scoring_criteria["negative_signals"]
        
        # Check for negative tags
        for tag in lead.tags:
            if tag in negative_signals:
                score += negative_signals[tag]
        
        # Days without response
        if lead.last_contact:
            days_silent = (datetime.now() - lead.last_contact).days
            if days_silent > 7:
                score += negative_signals["no_response_days"] * min(days_silent - 7, 30)
        
        return score
    
    def _determine_priority(self, score: float) -> str:
        """Determine lead priority based on score"""
        if score >= 80:
            return "urgent"
        elif score >= 60:
            return "high"
        elif score >= 40:
            return "medium"
        else:
            return "low"
    
    def _calculate_conversion_probability(self, score: float, lead: Lead) -> float:
        """Calculate probability of conversion"""
        
        # Base probability from score
        base_prob = score / 100 * 0.5  # Max 50% from score alone
        
        # Adjust based on source
        source_multipliers = {
            LeadSource.CUSTOMER_REFERRAL: 1.5,
            LeadSource.PARTNER_REFERRAL: 1.3,
            LeadSource.PRODUCT_TRIAL: 1.2,
            LeadSource.INBOUND_WEBSITE: 1.1,
            LeadSource.CONTENT_MARKETING: 1.0,
            LeadSource.EVENT_NETWORKING: 0.9,
            LeadSource.PAID_ADVERTISING: 0.8,
            LeadSource.OUTBOUND_COLD: 0.7,
            LeadSource.SOCIAL_MEDIA: 0.6
        }
        
        source_mult = source_multipliers.get(lead.source, 1.0)
        adjusted_prob = base_prob * source_mult
        
        # Adjust based on stage
        if lead.stage in [LeadStage.PROPOSAL, LeadStage.NEGOTIATION]:
            adjusted_prob *= 1.5
        elif lead.stage == LeadStage.OPPORTUNITY:
            adjusted_prob *= 1.2
        
        return min(adjusted_prob, 0.95)  # Cap at 95%

class SalesAutomationWorkflow:
    """Automated sales workflow engine"""
    
    def __init__(self):
        self.scoring_engine = LeadScoringEngine()
        self.nurture_campaigns = self._initialize_campaigns()
        self.automation_rules = self._initialize_rules()
        
    def _initialize_campaigns(self) -> Dict:
        """Initialize nurture campaigns"""
        return {
            "education": {
                "target_score_range": (20, 40),
                "sequence": [
                    {"day": 0, "action": "send_welcome_email"},
                    {"day": 3, "action": "send_educational_content"},
                    {"day": 7, "action": "send_case_study"},
                    {"day": 14, "action": "send_webinar_invite"},
                    {"day": 21, "action": "send_roi_calculator"}
                ]
            },
            "activation": {
                "target_score_range": (40, 60),
                "sequence": [
                    {"day": 0, "action": "send_demo_offer"},
                    {"day": 2, "action": "call_attempt"},
                    {"day": 5, "action": "send_testimonials"},
                    {"day": 7, "action": "send_limited_time_offer"},
                    {"day": 10, "action": "executive_outreach"}
                ]
            },
            "conversion": {
                "target_score_range": (60, 100),
                "sequence": [
                    {"day": 0, "action": "schedule_demo"},
                    {"day": 1, "action": "send_prep_materials"},
                    {"day": 3, "action": "conduct_demo"},
                    {"day": 4, "action": "send_proposal"},
                    {"day": 7, "action": "follow_up_call"}
                ]
            },
            "re_engagement": {
                "target_score_range": (0, 20),
                "sequence": [
                    {"day": 0, "action": "send_re_engagement_email"},
                    {"day": 30, "action": "send_product_updates"},
                    {"day": 60, "action": "send_special_offer"},
                    {"day": 90, "action": "last_chance_email"}
                ]
            }
        }
    
    def _initialize_rules(self) -> List[Dict]:
        """Initialize automation rules"""
        return [
            {
                "name": "high_value_alert",
                "condition": lambda l: l.lead_score >= 80 and l.company_size in ["201-1000", "1000+"],
                "action": "notify_sales_manager"
            },
            {
                "name": "hot_lead_assignment",
                "condition": lambda l: l.lead_score >= 70 and l.timeline == "immediate",
                "action": "assign_to_senior_rep"
            },
            {
                "name": "demo_request_fast_track",
                "condition": lambda l: "demo_request" in [i.get("action") for i in l.interactions],
                "action": "schedule_demo_within_24h"
            },
            {
                "name": "stale_lead_reactivation",
                "condition": lambda l: l.last_contact and (datetime.now() - l.last_contact).days > 30,
                "action": "move_to_re_engagement"
            },
            {
                "name": "competitor_alert",
                "condition": lambda l: "competitor" in ' '.join(l.tags).lower(),
                "action": "competitive_battlecard"
            }
        ]
    
    def process_lead(self, lead: Lead) -> Dict:
        """Process lead through automation workflow"""
        
        # Score the lead
        score = self.scoring_engine.score_lead(lead)
        
        # Determine appropriate campaign
        campaign = self._select_campaign(lead)
        
        # Apply automation rules
        triggered_rules = self._apply_rules(lead)
        
        # Generate next actions
        next_actions = self._generate_next_actions(lead, campaign, triggered_rules)
        
        # Update lead stage if needed
        new_stage = self._determine_stage(lead)
        if new_stage != lead.stage:
            lead.stage = new_stage
            lead.updated_date = datetime.now()
        
        return {
            "lead_id": lead.lead_id,
            "score": score,
            "priority": lead.priority,
            "conversion_probability": lead.conversion_probability,
            "assigned_campaign": campaign,
            "triggered_rules": triggered_rules,
            "next_actions": next_actions,
            "stage": lead.stage.value,
            "recommended_owner": self._recommend_owner(lead)
        }
    
    def _select_campaign(self, lead: Lead) -> Optional[str]:
        """Select appropriate nurture campaign"""
        
        for campaign_name, campaign_config in self.nurture_campaigns.items():
            min_score, max_score = campaign_config["target_score_range"]
            if min_score <= lead.lead_score <= max_score:
                return campaign_name
        
        return None
    
    def _apply_rules(self, lead: Lead) -> List[str]:
        """Apply automation rules and return triggered actions"""
        
        triggered = []
        
        for rule in self.automation_rules:
            if rule["condition"](lead):
                triggered.append(rule["action"])
        
        return triggered
    
    def _generate_next_actions(self, 
                              lead: Lead,
                              campaign: Optional[str],
                              triggered_rules: List[str]) -> List[Dict]:
        """Generate next action recommendations"""
        
        actions = []
        
        # Add campaign actions
        if campaign:
            campaign_config = self.nurture_campaigns[campaign]
            # Find next action in sequence
            for step in campaign_config["sequence"]:
                action_date = lead.created_date + timedelta(days=step["day"])
                if action_date > datetime.now():
                    actions.append({
                        "action": step["action"],
                        "scheduled_date": action_date.isoformat(),
                        "campaign": campaign
                    })
                    break
        
        # Add rule-triggered actions
        for rule_action in triggered_rules:
            actions.append({
                "action": rule_action,
                "scheduled_date": datetime.now().isoformat(),
                "type": "immediate"
            })
        
        # Add stage-specific actions
        if lead.stage == LeadStage.SALES_QUALIFIED:
            actions.append({
                "action": "schedule_discovery_call",
                "scheduled_date": (datetime.now() + timedelta(days=1)).isoformat(),
                "type": "stage_based"
            })
        elif lead.stage == LeadStage.PROPOSAL:
            actions.append({
                "action": "send_roi_analysis",
                "scheduled_date": (datetime.now() + timedelta(days=2)).isoformat(),
                "type": "stage_based"
            })
        
        return actions
    
    def _determine_stage(self, lead: Lead) -> LeadStage:
        """Determine appropriate stage based on lead data"""
        
        # Check for stage progression triggers
        if lead.lead_score >= 70 and lead.budget_range and lead.timeline:
            return LeadStage.SALES_QUALIFIED
        elif lead.lead_score >= 50:
            return LeadStage.MARKETING_QUALIFIED
        elif lead.lead_score < 20 and lead.last_contact:
            if (datetime.now() - lead.last_contact).days > 60:
                return LeadStage.NURTURE
        
        # Check for specific interaction-based stages
        interactions = [i.get("action") for i in lead.interactions]
        if "proposal_sent" in interactions:
            return LeadStage.PROPOSAL
        elif "demo_completed" in interactions:
            return LeadStage.OPPORTUNITY
        
        return lead.stage
    
    def _recommend_owner(self, lead: Lead) -> str:
        """Recommend sales rep assignment"""
        
        # High-value leads to senior reps
        if lead.priority == "urgent":
            return "senior_sales_rep"
        elif lead.priority == "high":
            return "experienced_rep"
        elif lead.priority == "medium":
            return "standard_rep"
        else:
            return "junior_rep_or_automation"