"""
Platform-agnostic business logic engine
Contains pricing, customer profiling, and revenue optimization logic
"""

from enum import Enum
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta
import json

class MarketSegment(Enum):
    """Target market segments with revenue potential"""
    LOCAL_BUSINESS = "local_business"  # $50B opportunity
    ENTERPRISE_REPLACEMENT = "enterprise"  # $500B opportunity  
    CONSUMER_EXPERTISE = "consumer"  # $2T opportunity
    HEALTHCARE = "healthcare"  # $100B opportunity
    REAL_ESTATE = "real_estate"  # $30B opportunity
    LEGAL = "legal"  # $20B opportunity
    FINANCIAL = "financial"  # $40B opportunity
    EDUCATION = "education"  # $25B opportunity
    HOSPITALITY = "hospitality"  # $15B opportunity
    RETAIL = "retail"  # $35B opportunity

@dataclass
class CustomerProfile:
    """Platform-agnostic customer profile"""
    segment: MarketSegment
    company_size: str  # "1-10", "11-50", "51-200", "201-1000", "1000+"
    current_pain_cost: float  # Annual cost of problem we solve
    decision_maker: str  # Title of decision maker
    sales_cycle_days: int
    implementation_complexity: str  # "simple", "moderate", "complex"
    churn_risk: float  # 0-1 probability
    lifetime_value: float  # Projected LTV
    acquisition_cost: float  # CAC
    profit_margin: float
    expansion_potential: float  # Revenue expansion multiplier
    
    # Additional profiling
    industry_specific_needs: List[str] = field(default_factory=list)
    compliance_requirements: List[str] = field(default_factory=list)
    integration_requirements: List[str] = field(default_factory=list)
    success_metrics: Dict[str, float] = field(default_factory=dict)
    
    def calculate_unit_economics(self) -> Dict:
        """Calculate unit economics for this profile"""
        ltv_cac_ratio = self.lifetime_value / (self.acquisition_cost + 1)
        payback_months = self.acquisition_cost / (self.lifetime_value / 36) if self.lifetime_value > 0 else float('inf')
        gross_margin = self.profit_margin * 100
        
        return {
            "ltv": self.lifetime_value,
            "cac": self.acquisition_cost,
            "ltv_cac_ratio": ltv_cac_ratio,
            "payback_months": payback_months,
            "gross_margin_percent": gross_margin,
            "profit_per_customer": self.lifetime_value * self.profit_margin,
            "profitable": ltv_cac_ratio > 3.0,
            "expansion_revenue": self.lifetime_value * self.expansion_potential,
            "total_addressable_value": self.lifetime_value * (1 + self.expansion_potential)
        }
    
    def get_risk_score(self) -> float:
        """Calculate customer risk score (0-100, lower is better)"""
        risk_score = 0.0
        
        # Churn risk component (40% weight)
        risk_score += self.churn_risk * 40
        
        # Implementation complexity (30% weight)
        complexity_scores = {"simple": 0, "moderate": 15, "complex": 30}
        risk_score += complexity_scores.get(self.implementation_complexity, 30)
        
        # Sales cycle length (20% weight)
        if self.sales_cycle_days > 90:
            risk_score += 20
        elif self.sales_cycle_days > 45:
            risk_score += 10
        else:
            risk_score += 5
            
        # Profitability (10% weight)
        if self.profit_margin < 0.2:
            risk_score += 10
        elif self.profit_margin < 0.4:
            risk_score += 5
            
        return min(risk_score, 100)

