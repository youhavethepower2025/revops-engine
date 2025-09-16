#!/usr/bin/env python3
"""
AGENT.FORGE MONITORING
Real-time monitoring of Context IS Runtime performance

From Medellín with operational excellence
"""

import asyncio
import asyncpg
import json
from datetime import datetime, timedelta
from typing import Dict, List
import os

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://localhost/agentforge")

class RuntimeMonitor:
    """Monitor Context IS Runtime metrics"""
    
    def __init__(self, db_url: str):
        self.db_url = db_url
        self.db_pool = None
    
    async def connect(self):
        """Connect to database"""
        self.db_pool = await asyncpg.create_pool(self.db_url)
    
    async def disconnect(self):
        """Disconnect from database"""
        if self.db_pool:
            await self.db_pool.close()
    
    async def get_runtime_metrics(self, hours: int = 24) -> Dict:
        """Get runtime metrics for the past N hours"""
        
        async with self.db_pool.acquire() as conn:
            # Get conversation metrics
            conv_metrics = await conn.fetchrow(
                """
                SELECT 
                    COUNT(DISTINCT c.id) as total_conversations,
                    COUNT(m.id) as total_messages,
                    AVG(m.response_time_ms) as avg_response_time,
                    PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY m.response_time_ms) as median_response_time,
                    PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY m.response_time_ms) as p95_response_time,
                    COUNT(DISTINCT c.visitor_id) as unique_visitors,
                    AVG(c.message_count) as avg_messages_per_conversation
                FROM conversations c
                JOIN messages m ON c.id = m.conversation_id
                WHERE c.started_at >= NOW() - INTERVAL '%s hours'
                """,
                hours
            )
            
            # Get intent distribution
            intent_dist = await conn.fetch(
                """
                SELECT 
                    m.intent,
                    COUNT(*) as count,
                    AVG(m.intent_confidence) as avg_confidence
                FROM messages m
                JOIN conversations c ON m.conversation_id = c.id
                WHERE c.started_at >= NOW() - INTERVAL '%s hours'
                AND m.intent IS NOT NULL
                GROUP BY m.intent
                ORDER BY count DESC
                LIMIT 10
                """,
                hours
            )
            
            # Get runtime state distribution
            runtime_states = await conn.fetch(
                """
                SELECT 
                    event_data->>'transformation_state' as state,
                    COUNT(*) as count,
                    AVG((event_data->>'context_density')::float) as avg_density,
                    AVG((event_data->>'information_velocity')::float) as avg_velocity
                FROM analytics_events
                WHERE event_type = 'runtime_pattern'
                AND created_at >= NOW() - INTERVAL '%s hours'
                GROUP BY event_data->>'transformation_state'
                """,
                hours
            )
            
            # Get error rate
            errors = await conn.fetchrow(
                """
                SELECT 
                    COUNT(*) FILTER (WHERE event_data->>'error' IS NOT NULL) as error_count,
                    COUNT(*) as total_events,
                    CASE 
                        WHEN COUNT(*) > 0 
                        THEN (COUNT(*) FILTER (WHERE event_data->>'error' IS NOT NULL)::float / COUNT(*)::float) * 100
                        ELSE 0
                    END as error_rate
                FROM analytics_events
                WHERE created_at >= NOW() - INTERVAL '%s hours'
                """,
                hours
            )
            
            # Get client activity
            client_activity = await conn.fetch(
                """
                SELECT 
                    cl.name as client_name,
                    cl.widget_id,
                    COUNT(DISTINCT c.id) as conversations,
                    COUNT(m.id) as messages,
                    AVG(m.response_time_ms) as avg_response_time
                FROM clients cl
                JOIN conversations c ON cl.id = c.client_id
                JOIN messages m ON c.id = m.conversation_id
                WHERE c.started_at >= NOW() - INTERVAL '%s hours'
                GROUP BY cl.id, cl.name, cl.widget_id
                ORDER BY messages DESC
                LIMIT 10
                """,
                hours
            )
            
            return {
                "period_hours": hours,
                "timestamp": datetime.utcnow().isoformat(),
                "conversation_metrics": dict(conv_metrics) if conv_metrics else {},
                "intent_distribution": [dict(i) for i in intent_dist],
                "runtime_states": [dict(s) for s in runtime_states],
                "error_metrics": dict(errors) if errors else {},
                "top_clients": [dict(c) for c in client_activity]
            }
    
    async def get_real_time_stats(self) -> Dict:
        """Get real-time statistics"""
        
        async with self.db_pool.acquire() as conn:
            # Current active conversations (last 5 minutes)
            active_convs = await conn.fetchval(
                """
                SELECT COUNT(DISTINCT id)
                FROM conversations
                WHERE last_message_at >= NOW() - INTERVAL '5 minutes'
                """
            )
            
            # Messages in last minute
            recent_messages = await conn.fetchval(
                """
                SELECT COUNT(*)
                FROM messages
                WHERE created_at >= NOW() - INTERVAL '1 minute'
                """
            )
            
            # Average response time (last hour)
            avg_response = await conn.fetchval(
                """
                SELECT AVG(response_time_ms)
                FROM messages
                WHERE created_at >= NOW() - INTERVAL '1 hour'
                AND role = 'assistant'
                """
            )
            
            # Context density trend (last hour)
            density_trend = await conn.fetch(
                """
                SELECT 
                    DATE_TRUNC('minute', created_at) as minute,
                    AVG((event_data->>'context_density')::float) as avg_density
                FROM analytics_events
                WHERE event_type = 'runtime_pattern'
                AND created_at >= NOW() - INTERVAL '1 hour'
                GROUP BY DATE_TRUNC('minute', created_at)
                ORDER BY minute DESC
                LIMIT 60
                """
            )
            
            return {
                "timestamp": datetime.utcnow().isoformat(),
                "active_conversations": active_convs or 0,
                "messages_per_minute": recent_messages or 0,
                "avg_response_time_ms": float(avg_response or 0),
                "context_density_trend": [
                    {
                        "time": row['minute'].isoformat(),
                        "density": float(row['avg_density'] or 0)
                    }
                    for row in density_trend
                ]
            }
    
    async def check_health(self) -> Dict:
        """Check system health"""
        
        health = {
            "status": "healthy",
            "checks": {},
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Check database connection
        try:
            async with self.db_pool.acquire() as conn:
                await conn.fetchval("SELECT 1")
            health["checks"]["database"] = "healthy"
        except Exception as e:
            health["checks"]["database"] = f"unhealthy: {str(e)}"
            health["status"] = "degraded"
        
        # Check response times
        async with self.db_pool.acquire() as conn:
            avg_response = await conn.fetchval(
                """
                SELECT AVG(response_time_ms)
                FROM messages
                WHERE created_at >= NOW() - INTERVAL '5 minutes'
                AND role = 'assistant'
                """
            )
            
            if avg_response and avg_response > 5000:  # 5 seconds
                health["checks"]["response_time"] = f"degraded: {avg_response:.0f}ms avg"
                health["status"] = "degraded"
            else:
                health["checks"]["response_time"] = f"healthy: {avg_response:.0f}ms avg" if avg_response else "healthy: no recent data"
        
        # Check error rate
        async with self.db_pool.acquire() as conn:
            error_rate = await conn.fetchval(
                """
                SELECT 
                    CASE 
                        WHEN COUNT(*) > 0 
                        THEN (COUNT(*) FILTER (WHERE event_data->>'error' IS NOT NULL)::float / COUNT(*)::float) * 100
                        ELSE 0
                    END as error_rate
                FROM analytics_events
                WHERE created_at >= NOW() - INTERVAL '5 minutes'
                """
            )
            
            if error_rate and error_rate > 5:  # 5% error rate
                health["checks"]["error_rate"] = f"degraded: {error_rate:.1f}%"
                health["status"] = "degraded"
            else:
                health["checks"]["error_rate"] = f"healthy: {error_rate:.1f}%" if error_rate else "healthy: 0%"
        
        return health

async def print_dashboard(monitor: RuntimeMonitor):
    """Print monitoring dashboard"""
    
    # Clear screen
    print("\033[2J\033[H")
    
    print("="*80)
    print("🔥 AGENT.FORGE - CONTEXT IS RUNTIME MONITORING DASHBOARD")
    print("="*80)
    
    # Get metrics
    metrics = await monitor.get_runtime_metrics(24)
    realtime = await monitor.get_real_time_stats()
    health = await monitor.check_health()
    
    # Health Status
    status_emoji = "✅" if health["status"] == "healthy" else "⚠️"
    print(f"\n{status_emoji} System Status: {health['status'].upper()}")
    for check, status in health["checks"].items():
        check_emoji = "✅" if "healthy" in status else "❌"
        print(f"  {check_emoji} {check}: {status}")
    
    # Real-time Stats
    print(f"\n📊 REAL-TIME METRICS")
    print(f"  Active Conversations: {realtime['active_conversations']}")
    print(f"  Messages/minute: {realtime['messages_per_minute']}")
    print(f"  Avg Response Time: {realtime['avg_response_time_ms']:.0f}ms")
    
    # 24-hour Metrics
    conv_metrics = metrics["conversation_metrics"]
    if conv_metrics:
        print(f"\n📈 24-HOUR STATISTICS")
        print(f"  Total Conversations: {conv_metrics.get('total_conversations', 0)}")
        print(f"  Total Messages: {conv_metrics.get('total_messages', 0)}")
        print(f"  Unique Visitors: {conv_metrics.get('unique_visitors', 0)}")
        print(f"  Avg Messages/Conversation: {conv_metrics.get('avg_messages_per_conversation', 0):.1f}")
        print(f"  Response Times:")
        print(f"    - Average: {conv_metrics.get('avg_response_time', 0):.0f}ms")
        print(f"    - Median: {conv_metrics.get('median_response_time', 0):.0f}ms")
        print(f"    - 95th percentile: {conv_metrics.get('p95_response_time', 0):.0f}ms")
    
    # Intent Distribution
    if metrics["intent_distribution"]:
        print(f"\n🎯 TOP INTENTS (24h)")
        for intent in metrics["intent_distribution"][:5]:
            confidence = intent.get('avg_confidence', 0) * 100
            print(f"  {intent['intent']}: {intent['count']} ({confidence:.0f}% confidence)")
    
    # Runtime States
    if metrics["runtime_states"]:
        print(f"\n⚡ RUNTIME STATE DISTRIBUTION")
        for state in metrics["runtime_states"]:
            print(f"  {state['state']}: {state['count']} occurrences")
            print(f"    - Avg Density: {state.get('avg_density', 0):.2f}")
            print(f"    - Avg Velocity: {state.get('avg_velocity', 0):.2f}x")
    
    # Top Clients
    if metrics["top_clients"]:
        print(f"\n🏆 TOP ACTIVE CLIENTS (24h)")
        for client in metrics["top_clients"][:5]:
            print(f"  {client['client_name']}: {client['messages']} messages, {client['conversations']} conversations")
    
    # Error Metrics
    error_metrics = metrics["error_metrics"]
    if error_metrics:
        error_rate = error_metrics.get('error_rate', 0)
        error_emoji = "✅" if error_rate < 1 else "⚠️" if error_rate < 5 else "❌"
        print(f"\n{error_emoji} ERROR RATE: {error_rate:.2f}%")
        print(f"  Errors: {error_metrics.get('error_count', 0)}/{error_metrics.get('total_events', 0)}")
    
    print("\n" + "="*80)
    print(f"Last updated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC")
    print("Press Ctrl+C to exit")

async def main():
    """Main monitoring loop"""
    
    monitor = RuntimeMonitor(DATABASE_URL)
    await monitor.connect()
    
    try:
        while True:
            await print_dashboard(monitor)
            await asyncio.sleep(10)  # Refresh every 10 seconds
    except KeyboardInterrupt:
        print("\n\n👋 Monitoring stopped")
    finally:
        await monitor.disconnect()

if __name__ == "__main__":
    print("Starting Agent.Forge monitoring...")
    print("Connecting to database...")
    asyncio.run(main())
