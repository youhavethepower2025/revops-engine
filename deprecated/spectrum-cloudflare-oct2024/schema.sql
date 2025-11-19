-- Spectrum Database Schema
-- Multi-tenant agent definitions, conversations, and messages

-- Agent Definitions
CREATE TABLE spectrum_agents (
  id TEXT PRIMARY KEY,
  client_id TEXT NOT NULL,
  name TEXT NOT NULL,
  role TEXT NOT NULL,
  description TEXT,
  system_prompt TEXT NOT NULL,
  temperature REAL DEFAULT 0.7,
  model TEXT DEFAULT 'claude-sonnet-3-5-20241022',
  data_sources TEXT DEFAULT '[]',  -- JSON array as text
  color TEXT DEFAULT '#3b82f6',
  position INTEGER,
  enabled INTEGER DEFAULT 1,
  created_at INTEGER DEFAULT (unixepoch()),
  updated_at INTEGER DEFAULT (unixepoch())
);

CREATE INDEX idx_agents_client ON spectrum_agents(client_id, enabled);
CREATE UNIQUE INDEX idx_agents_role ON spectrum_agents(client_id, role);

-- Conversations
CREATE TABLE spectrum_conversations (
  id TEXT PRIMARY KEY,
  client_id TEXT NOT NULL,
  user_id TEXT,
  agent_id TEXT NOT NULL,
  started_at INTEGER DEFAULT (unixepoch()),
  last_message_at INTEGER DEFAULT (unixepoch()),
  message_count INTEGER DEFAULT 0,
  metadata TEXT DEFAULT '{}'  -- JSON object as text
);

CREATE INDEX idx_conversations_client ON spectrum_conversations(client_id, last_message_at DESC);

-- Messages
CREATE TABLE spectrum_messages (
  id TEXT PRIMARY KEY,
  conversation_id TEXT NOT NULL,
  role TEXT NOT NULL,  -- 'user', 'assistant', 'system'
  content TEXT NOT NULL,
  tool_calls TEXT,  -- JSON array as text
  tool_results TEXT,  -- JSON array as text
  tokens_used INTEGER,
  created_at INTEGER DEFAULT (unixepoch())
);

CREATE INDEX idx_messages_conversation ON spectrum_messages(conversation_id, created_at);
