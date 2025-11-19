-- Add memory table for remember/recall tools
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

CREATE INDEX IF NOT EXISTS idx_client_memory ON vapi_client_memory(client_id, key);
CREATE UNIQUE INDEX IF NOT EXISTS idx_client_memory_unique ON vapi_client_memory(client_id, key);

-- Add missing columns to vapi_calls if needed
ALTER TABLE vapi_calls ADD COLUMN summary TEXT;
ALTER TABLE vapi_calls ADD COLUMN ended_reason TEXT;
