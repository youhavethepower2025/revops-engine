-- The Exit - Complete Database Schema
-- SQLite (D1) schema with multi-tenant support and event sourcing

-- ============================================================================
-- CORE ENTITIES
-- ============================================================================

CREATE TABLE accounts (
  id TEXT PRIMARY KEY,
  name TEXT NOT NULL,
  settings JSON,
  created_at INTEGER NOT NULL,
  updated_at INTEGER NOT NULL
);

CREATE TABLE users (
  id TEXT PRIMARY KEY,
  account_id TEXT NOT NULL,
  email TEXT NOT NULL UNIQUE,
  role TEXT NOT NULL CHECK(role IN ('owner', 'admin', 'member')),
  auth_token TEXT,
  created_at INTEGER NOT NULL,
  FOREIGN KEY (account_id) REFERENCES accounts(id) ON DELETE CASCADE
);

CREATE INDEX idx_users_account ON users(account_id);
CREATE INDEX idx_users_email ON users(email);

CREATE TABLE leads (
  id TEXT PRIMARY KEY,
  account_id TEXT NOT NULL,
  campaign_id TEXT,
  name TEXT,
  email TEXT,
  phone TEXT,
  company TEXT,
  metadata JSON, -- Enriched data from research
  status TEXT NOT NULL CHECK(status IN ('new', 'researching', 'contacted', 'replied', 'qualified', 'dead')),
  score REAL, -- Priority score for queue ordering
  created_at INTEGER NOT NULL,
  updated_at INTEGER NOT NULL,
  FOREIGN KEY (account_id) REFERENCES accounts(id) ON DELETE CASCADE,
  FOREIGN KEY (campaign_id) REFERENCES campaigns(id) ON DELETE SET NULL
);

CREATE INDEX idx_leads_account ON leads(account_id);
CREATE INDEX idx_leads_campaign ON leads(campaign_id);
CREATE INDEX idx_leads_status ON leads(status);
CREATE INDEX idx_leads_score ON leads(score DESC);
CREATE INDEX idx_leads_email ON leads(email);
CREATE INDEX idx_leads_phone ON leads(phone);

CREATE TABLE campaigns (
  id TEXT PRIMARY KEY,
  account_id TEXT NOT NULL,
  name TEXT NOT NULL,
  status TEXT NOT NULL CHECK(status IN ('draft', 'active', 'paused', 'completed')),
  config JSON NOT NULL, -- Target criteria, messaging strategy, timing rules
  created_at INTEGER NOT NULL,
  started_at INTEGER,
  completed_at INTEGER,
  FOREIGN KEY (account_id) REFERENCES accounts(id) ON DELETE CASCADE
);

CREATE INDEX idx_campaigns_account ON campaigns(account_id);
CREATE INDEX idx_campaigns_status ON campaigns(status);

CREATE TABLE conversations (
  id TEXT PRIMARY KEY,
  account_id TEXT NOT NULL,
  lead_id TEXT NOT NULL,
  campaign_id TEXT,
  channel TEXT NOT NULL CHECK(channel IN ('email', 'sms', 'voice')),
  messages JSON NOT NULL, -- Array of message objects
  embedding_id TEXT, -- Reference to Vectorize vector
  status TEXT NOT NULL CHECK(status IN ('active', 'closed', 'needs_attention')),
  created_at INTEGER NOT NULL,
  updated_at INTEGER NOT NULL,
  FOREIGN KEY (account_id) REFERENCES accounts(id) ON DELETE CASCADE,
  FOREIGN KEY (lead_id) REFERENCES leads(id) ON DELETE CASCADE,
  FOREIGN KEY (campaign_id) REFERENCES campaigns(id) ON DELETE SET NULL
);

CREATE INDEX idx_conversations_account ON conversations(account_id);
CREATE INDEX idx_conversations_lead ON conversations(lead_id);
CREATE INDEX idx_conversations_status ON conversations(status);
CREATE INDEX idx_conversations_updated ON conversations(updated_at);