class PricingStrategy:
    """Platform-agnostic pricing strategy engine"""
    
    def __init__(self):
        self.base_tiers = self._initialize_tiers()
        self.value_multipliers = self._initialize_multipliers()
        self.discount_rules = self._initialize_discount_rules()
        
    def _initialize_tiers(self) -> Dict:
        """Initialize pricing tiers"""
        return {
            "starter": {
                "base_monthly": 997,
                "included_value": 1000,  # Platform-agnostic value units
                "overage_rate": 1.5,
                "features": ["basic_agent", "standard_voice", "email_support"],
                "target_segments": [MarketSegment.LOCAL_BUSINESS],
                "min_company_size": "1-10"
            },
            "professional": {
                "base_monthly": 2997,
                "included_value": 5000,
                "overage_rate": 1.0,
                "features": ["custom_agent", "premium_voice", "priority_support", "analytics", "integrations"],
                "target_segments": [MarketSegment.HEALTHCARE, MarketSegment.REAL_ESTATE],
                "min_company_size": "11-50"
            },
            "enterprise": {
                "base_monthly": 9997,
                "included_value": 20000,
                "overage_rate": 0.75,
                "features": ["unlimited_agents", "custom_integration", "dedicated_support", "sla", "compliance"],
                "target_segments": [MarketSegment.ENTERPRISE_REPLACEMENT, MarketSegment.FINANCIAL],
                "min_company_size": "51-200"
            },
            "scale": {
                "base_monthly": 29997,
                "included_value": 100000,
                "overage_rate": 0.50,
                "features": ["white_label", "api_access", "custom_development", "account_team", "priority_roadmap"],
                "target_segments": [MarketSegment.FINANCIAL, MarketSegment.ENTERPRISE_REPLACEMENT],
                "min_company_size": "201-1000"
            },
            "custom": {
                "base_monthly": None,  # Negotiated
                "included_value": None,
                "overage_rate": None,
                "features": ["everything", "custom_sla", "dedicated_infrastructure"],
                "target_segments": [MarketSegment.ENTERPRISE_REPLACEMENT],
                "min_company_size": "1000+"
            }
        }
    
    def _initialize_multipliers(self) -> Dict:
        """Initialize value-based pricing multipliers"""
        return {
            "saves_employee_cost": 3.0,  # Price at 3x of cost saved
            "revenue_generating": 2.5,   # Price at 2.5x of revenue generated
            "compliance_critical": 4.0,  # Price at 4x of compliance value
            "customer_experience": 2.0,  # Price at 2x of CX improvement value
            "operational_efficiency": 2.2,  # Price at 2.2x of efficiency gains
            "competitive_advantage": 3.5  # Price at 3.5x of competitive value
        }
    
    def _initialize_discount_rules(self) -> List[Dict]:
        """Initialize discount rules"""
        return [
            {
                "name": "volume_discount",
                "condition": lambda profile: profile.company_size in ["201-1000", "1000+"],
                "discount_percent": 20
            },
            {
                "name": "annual_prepay",
                "condition": lambda profile: True,  # Always available
                "discount_percent": 15
            },
            {
                "name": "nonprofit_discount",
                "condition": lambda profile: "nonprofit" in profile.industry_specific_needs,
                "discount_percent": 30
            },
            {
                "name": "startup_discount",
                "condition": lambda profile: profile.company_size == "1-10" and profile.segment == MarketSegment.LOCAL_BUSINESS,
                "discount_percent": 25
            },
            {
                "name": "partner_referral",
                "condition": lambda profile: "partner_referred" in profile.success_metrics,
                "discount_percent": 10
            }
        ]
    
    def calculate_optimal_price(self, 
                               customer: CustomerProfile,
                               value_created: float,
                               competitive_prices: List[float] = None) -> Dict:
        """Calculate optimal pricing for customer"""
        
        # Select base tier
        tier_name = self._select_tier(customer)
        tier = self.base_tiers[tier_name]
        
        # Calculate value-based price
        value_multiplier = self._get_value_multiplier(customer)
        value_based_monthly = (value_created / 12) * value_multiplier
        
        # Use higher of tier base or value-based
        if tier["base_monthly"]:
            base_monthly = max(tier["base_monthly"], value_based_monthly)
        else:
            base_monthly = value_based_monthly  # Custom tier
        
        # Apply applicable discounts
        total_discount = 0
        applied_discounts = []
        for rule in self.discount_rules:
            if rule["condition"](customer):
                total_discount += rule["discount_percent"]
                applied_discounts.append(rule["name"])
        
        # Cap total discount at 40%
        total_discount = min(total_discount, 40)
        
        # Calculate final price
        discounted_monthly = base_monthly * (1 - total_discount / 100)
        
        # Competitive positioning
        if competitive_prices:
            avg_competitor = sum(competitive_prices) / len(competitive_prices)
            price_position = (discounted_monthly - avg_competitor) / avg_competitor * 100
        else:
            price_position = 0
        
        # Calculate customer ROI
        monthly_value = value_created / 12
        customer_roi = ((monthly_value - discounted_monthly) / discounted_monthly * 100) if discounted_monthly > 0 else float('inf')
        
        # Build pricing package
        return {
            "tier": tier_name,
            "base_monthly": base_monthly,
            "discounted_monthly": discounted_monthly,
            "annual_price": discounted_monthly * 12,
            "annual_with_prepay": discounted_monthly * 12 * 0.85,  # Additional 15% for annual
            "applied_discounts": applied_discounts,
            "total_discount_percent": total_discount,
            "included_value": tier["included_value"],
            "overage_rate": tier["overage_rate"],
            "features": tier["features"],
            "customer_roi_percent": customer_roi,
            "payback_period_days": int((discounted_monthly / monthly_value * 30)) if monthly_value > 0 else None,
            "value_capture_ratio": discounted_monthly / monthly_value if monthly_value > 0 else 0,
            "competitive_position_percent": price_position,
            "recommendation": self._get_pricing_recommendation(customer_roi, price_position)
        }
    
    def _select_tier(self, customer: CustomerProfile) -> str:
        """Select appropriate tier for customer"""
        
        # Custom tier for very large enterprises
        if customer.company_size == "1000+":
            return "custom"
        
        # Match by segment and size
        for tier_name, tier_config in self.base_tiers.items():
            if tier_name == "custom":
                continue
                
            if (customer.segment in tier_config["target_segments"] and
                self._company_size_matches(customer.company_size, tier_config["min_company_size"])):
                return tier_name
        
        # Default to starter
        return "starter"
    
    def _company_size_matches(self, actual: str, minimum: str) -> bool:
        """Check if company size meets minimum"""
        size_order = ["1-10", "11-50", "51-200", "201-1000", "1000+"]
        
        try:
            actual_idx = size_order.index(actual)
            min_idx = size_order.index(minimum)
            return actual_idx >= min_idx
        except ValueError:
            return False
    
    def _get_value_multiplier(self, customer: CustomerProfile) -> float:
        """Get appropriate value multiplier"""
        
        # High-value scenarios
        if customer.current_pain_cost > 100000:
            return self.value_multipliers["saves_employee_cost"]
        
        # Compliance-critical industries
        if customer.segment in [MarketSegment.HEALTHCARE, MarketSegment.FINANCIAL, MarketSegment.LEGAL]:
            if "compliance" in customer.compliance_requirements:
                return self.value_multipliers["compliance_critical"]
        
        # Revenue-generating use cases
        if customer.segment in [MarketSegment.REAL_ESTATE, MarketSegment.RETAIL]:
            return self.value_multipliers["revenue_generating"]
        
        # Default to customer experience
        return self.value_multipliers["customer_experience"]
    
    def _get_pricing_recommendation(self, roi: float, competitive_position: float) -> str:
        """Generate pricing recommendation"""
        
        if roi > 300 and competitive_position < 20:
            return "HIGHLY RECOMMENDED - Exceptional ROI with competitive pricing"
        elif roi > 200:
            return "RECOMMENDED - Strong ROI justifies investment"
        elif roi > 100:
            return "VIABLE - Positive ROI with reasonable payback"
        elif roi > 50:
            return "CONSIDER - Modest ROI, negotiate if possible"
        else:
            return "REVIEW - Low ROI, consider value adds or different tier"

