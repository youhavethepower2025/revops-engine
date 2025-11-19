-- Migration 006: Job Hunt System - Organizations, Roles, People, Applications
-- Creates organization-first structure for targeted job search

-- ============================================================================
-- USER PROFILE
-- ============================================================================

CREATE TABLE user_profile (
  id TEXT PRIMARY KEY,
  account_id TEXT NOT NULL,

  -- Identity
  full_name TEXT NOT NULL,
  email TEXT NOT NULL,
  phone TEXT,
  location TEXT,
  linkedin_url TEXT,
  github_url TEXT,
  portfolio_url TEXT,

  -- Resume content (JSON for flexibility)
  summary TEXT,
  experience JSON,
  education JSON,
  skills JSON,
  certifications JSON,

  -- Job search preferences
  target_roles JSON,
  target_companies JSON,
  compensation_min INTEGER,
  location_preferences JSON,
  work_authorization TEXT,

  -- Application materials templates
  base_resume_md TEXT,
  base_cover_letter_template TEXT,

  created_at INTEGER NOT NULL,
  updated_at INTEGER NOT NULL,

  FOREIGN KEY (account_id) REFERENCES accounts(id) ON DELETE CASCADE
);

CREATE INDEX idx_user_profile_account ON user_profile(account_id);

-- ============================================================================
-- ORGANIZATIONS (Target companies like Anthropic, xAI, etc.)
-- ============================================================================

CREATE TABLE organizations (
  id TEXT PRIMARY KEY,
  account_id TEXT NOT NULL,

  -- Basic info
  name TEXT NOT NULL,
  domain TEXT,
  linkedin_slug TEXT,

  -- Company details (enriched by Research Agent)
  description TEXT,
  industry TEXT,
  employee_count TEXT,
  funding_stage TEXT,
  tech_stack JSON,
  culture_notes TEXT,

  -- Research metadata
  researched_at INTEGER,
  research_quality_score INTEGER,

  -- Priority & status
  priority INTEGER DEFAULT 0,
  status TEXT DEFAULT 'active',

  notes TEXT,

  created_at INTEGER NOT NULL,
  updated_at INTEGER NOT NULL,

  FOREIGN KEY (account_id) REFERENCES accounts(id) ON DELETE CASCADE
);

CREATE INDEX idx_orgs_account ON organizations(account_id);
CREATE INDEX idx_orgs_priority ON organizations(priority);
CREATE INDEX idx_orgs_status ON organizations(status);
CREATE INDEX idx_orgs_name ON organizations(name);

-- ============================================================================
-- PEOPLE (Hiring managers, recruiters, team leads at organizations)
-- ============================================================================

CREATE TABLE people (
  id TEXT PRIMARY KEY,
  org_id TEXT NOT NULL,
  account_id TEXT NOT NULL,

  -- Identity
  full_name TEXT NOT NULL,
  role_title TEXT,
  email TEXT,
  linkedin_url TEXT,

  -- Context
  department TEXT,
  decision_maker INTEGER DEFAULT 0,
  contact_priority INTEGER DEFAULT 0,

  -- Research notes
  background_notes TEXT,
  common_connections JSON,

  -- Contact status
  contacted_at INTEGER,
  responded_at INTEGER,
  last_interaction TEXT,

  created_at INTEGER NOT NULL,
  updated_at INTEGER NOT NULL,

  FOREIGN KEY (org_id) REFERENCES organizations(id) ON DELETE CASCADE,
  FOREIGN KEY (account_id) REFERENCES accounts(id) ON DELETE CASCADE
);

CREATE INDEX idx_people_org ON people(org_id);
CREATE INDEX idx_people_account ON people(account_id);
CREATE INDEX idx_people_contact_priority ON people(contact_priority DESC);

-- ============================================================================
-- ROLES (Job openings at organizations)
-- ============================================================================

