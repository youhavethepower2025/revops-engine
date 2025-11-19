-- D1 Database Schema for Multi-Tenant Retell Brain MCP
-- This is the semantic memory layer for ALL clients

-- Client configurations
CREATE TABLE IF NOT EXISTS clients (
    client_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    tier TEXT DEFAULT 'basic',
    ghl_api_key TEXT,
    ghl_location_id TEXT,
    retell_api_key TEXT,
    config JSON,
    status TEXT DEFAULT 'active',
    created_at INTEGER DEFAULT (unixepoch()),
    updated_at INTEGER DEFAULT (unixepoch())
);

-- Semantic memory - shared knowledge across all interactions
CREATE TABLE IF NOT EXISTS memory (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    client_id TEXT NOT NULL,
    key TEXT NOT NULL,
    value JSON,
    metadata JSON,
    created_at INTEGER DEFAULT (unixepoch()),
    updated_at INTEGER DEFAULT (unixepoch()),
    UNIQUE(client_id, key)
);

-- Call records - all Retell interactions
CREATE TABLE IF NOT EXISTS calls (
    call_id TEXT PRIMARY KEY,
    client_id TEXT NOT NULL,
    agent_id TEXT,
    phone_number TEXT,
    direction TEXT, -- 'inbound' or 'outbound'
    status TEXT,
    transcript JSON,
    metadata JSON,
    started_at INTEGER,
    ended_at INTEGER,
    created_at INTEGER DEFAULT (unixepoch())
);

-- Conversations - semantic breakdown of calls
CREATE TABLE IF NOT EXISTS conversations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    call_id TEXT NOT NULL,
    client_id TEXT NOT NULL,
    role TEXT, -- 'user' or 'assistant'
    content TEXT,
    metadata JSON,
    created_at INTEGER DEFAULT (unixepoch())
);

-- GHL contacts - CRM integration tracking
CREATE TABLE IF NOT EXISTS ghl_contacts (
    contact_id TEXT PRIMARY KEY,
    client_id TEXT NOT NULL,
    phone TEXT,
    email TEXT,
    data JSON,
    last_interaction INTEGER,
    created_at INTEGER DEFAULT (unixepoch()),
    updated_at INTEGER DEFAULT (unixepoch())
);

-- Agent configurations per client
CREATE TABLE IF NOT EXISTS agents (
    agent_id TEXT PRIMARY KEY,
    client_id TEXT NOT NULL,
    platform TEXT DEFAULT 'retell',
    name TEXT,
    prompt TEXT,
    config JSON,
    status TEXT DEFAULT 'active',
    created_at INTEGER DEFAULT (unixepoch()),
    updated_at INTEGER DEFAULT (unixepoch())
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_memory_client ON memory(client_id);
CREATE INDEX IF NOT EXISTS idx_calls_client ON calls(client_id);
CREATE INDEX IF NOT EXISTS idx_calls_phone ON calls(phone_number);
CREATE INDEX IF NOT EXISTS idx_conversations_call ON conversations(call_id);
CREATE INDEX IF NOT EXISTS idx_ghl_contacts_client ON ghl_contacts(client_id);
CREATE INDEX IF NOT EXISTS idx_ghl_contacts_phone ON ghl_contacts(phone);
CREATE INDEX IF NOT EXISTS idx_agents_client ON agents(client_id);
