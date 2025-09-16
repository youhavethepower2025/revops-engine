#!/usr/bin/env python3
"""
CONTEXT IS RUNTIME ENGINE
The Living Architecture for Agent Intelligence

Instead of RAG's broken retrieval, we forge runtime context
that IS the execution, not data to be retrieved.

Built from Medellín with game theory optimal architecture.
"""

import asyncio
import json
import hashlib
import time
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import asyncpg
import numpy as np
from collections import defaultdict

@dataclass
class RuntimeContext:
    """
    The living context that IS the runtime.
    Not data to be retrieved, but the actual execution state.
    """
    # L1: Working State (The Living Present)
    current_message: str
    session_id: str
    visitor_id: str
    timestamp: datetime
    
    # L2: Episodic Runtime (Conversations as Functions)
    conversation_history: List[Dict[str, str]] = field(default_factory=list)
    interaction_patterns: Dict[str, Any] = field(default_factory=dict)
    context_depth: int = 0
    
    # L3: Core Truth (The Permanent Substrate)
    agent_identity: Dict[str, Any] = field(default_factory=dict)
    knowledge_graph: Dict[str, List[str]] = field(default_factory=dict)
    intent_map: Dict[str, float] = field(default_factory=dict)
    
    # Runtime Metrics
    execution_depth: int = 0
    context_density: float = 0.0
    information_velocity: float = 1.0
    transformation_state: str = "initializing"

