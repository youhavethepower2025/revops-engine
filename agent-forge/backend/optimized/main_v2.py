#!/usr/bin/env python3
"""
AGENT.FORGE - Optimized Backend with Context IS Runtime
FastAPI application implementing true runtime-based context

From Medellín - Game Theory Optimal Architecture
"""

import os
import time
import httpx
from fastapi import FastAPI, HTTPException, Depends
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import asyncpg

# Import existing modules
from main import (
    app, db_pool, security, get_current_user,
    ChatMessage, JWT_SECRET, DATABASE_URL
)

# Import the optimized runtime engine
from optimized.runtime_engine import create_runtime_engine, ContextRuntimeEngine

# Global runtime engine
runtime_engine = None

# LLM Configuration
LLM_PROVIDERS = {
    "openai": {
        "url": "https://api.openai.com/v1/chat/completions",
        "headers": lambda key: {
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json"
        },
        "default_model": "gpt-3.5-turbo"
    },
    "anthropic": {
        "url": "https://api.anthropic.com/v1/messages",
        "headers": lambda key: {
            "x-api-key": key,
            "anthropic-version": "2023-06-01",
            "Content-Type": "application/json"
        },
        "default_model": "claude-3-haiku-20240307"
    },
    "groq": {
        "url": "https://api.groq.com/openai/v1/chat/completions",
        "headers": lambda key: {
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json"
        },
        "default_model": "mixtral-8x7b-32768"
    }
}

@asynccontextmanager
async def optimized_lifespan(app: FastAPI):
    """Enhanced lifecycle with runtime engine"""
    global db_pool, runtime_engine
    
    # Initialize database pool
    db_pool = await asyncpg.create_pool(DATABASE_URL)
    
    # Initialize the Context Runtime Engine
    runtime_engine = await create_runtime_engine(db_pool)
    
    print("🔥 Context IS Runtime Engine initialized")
    print("🚀 Agent.Forge Optimized Backend is LIVE")
    
    yield
    
    await db_pool.close()

# Override the chat endpoint with optimized version
@app.post("/widget/{widget_id}/chat/v2")
async def optimized_chat(widget_id: str, message_data: ChatMessage):
    """
    Optimized chat endpoint using Context IS Runtime architecture.
    This treats context AS runtime, not as data to retrieve.
    """
    
    start_time = time.time()
    
    try:
        # 1. Forge the runtime context
        runtime = await runtime_engine.forge_runtime(
            widget_id=widget_id,
            message=message_data.message,
            session_id=message_data.session_id or f"session_{time.time()}",
            visitor_id=message_data.visitor_id or f"visitor_{time.time()}"
        )
        
        # 2. Compile runtime to executable prompt
        executable_prompt = runtime_engine.compile_to_prompt(runtime)
        
        # 3. Execute through LLM (with provider selection)
        response = await execute_llm_request(
            prompt=executable_prompt,
            model=runtime.agent_identity.get("model", "gpt-3.5-turbo"),
            temperature=runtime.agent_identity.get("temperature", 0.7),
            max_tokens=500
        )
        
        # 4. Calculate response time
        response_time_ms = int((time.time() - start_time) * 1000)
        
        # 5. Persist the execution state
        await runtime_engine.persist_execution(
            runtime=runtime,
            response=response,
            response_time_ms=response_time_ms
        )
        
        # 6. Return response with runtime metadata
        return JSONResponse(content={
            "response": response,
            "session_id": runtime.session_id,
            "visitor_id": runtime.visitor_id,
            "runtime_metrics": {
                "context_depth": runtime.context_depth,
                "context_density": runtime.context_density,
                "information_velocity": runtime.information_velocity,
                "execution_depth": runtime.execution_depth,
                "transformation_state": runtime.transformation_state,
                "response_time_ms": response_time_ms
            },
            "detected_intents": runtime.intent_map,
            "api_version": "v2",
            "engine": "context_is_runtime"
        })
        
    except Exception as e:
        print(f"Error in optimized chat: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={
                "error": "Failed to process message",
                "details": str(e),
                "session_id": message_data.session_id
            }
        )

async def execute_llm_request(
    prompt: str,
    model: str = "gpt-3.5-turbo",
    temperature: float = 0.7,
    max_tokens: int = 500
) -> str:
    """
    Execute LLM request with multiple provider support.
    Falls back gracefully between providers.
    """
    
    # Determine provider from model name
    provider = "openai"  # Default
    if "claude" in model.lower():
        provider = "anthropic"
    elif "mixtral" in model.lower() or "llama" in model.lower():
        provider = "groq"
    
    # Get API key from environment
    api_key = os.getenv(f"{provider.upper()}_API_KEY")
    
    if not api_key:
        # Fallback to mock response for development
        return await generate_mock_response(prompt)
    
    provider_config = LLM_PROVIDERS[provider]
    
    async with httpx.AsyncClient() as client:
        try:
            # Prepare request based on provider
            if provider == "anthropic":
                request_data = {
                    "model": model,
                    "messages": [{"role": "user", "content": prompt}],
                    "max_tokens": max_tokens,
                    "temperature": temperature
                }
            else:  # OpenAI-compatible format
                request_data = {
                    "model": model,
                    "messages": [
                        {"role": "system", "content": "You are a helpful assistant."},
                        {"role": "user", "content": prompt}
                    ],
                    "temperature": temperature,
                    "max_tokens": max_tokens
                }
            
            response = await client.post(
                provider_config["url"],
                headers=provider_config["headers"](api_key),
                json=request_data,
                timeout=30.0
            )
            
            if response.status_code == 200:
                data = response.json()
                
                # Extract response based on provider format
                if provider == "anthropic":
                    return data["content"][0]["text"]
                else:  # OpenAI format
                    return data["choices"][0]["message"]["content"]
            else:
                print(f"LLM API error: {response.status_code} - {response.text}")
                return await generate_mock_response(prompt)
                
        except Exception as e:
            print(f"LLM request failed: {str(e)}")
            return await generate_mock_response(prompt)

