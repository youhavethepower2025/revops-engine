#!/usr/bin/env python3
"""
FastAPI server for Agentic Deployment Platform.

This server provides the core API endpoint for agent communication,
handling conversation logging and memory management.
"""

import os
import uuid
from datetime import datetime
from typing import List, Dict, Any, Optional
from contextlib import asynccontextmanager

import asyncpg
from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel, Field
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ProcessTurnRequest(BaseModel):
    """Request model for the process_turn endpoint."""
    session_id: str = Field(..., description="Unique session identifier")
    agent_id: str = Field(..., description="Agent identifier")
    customer_id: str = Field(..., description="Customer identifier")
    user_message: str = Field(..., description="The user's message")
    turn_id: Optional[int] = Field(None, description="Turn ID (auto-generated if not provided)")


class ConversationTurn(BaseModel):
    """Model representing a single conversation turn."""
    turn_id: int
    speaker: str  # 'user' or 'agent'
    message_text: str
    timestamp: datetime


class MemoryItem(BaseModel):
    """Model representing a memory key-value pair."""
    key: str
    value: str
    updated_at: datetime


class ProcessTurnResponse(BaseModel):
    """Response model for the process_turn endpoint."""
    session_id: str
    turn_id: int
    agent_response: str
    conversation_history: List[ConversationTurn]
    relevant_memory: List[MemoryItem]


class DatabaseManager:
    """Manages database connections and operations."""
    
    def __init__(self):
        self.host = os.getenv('DB_HOST', 'localhost')
        self.port = os.getenv('DB_PORT', '5432')
        self.user = os.getenv('DB_USER', 'postgres')
        self.password = os.getenv('DB_PASSWORD', 'postgres')
        self.database = os.getenv('DB_NAME', 'agentic_platform')
        self.pool: Optional[asyncpg.Pool] = None

    async def create_pool(self):
        """Create the connection pool."""
        try:
            self.pool = await asyncpg.create_pool(
                host=self.host,
                port=self.port,
                user=self.user,
                password=self.password,
                database=self.database,
                min_size=2,
                max_size=10,
                command_timeout=60
            )
            logger.info(f"✓ Database pool created for {self.database}")
        except Exception as e:
            logger.error(f"✗ Failed to create database pool: {e}")
            raise

    async def close_pool(self):
        """Close the connection pool."""
        if self.pool:
            await self.pool.close()
            logger.info("✓ Database pool closed")

    async def get_next_turn_id(self, session_id: str) -> int:
        """Get the next turn ID for a session."""
        async with self.pool.acquire() as conn:
            result = await conn.fetchval(
                "SELECT COALESCE(MAX(turn_id), 0) + 1 FROM conversations WHERE session_id = $1",
                session_id
            )
            return result

    async def save_message(self, session_id: str, turn_id: int, agent_id: str, 
                          customer_id: str, speaker: str, message_text: str) -> None:
        """Save a message to the conversations table."""
        async with self.pool.acquire() as conn:
            try:
                await conn.execute(
                    """
                    INSERT INTO conversations 
                    (session_id, turn_id, agent_id, customer_id, speaker, message_text)
                    VALUES ($1, $2, $3, $4, $5, $6)
                    """,
                    session_id, turn_id, agent_id, customer_id, speaker, message_text
                )
                logger.info(f"✓ Saved {speaker} message for session {session_id}, turn {turn_id}")
            except Exception as e:
                logger.error(f"✗ Failed to save message: {e}")
                raise

    async def get_conversation_history(self, session_id: str) -> List[ConversationTurn]:
        """Load the entire conversation history for a session."""
        async with self.pool.acquire() as conn:
            try:
                rows = await conn.fetch(
                    """
                    SELECT turn_id, speaker, message_text, timestamp
                    FROM conversations 
                    WHERE session_id = $1 
                    ORDER BY turn_id ASC
                    """,
                    session_id
                )
                
                history = [
                    ConversationTurn(
                        turn_id=row['turn_id'],
                        speaker=row['speaker'],
                        message_text=row['message_text'],
                        timestamp=row['timestamp']
                    )
                    for row in rows
                ]
                
                logger.info(f"✓ Loaded {len(history)} conversation turns for session {session_id}")
                return history
                
            except Exception as e:
                logger.error(f"✗ Failed to load conversation history: {e}")
                raise

    async def get_agent_memory(self, agent_id: str, customer_id: str) -> List[MemoryItem]:
        """Load relevant memory for a specific agent and customer."""
        async with self.pool.acquire() as conn:
            try:
                rows = await conn.fetch(
                    """
                    SELECT memory_key, memory_value, updated_at
                    FROM agent_memory 
                    WHERE agent_id = $1 AND customer_id = $2
                    ORDER BY updated_at DESC
                    """,
                    agent_id, customer_id
                )
                
                memory = [
                    MemoryItem(
                        key=row['memory_key'],
                        value=row['memory_value'],
                        updated_at=row['updated_at']
                    )
                    for row in rows
                ]
                
                logger.info(f"✓ Loaded {len(memory)} memory items for agent {agent_id}, customer {customer_id}")
                return memory
                
            except Exception as e:
                logger.error(f"✗ Failed to load agent memory: {e}")
                raise

    async def upsert_memory(self, agent_id: str, customer_id: str, key: str, value: str) -> None:
        """Insert or update a memory item."""
        async with self.pool.acquire() as conn:
            try:
                await conn.execute(
                    """
                    INSERT INTO agent_memory (agent_id, customer_id, memory_key, memory_value)
                    VALUES ($1, $2, $3, $4)
                    ON CONFLICT (agent_id, customer_id, memory_key)
                    DO UPDATE SET memory_value = EXCLUDED.memory_value, updated_at = CURRENT_TIMESTAMP
                    """,
                    agent_id, customer_id, key, value
                )
                logger.info(f"✓ Updated memory for agent {agent_id}, customer {customer_id}: {key}")
            except Exception as e:
                logger.error(f"✗ Failed to upsert memory: {e}")
                raise