class RevenueOptimizer:
    """Optimizes revenue across customer portfolio"""
    
    def __init__(self):
        self.pricing_strategy = PricingStrategy()
        
    def optimize_customer_mix(self, 
                             opportunities: List[CustomerProfile],
                             capacity_limit: int = 100) -> Dict:
        """Optimize customer mix for maximum revenue"""
        
        # Score each opportunity
        scored_opportunities = []
        for opp in opportunities:
            score = self._score_opportunity(opp)
            scored_opportunities.append((score, opp))
        
        # Sort by score (descending)
        scored_opportunities.sort(key=lambda x: x[0], reverse=True)
        
        # Select top opportunities within capacity
        selected = []
        total_capacity_used = 0
        
        for score, opp in scored_opportunities:
            # Estimate capacity consumption (simplified)
            capacity_needed = self._estimate_capacity(opp)
            
            if total_capacity_used + capacity_needed <= capacity_limit:
                selected.append(opp)
                total_capacity_used += capacity_needed
        
        # Calculate portfolio metrics
        total_revenue = sum(opp.lifetime_value for opp in selected)
        total_cac = sum(opp.acquisition_cost for opp in selected)
        avg_ltv_cac = total_revenue / total_cac if total_cac > 0 else 0
        
        segment_mix = {}
        for opp in selected:
            segment = opp.segment.value
            segment_mix[segment] = segment_mix.get(segment, 0) + 1
        
        return {
            "selected_customers": len(selected),
            "total_revenue": total_revenue,
            "total_cac": total_cac,
            "portfolio_ltv_cac_ratio": avg_ltv_cac,
            "capacity_utilization": total_capacity_used / capacity_limit * 100,
            "segment_mix": segment_mix,
            "rejected_opportunities": len(opportunities) - len(selected)
        }
    
    def _score_opportunity(self, customer: CustomerProfile) -> float:
        """Score opportunity for prioritization"""
        
        economics = customer.calculate_unit_economics()
        
        # Weighted scoring
        score = 0
        
        # LTV/CAC ratio (40% weight)
        score += min(economics["ltv_cac_ratio"] * 10, 40)
        
        # Profit margin (30% weight)
        score += customer.profit_margin * 30
        
        # Quick payback (20% weight)
        if economics["payback_months"] < 3:
            score += 20
        elif economics["payback_months"] < 6:
            score += 15
        elif economics["payback_months"] < 12:
            score += 10
        else:
            score += 5
        
        # Low risk (10% weight)
        risk_score = customer.get_risk_score()
        score += (100 - risk_score) / 10
        
        return score
    
    def _estimate_capacity(self, customer: CustomerProfile) -> int:
        """Estimate capacity consumption"""
        
        # Simple model based on company size
        size_capacity = {
            "1-10": 1,
            "11-50": 3,
            "51-200": 5,
            "201-1000": 10,
            "1000+": 20
        }
        
        base_capacity = size_capacity.get(customer.company_size, 5)
        
        # Adjust for complexity
        if customer.implementation_complexity == "complex":
            base_capacity *= 2
        elif customer.implementation_complexity == "moderate":
            base_capacity *= 1.5
            
        return int(base_capacity)