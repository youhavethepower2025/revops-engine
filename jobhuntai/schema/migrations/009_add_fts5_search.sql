-- Migration 009: Add FTS5 full-text search for roles
-- Enables AI-powered semantic search across job listings
-- Searches job titles, descriptions, and requirements

-- Create FTS5 virtual table (SQLite full-text search engine)
CREATE VIRTUAL TABLE IF NOT EXISTS roles_fts USING fts5(
  role_title,
  description,
  requirements,
  content='roles',           -- Points to the roles table
  content_rowid='rowid'      -- Maps to roles.rowid for JOIN operations
);

-- Populate FTS table from existing roles
INSERT INTO roles_fts(rowid, role_title, description, requirements)
SELECT rowid, role_title, description, requirements
FROM roles;

-- Trigger: Keep FTS table in sync on INSERT
CREATE TRIGGER IF NOT EXISTS roles_fts_insert AFTER INSERT ON roles BEGIN
  INSERT INTO roles_fts(rowid, role_title, description, requirements)
  VALUES (new.rowid, new.role_title, new.description, new.requirements);
END;

-- Trigger: Keep FTS table in sync on UPDATE
CREATE TRIGGER IF NOT EXISTS roles_fts_update AFTER UPDATE ON roles BEGIN
  UPDATE roles_fts
  SET role_title = new.role_title,
      description = new.description,
      requirements = new.requirements
  WHERE rowid = new.rowid;
END;

-- Trigger: Keep FTS table in sync on DELETE
CREATE TRIGGER IF NOT EXISTS roles_fts_delete AFTER DELETE ON roles BEGIN
  DELETE FROM roles_fts WHERE rowid = old.rowid;
END;

-- Example queries (for documentation):
-- Find ML roles with Python:
--   SELECT r.* FROM roles r
--   JOIN roles_fts fts ON r.rowid = fts.rowid
--   WHERE fts MATCH 'machine learning AND python'
--   ORDER BY fts.rank DESC;
--
-- Search with wildcards (typo-tolerant):
--   WHERE fts MATCH 'mach* learn*'
--
-- Phrase search:
--   WHERE fts MATCH '"distributed systems"'