CREATE TABLE actions (
  id TEXT PRIMARY KEY,
  account_id TEXT NOT NULL,
  lead_id TEXT NOT NULL,
  campaign_id TEXT,
  type TEXT NOT NULL CHECK(type IN ('research', 'outreach', 'follow_up', 'call', 'analyze')),
  status TEXT NOT NULL CHECK(status IN ('queued', 'processing', 'completed', 'failed')),
  result JSON,
  error TEXT,
  created_at INTEGER NOT NULL,
  started_at INTEGER,
  completed_at INTEGER,
  FOREIGN KEY (account_id) REFERENCES accounts(id) ON DELETE CASCADE,
  FOREIGN KEY (lead_id) REFERENCES leads(id) ON DELETE CASCADE,
  FOREIGN KEY (campaign_id) REFERENCES campaigns(id) ON DELETE SET NULL
);

CREATE INDEX idx_actions_account ON actions(account_id);
CREATE INDEX idx_actions_lead ON actions(lead_id);
CREATE INDEX idx_actions_status ON actions(status);
CREATE INDEX idx_actions_type ON actions(type);
CREATE INDEX idx_actions_created ON actions(created_at);

-- ============================================================================
-- EVENT SOURCING & OBSERVABILITY
-- ============================================================================

CREATE TABLE events (
  id TEXT PRIMARY KEY,
  trace_id TEXT NOT NULL, -- Ties multi-agent flows together
  parent_span_id TEXT, -- For nested operations
  account_id TEXT NOT NULL,
  event_type TEXT NOT NULL, -- agent_started, action_completed, pattern_detected, etc.
  entity_type TEXT, -- lead, campaign, conversation, action
  entity_id TEXT,
  payload JSON NOT NULL, -- Full context of what happened
  timestamp INTEGER NOT NULL,
  FOREIGN KEY (account_id) REFERENCES accounts(id) ON DELETE CASCADE
);

CREATE INDEX idx_events_trace ON events(trace_id);
CREATE INDEX idx_events_account_time ON events(account_id, timestamp);
CREATE INDEX idx_events_type ON events(event_type);
CREATE INDEX idx_events_entity ON events(entity_type, entity_id);

CREATE TABLE decision_logs (
  id TEXT PRIMARY KEY,
  trace_id TEXT NOT NULL,
  account_id TEXT NOT NULL,
  agent_type TEXT NOT NULL, -- research, outreach, response, analytics, voice
  action_id TEXT,
  lead_id TEXT,
  input_context JSON NOT NULL, -- What the agent saw
  reasoning TEXT, -- LLM chain-of-thought or decision rationale
  decision JSON NOT NULL, -- What the agent chose to do
  outcome JSON, -- What actually happened (populated after action completes)
  timestamp INTEGER NOT NULL,
  FOREIGN KEY (account_id) REFERENCES accounts(id) ON DELETE CASCADE,
  FOREIGN KEY (action_id) REFERENCES actions(id) ON DELETE SET NULL,
  FOREIGN KEY (lead_id) REFERENCES leads(id) ON DELETE CASCADE
);

CREATE INDEX idx_decision_logs_trace ON decision_logs(trace_id);
CREATE INDEX idx_decision_logs_account ON decision_logs(account_id);
CREATE INDEX idx_decision_logs_agent ON decision_logs(agent_type);
CREATE INDEX idx_decision_logs_action ON decision_logs(action_id);
CREATE INDEX idx_decision_logs_time ON decision_logs(timestamp);

CREATE TABLE flow_traces (
  id TEXT PRIMARY KEY,
  trace_id TEXT NOT NULL,
  span_id TEXT NOT NULL,
  parent_span_id TEXT,
  account_id TEXT NOT NULL,
  agent_type TEXT NOT NULL,
  operation TEXT NOT NULL, -- build_context, generate_message, send_email, etc.
  duration_ms INTEGER,
  status TEXT NOT NULL CHECK(status IN ('started', 'completed', 'failed')),
  metadata JSON,
  started_at INTEGER NOT NULL,
  completed_at INTEGER,
  FOREIGN KEY (account_id) REFERENCES accounts(id) ON DELETE CASCADE
);

CREATE INDEX idx_flow_traces_trace ON flow_traces(trace_id);
CREATE INDEX idx_flow_traces_span ON flow_traces(span_id);
CREATE INDEX idx_flow_traces_account ON flow_traces(account_id);

-- ============================================================================
-- KNOWLEDGE LAYER
-- ============================================================================