CREATE TABLE roles (
  id TEXT PRIMARY KEY,
  org_id TEXT NOT NULL,
  account_id TEXT NOT NULL,

  -- Role details
  role_title TEXT NOT NULL,
  department TEXT,
  level TEXT,

  -- Job details
  job_url TEXT,
  posted_date INTEGER,
  salary_range TEXT,
  location TEXT,
  work_arrangement TEXT,

  -- Requirements (enriched by Research Agent)
  requirements JSON,
  nice_to_haves JSON,
  tech_stack JSON,

  -- Fit analysis (from Strategy Agent)
  fit_score INTEGER,
  fit_reasoning TEXT,
  positioning_strategy TEXT,
  key_experiences_to_highlight JSON,
  potential_concerns JSON,

  -- Application status
  status TEXT DEFAULT 'identified',
  applied_at INTEGER,

  -- Hiring contacts
  hiring_manager_id TEXT,
  recruiter_id TEXT,

  notes TEXT,

  created_at INTEGER NOT NULL,
  updated_at INTEGER NOT NULL,

  FOREIGN KEY (org_id) REFERENCES organizations(id) ON DELETE CASCADE,
  FOREIGN KEY (account_id) REFERENCES accounts(id) ON DELETE CASCADE,
  FOREIGN KEY (hiring_manager_id) REFERENCES people(id) ON DELETE SET NULL,
  FOREIGN KEY (recruiter_id) REFERENCES people(id) ON DELETE SET NULL
);

CREATE INDEX idx_roles_org ON roles(org_id);
CREATE INDEX idx_roles_account ON roles(account_id);
CREATE INDEX idx_roles_fit_score ON roles(fit_score DESC);
CREATE INDEX idx_roles_status ON roles(status);
CREATE INDEX idx_roles_posted_date ON roles(posted_date DESC);

-- ============================================================================
-- APPLICATIONS (Draft and sent applications)
-- ============================================================================

CREATE TABLE applications (
  id TEXT PRIMARY KEY,
  role_id TEXT NOT NULL,
  org_id TEXT NOT NULL,
  account_id TEXT NOT NULL,

  -- Application content
  cover_letter TEXT NOT NULL,
  resume_version TEXT,
  additional_materials JSON,

  -- Email details (if sent via system)
  email_to TEXT,
  email_subject TEXT,
  email_body TEXT,

  -- Tracking
  status TEXT DEFAULT 'draft',
  applied_via TEXT,
  referrer_name TEXT,

  -- Response tracking
  sent_at INTEGER,
  opened_at INTEGER,
  responded_at INTEGER,
  response_type TEXT,

  notes TEXT,

  created_at INTEGER NOT NULL,
  updated_at INTEGER NOT NULL,

  FOREIGN KEY (role_id) REFERENCES roles(id) ON DELETE CASCADE,
  FOREIGN KEY (org_id) REFERENCES organizations(id) ON DELETE CASCADE,
  FOREIGN KEY (account_id) REFERENCES accounts(id) ON DELETE CASCADE
);

CREATE INDEX idx_applications_role ON applications(role_id);
CREATE INDEX idx_applications_org ON applications(org_id);
CREATE INDEX idx_applications_account ON applications(account_id);
CREATE INDEX idx_applications_status ON applications(status);
CREATE INDEX idx_applications_sent_at ON applications(sent_at DESC);

-- ============================================================================
-- INTERVIEWS
-- ============================================================================

CREATE TABLE interviews (
  id TEXT PRIMARY KEY,
  role_id TEXT NOT NULL,
  org_id TEXT NOT NULL,
  account_id TEXT NOT NULL,

  -- Interview details
  interview_type TEXT NOT NULL,
  interviewer_id TEXT,
  interviewer_name TEXT,

  scheduled_at INTEGER NOT NULL,
  duration_minutes INTEGER,
  location TEXT,
  timezone TEXT,

  -- Preparation
  prep_notes TEXT,
  questions_to_ask JSON,
  topics_to_cover JSON,

  -- Post-interview
  status TEXT DEFAULT 'scheduled',
  interview_notes TEXT,
  feedback_received TEXT,
  follow_up_sent_at INTEGER,

  created_at INTEGER NOT NULL,
  updated_at INTEGER NOT NULL,

  FOREIGN KEY (role_id) REFERENCES roles(id) ON DELETE CASCADE,
  FOREIGN KEY (org_id) REFERENCES organizations(id) ON DELETE CASCADE,
  FOREIGN KEY (account_id) REFERENCES accounts(id) ON DELETE CASCADE,
  FOREIGN KEY (interviewer_id) REFERENCES people(id) ON DELETE SET NULL
);

CREATE INDEX idx_interviews_role ON interviews(role_id);
CREATE INDEX idx_interviews_org ON interviews(org_id);
CREATE INDEX idx_interviews_account ON interviews(account_id);
CREATE INDEX idx_interviews_scheduled_at ON interviews(scheduled_at);
CREATE INDEX idx_interviews_status ON interviews(status);

