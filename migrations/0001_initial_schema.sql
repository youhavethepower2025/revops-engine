-- RevOps MCP Engine - D1 Database Schema (SQLite)
-- Salesforce-compatible CRM schema optimized for Cloudflare edge

-- ============================================================================
-- TENANT MANAGEMENT
-- ============================================================================

CREATE TABLE IF NOT EXISTS tenants (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    domain TEXT,
    subscription_tier TEXT NOT NULL DEFAULT 'starter', -- starter, professional, enterprise
    mcp_endpoint TEXT, -- Custom MCP endpoint URL
    api_key_hash TEXT UNIQUE,
    settings TEXT DEFAULT '{}', -- JSON: customization, branding, etc.
    is_active INTEGER DEFAULT 1,
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now'))
);

CREATE INDEX idx_tenants_domain ON tenants(domain);
CREATE INDEX idx_tenants_api_key ON tenants(api_key_hash);

-- ============================================================================
-- SALESFORCE-COMPATIBLE SCHEMA
-- ============================================================================

-- ACCOUNTS (Companies/Organizations)
CREATE TABLE IF NOT EXISTS sf_accounts (
    Id TEXT PRIMARY KEY, -- Salesforce 18-char format
    tenant_id TEXT NOT NULL,
    Name TEXT NOT NULL,
    Type TEXT, -- Customer, Prospect, Partner, Competitor
    Industry TEXT,
    AnnualRevenue REAL,
    NumberOfEmployees INTEGER,
    BillingStreet TEXT,
    BillingCity TEXT,
    BillingState TEXT,
    BillingPostalCode TEXT,
    BillingCountry TEXT,
    Phone TEXT,
    Website TEXT,
    OwnerId TEXT,
    ParentAccountId TEXT,
    Description TEXT,
    CreatedDate TEXT DEFAULT (datetime('now')),
    LastModifiedDate TEXT DEFAULT (datetime('now')),
    IsDeleted INTEGER DEFAULT 0,
    custom_fields TEXT DEFAULT '{}', -- JSON for extensibility

    FOREIGN KEY (tenant_id) REFERENCES tenants(id) ON DELETE CASCADE
);

CREATE INDEX idx_sf_accounts_tenant ON sf_accounts(tenant_id);
CREATE INDEX idx_sf_accounts_name ON sf_accounts(Name);
CREATE INDEX idx_sf_accounts_owner ON sf_accounts(OwnerId);
CREATE INDEX idx_sf_accounts_industry ON sf_accounts(Industry);

-- CONTACTS
CREATE TABLE IF NOT EXISTS sf_contacts (
    Id TEXT PRIMARY KEY,
    tenant_id TEXT NOT NULL,
    AccountId TEXT,
    FirstName TEXT,
    LastName TEXT NOT NULL,
    Email TEXT,
    Phone TEXT,
    MobilePhone TEXT,
    Title TEXT,
    Department TEXT,
    MailingStreet TEXT,
    MailingCity TEXT,
    MailingState TEXT,
    MailingPostalCode TEXT,
    MailingCountry TEXT,
    LeadSource TEXT, -- Web, Referral, Partner, etc.
    OwnerId TEXT,
    Description TEXT,
    CreatedDate TEXT DEFAULT (datetime('now')),
    LastModifiedDate TEXT DEFAULT (datetime('now')),
    IsDeleted INTEGER DEFAULT 0,
    custom_fields TEXT DEFAULT '{}',

    FOREIGN KEY (tenant_id) REFERENCES tenants(id) ON DELETE CASCADE,
    FOREIGN KEY (AccountId) REFERENCES sf_accounts(Id) ON DELETE SET NULL
);

CREATE INDEX idx_sf_contacts_tenant ON sf_contacts(tenant_id);
CREATE INDEX idx_sf_contacts_account ON sf_contacts(AccountId);
CREATE INDEX idx_sf_contacts_email ON sf_contacts(Email);
CREATE INDEX idx_sf_contacts_owner ON sf_contacts(OwnerId);
CREATE INDEX idx_sf_contacts_name ON sf_contacts(LastName, FirstName);

