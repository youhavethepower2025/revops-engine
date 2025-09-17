-- Simple analytics tables for Agent.Forge
-- Just usage tracking for billing

-- Message analytics for billing
CREATE TABLE IF NOT EXISTS message_analytics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    client_id UUID REFERENCES clients(id) ON DELETE CASCADE,
    session_id VARCHAR(100),
    message_length INTEGER,
    response_length INTEGER,
    tokens_used INTEGER,
    response_time TIMESTAMP DEFAULT NOW(),
    created_at TIMESTAMP DEFAULT NOW()
);

-- Session tracking
CREATE TABLE IF NOT EXISTS session_analytics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    client_id UUID REFERENCES clients(id) ON DELETE CASCADE,
    session_id VARCHAR(100) UNIQUE,
    started_at TIMESTAMP DEFAULT NOW(),
    ended_at TIMESTAMP,
    message_count INTEGER DEFAULT 0,
    total_tokens INTEGER DEFAULT 0
);

-- Daily usage rollup for billing
CREATE TABLE IF NOT EXISTS daily_usage (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    team_id UUID REFERENCES teams(id) ON DELETE CASCADE,
    date DATE,
    total_messages INTEGER DEFAULT 0,
    total_tokens INTEGER DEFAULT 0,
    total_sessions INTEGER DEFAULT 0,
    UNIQUE(team_id, date)
);

-- Indexes for performance
CREATE INDEX idx_message_analytics_client ON message_analytics(client_id, created_at);
CREATE INDEX idx_session_analytics_client ON session_analytics(client_id);
CREATE INDEX idx_daily_usage_team ON daily_usage(team_id, date);