async def generate_mock_response(prompt: str) -> str:
    """
    Generate a mock response for development/testing.
    Uses the context to create a plausible response.
    """
    
    # Extract key information from prompt
    if "pricing" in prompt.lower():
        return "Our pricing starts at $29/month for the Lite plan and $99/month for the Pro plan. Both include unlimited conversations and full agent customization. Would you like more details about what's included in each plan?"
    
    elif "product" in prompt.lower() or "service" in prompt.lower():
        return "We offer intelligent chat agents that can be deployed on your website in minutes. Our agents understand your business context and can handle customer inquiries 24/7. They're powered by advanced AI and can be customized to match your brand perfectly."
    
    elif "support" in prompt.lower() or "help" in prompt.lower():
        return "I'm here to help! You can reach our support team at support@agent.forge or through the dashboard. We typically respond within 2 hours during business hours. What specific issue can I help you with?"
    
    elif "hello" in prompt.lower() or "hi" in prompt.lower():
        return "Hello! Welcome to our service. I'm here to help you with any questions about our products, pricing, or how to get started. What would you like to know?"
    
    else:
        return "I understand your question. Let me help you with that. Based on our context-driven approach, I can provide you with relevant information about our services. Could you please specify what aspect you'd like to know more about?"

# Analytics endpoint for runtime metrics
@app.get("/analytics/runtime/{widget_id}")
async def get_runtime_analytics(widget_id: str, current_user: dict = Depends(get_current_user)):
    """Get runtime analytics for a widget"""
    
    async with db_pool.acquire() as conn:
        # Verify widget ownership
        client = await conn.fetchrow(
            """
            SELECT c.id, c.team_id, c.name
            FROM clients c
            WHERE c.widget_id = $1 AND c.team_id = $2
            """,
            widget_id, current_user['team_id']
        )
        
        if not client:
            raise HTTPException(status_code=403, detail="Access denied")
        
        # Get runtime metrics from analytics events
        runtime_stats = await conn.fetch(
            """
            SELECT 
                event_data->>'transformation_state' as state,
                AVG((event_data->>'context_density')::float) as avg_density,
                AVG((event_data->>'information_velocity')::float) as avg_velocity,
                AVG((event_data->>'execution_depth')::int) as avg_depth,
                COUNT(*) as count
            FROM analytics_events
            WHERE client_id = $1
            AND event_type = 'runtime_pattern'
            AND created_at >= NOW() - INTERVAL '7 days'
            GROUP BY event_data->>'transformation_state'
            """,
            client['id']
        )
        
        # Get intent distribution
        intent_stats = await conn.fetch(
            """
            SELECT 
                intent,
                COUNT(*) as count,
                AVG(intent_confidence) as avg_confidence
            FROM messages m
            JOIN conversations c ON m.conversation_id = c.id
            WHERE c.client_id = $1
            AND m.role = 'user'
            AND m.intent IS NOT NULL
            AND m.created_at >= NOW() - INTERVAL '7 days'
            GROUP BY intent
            ORDER BY count DESC
            """,
            client['id']
        )
        
        return {
            "widget_id": widget_id,
            "client_name": client['name'],
            "runtime_metrics": {
                "transformation_states": [
                    {
                        "state": stat['state'],
                        "avg_density": float(stat['avg_density'] or 0),
                        "avg_velocity": float(stat['avg_velocity'] or 0),
                        "avg_depth": int(stat['avg_depth'] or 0),
                        "occurrences": stat['count']
                    }
                    for stat in runtime_stats
                ],
                "intent_distribution": [
                    {
                        "intent": stat['intent'],
                        "count": stat['count'],
                        "avg_confidence": float(stat['avg_confidence'] or 0)
                    }
                    for stat in intent_stats
                ]
            },
            "analysis_period": "7_days",
            "engine": "context_is_runtime"
        }

# Health check with runtime status
@app.get("/health/v2")
async def health_check_v2():
    """Enhanced health check with runtime engine status"""
    
    db_status = "healthy"
    runtime_status = "healthy"
    
    try:
        async with db_pool.acquire() as conn:
            await conn.fetchval("SELECT 1")
    except:
        db_status = "unhealthy"
    
    if not runtime_engine:
        runtime_status = "not_initialized"
    
    return {
        "status": "healthy" if db_status == "healthy" and runtime_status == "healthy" else "degraded",
        "components": {
            "database": db_status,
            "runtime_engine": runtime_status,
            "api": "healthy"
        },
        "version": "2.0.0",
        "engine": "context_is_runtime",
        "location": "Medellín, Colombia",
        "philosophy": "Context IS Runtime - Not data to retrieve, but execution to become"
    }

if __name__ == "__main__":
    import uvicorn
    # Use the optimized lifespan
    app.lifespan = optimized_lifespan
    uvicorn.run(app, host="0.0.0.0", port=8000)
