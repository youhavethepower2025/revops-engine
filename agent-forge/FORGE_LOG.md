# FORGE LOG

## 2025-09-09 (Late Session)

**Action:** Major refactoring of the core chat logic and bug fixing.

**Changes:**

1.  **Deprecated Old Paradigm:**
    - Deleted `knowledge_engine.py` to remove the rigid, regex-based intent system.

2.  **Refactored `main.py`:**
    - Removed all imports and lifecycle management for the old knowledge engine.
    - Updated the `AgentCreate` data model to use a single `system_prompt` field, replacing `personality` and `instructions`.
    - Updated the `create_client` function to instantiate a default agent using the new `system_prompt`.
    - Completely rewrote the `/widget/{widget_id}/chat` endpoint to forge a new runtime.

3.  **New Runtime Logic (`chat_with_widget`):**
    - The endpoint now dynamically constructs a prompt for an LLM by fusing three components:
        1.  **Agent's Soul:** The `system_prompt` from the database.
        2.  **Dynamic Knowledge:** Relevant entries from the `knowledge_entries` table, retrieved via full-text search based on the user's message.
        3.  **Conversation History:** The last 20 messages from the current session.
    - The response currently returns the forged prompt for debugging, pending integration with an LLM.

4.  **Bug Fixes:**
    - Replaced 6 incorrect calls to a non-existent `verify_token` function with the correct `get_current_user` dependency in the `onboarding` and `analytics` endpoints.
    - Defined and inserted the missing `verify_client_access` security function to ensure teams can only access their own client data.

**Reason:**
- To transform the platform from a rigid, rule-based system to a flexible, powerful architecture aligned with the "Context IS Runtime" philosophy.
- To fix critical bugs that prevented the `onboarding` and `analytics` APIs from functioning.

**Files Modified:**
- `backend/main.py` (heavily modified)
- `backend/knowledge_engine.py` (deleted)

---

## 2025-09-09

**Action:** Refactored the `agents` table schema.

**Change:**
- Replaced the `personality` and `instructions` columns with a single `system_prompt` column of type `TEXT`.

**Reason:**
- To move from a rigid, field-based agent definition to a flexible, prompt-based identity. This aligns with the "Context IS Runtime" philosophy, allowing for a more powerful and dynamic agent definition in a single "big prompt space."

**Files Modified:**
- `database/schema.sql`
- `ARCHITECTURE.md`