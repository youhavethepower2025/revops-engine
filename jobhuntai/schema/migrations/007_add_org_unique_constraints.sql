-- Migration 007: Add UNIQUE constraints to organizations table to prevent duplicates
-- Created: 2025-01-10
-- Purpose: Prevent duplicate organizations per account (same domain or name)

-- Add UNIQUE constraint on (account_id, domain)
-- This prevents multiple orgs with same domain within an account
CREATE UNIQUE INDEX IF NOT EXISTS idx_organizations_account_domain
ON organizations(account_id, domain)
WHERE domain IS NOT NULL;

-- Add UNIQUE constraint on (account_id, LOWER(name))
-- This prevents multiple orgs with same name (case-insensitive) within an account
CREATE UNIQUE INDEX IF NOT EXISTS idx_organizations_account_name
ON organizations(account_id, LOWER(name));

-- Add similar constraint for roles to prevent duplicate role titles per org
CREATE UNIQUE INDEX IF NOT EXISTS idx_roles_org_title
ON roles(org_id, LOWER(role_title));

-- Note: Migration completed successfully
-- Constraints added:
--   - idx_organizations_account_domain: Prevents duplicate domains per account
--   - idx_organizations_account_name: Prevents duplicate org names per account (case-insensitive)
--   - idx_roles_org_title: Prevents duplicate role titles per org (case-insensitive)