-- OPPORTUNITIES (Deals)
CREATE TABLE IF NOT EXISTS sf_opportunities (
    Id TEXT PRIMARY KEY,
    tenant_id TEXT NOT NULL,
    AccountId TEXT,
    Name TEXT NOT NULL,
    StageName TEXT NOT NULL, -- Prospecting, Qualification, Proposal, Negotiation, Closed Won, Closed Lost
    Amount REAL,
    Probability INTEGER CHECK(Probability >= 0 AND Probability <= 100),
    CloseDate TEXT NOT NULL,
    ForecastCategory TEXT, -- Omitted, Pipeline, Best Case, Commit, Closed
    Type TEXT, -- New Business, Existing Business, Renewal
    LeadSource TEXT,
    NextStep TEXT,
    Description TEXT,
    OwnerId TEXT,
    CreatedDate TEXT DEFAULT (datetime('now')),
    LastModifiedDate TEXT DEFAULT (datetime('now')),
    IsClosed INTEGER DEFAULT 0,
    IsWon INTEGER DEFAULT 0,
    IsDeleted INTEGER DEFAULT 0,
    custom_fields TEXT DEFAULT '{}',

    FOREIGN KEY (tenant_id) REFERENCES tenants(id) ON DELETE CASCADE,
    FOREIGN KEY (AccountId) REFERENCES sf_accounts(Id) ON DELETE SET NULL
);

CREATE INDEX idx_sf_opps_tenant ON sf_opportunities(tenant_id);
CREATE INDEX idx_sf_opps_account ON sf_opportunities(AccountId);
CREATE INDEX idx_sf_opps_stage ON sf_opportunities(StageName);
CREATE INDEX idx_sf_opps_closedate ON sf_opportunities(CloseDate);
CREATE INDEX idx_sf_opps_owner ON sf_opportunities(OwnerId);
CREATE INDEX idx_sf_opps_amount ON sf_opportunities(Amount);

-- TASKS
CREATE TABLE IF NOT EXISTS sf_tasks (
    Id TEXT PRIMARY KEY,
    tenant_id TEXT NOT NULL,
    WhoId TEXT, -- Contact or Lead ID
    WhatId TEXT, -- Account, Opportunity, etc.
    Subject TEXT NOT NULL,
    Status TEXT NOT NULL DEFAULT 'Not Started', -- Not Started, In Progress, Completed, Waiting, Deferred
    Priority TEXT DEFAULT 'Normal', -- High, Normal, Low
    ActivityDate TEXT, -- Due date
    Description TEXT,
    OwnerId TEXT,
    CreatedDate TEXT DEFAULT (datetime('now')),
    IsClosed INTEGER DEFAULT 0,
    IsDeleted INTEGER DEFAULT 0,
    custom_fields TEXT DEFAULT '{}',

    FOREIGN KEY (tenant_id) REFERENCES tenants(id) ON DELETE CASCADE
);

CREATE INDEX idx_sf_tasks_tenant ON sf_tasks(tenant_id);
CREATE INDEX idx_sf_tasks_owner ON sf_tasks(OwnerId);
CREATE INDEX idx_sf_tasks_status ON sf_tasks(Status);
CREATE INDEX idx_sf_tasks_date ON sf_tasks(ActivityDate);

-- EVENTS (Calendar)
CREATE TABLE IF NOT EXISTS sf_events (
    Id TEXT PRIMARY KEY,
    tenant_id TEXT NOT NULL,
    WhoId TEXT,
    WhatId TEXT,
    Subject TEXT NOT NULL,
    StartDateTime TEXT NOT NULL,
    EndDateTime TEXT NOT NULL,
    Location TEXT,
    Description TEXT,
    OwnerId TEXT,
    IsAllDayEvent INTEGER DEFAULT 0,
    CreatedDate TEXT DEFAULT (datetime('now')),
    IsDeleted INTEGER DEFAULT 0,
    custom_fields TEXT DEFAULT '{}',

    FOREIGN KEY (tenant_id) REFERENCES tenants(id) ON DELETE CASCADE
);

CREATE INDEX idx_sf_events_tenant ON sf_events(tenant_id);
CREATE INDEX idx_sf_events_start ON sf_events(StartDateTime);
CREATE INDEX idx_sf_events_owner ON sf_events(OwnerId);

-- ============================================================================
-- CUSTOM FIELDS METADATA
-- ============================================================================

CREATE TABLE IF NOT EXISTS custom_field_definitions (
    id TEXT PRIMARY KEY,
    tenant_id TEXT NOT NULL,
    object_name TEXT NOT NULL, -- 'Contact', 'Opportunity', 'Account', etc.
    api_name TEXT NOT NULL, -- e.g., 'annual_contract_value__c'
    label TEXT NOT NULL,
    field_type TEXT NOT NULL, -- text, number, date, picklist, etc.
    is_required INTEGER DEFAULT 0,
    default_value TEXT,
    picklist_values TEXT, -- JSON array
    help_text TEXT,
    is_active INTEGER DEFAULT 1,
    created_at TEXT DEFAULT (datetime('now')),

    FOREIGN KEY (tenant_id) REFERENCES tenants(id) ON DELETE CASCADE,
    UNIQUE(tenant_id, object_name, api_name)
);

CREATE INDEX idx_custom_fields_tenant ON custom_field_definitions(tenant_id, object_name);

