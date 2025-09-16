#!/usr/bin/env python3
"""
REBECCA'S WORKFLOW INTEGRATION
Bridging manual expertise with automated deployment

This captures Rebecca's proven process while we build automation
"""

from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from dataclasses import dataclass
import json
import asyncpg
from enum import Enum

class ClientStage(Enum):
    """Rebecca's client onboarding stages"""
    INTAKE = "intake"
    PAYMENT_PENDING = "payment_pending"
    INTERVIEW_SCHEDULED = "interview_scheduled"
    INTERVIEW_COMPLETED = "interview_completed"
    RESEARCH_PHASE = "research_phase"
    KNOWLEDGE_BUILDING = "knowledge_building"
    TESTING = "testing"
    LIVE = "live"

@dataclass
class ClientWorkflow:
    """Track where each client is in Rebecca's process"""
    client_id: str
    stage: ClientStage
    intake_form: Dict[str, Any]
    interview_notes: Optional[str] = None
    research_data: Optional[Dict[str, Any]] = None
    crawl_configs: List[Dict[str, Any]] = None
    testing_feedback: List[str] = None
    go_live_date: Optional[datetime] = None

class RebeccaWorkflowEngine:
    """
    Supports Rebecca's manual process with structure and tracking
    """
    
    def __init__(self, db_pool: asyncpg.Pool):
        self.db = db_pool
    
    async def create_intake(self, intake_data: Dict[str, Any]) -> str:
        """
        Store intake form data
        Rebecca can paste from her current form
        """
        client_id = str(uuid.uuid4())
        
        async with self.db.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO client_workflows 
                (client_id, stage, intake_data, created_at)
                VALUES ($1, $2, $3, $4)
                """,
                client_id, ClientStage.INTAKE.value,
                json.dumps(intake_data), datetime.utcnow()
            )
            
            # Create basic client record
            await conn.execute(
                """
                INSERT INTO clients 
                (id, team_id, name, domain, widget_id, active)
                VALUES ($1, $2, $3, $4, $5, false)
                """,
                client_id, 
                intake_data.get('team_id'),
                intake_data.get('business_name'),
                intake_data.get('website'),
                f"widget_{secrets.token_urlsafe(8)}"
            )
        
        return client_id
    
    async def save_interview_transcript(
        self, 
        client_id: str, 
        transcript: str,
        key_points: List[str],
        follow_ups: List[str]
    ):
        """
        After