CREATE TABLE patterns (
  id TEXT PRIMARY KEY,
  account_id TEXT NOT NULL,
  pattern_type TEXT NOT NULL, -- messaging, timing, channel, objection_handling
  pattern_data JSON NOT NULL, -- The actual pattern (e.g., message template, timing rule)

  -- Context where pattern applies
  context_conditions JSON, -- vertical, company_size, persona, etc.

  -- Validation metrics
  sample_size INTEGER NOT NULL DEFAULT 0,
  success_count INTEGER NOT NULL DEFAULT 0,
  success_rate REAL,
  baseline_rate REAL,
  confidence_interval_low REAL,
  confidence_interval_high REAL,
  p_value REAL,

  -- Lifecycle
  status TEXT NOT NULL CHECK(status IN ('hypothesis', 'validated', 'active', 'retired')),
  embedding_id TEXT, -- Reference to Vectorize vector

  created_at INTEGER NOT NULL,
  validated_at INTEGER,
  retired_at INTEGER,

  FOREIGN KEY (account_id) REFERENCES accounts(id) ON DELETE CASCADE
);

CREATE INDEX idx_patterns_account ON patterns(account_id);
CREATE INDEX idx_patterns_type ON patterns(pattern_type);
CREATE INDEX idx_patterns_status ON patterns(status);

CREATE TABLE agent_memory (
  id TEXT PRIMARY KEY,
  account_id TEXT NOT NULL,
  agent_type TEXT NOT NULL,

  -- What the agent has learned
  learned_context JSON NOT NULL, -- Vertical knowledge, persona insights, etc.
  decision_history JSON, -- What I tried, what worked
  active_hypotheses JSON, -- Things I'm testing

  updated_at INTEGER NOT NULL,

  FOREIGN KEY (account_id) REFERENCES accounts(id) ON DELETE CASCADE,
  UNIQUE(account_id, agent_type)
);

CREATE INDEX idx_agent_memory_account ON agent_memory(account_id);
CREATE INDEX idx_agent_memory_agent ON agent_memory(agent_type);

-- ============================================================================
-- ANALYTICS
-- ============================================================================

CREATE TABLE analytics (
  id TEXT PRIMARY KEY,
  account_id TEXT NOT NULL,
  campaign_id TEXT,
  metric_type TEXT NOT NULL, -- sent, opened, replied, booked, converted
  value REAL NOT NULL,
  dimensions JSON, -- channel, pattern_id, etc.
  timestamp INTEGER NOT NULL,
  FOREIGN KEY (account_id) REFERENCES accounts(id) ON DELETE CASCADE,
  FOREIGN KEY (campaign_id) REFERENCES campaigns(id) ON DELETE CASCADE
);

CREATE INDEX idx_analytics_account ON analytics(account_id);
CREATE INDEX idx_analytics_campaign ON analytics(campaign_id);
CREATE INDEX idx_analytics_metric ON analytics(metric_type);
CREATE INDEX idx_analytics_time ON analytics(timestamp);

-- ============================================================================
-- GOVERNANCE & COMPLIANCE
-- ============================================================================

CREATE TABLE compliance_checks (
  id TEXT PRIMARY KEY,
  account_id TEXT NOT NULL,
  action_id TEXT NOT NULL,
  rule_type TEXT NOT NULL, -- can_spam, gdpr, tcpa, custom
  passed INTEGER NOT NULL, -- 1 = passed, 0 = failed
  reason TEXT,
  timestamp INTEGER NOT NULL,
  FOREIGN KEY (account_id) REFERENCES accounts(id) ON DELETE CASCADE,
  FOREIGN KEY (action_id) REFERENCES actions(id) ON DELETE CASCADE
);

CREATE INDEX idx_compliance_account ON compliance_checks(account_id);
CREATE INDEX idx_compliance_action ON compliance_checks(action_id);
CREATE INDEX idx_compliance_passed ON compliance_checks(passed);

CREATE TABLE approval_workflows (
  id TEXT PRIMARY KEY,
  account_id TEXT NOT NULL,
  action_id TEXT NOT NULL,
  status TEXT NOT NULL CHECK(status IN ('pending', 'approved', 'denied')),
  approver_id TEXT,
  decision_reason TEXT,
  created_at INTEGER NOT NULL,
  decided_at INTEGER,
  FOREIGN KEY (account_id) REFERENCES accounts(id) ON DELETE CASCADE,
  FOREIGN KEY (action_id) REFERENCES actions(id) ON DELETE CASCADE,
  FOREIGN KEY (approver_id) REFERENCES users(id) ON DELETE SET NULL
);

