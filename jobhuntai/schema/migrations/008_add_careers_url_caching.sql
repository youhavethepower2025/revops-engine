-- Migration 008: Add careers URL caching to organizations table
-- This enables smart caching of discovered career page URLs
-- Reduces discovery calls and improves performance

-- Add caching columns
ALTER TABLE organizations ADD COLUMN careers_url TEXT;
ALTER TABLE organizations ADD COLUMN careers_url_discovered_at INTEGER;
ALTER TABLE organizations ADD COLUMN careers_url_last_checked INTEGER;
ALTER TABLE organizations ADD COLUMN careers_url_discovery_method TEXT;
  -- Possible values: 'hardcoded', 'ai_search', 'manual'

-- Create indexes for efficient lookups
CREATE INDEX IF NOT EXISTS idx_orgs_careers_url ON organizations(careers_url);
CREATE INDEX IF NOT EXISTS idx_orgs_careers_url_discovered ON organizations(careers_url_discovered_at);

-- Update existing organizations with NULL values (explicit initialization)
UPDATE organizations SET
  careers_url = NULL,
  careers_url_discovered_at = NULL,
  careers_url_last_checked = NULL,
  careers_url_discovery_method = NULL
WHERE careers_url IS NULL;
