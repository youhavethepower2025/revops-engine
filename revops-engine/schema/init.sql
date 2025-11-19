-- RevOps Engine Database Schema
-- D1 Database: revops-engine-dev

-- campaigns table
CREATE TABLE IF NOT EXISTS campaigns (
  id TEXT PRIMARY KEY,
  user_id TEXT NOT NULL,
  name TEXT NOT NULL,
  status TEXT DEFAULT 'draft',
  target_criteria TEXT, -- JSON: industry, stage, roles, etc.
  created_at INTEGER DEFAULT (strftime('%s', 'now')),
  updated_at INTEGER DEFAULT (strftime('%s', 'now'))
);

-- prospects table
CREATE TABLE IF NOT EXISTS prospects (
  id TEXT PRIMARY KEY,
  campaign_id TEXT,
  user_id TEXT NOT NULL,
  company_name TEXT,
  company_domain TEXT,
  person_name TEXT,
  person_email TEXT,
  person_title TEXT,
  person_linkedin TEXT,
  enrichment_data TEXT, -- JSON: social, professional, etc.
  research_notes TEXT, -- JSON: AI-generated context
  status TEXT DEFAULT 'new', -- new, researched, drafted, approved, sent
  created_at INTEGER DEFAULT (strftime('%s', 'now')),
  FOREIGN KEY (campaign_id) REFERENCES campaigns(id)
);

-- messages table
CREATE TABLE IF NOT EXISTS messages (
  id TEXT PRIMARY KEY,
  prospect_id TEXT,
  campaign_id TEXT,
  user_id TEXT NOT NULL,
  subject TEXT,
  body TEXT,
  status TEXT DEFAULT 'draft', -- draft, approved, scheduled, sent
  sent_at INTEGER,
  opened_at INTEGER,
  clicked_at INTEGER,
  replied_at INTEGER,
  created_at INTEGER DEFAULT (strftime('%s', 'now')),
  FOREIGN KEY (prospect_id) REFERENCES prospects(id),
  FOREIGN KEY (campaign_id) REFERENCES campaigns(id)
);

-- interactions table
CREATE TABLE IF NOT EXISTS interactions (
  id TEXT PRIMARY KEY,
  message_id TEXT,
  prospect_id TEXT,
  type TEXT NOT NULL, -- open, click, reply
  data TEXT, -- JSON: metadata
  timestamp INTEGER DEFAULT (strftime('%s', 'now')),
  FOREIGN KEY (message_id) REFERENCES messages(id),
  FOREIGN KEY (prospect_id) REFERENCES prospects(id)
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_campaigns_user ON campaigns(user_id);
CREATE INDEX IF NOT EXISTS idx_campaigns_status ON campaigns(status);
CREATE INDEX IF NOT EXISTS idx_prospects_campaign ON prospects(campaign_id);
CREATE INDEX IF NOT EXISTS idx_prospects_user ON prospects(user_id);
CREATE INDEX IF NOT EXISTS idx_prospects_status ON prospects(status);
CREATE INDEX IF NOT EXISTS idx_prospects_email ON prospects(person_email);
CREATE INDEX IF NOT EXISTS idx_messages_prospect ON messages(prospect_id);
CREATE INDEX IF NOT EXISTS idx_messages_campaign ON messages(campaign_id);
CREATE INDEX IF NOT EXISTS idx_messages_user ON messages(user_id);
CREATE INDEX IF NOT EXISTS idx_messages_status ON messages(status);
CREATE INDEX IF NOT EXISTS idx_interactions_message ON interactions(message_id);
CREATE INDEX IF NOT EXISTS idx_interactions_prospect ON interactions(prospect_id);
CREATE INDEX IF NOT EXISTS idx_interactions_type ON interactions(type);


