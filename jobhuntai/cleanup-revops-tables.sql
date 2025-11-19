-- JobHunt AI Database Cleanup
-- Removing all RevOps legacy tables
-- Date: November 13, 2025

-- Disable foreign key constraints temporarily
PRAGMA foreign_keys = OFF;

-- Drop RevOps tables (in order to handle dependencies)
DROP TABLE IF EXISTS decision_logs;
DROP TABLE IF EXISTS flow_traces;
DROP TABLE IF EXISTS dead_letter_queue;
DROP TABLE IF EXISTS circuit_breaker_state;
DROP TABLE IF EXISTS approval_workflows;
DROP TABLE IF EXISTS compliance_checks;
DROP TABLE IF EXISTS opt_outs;
DROP TABLE IF EXISTS conversations;
DROP TABLE IF EXISTS campaigns;
DROP TABLE IF EXISTS leads;
DROP TABLE IF EXISTS actions;
DROP TABLE IF EXISTS call_records;
DROP TABLE IF EXISTS agent_versions;
DROP TABLE IF EXISTS agent_memory;
DROP TABLE IF EXISTS patterns;
DROP TABLE IF EXISTS experiments;
DROP TABLE IF EXISTS analytics;
DROP TABLE IF EXISTS users;

-- Re-enable foreign key constraints
PRAGMA foreign_keys = ON;

-- Verify remaining tables (should only be JobHunt AI tables)
SELECT 'REMAINING TABLES:' as message;
SELECT name FROM sqlite_master WHERE type='table' ORDER BY name;
