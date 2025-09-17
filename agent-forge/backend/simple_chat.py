#!/usr/bin/env python3
"""
Simplified Chat Handler for Agent.Forge
Pure knowledge retrieval and response generation
No consciousness bullshit, just revenue
"""

async def handle_chat(widget_id: str, message: str, session_id: str, db_pool, redis_client):
    """
    Simple chat handler focused on commercial value

    1. Get agent config
    2. Retrieve relevant knowledge
    3. Get recent conversation history
    4. Generate response with LLM
    5. Store and return
    """

    from llm_integration import llm
    import uuid
    import secrets
    from datetime import datetime

    async with db_pool.acquire() as conn:
        # 1. Get agent configuration
        agent = await conn.fetchrow("""
            SELECT a.system_prompt, a.model, a.temperature, a.max_tokens,
                   c.id as client_id, c.name as client_name
            FROM agents a
            JOIN clients c ON a.client_id = c.id
            WHERE c.widget_id = $1 AND a.active = true AND c.active = true
            LIMIT 1
        """, widget_id)

        if not agent:
            return {"error": "Widget not found or inactive"}

        client_id = agent['client_id']

        # 2. Try Redis cache first for recent context
        cache_key = f"context:{client_id}:{session_id}"
        cached_context = await redis_client.get(cache_key)

        if cached_context:
            conversation_context = cached_context
        else:
            # 3. Get conversation history from DB
            history = await conn.fetch("""
                SELECT role, content FROM messages
                WHERE conversation_id = (
                    SELECT id FROM conversations
                    WHERE session_id = $1 AND client_id = $2
                    ORDER BY started_at DESC
                    LIMIT 1
                )
                ORDER BY created_at DESC
                LIMIT 10
            """, session_id, client_id)

            # Format history
            conversation_context = "\n".join([
                f"{msg['role']}: {msg['content']}"
                for msg in reversed(history)
            ]) if history else ""

            # Cache for 5 minutes
            await redis_client.set(cache_key, conversation_context, ex=300)

        # 4. Get relevant knowledge (simple keyword search)
        keywords = message.lower().split()[:5]  # Top 5 words

        knowledge = await conn.fetch("""
            SELECT title, content FROM knowledge_entries
            WHERE client_id = $1
              AND active = true
              AND (
                  title ILIKE ANY($2) OR
                  content ILIKE ANY($2)
              )
            ORDER BY priority DESC
            LIMIT 3
        """, client_id, [f'%{kw}%' for kw in keywords])

        # 5. Build simple, effective prompt
        knowledge_context = "\n".join([
            f"Knowledge: {k['title']}\n{k['content']}"
            for k in knowledge
        ]) if knowledge else ""

        prompt = f"""System: {agent['system_prompt']}

{f"Relevant Information:\n{knowledge_context}\n" if knowledge_context else ""}
{f"Recent Conversation:\n{conversation_context}\n" if conversation_context else ""}
User: {message}
Assistant:"""

        # 6. Generate response with LLM
        response = await llm.generate_response(
            prompt=prompt,
            model=agent['model'],
            temperature=agent['temperature'] or 0.7,
            max_tokens=agent['max_tokens'] or 500
        )

        # 7. Store conversation in database
        conversation = await conn.fetchrow(
            "SELECT id FROM conversations WHERE session_id = $1 AND client_id = $2",
            session_id, client_id
        )

        if not conversation:
            # Create new conversation
            conversation_id = str(uuid.uuid4())
            visitor_id = f"visitor_{secrets.token_urlsafe(8)}"

            await conn.execute("""
                INSERT INTO conversations (id, client_id, session_id, visitor_id, started_at)
                VALUES ($1, $2, $3, $4, $5)
            """, conversation_id, client_id, session_id, visitor_id, datetime.utcnow())
        else:
            conversation_id = conversation['id']

        # Store messages
        await conn.execute(
            "INSERT INTO messages (conversation_id, role, content) VALUES ($1, 'user', $2)",
            conversation_id, message
        )

        await conn.execute(
            "INSERT INTO messages (conversation_id, role, content) VALUES ($1, 'assistant', $2)",
            conversation_id, response
        )

        # 8. Track analytics (for revenue insights)
        await conn.execute("""
            INSERT INTO message_analytics (client_id, session_id, message_length, response_time)
            VALUES ($1, $2, $3, NOW())
        """, client_id, session_id, len(message))

        # Clear cache after response
        await redis_client.delete(cache_key)

        return {
            "response": response,
            "session_id": session_id,
            "tokens_used": len(prompt.split()) + len(response.split())  # Rough estimate
        }