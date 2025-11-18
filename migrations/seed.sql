-- RevOps MCP Engine - Seed Data for Development/Testing

-- Create demo tenant
INSERT INTO tenants (id, name, domain, subscription_tier, is_active)
VALUES ('demo-tenant-001', 'Acme Corporation', 'acme.com', 'professional', 1);

-- Create demo accounts
INSERT INTO sf_accounts (Id, tenant_id, Name, Type, Industry, AnnualRevenue, NumberOfEmployees, BillingCity, BillingState, BillingCountry, Phone, Website)
VALUES
    ('001demo00001', 'demo-tenant-001', 'Enterprise Tech Inc', 'Customer', 'Technology', 50000000, 500, 'San Francisco', 'CA', 'USA', '415-555-0100', 'https://enterprisetech.example'),
    ('001demo00002', 'demo-tenant-001', 'Global Retail Co', 'Prospect', 'Retail', 25000000, 1200, 'New York', 'NY', 'USA', '212-555-0200', 'https://globalretail.example'),
    ('001demo00003', 'demo-tenant-001', 'FinTech Solutions', 'Customer', 'Financial Services', 75000000, 300, 'Austin', 'TX', 'USA', '512-555-0300', 'https://fintechsolutions.example');

-- Create demo contacts
INSERT INTO sf_contacts (Id, tenant_id, AccountId, FirstName, LastName, Email, Phone, Title, Department, LeadSource, MailingCity, MailingState, MailingCountry)
VALUES
    ('003demo00001', 'demo-tenant-001', '001demo00001', 'Sarah', 'Johnson', 'sarah.johnson@enterprisetech.example', '415-555-0101', 'VP of Sales', 'Sales', 'Web', 'San Francisco', 'CA', 'USA'),
    ('003demo00002', 'demo-tenant-001', '001demo00001', 'Michael', 'Chen', 'michael.chen@enterprisetech.example', '415-555-0102', 'CTO', 'Engineering', 'Partner Referral', 'San Francisco', 'CA', 'USA'),
    ('003demo00003', 'demo-tenant-001', '001demo00002', 'Emily', 'Rodriguez', 'emily.rodriguez@globalretail.example', '212-555-0201', 'Director of Operations', 'Operations', 'Web', 'New York', 'NY', 'USA'),
    ('003demo00004', 'demo-tenant-001', '001demo00003', 'David', 'Kim', 'david.kim@fintechsolutions.example', '512-555-0301', 'Chief Innovation Officer', 'Product', 'Web', 'Austin', 'TX', 'USA'),
    ('003demo00005', 'demo-tenant-001', '001demo00003', 'Jennifer', 'Martinez', 'jennifer.martinez@fintechsolutions.example', '512-555-0302', 'Head of Engineering', 'Engineering', 'Partner Referral', 'Austin', 'TX', 'USA');

-- Create demo opportunities
INSERT INTO sf_opportunities (Id, tenant_id, AccountId, Name, StageName, Amount, Probability, CloseDate, Type, LeadSource)
VALUES
    ('006demo00001', 'demo-tenant-001', '001demo00001', 'Enterprise Tech - Platform Expansion', 'Proposal/Price Quote', 150000, 75, date('now', '+30 days'), 'Existing Business', 'Web'),
    ('006demo00002', 'demo-tenant-001', '001demo00002', 'Global Retail - New Implementation', 'Qualification', 250000, 40, date('now', '+60 days'), 'New Business', 'Web'),
    ('006demo00003', 'demo-tenant-001', '001demo00003', 'FinTech - Annual Renewal', 'Negotiation/Review', 200000, 90, date('now', '+15 days'), 'Renewal', 'Partner Referral'),
    ('006demo00004', 'demo-tenant-001', '001demo00001', 'Enterprise Tech - Integration Services', 'Closed Won', 75000, 100, date('now', '-5 days'), 'Existing Business', 'Web');

UPDATE sf_opportunities SET IsClosed = 1, IsWon = 1 WHERE Id = '006demo00004';