-- ============================================================================
-- PICKLIST VALUES (for dropdowns)
-- ============================================================================

CREATE TABLE IF NOT EXISTS picklist_values (
    id TEXT PRIMARY KEY,
    tenant_id TEXT NOT NULL,
    object_name TEXT NOT NULL,
    field_name TEXT NOT NULL,
    value TEXT NOT NULL,
    label TEXT NOT NULL,
    is_default INTEGER DEFAULT 0,
    sort_order INTEGER,
    is_active INTEGER DEFAULT 1,

    FOREIGN KEY (tenant_id) REFERENCES tenants(id) ON DELETE CASCADE,
    UNIQUE(tenant_id, object_name, field_name, value)
);

CREATE INDEX idx_picklist_values_tenant ON picklist_values(tenant_id, object_name, field_name);

-- ============================================================================
-- API KEYS & AUTHENTICATION
-- ============================================================================

CREATE TABLE IF NOT EXISTS api_keys (
    id TEXT PRIMARY KEY,
    tenant_id TEXT NOT NULL,
    key_hash TEXT NOT NULL UNIQUE,
    key_prefix TEXT NOT NULL, -- First 12 chars for identification
    name TEXT,
    scopes TEXT DEFAULT '["read"]', -- JSON array: read, write, admin
    rate_limit_per_minute INTEGER DEFAULT 60,
    rate_limit_per_day INTEGER DEFAULT 10000,
    is_active INTEGER DEFAULT 1,
    expires_at TEXT,
    last_used_at TEXT,
    created_at TEXT DEFAULT (datetime('now')),
    created_by TEXT,

    FOREIGN KEY (tenant_id) REFERENCES tenants(id) ON DELETE CASCADE
);

CREATE INDEX idx_api_keys_hash ON api_keys(key_hash);
CREATE INDEX idx_api_keys_tenant ON api_keys(tenant_id);

-- ============================================================================
-- USAGE TRACKING & ANALYTICS
-- ============================================================================

CREATE TABLE IF NOT EXISTS api_usage (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tenant_id TEXT NOT NULL,
    api_key_id TEXT,
    tool_name TEXT,
    endpoint TEXT,
    method TEXT,
    status_code INTEGER,
    response_time_ms INTEGER,
    timestamp TEXT DEFAULT (datetime('now')),

    FOREIGN KEY (tenant_id) REFERENCES tenants(id) ON DELETE CASCADE
);

CREATE INDEX idx_api_usage_tenant ON api_usage(tenant_id, timestamp);
CREATE INDEX idx_api_usage_tool ON api_usage(tool_name);

-- ============================================================================
-- EVENT LOG (Change Data Capture)
-- ============================================================================

CREATE TABLE IF NOT EXISTS event_log (
    id TEXT PRIMARY KEY,
    tenant_id TEXT NOT NULL,
    event_type TEXT NOT NULL, -- contact.created, opportunity.stage_changed, etc.
    aggregate_type TEXT NOT NULL, -- Contact, Opportunity, Account
    aggregate_id TEXT NOT NULL,
    payload TEXT NOT NULL, -- JSON
    metadata TEXT DEFAULT '{}', -- JSON
    occurred_at TEXT DEFAULT (datetime('now')),
    processed_at TEXT,

    FOREIGN KEY (tenant_id) REFERENCES tenants(id) ON DELETE CASCADE
);

CREATE INDEX idx_events_tenant ON event_log(tenant_id, occurred_at);
CREATE INDEX idx_events_type ON event_log(event_type);
CREATE INDEX idx_events_aggregate ON event_log(aggregate_type, aggregate_id);

-- ============================================================================
-- TRIGGERS FOR AUTOMATIC TIMESTAMPS
-- ============================================================================

-- Update LastModifiedDate on contacts
CREATE TRIGGER IF NOT EXISTS update_contact_timestamp
AFTER UPDATE ON sf_contacts
BEGIN
    UPDATE sf_contacts
    SET LastModifiedDate = datetime('now')
    WHERE Id = NEW.Id;
END;

-- Update LastModifiedDate on accounts
CREATE TRIGGER IF NOT EXISTS update_account_timestamp
AFTER UPDATE ON sf_accounts
BEGIN
    UPDATE sf_accounts
    SET LastModifiedDate = datetime('now')
    WHERE Id = NEW.Id;
END;

-- Update LastModifiedDate on opportunities
CREATE TRIGGER IF NOT EXISTS update_opportunity_timestamp
AFTER UPDATE ON sf_opportunities
BEGIN
    UPDATE sf_opportunities
    SET LastModifiedDate = datetime('now')
    WHERE Id = NEW.Id;
END;

-- ============================================================================
-- TRIGGERS FOR EVENT LOGGING (Change Data Capture)
-- ============================================================================