-- ============================================================================
-- SEED DATA: John Kruze Profile
-- ============================================================================

-- First, create a test account for John Kruze
INSERT INTO accounts (
  id,
  name,
  settings,
  created_at,
  updated_at
) VALUES (
  'account_john_kruze',
  'John Kruze - Job Hunt',
  '{}',
  strftime('%s', 'now') * 1000,
  strftime('%s', 'now') * 1000
);

-- Then create the user profile linked to this account
INSERT INTO user_profile (
  id,
  account_id,
  full_name,
  email,
  phone,
  location,
  linkedin_url,
  github_url,
  portfolio_url,
  summary,
  skills,
  experience,
  education,
  target_roles,
  target_companies,
  compensation_min,
  location_preferences,
  work_authorization,
  base_cover_letter_template,
  created_at,
  updated_at
) VALUES (
  'profile_john_kruze',
  'account_john_kruze',
  'John Kruze',
  'john.kruze@example.com',
  NULL,
  'Remote / LATAM',
  'https://linkedin.com/in/johnkruze',
  'https://github.com/johnkruze',
  'https://portfolio.example.com',
  'Full-stack AI orchestration architect with 18 months of production deployment experience and 3 years of deep Claude expertise. Rare convergence of: Early MCP adoption (first cohort, November 2024), Production-grade multi-agent systems (live URLs, 13+ days uptime), Cross-domain communication (military → business → technical leadership), Founder velocity (weekend builds to production deployment).',
  '["Python", "FastAPI", "TypeScript", "JavaScript", "PostgreSQL", "SQLite", "MCP Protocol", "Docker", "Docker Compose", "Cloudflare Workers", "Cloudflare D1", "DigitalOcean", "Claude API", "Multi-agent orchestration", "Tool calling", "REST APIs", "WebSockets", "SSE", "JSON-RPC 2.0", "AI Systems", "LLM Integration", "Edge Computing", "Production Infrastructure", "Asyncio", "SQL", "Git", "Linux", "Bash"]',
  '[
    {
      "title": "AI Systems Architect / Founder",
      "company": "Self-directed Projects",
      "duration": "18 months",
      "highlights": [
        "Built 3 production AI orchestration systems with 13+ days continuous uptime",
        "Developed 51 working MCP tools across 8 categories (memory, voice, CRM, deployment, Docker)",
        "First cohort MCP implementation (November 2024)",
        "90-second deployment pipeline to production servers",
        "Multi-tenant architecture designed from day one",
        "$20-35/month operating cost (10-50x more cost-efficient than typical)",
        "Real API integrations: Claude, VAPI, GoHighLevel, Railway, Gmail"
      ]
    },
    {
      "title": "Business Leadership",
      "company": "Various",
      "duration": "13 years",
      "highlights": [
        "Worked with CMOs, CEOs on GTM strategy",
        "Cross-functional communication between technical and business teams",
        "Tony Robbins Platinum (7 years) - high-context entrepreneurial network"
      ]
    },
    {
      "title": "Military Service",
      "company": "US Military",
      "duration": "7 years",
      "highlights": [
        "Systems thinking and discipline",
        "Leadership under pressure",
        "Complex system orchestration"
      ]
    }
  ]',
  '[
    {
      "degree": "Self-taught",
      "field": "AI Systems & Infrastructure",
      "notes": "Terminal-first opened May 2024, production deployments by November 2025"
    }
  ]',
  '["AI Systems Architect", "Principal AI Engineer", "Staff AI Integration Engineer", "Head of AI Implementation", "AI Platform Lead", "Developer Relations Engineer (AI)", "Technical AI Lead", "AI Orchestration Architect", "MCP Implementation Lead", "Solutions Architect (AI)"]',
  '["Anthropic", "xAI", "OpenAI", "Cloudflare", "Replit", "Cursor", "Modal"]',
  400000,
  '["Remote", "Hybrid (3 days/week max)", "LATAM"]',
  'US Citizen / Authorized to work in US',
  'Dear Hiring Team,

I am reaching out regarding the [ROLE_TITLE] position at [COMPANY_NAME].

[POSITIONING_STRATEGY - to be customized per application]

[KEY_EXPERIENCES_TO_HIGHLIGHT - to be inserted by Outreach Agent]

I would welcome the opportunity to discuss how my experience could contribute to your team.

Best regards,
John Kruze',
  strftime('%s', 'now') * 1000,
  strftime('%s', 'now') * 1000
);
