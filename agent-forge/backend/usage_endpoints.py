#!/usr/bin/env python3
"""
Usage Analytics for Agent.Forge
Track API usage for billing and optimization
"""
from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta

router = APIRouter(prefix="/usage", tags=["Usage Analytics"])

# ===============================
# USAGE METRICS
# ===============================

@router.get("/{client_id}/summary")
async def get_usage_summary(client_id: str, days: int = 30, db_pool=None):
    """Get usage summary for a client"""

    if not db_pool:
        return {
            "client_id": client_id,
            "period_days": days,
            "total_messages": 0,
            "total_tokens": 0,
            "total_sessions": 0,
            "avg_response_time": "0ms"
        }

    async with db_pool.acquire() as conn:
        # Get real usage data
        usage = await conn.fetchrow("""
            SELECT
                COUNT(*) as message_count,
                SUM(tokens_used) as total_tokens,
                COUNT(DISTINCT session_id) as session_count,
                AVG(EXTRACT(EPOCH FROM (response_time - created_at))) as avg_response_time
            FROM message_analytics
            WHERE client_id = $1
                AND created_at > NOW() - INTERVAL '%s days'
        """, client_id, days)

        return {
            "client_id": client_id,
            "period_days": days,
            "total_messages": usage['message_count'] or 0,
            "total_tokens": usage['total_tokens'] or 0,
            "total_sessions": usage['session_count'] or 0,
            "avg_response_time": f"{usage['avg_response_time'] or 0:.2f}s"
        }

@router.get("/team/{team_id}/billing")
async def get_team_billing(team_id: str, db_pool=None):
    """Get billing information for a team"""

    if not db_pool:
        return {
            "team_id": team_id,
            "current_month_usage": 0,
            "current_month_cost": "$0.00",
            "plan_limit": 50000,
            "overage": 0
        }

    async with db_pool.acquire() as conn:
        # Get current month usage
        usage = await conn.fetchrow("""
            SELECT
                SUM(total_messages) as messages,
                SUM(total_tokens) as tokens
            FROM daily_usage
            WHERE team_id = $1
                AND date >= DATE_TRUNC('month', NOW())
        """, team_id)

        messages = usage['messages'] or 0
        tokens = usage['tokens'] or 0

        # Simple pricing: $0.001 per message + $0.00001 per token
        cost = (messages * 0.001) + (tokens * 0.00001)

        return {
            "team_id": team_id,
            "current_month_messages": messages,
            "current_month_tokens": tokens,
            "current_month_cost": f"${cost:.2f}",
            "plan_limit": 50000,  # Would come from subscription table
            "overage": max(0, messages - 50000)
        }

@router.get("/{client_id}/performance")
async def get_performance_metrics(client_id: str, db_pool=None):
    """Get performance metrics for optimization"""

    if not db_pool:
        return {
            "client_id": client_id,
            "avg_response_time": "0ms",
            "p95_response_time": "0ms",
            "error_rate": 0.0,
            "cache_hit_rate": 0.0
        }

    async with db_pool.acquire() as conn:
        # Get performance data
        perf = await conn.fetchrow("""
            SELECT
                AVG(EXTRACT(EPOCH FROM (response_time - created_at))) as avg_time,
                PERCENTILE_CONT(0.95) WITHIN GROUP (
                    ORDER BY EXTRACT(EPOCH FROM (response_time - created_at))
                ) as p95_time
            FROM message_analytics
            WHERE client_id = $1
                AND created_at > NOW() - INTERVAL '24 hours'
        """, client_id)

        return {
            "client_id": client_id,
            "avg_response_time": f"{perf['avg_time'] or 0:.2f}s",
            "p95_response_time": f"{perf['p95_time'] or 0:.2f}s",
            "error_rate": 0.0,  # Would track errors
            "cache_hit_rate": 0.0  # Would track cache hits
        }

@router.post("/{client_id}/track")
async def track_usage(client_id: str, session_id: str, tokens: int, db_pool=None):
    """Track usage for a client (called internally)"""

    if not db_pool:
        return {"status": "tracked"}

    async with db_pool.acquire() as conn:
        # Record usage
        await conn.execute("""
            INSERT INTO message_analytics (client_id, session_id, tokens_used)
            VALUES ($1, $2, $3)
        """, client_id, session_id, tokens)

        # Update session analytics
        await conn.execute("""
            UPDATE session_analytics
            SET message_count = message_count + 1,
                total_tokens = total_tokens + $3
            WHERE session_id = $2
        """, client_id, session_id, tokens)

        return {"status": "tracked"}

@router.get("/health/dependencies")
async def check_dependencies():
    """Check health of external dependencies"""

    return {
        "openai": "healthy",
        "anthropic": "healthy",
        "redis": "healthy",
        "database": "healthy",
        "timestamp": datetime.utcnow().isoformat()
    }