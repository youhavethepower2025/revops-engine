// Type definitions for RevOps MCP Engine

export interface Env {
  DB: D1Database;
  CACHE: KVNamespace;
  MCP_SERVER: DurableObjectNamespace;
  ANALYTICS: AnalyticsEngineDataset;
  FILES?: R2Bucket;
  JWT_SECRET: string;
  OPENAI_API_KEY?: string;
  ANTHROPIC_API_KEY?: string;
}

// Salesforce-compatible types
export interface SFContact {
  Id: string;
  tenant_id: string;
  AccountId?: string;
  FirstName?: string;
  LastName: string;
  Email?: string;
  Phone?: string;
  MobilePhone?: string;
  Title?: string;
  Department?: string;
  MailingStreet?: string;
  MailingCity?: string;
  MailingState?: string;
  MailingPostalCode?: string;
  MailingCountry?: string;
  LeadSource?: string;
  OwnerId?: string;
  Description?: string;
  CreatedDate?: string;
  LastModifiedDate?: string;
  IsDeleted?: number;
  custom_fields?: string;
}

export interface SFAccount {
  Id: string;
  tenant_id: string;
  Name: string;
  Type?: string;
  Industry?: string;
  AnnualRevenue?: number;
  NumberOfEmployees?: number;
  BillingStreet?: string;
  BillingCity?: string;
  BillingState?: string;
  BillingPostalCode?: string;
  BillingCountry?: string;
  Phone?: string;
  Website?: string;
  OwnerId?: string;
  ParentAccountId?: string;
  Description?: string;
  CreatedDate?: string;
  LastModifiedDate?: string;
  IsDeleted?: number;
  custom_fields?: string;
}

export interface SFOpportunity {
  Id: string;
  tenant_id: string;
  AccountId?: string;
  Name: string;
  StageName: string;
  Amount?: number;
  Probability?: number;
  CloseDate: string;
  ForecastCategory?: string;
  Type?: string;
  LeadSource?: string;
  NextStep?: string;
  Description?: string;
  OwnerId?: string;
  CreatedDate?: string;
  LastModifiedDate?: string;
  IsClosed?: number;
  IsWon?: number;
  IsDeleted?: number;
  custom_fields?: string;
}

export interface SFTask {
  Id: string;
  tenant_id: string;
  WhoId?: string;
  WhatId?: string;
  Subject: string;
  Status: string;
  Priority?: string;
  ActivityDate?: string;
  Description?: string;
  OwnerId?: string;
  CreatedDate?: string;
  IsClosed?: number;
  IsDeleted?: number;
  custom_fields?: string;
}

export interface SFEvent {
  Id: string;
  tenant_id: string;
  WhoId?: string;
  WhatId?: string;
  Subject: string;
  StartDateTime: string;
  EndDateTime: string;
  Location?: string;
  Description?: string;
  OwnerId?: string;
  IsAllDayEvent?: number;
  CreatedDate?: string;
  IsDeleted?: number;
  custom_fields?: string;
}

// MCP Protocol types
export interface MCPRequest {
  jsonrpc: '2.0';
  id: number | string;
  method: string;
  params?: any;
}

export interface MCPResponse {
  jsonrpc: '2.0';
  id: number | string;
  result?: any;
  error?: MCPError;
}

export interface MCPError {
  code: number;
  message: string;
  data?: any;
}

export interface MCPTool {
  name: string;
  description: string;
  inputSchema: {
    type: 'object';
    properties: Record<string, any>;
    required?: string[];
  };
}

// Cache key types
export type CacheKey = `contact:${string}` | `account:${string}` | `opportunity:${string}` | `tenant:${string}`;

// Event types for CDC
export type EventType =
  | 'contact.created'
  | 'contact.updated'
  | 'contact.deleted'
  | 'account.created'
  | 'account.updated'
  | 'account.deleted'
  | 'opportunity.created'
  | 'opportunity.updated'
  | 'opportunity.stage_changed'
  | 'opportunity.closed_won'
  | 'opportunity.closed_lost'
  | 'task.created'
  | 'task.completed';

export interface DomainEvent {
  id: string;
  tenant_id: string;
  event_type: EventType;
  aggregate_type: string;
  aggregate_id: string;
  payload: any;
  metadata?: any;
  occurred_at: string;
}
