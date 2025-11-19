-- Content Intelligence Database Schema
-- D1 Database: content-intelligence-dev

-- research_topics table
CREATE TABLE IF NOT EXISTS research_topics (
  id TEXT PRIMARY KEY,
  user_id TEXT NOT NULL,
  topic TEXT NOT NULL,
  status TEXT DEFAULT 'active',
  created_at INTEGER DEFAULT (strftime('%s', 'now')),
  updated_at INTEGER DEFAULT (strftime('%s', 'now'))
);

-- sources table
CREATE TABLE IF NOT EXISTS sources (
  id TEXT PRIMARY KEY,
  topic_id TEXT,
  user_id TEXT NOT NULL,
  url TEXT NOT NULL,
  title TEXT,
  content TEXT,
  source_type TEXT, -- web, academic, social, blog
  fetched_at INTEGER DEFAULT (strftime('%s', 'now')),
  FOREIGN KEY (topic_id) REFERENCES research_topics(id)
);

-- insights table
CREATE TABLE IF NOT EXISTS insights (
  id TEXT PRIMARY KEY,
  source_id TEXT,
  topic_id TEXT,
  user_id TEXT NOT NULL,
  claim TEXT,
  evidence TEXT,
  confidence REAL,
  extracted_at INTEGER DEFAULT (strftime('%s', 'now')),
  FOREIGN KEY (source_id) REFERENCES sources(id),
  FOREIGN KEY (topic_id) REFERENCES research_topics(id)
);

-- knowledge_graph table
CREATE TABLE IF NOT EXISTS knowledge_graph (
  id TEXT PRIMARY KEY,
  topic_id TEXT,
  user_id TEXT NOT NULL,
  entity_a TEXT,
  relationship TEXT,
  entity_b TEXT,
  strength REAL,
  FOREIGN KEY (topic_id) REFERENCES research_topics(id)
);

-- reports table
CREATE TABLE IF NOT EXISTS reports (
  id TEXT PRIMARY KEY,
  topic_id TEXT,
  user_id TEXT NOT NULL,
  title TEXT,
  content TEXT,
  sources_count INTEGER,
  generated_at INTEGER DEFAULT (strftime('%s', 'now')),
  FOREIGN KEY (topic_id) REFERENCES research_topics(id)
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_topics_user ON research_topics(user_id);
CREATE INDEX IF NOT EXISTS idx_topics_status ON research_topics(status);
CREATE INDEX IF NOT EXISTS idx_sources_topic ON sources(topic_id);
CREATE INDEX IF NOT EXISTS idx_sources_user ON sources(user_id);
CREATE INDEX IF NOT EXISTS idx_sources_type ON sources(source_type);
CREATE INDEX IF NOT EXISTS idx_insights_source ON insights(source_id);
CREATE INDEX IF NOT EXISTS idx_insights_topic ON insights(topic_id);
CREATE INDEX IF NOT EXISTS idx_insights_user ON insights(user_id);
CREATE INDEX IF NOT EXISTS idx_knowledge_topic ON knowledge_graph(topic_id);
CREATE INDEX IF NOT EXISTS idx_knowledge_user ON knowledge_graph(user_id);
CREATE INDEX IF NOT EXISTS idx_reports_topic ON reports(topic_id);
CREATE INDEX IF NOT EXISTS idx_reports_user ON reports(user_id);