CREATE INDEX idx_approvals_account ON approval_workflows(account_id);
CREATE INDEX idx_approvals_status ON approval_workflows(status);

CREATE TABLE opt_outs (
  id TEXT PRIMARY KEY,
  account_id TEXT NOT NULL,
  email TEXT,
  phone TEXT,
  channel TEXT, -- email, sms, voice, all
  opted_out_at INTEGER NOT NULL,
  FOREIGN KEY (account_id) REFERENCES accounts(id) ON DELETE CASCADE
);

CREATE INDEX idx_opt_outs_account ON opt_outs(account_id);
CREATE INDEX idx_opt_outs_email ON opt_outs(email);
CREATE INDEX idx_opt_outs_phone ON opt_outs(phone);

-- ============================================================================
-- RESILIENCE
-- ============================================================================

CREATE TABLE circuit_breaker_state (
  id TEXT PRIMARY KEY,
  account_id TEXT,
  service_name TEXT NOT NULL, -- sendgrid, twilio, retell, etc.
  state TEXT NOT NULL CHECK(state IN ('closed', 'open', 'half_open')),
  failure_count INTEGER NOT NULL DEFAULT 0,
  last_failure_at INTEGER,
  opened_at INTEGER,
  last_check_at INTEGER NOT NULL,
  UNIQUE(account_id, service_name)
);

CREATE INDEX idx_circuit_breaker_service ON circuit_breaker_state(service_name);
CREATE INDEX idx_circuit_breaker_state ON circuit_breaker_state(state);

CREATE TABLE dead_letter_queue (
  id TEXT PRIMARY KEY,
  account_id TEXT NOT NULL,
  action_id TEXT NOT NULL,
  failure_reason TEXT NOT NULL,
  retry_count INTEGER NOT NULL DEFAULT 0,
  payload JSON NOT NULL, -- Original action data
  failed_at INTEGER NOT NULL,
  last_retry_at INTEGER,
  FOREIGN KEY (account_id) REFERENCES accounts(id) ON DELETE CASCADE
);

CREATE INDEX idx_dlq_account ON dead_letter_queue(account_id);
CREATE INDEX idx_dlq_failed_at ON dead_letter_queue(failed_at);

-- ============================================================================
-- EVOLUTION & EXPERIMENTATION (Phase 4)
-- ============================================================================

CREATE TABLE agent_versions (
  id TEXT PRIMARY KEY,
  account_id TEXT NOT NULL,
  agent_type TEXT NOT NULL,
  version_id TEXT NOT NULL,
  prompt TEXT NOT NULL,
  config JSON,

  -- Performance metrics
  invocations INTEGER NOT NULL DEFAULT 0,
  success_rate REAL,
  avg_outcome_score REAL,

  status TEXT NOT NULL CHECK(status IN ('testing', 'active', 'retired')),
  created_at INTEGER NOT NULL,
  activated_at INTEGER,
  retired_at INTEGER,

  FOREIGN KEY (account_id) REFERENCES accounts(id) ON DELETE CASCADE
);

CREATE INDEX idx_agent_versions_account ON agent_versions(account_id);
CREATE INDEX idx_agent_versions_type ON agent_versions(agent_type);
CREATE INDEX idx_agent_versions_status ON agent_versions(status);

CREATE TABLE experiments (
  id TEXT PRIMARY KEY,
  account_id TEXT NOT NULL,
  experiment_type TEXT NOT NULL, -- agent_version, pattern, workflow
  variant_a TEXT NOT NULL, -- ID of control
  variant_b TEXT NOT NULL, -- ID of challenger
  traffic_split REAL NOT NULL DEFAULT 0.5, -- % to variant_b

  -- Results
  variant_a_samples INTEGER NOT NULL DEFAULT 0,
  variant_a_success_rate REAL,
  variant_b_samples INTEGER NOT NULL DEFAULT 0,
  variant_b_success_rate REAL,
  winner TEXT, -- a, b, or null

  status TEXT NOT NULL CHECK(status IN ('running', 'completed', 'cancelled')),
  created_at INTEGER NOT NULL,
  completed_at INTEGER,

  FOREIGN KEY (account_id) REFERENCES accounts(id) ON DELETE CASCADE
);

CREATE INDEX idx_experiments_account ON experiments(account_id);
CREATE INDEX idx_experiments_status ON experiments(status);