-- Create demo tasks
INSERT INTO sf_tasks (Id, tenant_id, WhoId, WhatId, Subject, Status, Priority, ActivityDate, Description)
VALUES
    ('00Tdemo00001', 'demo-tenant-001', '003demo00001', '006demo00001', 'Follow up on proposal questions', 'In Progress', 'High', date('now', '+2 days'), 'Sarah had questions about implementation timeline'),
    ('00Tdemo00002', 'demo-tenant-001', '003demo00003', '006demo00002', 'Schedule discovery call', 'Not Started', 'High', date('now', '+1 day'), 'Initial discovery to understand requirements'),
    ('00Tdemo00003', 'demo-tenant-001', '003demo00004', '006demo00003', 'Send renewal contract', 'Completed', 'High', date('now', '-2 days'), 'Contract sent and signed'),
    ('00Tdemo00004', 'demo-tenant-001', '003demo00002', '001demo00001', 'Technical architecture review', 'Not Started', 'Normal', date('now', '+7 days'), 'Review integration requirements with CTO');

UPDATE sf_tasks SET IsClosed = 1 WHERE Id = '00Tdemo00003';

-- Create demo events
INSERT INTO sf_events (Id, tenant_id, WhoId, WhatId, Subject, StartDateTime, EndDateTime, Location)
VALUES
    ('00Udemo00001', 'demo-tenant-001', '003demo00001', '006demo00001', 'Proposal Review Meeting', datetime('now', '+3 days', '+10 hours'), datetime('now', '+3 days', '+11 hours'), 'Zoom'),
    ('00Udemo00002', 'demo-tenant-001', '003demo00003', '006demo00002', 'Discovery Call', datetime('now', '+1 day', '+14 hours'), datetime('now', '+1 day', '+15 hours'), 'Google Meet'),
    ('00Udemo00003', 'demo-tenant-001', '003demo00004', '006demo00003', 'Contract Signing', datetime('now', '+15 days', '+10 hours'), datetime('now', '+15 days', '+11 hours'), 'FinTech HQ');

-- Create custom field definitions for demo
INSERT INTO custom_field_definitions (id, tenant_id, object_name, api_name, label, field_type, is_required, help_text)
VALUES
    ('cfd-001', 'demo-tenant-001', 'Contact', 'linkedin_url__c', 'LinkedIn URL', 'url', 0, 'Contact LinkedIn profile URL'),
    ('cfd-002', 'demo-tenant-001', 'Contact', 'lead_score__c', 'Lead Score', 'number', 0, 'Calculated lead score 0-100'),
    ('cfd-003', 'demo-tenant-001', 'Opportunity', 'contract_term__c', 'Contract Term (Months)', 'number', 0, 'Length of contract in months'),
    ('cfd-004', 'demo-tenant-001', 'Opportunity', 'implementation_complexity__c', 'Implementation Complexity', 'picklist', 0, 'Expected implementation complexity'),
    ('cfd-005', 'demo-tenant-001', 'Account', 'customer_tier__c', 'Customer Tier', 'picklist', 0, 'Customer segmentation tier');

-- Create picklist values for custom fields
INSERT INTO picklist_values (id, tenant_id, object_name, field_name, value, label, sort_order, is_active)
VALUES
    ('pv-001', 'demo-tenant-001', 'Opportunity', 'implementation_complexity__c', 'Low', 'Low', 1, 1),
    ('pv-002', 'demo-tenant-001', 'Opportunity', 'implementation_complexity__c', 'Medium', 'Medium', 2, 1),
    ('pv-003', 'demo-tenant-001', 'Opportunity', 'implementation_complexity__c', 'High', 'High', 3, 1),
    ('pv-004', 'demo-tenant-001', 'Account', 'customer_tier__c', 'Enterprise', 'Enterprise', 1, 1),
    ('pv-005', 'demo-tenant-001', 'Account', 'customer_tier__c', 'Mid-Market', 'Mid-Market', 2, 1),
    ('pv-006', 'demo-tenant-001', 'Account', 'customer_tier__c', 'SMB', 'SMB', 3, 1);
