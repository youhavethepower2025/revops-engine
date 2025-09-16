-- ===============================
-- AGENT.FORGE DATABASE SCHEMA
-- The Memory of Númenor - Built to Last Ages
-- ===============================

-- Enable UUID generation
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm"; -- For text search optimization

-- ===============================
-- TEAMS (The Realms of Middle-earth)
-- ===============================
CREATE TABLE teams (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    domain VARCHAR(255) UNIQUE NOT NULL,
    subscription_tier VARCHAR(50) DEFAULT 'starter' CHECK (subscription_tier IN ('starter', 'professional', 'enterprise')),
    billing_email VARCHAR(255),
    stripe_customer_id VARCHAR(255),
    settings JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    active BOOLEAN DEFAULT true
);

-- Index for fast domain lookups
CREATE INDEX idx_teams_domain ON teams(domain);
CREATE INDEX idx_teams_active ON teams(active) WHERE active = true;

-- ===============================
-- TEAM MEMBERS (The Rangers of Númenor)
-- ===============================
CREATE TABLE team_members (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    team_id UUID NOT NULL REFERENCES teams(id) ON DELETE CASCADE,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    salt VARCHAR(255) NOT NULL,
    role VARCHAR(50) DEFAULT 'member' CHECK (role IN ('owner', 'admin', 'member')),
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    avatar_url VARCHAR(500),
    last_login TIMESTAMP WITH TIME ZONE,
    email_verified BOOLEAN DEFAULT false,
    settings JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    active BOOLEAN DEFAULT true
);

-- Indexes for authentication and team management
CREATE INDEX idx_team_members_email ON team_members(email);
CREATE INDEX idx_team_members_team_id ON team_members(team_id);
CREATE INDEX idx_team_members_active ON team_members(active) WHERE active = true;

