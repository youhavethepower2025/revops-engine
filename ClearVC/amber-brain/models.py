"""
Database Models for Amber Brain
"""

from sqlalchemy import create_engine, Column, String, Text, DateTime, Float, JSON, Enum as SQLEnum, ForeignKey, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from datetime import datetime
import enum
import os
from typing import Optional, Dict, Any

Base = declarative_base()

class CallerType(enum.Enum):
    NEW = "new"
    EXISTING_CONTACT = "existing_contact"
    VIP = "vip"
    ACTIVE_OPPORTUNITY = "active_opportunity"
    EXISTING_ISSUE = "existing_issue"
    PAST_CLIENT = "past_client"

class CallStatus(enum.Enum):
    ACTIVE = "active"
    COMPLETED = "completed"
    FAILED = "failed"
    ESCALATED = "escalated"

class Contact(Base):
    __tablename__ = 'contacts'

    id = Column(String, primary_key=True)
    phone_number = Column(String, unique=True, index=True)
    ghl_contact_id = Column(String, unique=True, nullable=True)
    name = Column(String, nullable=True)
    email = Column(String, nullable=True)
    tags = Column(JSON, default=list)
    custom_fields = Column(JSON, default=dict)
    total_value = Column(Float, default=0.0)
    caller_type = Column(SQLEnum(CallerType), default=CallerType.NEW)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    calls = relationship("CallSession", back_populates="contact")
    notes = relationship("ContactNote", back_populates="contact")

class CallSession(Base):
    __tablename__ = 'call_sessions'

    call_id = Column(String, primary_key=True)
    phone_number = Column(String, index=True)
    contact_id = Column(String, ForeignKey('contacts.id'), nullable=True)
    caller_type = Column(SQLEnum(CallerType))
    status = Column(SQLEnum(CallStatus), default=CallStatus.ACTIVE)
    started_at = Column(DateTime, default=datetime.utcnow)
    ended_at = Column(DateTime, nullable=True)
    duration_seconds = Column(Float, nullable=True)
    transcript = Column(Text, nullable=True)
    summary = Column(JSON, nullable=True)
    conversation_strategy = Column(JSON, nullable=True)
    captured_info = Column(JSON, default=dict)
    insights = Column(JSON, default=list)
    follow_ups_created = Column(Boolean, default=False)

    # Relationships
    contact = relationship("Contact", back_populates="calls")
    events = relationship("CallEvent", back_populates="call_session")

class CallEvent(Base):
    __tablename__ = 'call_events'

    id = Column(String, primary_key=True)
    call_id = Column(String, ForeignKey('call_sessions.call_id'))
    timestamp = Column(DateTime, default=datetime.utcnow)
    event_type = Column(String)  # tool_call, escalation, booking, etc.
    data = Column(JSON)

    # Relationships
    call_session = relationship("CallSession", back_populates="events")

class ContactNote(Base):
    __tablename__ = 'contact_notes'

    id = Column(String, primary_key=True)
    contact_id = Column(String, ForeignKey('contacts.id'))
    note = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    created_by = Column(String, default="amber_brain")

    # Relationships
    contact = relationship("Contact", back_populates="notes")

class FollowUpTask(Base):
    __tablename__ = 'follow_up_tasks'

    id = Column(String, primary_key=True)
    call_id = Column(String, ForeignKey('call_sessions.call_id'))
    contact_id = Column(String, ForeignKey('contacts.id'))
    task_type = Column(String)  # callback, email, appointment, etc.
    description = Column(Text)
    due_date = Column(DateTime)
    completed = Column(Boolean, default=False)
    ghl_task_id = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class ConversationMemory(Base):
    __tablename__ = 'conversation_memory'

    id = Column(String, primary_key=True)
    phone_number = Column(String, index=True)
    memory_type = Column(String)  # episodic, semantic, procedural
    content = Column(JSON)
    embedding = Column(JSON, nullable=True)  # For vector search
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=True)

# Database connection manager
class DatabaseManager:
    def __init__(self):
        self.engine = None
        self.async_session = None

    async def init(self):
        """Initialize database connection"""
        database_url = os.getenv('DATABASE_URL', 'postgresql+asyncpg://clearvc:clearvc_secure_password@postgres:5432/clearvc_brain')

        self.engine = create_async_engine(
            database_url,
            echo=False,
            pool_size=20,
            max_overflow=40
        )

        self.async_session = sessionmaker(
            self.engine,
            class_=AsyncSession,
            expire_on_commit=False
        )

        # Create tables if they don't exist
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    async def get_session(self) -> AsyncSession:
        """Get database session"""
        async with self.async_session() as session:
            yield session

    async def close(self):
        """Close database connection"""
        if self.engine:
            await self.engine.dispose()

    async def execute(self, query):
        """Execute raw query"""
        async with self.async_session() as session:
            result = await session.execute(query)
            await session.commit()
            return result

# Singleton instance
db = DatabaseManager()

# Helper functions for common operations
class CallSession:
    @staticmethod
    async def create(call_id: str, phone_number: str, caller_type: CallerType, started_at: datetime) -> 'CallSession':
        """Create a new call session"""
        async with db.async_session() as session:
            call_session = CallSession(
                call_id=call_id,
                phone_number=phone_number,
                caller_type=caller_type,
                started_at=started_at,
                status=CallStatus.ACTIVE
            )
            session.add(call_session)
            await session.commit()
            return call_session

    @staticmethod
    async def update(call_id: str, **kwargs):
        """Update call session"""
        async with db.async_session() as session:
            result = await session.execute(
                f"UPDATE call_sessions SET {', '.join([f'{k}=%s' for k in kwargs.keys()])} WHERE call_id=%s",
                list(kwargs.values()) + [call_id]
            )
            await session.commit()
            return result

    @staticmethod
    async def get(call_id: str) -> Optional['CallSession']:
        """Get call session by ID"""
        async with db.async_session() as session:
            result = await session.execute(
                "SELECT * FROM call_sessions WHERE call_id = %s",
                [call_id]
            )
            return result.first()