-- Log contact creation events
CREATE TRIGGER IF NOT EXISTS log_contact_created
AFTER INSERT ON sf_contacts
BEGIN
    INSERT INTO event_log (id, tenant_id, event_type, aggregate_type, aggregate_id, payload)
    VALUES (
        lower(hex(randomblob(16))),
        NEW.tenant_id,
        'contact.created',
        'Contact',
        NEW.Id,
        json_object(
            'Id', NEW.Id,
            'FirstName', NEW.FirstName,
            'LastName', NEW.LastName,
            'Email', NEW.Email,
            'AccountId', NEW.AccountId
        )
    );
END;

-- Log contact updates
CREATE TRIGGER IF NOT EXISTS log_contact_updated
AFTER UPDATE ON sf_contacts
BEGIN
    INSERT INTO event_log (id, tenant_id, event_type, aggregate_type, aggregate_id, payload)
    VALUES (
        lower(hex(randomblob(16))),
        NEW.tenant_id,
        'contact.updated',
        'Contact',
        NEW.Id,
        json_object(
            'Id', NEW.Id,
            'changes', json_object(
                'old', json_object('FirstName', OLD.FirstName, 'LastName', OLD.LastName, 'Email', OLD.Email),
                'new', json_object('FirstName', NEW.FirstName, 'LastName', NEW.LastName, 'Email', NEW.Email)
            )
        )
    );
END;

-- Log opportunity stage changes
CREATE TRIGGER IF NOT EXISTS log_opportunity_stage_changed
AFTER UPDATE OF StageName ON sf_opportunities
WHEN OLD.StageName != NEW.StageName
BEGIN
    INSERT INTO event_log (id, tenant_id, event_type, aggregate_type, aggregate_id, payload)
    VALUES (
        lower(hex(randomblob(16))),
        NEW.tenant_id,
        'opportunity.stage_changed',
        'Opportunity',
        NEW.Id,
        json_object(
            'Id', NEW.Id,
            'Name', NEW.Name,
            'oldStage', OLD.StageName,
            'newStage', NEW.StageName,
            'Amount', NEW.Amount
        )
    );
END;

-- ============================================================================
-- INITIAL DATA (Standard Picklist Values)
-- ============================================================================

-- Default Opportunity Stages (Salesforce standard)
INSERT OR IGNORE INTO picklist_values (id, tenant_id, object_name, field_name, value, label, sort_order, is_active)
VALUES
    ('stage_prospecting', 'default', 'Opportunity', 'StageName', 'Prospecting', 'Prospecting', 1, 1),
    ('stage_qualification', 'default', 'Opportunity', 'StageName', 'Qualification', 'Qualification', 2, 1),
    ('stage_needs_analysis', 'default', 'Opportunity', 'StageName', 'Needs Analysis', 'Needs Analysis', 3, 1),
    ('stage_value_prop', 'default', 'Opportunity', 'StageName', 'Value Proposition', 'Value Proposition', 4, 1),
    ('stage_decision', 'default', 'Opportunity', 'StageName', 'Decision Makers', 'Decision Makers', 5, 1),
    ('stage_proposal', 'default', 'Opportunity', 'StageName', 'Proposal/Price Quote', 'Proposal/Price Quote', 6, 1),
    ('stage_negotiation', 'default', 'Opportunity', 'StageName', 'Negotiation/Review', 'Negotiation/Review', 7, 1),
    ('stage_closed_won', 'default', 'Opportunity', 'StageName', 'Closed Won', 'Closed Won', 8, 1),
    ('stage_closed_lost', 'default', 'Opportunity', 'StageName', 'Closed Lost', 'Closed Lost', 9, 1);

-- Default Lead Sources
INSERT OR IGNORE INTO picklist_values (id, tenant_id, object_name, field_name, value, label, sort_order, is_active)
VALUES
    ('lead_web', 'default', 'Contact', 'LeadSource', 'Web', 'Web', 1, 1),
    ('lead_phone', 'default', 'Contact', 'LeadSource', 'Phone Inquiry', 'Phone Inquiry', 2, 1),
    ('lead_partner', 'default', 'Contact', 'LeadSource', 'Partner Referral', 'Partner Referral', 3, 1),
    ('lead_purchased', 'default', 'Contact', 'LeadSource', 'Purchased List', 'Purchased List', 4, 1),
    ('lead_other', 'default', 'Contact', 'LeadSource', 'Other', 'Other', 5, 1);

-- Schema version tracking
CREATE TABLE IF NOT EXISTS schema_version (
    version INTEGER PRIMARY KEY,
    applied_at TEXT DEFAULT (datetime('now'))
);

INSERT INTO schema_version (version) VALUES (1);