-- ===============================
-- CLIENTS (The Protected Realms)
-- ===============================
CREATE TABLE clients (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    team_id UUID NOT NULL REFERENCES teams(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    domain VARCHAR(255),
    widget_id VARCHAR(255) UNIQUE NOT NULL,
    
    -- Widget customization (The heraldry of each realm)
    brand_color VARCHAR(7) DEFAULT '#007bff',
    secondary_color VARCHAR(7) DEFAULT '#6c757d',
    widget_position VARCHAR(20) DEFAULT 'bottom-right' CHECK (widget_position IN ('bottom-right', 'bottom-left', 'top-right', 'top-left')),
    widget_size VARCHAR(10) DEFAULT 'medium' CHECK (widget_size IN ('small', 'medium', 'large')),
    welcome_message TEXT DEFAULT 'Hi! How can I help you today?',
    
    -- Business info
    industry VARCHAR(100),
    timezone VARCHAR(50) DEFAULT 'UTC',
    business_hours JSONB DEFAULT '{"monday": {"open": "09:00", "close": "17:00"}, "tuesday": {"open": "09:00", "close": "17:00"}, "wednesday": {"open": "09:00", "close": "17:00"}, "thursday": {"open": "09:00", "close": "17:00"}, "friday": {"open": "09:00", "close": "17:00"}}',
    
    -- Analytics
    total_conversations INTEGER DEFAULT 0,
    total_messages INTEGER DEFAULT 0,
    last_conversation TIMESTAMP WITH TIME ZONE,
    
    -- Metadata
    settings JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    active BOOLEAN DEFAULT true
);

-- Indexes for efficient client management
CREATE UNIQUE INDEX idx_clients_widget_id ON clients(widget_id);
CREATE INDEX idx_clients_team_id ON clients(team_id);
CREATE INDEX idx_clients_active ON clients(active) WHERE active = true;
CREATE INDEX idx_clients_domain ON clients(domain) WHERE domain IS NOT NULL;

-- ===============================
-- AGENTS (The Maiar Servants)
-- ===============================
CREATE TABLE agents (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    client_id UUID NOT NULL REFERENCES clients(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    system_prompt TEXT,
    
    -- AI Model configuration
    model VARCHAR(100) DEFAULT 'gpt-3.5-turbo',
    temperature DECIMAL(3,2) DEFAULT 0.7 CHECK (temperature >= 0 AND temperature <= 2.0),
    max_tokens INTEGER DEFAULT 500 CHECK (max_tokens > 0),
    top_p DECIMAL(3,2) DEFAULT 1.0 CHECK (top_p >= 0 AND top_p <= 1.0),
    
    -- Agent behavior
    response_style VARCHAR(50) DEFAULT 'helpful' CHECK (response_style IN ('helpful', 'professional', 'casual', 'formal', 'creative')),
    fallback_message TEXT DEFAULT 'I''m sorry, I don''t have enough information to answer that question. Please contact our support team for assistance.',
    
    -- Performance tracking
    total_messages INTEGER DEFAULT 0,
    avg_response_time INTEGER DEFAULT 0, -- milliseconds
    satisfaction_rating DECIMAL(3,2) DEFAULT 0.0,
    
    -- Metadata
    version INTEGER DEFAULT 1,
    settings JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    active BOOLEAN DEFAULT true
);

-- Indexes for agent management
CREATE INDEX idx_agents_client_id ON agents(client_id);
CREATE INDEX idx_agents_active ON agents(active) WHERE active = true;
CREATE INDEX idx_agents_model ON agents(model);

-- ===============================
-- KNOWLEDGE BASE (The Great Library)
-- ===============================
CREATE TABLE knowledge_entries (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    client_id UUID NOT NULL REFERENCES clients(id) ON DELETE CASCADE,
    
    -- Content organization
    intent VARCHAR(100) NOT NULL,
    content_type VARCHAR(50) NOT NULL CHECK (content_type IN ('core_fact', 'current_info', 'faq', 'policy', 'procedure')),
    category VARCHAR(100),
    title VARCHAR(255) NOT NULL,
    content TEXT NOT NULL,
    
    -- Search and matching
    keywords TEXT[] DEFAULT '{}',
    tags VARCHAR(50)[] DEFAULT '{}',
    priority INTEGER DEFAULT 1 CHECK (priority >= 1 AND priority <= 10),
    
    -- Usage tracking
    access_count INTEGER DEFAULT 0,
    last_accessed TIMESTAMP WITH TIME ZONE,
    effectiveness_score DECIMAL(3,2) DEFAULT 0.0,
    
    -- Versioning
    version INTEGER DEFAULT 1,
    parent_id UUID REFERENCES knowledge_entries(id),
    
    -- Metadata
    created_by UUID REFERENCES team_members(id),
    settings JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    active BOOLEAN DEFAULT true
);

-- Indexes for knowledge retrieval (The paths to wisdom)
CREATE INDEX idx_knowledge_client_id ON knowledge_entries(client_id);
CREATE INDEX idx_knowledge_intent ON knowledge_entries(intent);
CREATE INDEX idx_knowledge_content_type ON knowledge_entries(content_type);
CREATE INDEX idx_knowledge_priority ON knowledge_entries(priority DESC);
CREATE INDEX idx_knowledge_active ON knowledge_entries(active) WHERE active = true;
CREATE INDEX idx_knowledge_keywords ON knowledge_entries USING GIN(keywords);
CREATE INDEX idx_knowledge_tags ON knowledge_entries USING GIN(tags);

-- Full text search index
CREATE INDEX idx_knowledge_search ON knowledge_entries USING GIN(to_tsvector('english', title || ' ' || content));

-- ===============================
-- CONVERSATIONS (The Chronicles)
-- ===============================
CREATE TABLE conversations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    client_id UUID NOT NULL REFERENCES clients(id) ON DELETE CASCADE,
    
    -- Session tracking
    session_id VARCHAR(255) NOT NULL,
    visitor_id VARCHAR(255),
    
    -- Conversation metadata
    channel VARCHAR(50) DEFAULT 'widget' CHECK (channel IN ('widget', 'api', 'test')),
    user_agent TEXT,
    ip_address INET,
    referrer_url TEXT,
    page_url TEXT,
    
    -- Geographic info
    country_code VARCHAR(2),
    timezone VARCHAR(50),
    
    -- Conversation metrics
    message_count INTEGER DEFAULT 0,
    duration_seconds INTEGER,
    satisfaction_rating INTEGER CHECK (satisfaction_rating >= 1 AND satisfaction_rating <= 5),
    resolution_status VARCHAR(50) DEFAULT 'ongoing' CHECK (resolution_status IN ('ongoing', 'resolved', 'escalated', 'abandoned')),
    
    -- Timestamps
    started_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    ended_at TIMESTAMP WITH TIME ZONE,
    last_message_at TIMESTAMP WITH TIME ZONE
);

-- Indexes for conversation analysis
CREATE INDEX idx_conversations_client_id ON conversations(client_id);
CREATE INDEX idx_conversations_session_id ON conversations(session_id);
CREATE INDEX idx_conversations_visitor_id ON conversations(visitor_id) WHERE visitor_id IS NOT NULL;
CREATE INDEX idx_conversations_started_at ON conversations(started_at);
CREATE INDEX idx_conversations_resolution ON conversations(resolution_status);

-- ===============================
-- MESSAGES (The Words of Power)
-- ===============================
CREATE TABLE messages (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    conversation_id UUID NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
    
    -- Message content
    role VARCHAR(20) NOT NULL CHECK (role IN ('user', 'assistant', 'system')),
    content TEXT NOT NULL,
    
    -- AI processing metadata
    intent VARCHAR(100),
    intent_confidence DECIMAL(3,2),
    entities JSONB DEFAULT '{}',
    sentiment VARCHAR(20) CHECK (sentiment IN ('positive', 'negative', 'neutral')),
    sentiment_score DECIMAL(3,2),
    
    -- Response metadata (for assistant messages)
    model_used VARCHAR(100),
    tokens_used INTEGER,
    response_time_ms INTEGER,
    knowledge_sources UUID[], -- Array of knowledge_entry IDs used
    
    -- Quality tracking
    quality_score DECIMAL(3,2),
    feedback_rating INTEGER CHECK (feedback_rating >= 1 AND feedback_rating <= 5),
    
    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes for message retrieval and analysis
CREATE INDEX idx_messages_conversation_id ON messages(conversation_id);
CREATE INDEX idx_messages_role ON messages(role);
CREATE INDEX idx_messages_intent ON messages(intent) WHERE intent IS NOT NULL;
CREATE INDEX idx_messages_created_at ON messages(created_at);
CREATE INDEX idx_messages_sentiment ON messages(sentiment) WHERE sentiment IS NOT NULL;

-- ===============================
-- ANALYTICS EVENTS (The Seeing Stones)
-- ===============================
CREATE TABLE analytics_events (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    client_id UUID NOT NULL REFERENCES clients(id) ON DELETE CASCADE,
    
    -- Event classification
    event_type VARCHAR(100) NOT NULL,
    event_category VARCHAR(50) DEFAULT 'interaction',
    
    -- Event data
    event_data JSONB NOT NULL DEFAULT '{}',
    
    -- Session tracking
    visitor_id VARCHAR(255),
    session_id VARCHAR(255),
    conversation_id UUID REFERENCES conversations(id),
    
    -- Context
    page_url TEXT,
    referrer_url TEXT,
    user_agent TEXT,
    
    -- Geographic
    country_code VARCHAR(2),
    city VARCHAR(100),
    
    -- Timestamp
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes for analytics queries
CREATE INDEX idx_analytics_client_id ON analytics_events(client_id);
CREATE INDEX idx_analytics_event_type ON analytics_events(event_type);
CREATE INDEX idx_analytics_created_at ON analytics_events(created_at);
CREATE INDEX idx_analytics_visitor_id ON analytics_events(visitor_id) WHERE visitor_id IS NOT NULL;
CREATE INDEX idx_analytics_session_id ON analytics_events(session_id) WHERE session_id IS NOT NULL;

-- ===============================
-- INTEGRATIONS (The Alliances)
-- ===============================
CREATE TABLE integrations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    team_id UUID NOT NULL REFERENCES teams(id) ON DELETE CASCADE,
    
    -- Integration details
    provider VARCHAR(50) NOT NULL CHECK (provider IN ('slack', 'zapier', 'webhook', 'email', 'crm')),
    name VARCHAR(255) NOT NULL,
    
    -- Configuration
    config JSONB NOT NULL DEFAULT '{}',
    credentials_encrypted TEXT, -- Encrypted credentials
    
    -- Status
    status VARCHAR(20) DEFAULT 'active' CHECK (status IN ('active', 'inactive', 'error')),
    last_sync TIMESTAMP WITH TIME ZONE,
    error_message TEXT,
    
    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes for integration management
CREATE INDEX idx_integrations_team_id ON integrations(team_id);
CREATE INDEX idx_integrations_provider ON integrations(provider);
CREATE INDEX idx_integrations_status ON integrations(status);

-- ===============================
-- BILLING & USAGE (The Treasury)
-- ===============================
CREATE TABLE usage_records (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    team_id UUID NOT NULL REFERENCES teams(id) ON DELETE CASCADE,
    
    -- Usage metrics
    metric_type VARCHAR(50) NOT NULL CHECK (metric_type IN ('messages', 'conversations', 'agents', 'storage_mb')),
    quantity INTEGER NOT NULL DEFAULT 0,
    
    -- Billing period
    period_start DATE NOT NULL,
    period_end DATE NOT NULL,
    
    -- Metadata
    recorded_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes for billing queries
CREATE INDEX idx_usage_team_id ON usage_records(team_id);
CREATE INDEX idx_usage_period ON usage_records(period_start, period_end);
CREATE INDEX idx_usage_metric ON usage_records(metric_type);

-- ===============================
-- TRIGGERS (The Watchers)
-- ===============================

-- Update timestamps automatically
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Apply timestamp triggers to relevant tables
CREATE TRIGGER update_teams_updated_at BEFORE UPDATE ON teams FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_team_members_updated_at BEFORE UPDATE ON team_members FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_clients_updated_at BEFORE UPDATE ON clients FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_agents_updated_at BEFORE UPDATE ON agents FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_knowledge_updated_at BEFORE UPDATE ON knowledge_entries FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_integrations_updated_at BEFORE UPDATE ON integrations FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Update conversation metrics
CREATE OR REPLACE FUNCTION update_conversation_metrics()
RETURNS TRIGGER AS $$
BEGIN
    IF TG_OP = 'INSERT' THEN
        -- Update message count and last message time
        UPDATE conversations 
        SET message_count = message_count + 1,
            last_message_at = NEW.created_at
        WHERE id = NEW.conversation_id;
        
        -- Update client totals
        UPDATE clients 
        SET total_messages = total_messages + 1
        WHERE id = (SELECT client_id FROM conversations WHERE id = NEW.conversation_id);
        
        RETURN NEW;
    END IF;
    RETURN NULL;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_conversation_metrics_trigger 
    AFTER INSERT ON messages 
    FOR EACH ROW EXECUTE FUNCTION update_conversation_metrics();

-- ===============================
-- VIEWS (The Maps of Wisdom)
-- ===============================

-- Client dashboard view
CREATE VIEW client_dashboard_stats AS
SELECT 
    c.id,
    c.name,
    c.widget_id,
    c.total_conversations,
    c.total_messages,
    c.last_conversation,
    COUNT(DISTINCT conv.id) as conversations_last_30_days,
    COUNT(DISTINCT msg.id) as messages_last_30_days,
    AVG(conv.satisfaction_rating) as avg_satisfaction,
    COUNT(DISTINCT a.id) as active_agents,
    COUNT(DISTINCT k.id) as knowledge_entries
FROM clients c
LEFT JOIN conversations conv ON c.id = conv.client_id AND conv.started_at >= NOW() - INTERVAL '30 days'
LEFT JOIN messages msg ON conv.id = msg.conversation_id AND msg.created_at >= NOW() - INTERVAL '30 days'
LEFT JOIN agents a ON c.id = a.client_id AND a.active = true
LEFT JOIN knowledge_entries k ON c.id = k.client_id AND k.active = true
WHERE c.active = true
GROUP BY c.id, c.name, c.widget_id, c.total_conversations, c.total_messages, c.last_conversation;

-- Team overview
CREATE VIEW team_overview AS
SELECT 
    t.id,
    t.name,
    t.subscription_tier,
    COUNT(DISTINCT tm.id) as team_members,
    COUNT(DISTINCT c.id) as active_clients,
    COUNT(DISTINCT conv.id) as total_conversations,
    COUNT(DISTINCT conv.id) FILTER (WHERE conv.started_at >= NOW() - INTERVAL '30 days') as conversations_last_30_days,
    SUM(c.total_messages) as total_messages
FROM teams t
LEFT JOIN team_members tm ON t.id = tm.team_id AND tm.active = true
LEFT JOIN clients c ON t.id = c.team_id AND c.active = true
LEFT JOIN conversations conv ON c.id = conv.client_id
WHERE t.active = true
GROUP BY t.id, t.name, t.subscription_tier;

-- ===============================
-- SAMPLE DATA (The First Light)
-- ===============================

-- Insert a sample team for testing
INSERT INTO teams (name, domain, subscription_tier) 
VALUES ('Sample Team', 'example.com', 'professional');

-- Get the team ID for sample data
DO $$
DECLARE
    sample_team_id UUID;
BEGIN
    SELECT id INTO sample_team_id FROM teams WHERE domain = 'example.com';
    
    -- Insert sample team member
    INSERT INTO team_members (team_id, email, password_hash, salt, role, first_name, last_name)
    VALUES (
        sample_team_id, 
        'admin@example.com', 
        'hashed_password_here', 
        'salt_here', 
        'owner',
        'Sample',
        'Admin'
    );
END $$;

-- ===============================
-- ONBOARDING SYSTEM (The Great Journey)
-- ===============================

CREATE TABLE onboarding_progress (
    client_id UUID PRIMARY KEY REFERENCES clients(id) ON DELETE CASCADE,
    current_stage VARCHAR(50) NOT NULL DEFAULT 'welcome',
    completed_stages JSONB DEFAULT '[]'::jsonb,
    data_collected JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Index for onboarding queries
CREATE INDEX idx_onboarding_progress_stage ON onboarding_progress(current_stage);
CREATE INDEX idx_onboarding_progress_updated ON onboarding_progress(updated_at DESC);

-- ===============================
-- COMMENTS (The Lore)
-- ===============================

COMMENT ON TABLE teams IS 'Organizations using the Agent.Forge platform';
COMMENT ON TABLE team_members IS 'Users who belong to teams and manage agents';
COMMENT ON TABLE clients IS 'End clients who have agents deployed on their websites';
COMMENT ON TABLE agents IS 'AI agents that serve specific clients';
COMMENT ON TABLE knowledge_entries IS 'Knowledge base entries for each client, organized by intent';
COMMENT ON TABLE conversations IS 'Chat conversations between visitors and agents';
COMMENT ON TABLE messages IS 'Individual messages within conversations';
COMMENT ON TABLE analytics_events IS 'Detailed analytics and interaction tracking';
COMMENT ON TABLE integrations IS 'Third-party integrations for teams';
COMMENT ON TABLE usage_records IS 'Billing and usage tracking';
COMMENT ON TABLE onboarding_progress IS 'Client onboarding progress and collected setup data';

-- The database is complete - May it serve through all the ages of Middle-earth! 🏰