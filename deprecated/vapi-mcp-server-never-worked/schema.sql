-- schema.sql
-- Database schema for VAPI MCP Server

-- Client configurations (one per business using the system)
CREATE TABLE IF NOT EXISTS vapi_clients (
  client_id TEXT PRIMARY KEY,
  name TEXT NOT NULL,
  ghl_api_key TEXT NOT NULL,
  ghl_location_id TEXT NOT NULL,
  settings TEXT, -- JSON: voice preferences, business hours, etc.
  active INTEGER DEFAULT 1,
  created_at TEXT DEFAULT CURRENT_TIMESTAMP,
  updated_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_clients_active ON vapi_clients(active, created_at DESC);

-- Call logs (every VAPI call)
CREATE TABLE IF NOT EXISTS vapi_calls (
  call_id TEXT PRIMARY KEY,
  client_id TEXT NOT NULL,
  assistant_id TEXT,
  phone_number TEXT,
  caller_name TEXT,
  direction TEXT, -- 'inbound' or 'outbound'
  started_at TEXT NOT NULL,
  ended_at TEXT,
  duration_seconds INTEGER,
  status TEXT, -- 'in-progress', 'completed', 'failed', 'no-answer'
  cost REAL,
  summary TEXT,
  ended_reason TEXT,
  recording_url TEXT,
  created_at TEXT DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (client_id) REFERENCES vapi_clients(client_id)
);

CREATE INDEX idx_calls_client ON vapi_calls(client_id, started_at DESC);
CREATE INDEX idx_calls_phone ON vapi_calls(phone_number, started_at DESC);
CREATE INDEX idx_calls_status ON vapi_calls(status, client_id);

-- Transcripts (messages within calls)
CREATE TABLE IF NOT EXISTS vapi_transcripts (
  id TEXT PRIMARY KEY,
  call_id TEXT NOT NULL,
  role TEXT NOT NULL, -- 'user' or 'assistant' or 'system'
  content TEXT NOT NULL,
  timestamp TEXT NOT NULL,
  created_at TEXT DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (call_id) REFERENCES vapi_calls(call_id)
);

CREATE INDEX idx_transcripts_call ON vapi_transcripts(call_id, timestamp);

-- Tool executions during calls
CREATE TABLE IF NOT EXISTS vapi_tool_calls (
  id TEXT PRIMARY KEY,
  call_id TEXT NOT NULL,
  client_id TEXT,
  tool_name TEXT NOT NULL,
  arguments TEXT NOT NULL, -- JSON
  result TEXT, -- JSON
  success INTEGER,
  error TEXT,
  execution_time_ms INTEGER,
  timestamp TEXT NOT NULL,
  created_at TEXT DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (call_id) REFERENCES vapi_calls(call_id)
);

CREATE INDEX idx_tool_calls_call ON vapi_tool_calls(call_id, timestamp);
CREATE INDEX idx_tool_calls_tool ON vapi_tool_calls(tool_name);
CREATE INDEX idx_tool_calls_client ON vapi_tool_calls(client_id, tool_name, timestamp);

-- Client memory storage (for remember/recall tools)
CREATE TABLE IF NOT EXISTS vapi_client_memory (
  id TEXT PRIMARY KEY,
  client_id TEXT NOT NULL,
  key TEXT NOT NULL,
  value TEXT NOT NULL,
  metadata TEXT DEFAULT '{}',
  created_at TEXT DEFAULT CURRENT_TIMESTAMP,
  updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (client_id) REFERENCES vapi_clients(client_id)
);

CREATE INDEX idx_client_memory ON vapi_client_memory(client_id, key);
CREATE UNIQUE INDEX idx_client_memory_unique ON vapi_client_memory(client_id, key);