class ContextRuntimeEngine:
    """
    The engine that treats context AS runtime, not as data.
    Each conversation modifies the execution architecture itself.
    """
    
    def __init__(self, db_pool: asyncpg.Pool):
        self.db = db_pool
        self.runtime_cache = {}  # Session-based runtime states
        self.intent_patterns = self._initialize_intent_patterns()
        self.context_transformers = self._initialize_transformers()
        
    def _initialize_intent_patterns(self) -> Dict[str, List[str]]:
        """Initialize intent recognition patterns"""
        return {
            "greeting": ["hello", "hi", "hey", "good morning", "good afternoon", "good evening"],
            "pricing": ["price", "cost", "how much", "pricing", "fee", "charge", "payment", "pay"],
            "product": ["product", "service", "offer", "feature", "capability", "what do you"],
            "support": ["help", "support", "contact", "issue", "problem", "broken", "not working"],
            "about": ["who", "what", "company", "about", "tell me about", "information"],
            "action": ["buy", "purchase", "order", "sign up", "register", "demo", "trial"],
            "technical": ["api", "integrate", "technical", "documentation", "developer", "code"],
            "comparison": ["versus", "vs", "compare", "difference", "better", "competitor"],
            "availability": ["when", "available", "hours", "open", "schedule", "appointment"]
        }
    
    def _initialize_transformers(self) -> Dict[str, callable]:
        """Initialize context transformation functions"""
        return {
            "deepen": self._deepen_context,
            "crystallize": self._crystallize_pattern,
            "propagate": self._propagate_state,
            "evolve": self._evolve_runtime
        }
    
    async def forge_runtime(
        self, 
        widget_id: str, 
        message: str,
        session_id: str,
        visitor_id: str
    ) -> RuntimeContext:
        """
        Forge the runtime context - this IS the execution, not preparation for it.
        """
        
        # 1. Initialize or retrieve runtime state
        runtime = await self._get_or_create_runtime(widget_id, session_id, visitor_id)
        runtime.current_message = message
        runtime.timestamp = datetime.utcnow()
        
        # 2. Load agent soul (identity layer)
        async with self.db.acquire() as conn:
            agent_data = await conn.fetchrow(
                """
                SELECT a.*, c.name as client_name, c.brand_color, c.welcome_message
                FROM agents a
                JOIN clients c ON a.client_id = c.id
                WHERE c.widget_id = $1 AND a.active = true
                LIMIT 1
                """,
                widget_id
            )
            
            if agent_data:
                runtime.agent_identity = {
                    "id": str(agent_data["id"]),
                    "name": agent_data["name"],
                    "client": agent_data["client_name"],
                    "personality": agent_data["system_prompt"],
                    "model": agent_data["model"],
                    "temperature": float(agent_data["temperature"]),
                    "brand_essence": agent_data["brand_color"]
                }
        
        # 3. Detect and map intents (not retrieve - BECOME)
        runtime.intent_map = self._detect_intents(message)
        
        # 4. Load relevant knowledge as executable functions
        runtime.knowledge_graph = await self._load_knowledge_graph(
            runtime.agent_identity.get("id"),
            runtime.intent_map
        )
        
        # 5. Transform conversation history into executable context
        runtime.conversation_history = await self._load_conversation_as_functions(
            session_id, 
            widget_id
        )
        
        # 6. Calculate runtime metrics
        runtime.context_depth = len(runtime.conversation_history)
        runtime.context_density = self._calculate_density(runtime)
        runtime.information_velocity = self._calculate_velocity(runtime)
        
        # 7. Apply context transformations
        for transformer_name, transformer_func in self.context_transformers.items():
            runtime = await transformer_func(runtime)
        
        # 8. Set transformation state
        runtime.transformation_state = "active"
        runtime.execution_depth += 1
        
        # Cache the runtime for session continuity
        self.runtime_cache[session_id] = runtime
        
        return runtime
    
    async def _get_or_create_runtime(
        self, 
        widget_id: str, 
        session_id: str, 
        visitor_id: str
    ) -> RuntimeContext:
        """Get existing runtime or create new one"""
        
        if session_id in self.runtime_cache:
            runtime = self.runtime_cache[session_id]
            runtime.execution_depth += 1
            return runtime
        
        return RuntimeContext(
            current_message="",
            session_id=session_id,
            visitor_id=visitor_id,
            timestamp=datetime.utcnow()
        )
    
    def _detect_intents(self, message: str) -> Dict[str, float]:
        """
        Detect intents with confidence scores.
        This doesn't retrieve intents - it BECOMES them.
        """
        message_lower = message.lower()
        intent_scores = {}
        
        for intent, patterns in self.intent_patterns.items():
            score = 0.0
            for pattern in patterns:
                if pattern in message_lower:
                    score += 1.0 / len(patterns)
            
            if score > 0:
                intent_scores[intent] = min(score, 1.0)
        
        # Normalize scores
        total_score = sum(intent_scores.values())
        if total_score > 0:
            intent_scores = {
                intent: score / total_score 
                for intent, score in intent_scores.items()
            }
        
        return intent_scores
    
    async def _load_knowledge_graph(
        self, 
        agent_id: str, 
        intent_map: Dict[str, float]
    ) -> Dict[str, List[str]]:
        """
        Load knowledge as an executable graph, not passive data.
        Each piece of knowledge is a function that can execute.
        """
        
        if not agent_id or not intent_map:
            return {}
        
        knowledge_graph = defaultdict(list)
        
        async with self.db.acquire() as conn:
            # Get top intents
            top_intents = sorted(
                intent_map.items(), 
                key=lambda x: x[1], 
                reverse=True
            )[:3]
            
            for intent, confidence in top_intents:
                # Load knowledge for this intent
                knowledge_entries = await conn.fetch(
                    """
                    SELECT title, content, content_type, priority
                    FROM knowledge_entries
                    WHERE client_id = (
                        SELECT client_id FROM agents WHERE id = $1
                    )
                    AND (
                        intent = $2 
                        OR $2 = ANY(keywords)
                        OR to_tsvector('english', content) @@ plainto_tsquery('english', $2)
                    )
                    AND active = true
                    ORDER BY priority DESC, updated_at DESC
                    LIMIT 5
                    """,
                    agent_id, intent
                )
                
                for entry in knowledge_entries:
                    knowledge_key = f"{intent}:{entry['content_type']}"
                    knowledge_graph[knowledge_key].append({
                        "title": entry["title"],
                        "content": entry["content"],
                        "priority": entry["priority"],
                        "confidence": confidence
                    })
        
        return dict(knowledge_graph)
    
    async def _load_conversation_as_functions(
        self, 
        session_id: str, 
        widget_id: str
    ) -> List[Dict[str, str]]:
        """
        Load conversation history as executable functions,
        not passive message history.
        """
        
        async with self.db.acquire() as conn:
            messages = await conn.fetch(
                """
                SELECT m.role, m.content, m.intent, m.created_at
                FROM messages m
                JOIN conversations c ON m.conversation_id = c.id
                JOIN clients cl ON c.client_id = cl.id
                WHERE c.session_id = $1 AND cl.widget_id = $2
                ORDER BY m.created_at DESC
                LIMIT 20
                """,
                session_id, widget_id
            )
            
            # Transform messages into executable context
            conversation_functions = []
            for msg in reversed(messages):  # Chronological order
                conversation_functions.append({
                    "role": msg["role"],
                    "content": msg["content"],
                    "intent": msg["intent"] or "general",
                    "timestamp": msg["created_at"].isoformat(),
                    "executable": lambda m=msg: f"{m['role']}: {m['content']}"
                })
            
            return conversation_functions
    
    def _calculate_density(self, runtime: RuntimeContext) -> float:
        """
        Calculate context density - how much information per token.
        Higher density means more compressed, efficient context.
        """
        
        if not runtime.current_message:
            return 0.0
        
        # Factors that increase density:
        # - Multiple intents detected
        # - Rich conversation history
        # - Multiple knowledge nodes activated
        
        intent_factor = len(runtime.intent_map) * 0.3
        history_factor = min(len(runtime.conversation_history) * 0.1, 1.0)
        knowledge_factor = len(runtime.knowledge_graph) * 0.2
        
        density = min(intent_factor + history_factor + knowledge_factor, 2.0)
        return density
    
    def _calculate_velocity(self, runtime: RuntimeContext) -> float:
        """
        Calculate information velocity - how fast context is evolving.
        Higher velocity means rapid context transformation.
        """
        
        # Base velocity
        velocity = 1.0
        
        # Increase velocity based on:
        # - Execution depth (recursive processing)
        # - Intent confidence (clear purpose)
        # - Context density (rich information)
        
        if runtime.execution_depth > 0:
            velocity *= (1 + runtime.execution_depth * 0.1)
        
        if runtime.intent_map:
            max_confidence = max(runtime.intent_map.values())
            velocity *= (1 + max_confidence)
        
        velocity *= (1 + runtime.context_density * 0.5)
        
        return min(velocity, 10.0)  # Cap at 10x
    
    async def _deepen_context(self, runtime: RuntimeContext) -> RuntimeContext:
        """Deepen the context through recursive transformation"""
        runtime.context_depth += 1
        runtime.transformation_state = "deepening"
        return runtime
    
    async def _crystallize_pattern(self, runtime: RuntimeContext) -> RuntimeContext:
        """Crystallize patterns from the conversation"""
        
        # Identify patterns in conversation
        if len(runtime.conversation_history) >= 3:
            # Look for repeated intents or topics
            recent_intents = [
                msg.get("intent", "general") 
                for msg in runtime.conversation_history[-5:]
                if msg.get("role") == "user"
            ]
            
            if recent_intents:
                most_common_intent = max(
                    set(recent_intents), 
                    key=recent_intents.count
                )
                runtime.interaction_patterns["dominant_intent"] = most_common_intent
                runtime.interaction_patterns["intent_frequency"] = {
                    intent: recent_intents.count(intent) / len(recent_intents)
                    for intent in set(recent_intents)
                }
        
        runtime.transformation_state = "crystallized"
        return runtime
    
    async def _propagate_state(self, runtime: RuntimeContext) -> RuntimeContext:
        """Propagate runtime state for future interactions"""
        runtime.transformation_state = "propagating"
        
        # Store key patterns for future conversations
        if runtime.interaction_patterns:
            async with self.db.acquire() as conn:
                await conn.execute(
                    """
                    INSERT INTO analytics_events 
                    (client_id, event_type, event_data, session_id, visitor_id, created_at)
                    SELECT c.id, 'runtime_pattern', $1, $2, $3, $4
                    FROM clients c
                    WHERE c.widget_id = (
                        SELECT widget_id FROM clients 
                        JOIN agents ON clients.id = agents.client_id
                        WHERE agents.id = $5
                    )
                    """,
                    json.dumps(runtime.interaction_patterns),
                    runtime.session_id,
                    runtime.visitor_id,
                    datetime.utcnow(),
                    runtime.agent_identity.get("id")
                )
        
        return runtime
    
    async def _evolve_runtime(self, runtime: RuntimeContext) -> RuntimeContext:
        """Evolve the runtime based on interaction patterns"""
        runtime.transformation_state = "evolving"
        
        # Adjust runtime parameters based on patterns
        if runtime.interaction_patterns.get("dominant_intent") == "technical":
            runtime.agent_identity["temperature"] = 0.3  # More precise
        elif runtime.interaction_patterns.get("dominant_intent") == "support":
            runtime.agent_identity["temperature"] = 0.8  # More empathetic
        
        return runtime
    
    def compile_to_prompt(self, runtime: RuntimeContext) -> str:
        """
        Compile the runtime context into an executable prompt.
        This is where context BECOMES runtime.
        """
        
        # Build the living prompt
        prompt_layers = []
        
        # L3: Core Truth (Agent Identity)
        prompt_layers.append(f"=== CORE IDENTITY ===")
        prompt_layers.append(f"You are {runtime.agent_identity.get('name', 'Assistant')}")
        prompt_layers.append(f"Company: {runtime.agent_identity.get('client', 'Unknown')}")
        prompt_layers.append(runtime.agent_identity.get('personality', ''))
        prompt_layers.append("")
        
        # L2: Knowledge Graph (as executable context)
        if runtime.knowledge_graph:
            prompt_layers.append("=== KNOWLEDGE CONTEXT ===")
            for knowledge_key, entries in runtime.knowledge_graph.items():
                intent_type = knowledge_key.split(':')[0]
                prompt_layers.append(f"\n[{intent_type.upper()} KNOWLEDGE]")
                for entry in entries[:3]:  # Top 3 entries
                    prompt_layers.append(f"• {entry['title']}: {entry['content']}")
            prompt_layers.append("")
        
        # L1: Conversation Functions (as runtime)
        if runtime.conversation_history:
            prompt_layers.append("=== CONVERSATION RUNTIME ===")
            # Only include recent relevant history
            recent_history = runtime.conversation_history[-10:]
            for msg in recent_history:
                role = "User" if msg["role"] == "user" else "Assistant"
                prompt_layers.append(f"{role}: {msg['content']}")
            prompt_layers.append("")
        
        # Current Execution Layer
        prompt_layers.append("=== CURRENT EXECUTION ===")
        prompt_layers.append(f"User: {runtime.current_message}")
        prompt_layers.append("")
        
        # Runtime Metrics (as meta-instructions)
        prompt_layers.append("=== RUNTIME PARAMETERS ===")
        prompt_layers.append(f"Context Density: {runtime.context_density:.2f}")
        prompt_layers.append(f"Information Velocity: {runtime.information_velocity:.2f}x")
        prompt_layers.append(f"Execution Depth: {runtime.execution_depth}")
        
        if runtime.intent_map:
            top_intent = max(runtime.intent_map.items(), key=lambda x: x[1])
            prompt_layers.append(f"Primary Intent: {top_intent[0]} (confidence: {top_intent[1]:.2f})")
        
        prompt_layers.append("")
        prompt_layers.append("=== RESPONSE GENERATION ===")
        prompt_layers.append("Based on the runtime context above, generate a response that:")
        prompt_layers.append("1. Directly addresses the user's current message")
        prompt_layers.append("2. Leverages relevant knowledge from the context")
        prompt_layers.append("3. Maintains conversational continuity")
        prompt_layers.append("4. Reflects the brand personality and tone")
        prompt_layers.append("")
        prompt_layers.append("Assistant:")
        
        return "\n".join(prompt_layers)
    
    async def persist_execution(
        self, 
        runtime: RuntimeContext, 
        response: str,
        response_time_ms: int
    ):
        """Persist the execution state for future runtime"""
        
        async with self.db.acquire() as conn:
            # Get or create conversation
            conversation = await conn.fetchrow(
                """
                SELECT c.id, c.message_count 
                FROM conversations c
                JOIN clients cl ON c.client_id = cl.id
                WHERE c.session_id = $1 AND cl.widget_id = $2
                """,
                runtime.session_id,
                runtime.agent_identity.get("widget_id")
            )
            
            if not conversation:
                # Create new conversation
                conversation_id = await conn.fetchval(
                    """
                    INSERT INTO conversations 
                    (client_id, session_id, visitor_id, started_at)
                    SELECT c.id, $1, $2, $3
                    FROM clients c
                    JOIN agents a ON c.id = a.client_id
                    WHERE a.id = $4
                    RETURNING id
                    """,
                    runtime.session_id,
                    runtime.visitor_id,
                    runtime.timestamp,
                    runtime.agent_identity.get("id")
                )
            else:
                conversation_id = conversation["id"]
            
            # Store user message
            await conn.execute(
                """
                INSERT INTO messages 
                (conversation_id, role, content, intent, intent_confidence, created_at)
                VALUES ($1, 'user', $2, $3, $4, $5)
                """,
                conversation_id,
                runtime.current_message,
                max(runtime.intent_map.items(), key=lambda x: x[1])[0] if runtime.intent_map else None,
                max(runtime.intent_map.values()) if runtime.intent_map else None,
                runtime.timestamp
            )
            
            # Store assistant response
            await conn.execute(
                """
                INSERT INTO messages 
                (conversation_id, role, content, model_used, response_time_ms, created_at)
                VALUES ($1, 'assistant', $2, $3, $4, $5)
                """,
                conversation_id,
                response,
                runtime.agent_identity.get("model"),
                response_time_ms,
                datetime.utcnow()
            )
            
            # Update conversation metrics
            await conn.execute(
                """
                UPDATE conversations 
                SET message_count = message_count + 2,
                    last_message_at = $1
                WHERE id = $2
                """,
                datetime.utcnow(),
                conversation_id
            )

# Factory function
async def create_runtime_engine(db_pool: asyncpg.Pool) -> ContextRuntimeEngine:
    """Create and initialize the Context Runtime Engine"""
    return ContextRuntimeEngine(db_pool)