# Global database manager instance
db_manager = DatabaseManager()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifespan - startup and shutdown."""
    # Startup
    logger.info("🚀 Starting Agentic Deployment Platform server...")
    await db_manager.create_pool()
    yield
    # Shutdown
    logger.info("🛑 Shutting down server...")
    await db_manager.close_pool()


# Create FastAPI application
app = FastAPI(
    title="Agentic Deployment Platform",
    description="Core API server for agent communication and memory management",
    version="1.0.0",
    lifespan=lifespan
)


def generate_agent_response(user_message: str, conversation_history: List[ConversationTurn], 
                           relevant_memory: List[MemoryItem]) -> str:
    """
    Generate an agent response based on user message, history, and memory.
    
    This is a placeholder implementation. In production, this would integrate
    with your actual AI/ML agent system.
    """
    # Simple placeholder response
    response_templates = [
        f"I understand you said: '{user_message}'. Let me help you with that.",
        f"Thank you for your message. I've processed: '{user_message}'",
        f"Based on our conversation, regarding '{user_message}', I can assist you.",
    ]
    
    # Use conversation length to vary responses
    template_index = len(conversation_history) % len(response_templates)
    base_response = response_templates[template_index]
    
    # Add memory context if available
    if relevant_memory:
        memory_context = f" I remember that {relevant_memory[0].key}: {relevant_memory[0].value}."
        base_response += memory_context
    
    return base_response


@app.get("/")
async def root():
    """Health check endpoint."""
    return {
        "status": "healthy", 
        "service": "Agentic Deployment Platform",
        "version": "1.0.0"
    }


@app.post("/v1/process_turn", response_model=ProcessTurnResponse)
async def process_turn(request: ProcessTurnRequest):
    """
    Universal endpoint for agent communication.
    
    Handles a single conversation turn by:
    1. Saving the user's message
    2. Loading conversation history
    3. Loading relevant agent memory
    4. Generating agent response
    5. Saving agent response
    """
    try:
        # Determine turn ID
        turn_id = request.turn_id
        if turn_id is None:
            turn_id = await db_manager.get_next_turn_id(request.session_id)
        
        # Step 1: Save the incoming user message
        await db_manager.save_message(
            session_id=request.session_id,
            turn_id=turn_id,
            agent_id=request.agent_id,
            customer_id=request.customer_id,
            speaker='user',
            message_text=request.user_message
        )
        
        # Step 2: Load conversation history
        conversation_history = await db_manager.get_conversation_history(request.session_id)
        
        # Step 3: Load relevant agent memory
        relevant_memory = await db_manager.get_agent_memory(request.agent_id, request.customer_id)
        
        # Step 4: Generate agent response (placeholder implementation)
        agent_response = generate_agent_response(
            request.user_message, 
            conversation_history, 
            relevant_memory
        )
        
        # Step 5: Save agent response
        await db_manager.save_message(
            session_id=request.session_id,
            turn_id=turn_id,
            agent_id=request.agent_id,
            customer_id=request.customer_id,
            speaker='agent',
            message_text=agent_response
        )
        
        # Optional: Update agent memory with any new insights
        # For now, we'll just store the session count as an example
        await db_manager.upsert_memory(
            agent_id=request.agent_id,
            customer_id=request.customer_id,
            key="total_messages",
            value=str(len(conversation_history) + 1)
        )
        
        # Refresh conversation history to include the agent's response
        updated_history = await db_manager.get_conversation_history(request.session_id)
        updated_memory = await db_manager.get_agent_memory(request.agent_id, request.customer_id)
        
        return ProcessTurnResponse(
            session_id=request.session_id,
            turn_id=turn_id,
            agent_response=agent_response,
            conversation_history=updated_history,
            relevant_memory=updated_memory
        )
        
    except Exception as e:
        logger.error(f"✗ Error processing turn: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to process turn: {str(e)}")


@app.get("/v1/conversation/{session_id}")
async def get_conversation(session_id: str):
    """Get the full conversation history for a session."""
    try:
        history = await db_manager.get_conversation_history(session_id)
        return {"session_id": session_id, "conversation_history": history}
    except Exception as e:
        logger.error(f"✗ Error retrieving conversation: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve conversation: {str(e)}")


@app.get("/v1/memory/{agent_id}/{customer_id}")
async def get_memory(agent_id: str, customer_id: str):
    """Get agent memory for a specific agent-customer pair."""
    try:
        memory = await db_manager.get_agent_memory(agent_id, customer_id)
        return {"agent_id": agent_id, "customer_id": customer_id, "memory": memory}
    except Exception as e:
        logger.error(f"✗ Error retrieving memory: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve memory: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    
    # Load server configuration from environment
    host = os.getenv("SERVER_HOST", "0.0.0.0")
    port = int(os.getenv("SERVER_PORT", "8000"))
    
    logger.info(f"Starting server on {host}:{port}")
    uvicorn.run(
        "agent_server:app",
        host=host,
        port=port,
        reload=os.getenv("RELOAD", "false").lower() == "true"
    )