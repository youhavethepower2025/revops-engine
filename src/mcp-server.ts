/**
 * RevOps MCP Server - Durable Object Implementation
 *
 * Each tenant gets their own Durable Object instance acting as an MCP server.
 * Provides native CRM tools compatible with Salesforce API.
 */

import { DurableObject } from 'cloudflare:workers';
import type { Env, MCPRequest, MCPResponse, MCPTool, SFContact, SFAccount, SFOpportunity, SFTask } from './types';

export class MCPServer extends DurableObject {
  private tenantId: string;
  private db: D1Database;
  private cache: KVNamespace;

  constructor(ctx: DurableObjectState, env: Env) {
    super(ctx, env);
    this.db = env.DB;
    this.cache = env.CACHE;

    // Extract tenant ID from Durable Object ID
    this.tenantId = ctx.id.toString().split(':')[1] || 'unknown';
  }

  /**
   * Handle MCP protocol requests
   */
  async fetch(request: Request): Promise<Response> {
    const url = new URL(request.url);

    // CORS headers for browser clients
    const corsHeaders = {
      'Access-Control-Allow-Origin': '*',
      'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
      'Access-Control-Allow-Headers': 'Content-Type, Authorization',
    };

    if (request.method === 'OPTIONS') {
      return new Response(null, { headers: corsHeaders });
    }

    try {
      // Health check
      if (url.pathname === '/health') {
        return this.jsonResponse({ status: 'healthy', tenant: this.tenantId }, 200, corsHeaders);
      }

      // MCP protocol endpoint
      if (url.pathname === '/mcp' && request.method === 'POST') {
        const mcpRequest: MCPRequest = await request.json();
        const mcpResponse = await this.handleMCPRequest(mcpRequest);
        return this.jsonResponse(mcpResponse, 200, corsHeaders);
      }

      // List available tools
      if (url.pathname === '/tools' && request.method === 'GET') {
        const tools = this.getAvailableTools();
        return this.jsonResponse({ tools }, 200, corsHeaders);
      }

      return this.jsonResponse({ error: 'Not found' }, 404, corsHeaders);
    } catch (error: any) {
      console.error('MCP Server error:', error);
      return this.jsonResponse(
        { error: error.message || 'Internal server error' },
        500,
        corsHeaders
      );
    }
  }

  /**
   * Handle MCP JSON-RPC requests
   */
  private async handleMCPRequest(request: MCPRequest): Promise<MCPResponse> {
    const { id, method, params } = request;

    try {
      // MCP protocol methods
      switch (method) {
        case 'initialize':
          return this.createResponse(id, {
            protocolVersion: '2024-11-05',
            capabilities: {
              tools: {},
            },
            serverInfo: {
              name: 'RevOps CRM MCP Server',
              version: '1.0.0',
            },
          });

        case 'tools/list':
          return this.createResponse(id, {
            tools: this.getAvailableTools(),
          });

        case 'tools/call':
          const result = await this.executeTool(params.name, params.arguments);
          return this.createResponse(id, {
            content: [
              {
                type: 'text',
                text: JSON.stringify(result, null, 2),
              },
            ],
          });

        default:
          return this.createErrorResponse(id, -32601, `Method not found: ${method}`);
      }
    } catch (error: any) {
      console.error('MCP request error:', error);
      return this.createErrorResponse(id, -32603, error.message);
    }
  }

  /**
   * Execute CRM tool
   */
  private async executeTool(toolName: string, args: any): Promise<any> {
    const startTime = Date.now();

    try {
      let result;

      switch (toolName) {
        case 'create_contact':
          result = await this.createContact(args);
          break;
        case 'get_contact':
          result = await this.getContact(args);
          break;
        case 'search_contacts':
          result = await this.searchContacts(args);
          break;
        case 'update_contact':
          result = await this.updateContact(args);
          break;

        case 'create_account':
          result = await this.createAccount(args);
          break;
        case 'get_account':
          result = await this.getAccount(args);
          break;
        case 'search_accounts':
          result = await this.searchAccounts(args);
          break;

        case 'create_opportunity':
          result = await this.createOpportunity(args);
          break;
        case 'get_opportunity':
          result = await this.getOpportunity(args);
          break;
        case 'update_opportunity_stage':
          result = await this.updateOpportunityStage(args);
          break;
        case 'search_opportunities':
          result = await this.searchOpportunities(args);
          break;

        case 'create_task':
          result = await this.createTask(args);
          break;
        case 'get_tasks':
          result = await this.getTasks(args);
          break;

        default:
          throw new Error(`Unknown tool: ${toolName}`);
      }

      // Log usage
      const responseTime = Date.now() - startTime;
      await this.logUsage(toolName, 200, responseTime);

      return result;
    } catch (error: any) {
      await this.logUsage(toolName, 500, Date.now() - startTime);
      throw error;
    }
  }

  /**
   * Get list of available MCP tools
   */
  private getAvailableTools(): MCPTool[] {
    return [
      {
        name: 'create_contact',
        description: 'Create a new contact in the CRM',
        inputSchema: {
          type: 'object',
          properties: {
            FirstName: { type: 'string', description: 'Contact first name' },
            LastName: { type: 'string', description: 'Contact last name' },
            Email: { type: 'string', description: 'Email address' },
            Phone: { type: 'string', description: 'Phone number' },
            AccountId: { type: 'string', description: 'Associated account ID' },
            Title: { type: 'string', description: 'Job title' },
            Department: { type: 'string', description: 'Department' },
            LeadSource: { type: 'string', description: 'How contact was acquired' },
          },
          required: ['LastName'],
        },
      },
      {
        name: 'get_contact',
        description: 'Get contact details by ID',
        inputSchema: {
          type: 'object',
          properties: {
            Id: { type: 'string', description: 'Contact ID' },
          },
          required: ['Id'],
        },
      },
      {
        name: 'search_contacts',
        description: 'Search contacts by various criteria',
        inputSchema: {
          type: 'object',
          properties: {
            email: { type: 'string', description: 'Search by email' },
            phone: { type: 'string', description: 'Search by phone' },
            name: { type: 'string', description: 'Search by name' },
            accountId: { type: 'string', description: 'Filter by account' },
            limit: { type: 'number', description: 'Max results', default: 10 },
          },
        },
      },
      {
        name: 'update_contact',
        description: 'Update contact fields',
        inputSchema: {
          type: 'object',
          properties: {
            Id: { type: 'string', description: 'Contact ID' },
            FirstName: { type: 'string' },
            LastName: { type: 'string' },
            Email: { type: 'string' },
            Phone: { type: 'string' },
            Title: { type: 'string' },
          },
          required: ['Id'],
        },
      },
      {
        name: 'create_account',
        description: 'Create a new account (company)',
        inputSchema: {
          type: 'object',
          properties: {
            Name: { type: 'string', description: 'Company name' },
            Industry: { type: 'string', description: 'Industry' },
            AnnualRevenue: { type: 'number', description: 'Annual revenue' },
            NumberOfEmployees: { type: 'number', description: 'Employee count' },
            Website: { type: 'string', description: 'Company website' },
            Phone: { type: 'string', description: 'Main phone number' },
          },
          required: ['Name'],
        },
      },
      {
        name: 'get_account',
        description: 'Get account details by ID',
        inputSchema: {
          type: 'object',
          properties: {
            Id: { type: 'string', description: 'Account ID' },
          },
          required: ['Id'],
        },
      },
      {
        name: 'search_accounts',
        description: 'Search accounts by name or industry',
        inputSchema: {
          type: 'object',
          properties: {
            name: { type: 'string', description: 'Search by name' },
            industry: { type: 'string', description: 'Filter by industry' },
            limit: { type: 'number', description: 'Max results', default: 10 },
          },
        },
      },
      {
        name: 'create_opportunity',
        description: 'Create a new sales opportunity',
        inputSchema: {
          type: 'object',
          properties: {
            Name: { type: 'string', description: 'Opportunity name' },
            AccountId: { type: 'string', description: 'Associated account' },
            StageName: { type: 'string', description: 'Pipeline stage' },
            Amount: { type: 'number', description: 'Deal value' },
            CloseDate: { type: 'string', description: 'Expected close date (YYYY-MM-DD)' },
            Probability: { type: 'number', description: 'Win probability 0-100' },
            Type: { type: 'string', description: 'Opportunity type' },
          },
          required: ['Name', 'StageName', 'CloseDate'],
        },
      },
      {
        name: 'get_opportunity',
        description: 'Get opportunity details by ID',
        inputSchema: {
          type: 'object',
          properties: {
            Id: { type: 'string', description: 'Opportunity ID' },
          },
          required: ['Id'],
        },
      },
      {
        name: 'update_opportunity_stage',
        description: 'Update opportunity pipeline stage',
        inputSchema: {
          type: 'object',
          properties: {
            Id: { type: 'string', description: 'Opportunity ID' },
            StageName: { type: 'string', description: 'New stage name' },
            notes: { type: 'string', description: 'Notes about stage change' },
          },
          required: ['Id', 'StageName'],
        },
      },
      {
        name: 'search_opportunities',
        description: 'Search opportunities with filters',
        inputSchema: {
          type: 'object',
          properties: {
            accountId: { type: 'string', description: 'Filter by account' },
            stage: { type: 'string', description: 'Filter by stage' },
            minAmount: { type: 'number', description: 'Minimum deal value' },
            limit: { type: 'number', description: 'Max results', default: 20 },
          },
        },
      },
      {
        name: 'create_task',
        description: 'Create a new task',
        inputSchema: {
          type: 'object',
          properties: {
            Subject: { type: 'string', description: 'Task subject' },
            WhoId: { type: 'string', description: 'Related contact ID' },
            WhatId: { type: 'string', description: 'Related account/opportunity ID' },
            Status: { type: 'string', description: 'Task status', default: 'Not Started' },
            Priority: { type: 'string', description: 'Priority level', default: 'Normal' },
            ActivityDate: { type: 'string', description: 'Due date (YYYY-MM-DD)' },
            Description: { type: 'string', description: 'Task description' },
          },
          required: ['Subject'],
        },
      },
      {
        name: 'get_tasks',
        description: 'Get tasks with optional filters',
        inputSchema: {
          type: 'object',
          properties: {
            status: { type: 'string', description: 'Filter by status' },
            limit: { type: 'number', description: 'Max results', default: 20 },
          },
        },
      },
    ];
  }

  // ========================================================================
  // CONTACT OPERATIONS
  // ========================================================================

  private async createContact(args: Partial<SFContact>): Promise<SFContact> {
    const id = this.generateSalesforceId('003');
    const now = new Date().toISOString();

    const contact: SFContact = {
      Id: id,
      tenant_id: this.tenantId,
      LastName: args.LastName!,
      FirstName: args.FirstName,
      Email: args.Email,
      Phone: args.Phone,
      AccountId: args.AccountId,
      Title: args.Title,
      Department: args.Department,
      LeadSource: args.LeadSource,
      CreatedDate: now,
      LastModifiedDate: now,
    };

    await this.db
      .prepare(
        `INSERT INTO sf_contacts (Id, tenant_id, FirstName, LastName, Email, Phone, AccountId, Title, Department, LeadSource)
         VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)`
      )
      .bind(
        contact.Id,
        contact.tenant_id,
        contact.FirstName,
        contact.LastName,
        contact.Email,
        contact.Phone,
        contact.AccountId,
        contact.Title,
        contact.Department,
        contact.LeadSource
      )
      .run();

    // Cache the contact
    await this.cacheContact(contact);

    return contact;
  }

  private async getContact(args: { Id: string }): Promise<SFContact | null> {
    // Try cache first
    const cacheKey = `contact:${args.Id}`;
    const cached = await this.cache.get(cacheKey, 'json');
    if (cached) return cached as SFContact;

    // Query database
    const result = await this.db
      .prepare('SELECT * FROM sf_contacts WHERE Id = ? AND tenant_id = ? AND IsDeleted = 0')
      .bind(args.Id, this.tenantId)
      .first<SFContact>();

    if (result) {
      await this.cacheContact(result);
    }

    return result;
  }

  private async searchContacts(args: {
    email?: string;
    phone?: string;
    name?: string;
    accountId?: string;
    limit?: number;
  }): Promise<SFContact[]> {
    const limit = args.limit || 10;
    let query = 'SELECT * FROM sf_contacts WHERE tenant_id = ? AND IsDeleted = 0';
    const bindings: any[] = [this.tenantId];

    if (args.email) {
      query += ' AND Email LIKE ?';
      bindings.push(`%${args.email}%`);
    }
    if (args.phone) {
      query += ' AND (Phone LIKE ? OR MobilePhone LIKE ?)';
      bindings.push(`%${args.phone}%`, `%${args.phone}%`);
    }
    if (args.name) {
      query += ' AND (FirstName LIKE ? OR LastName LIKE ?)';
      bindings.push(`%${args.name}%`, `%${args.name}%`);
    }
    if (args.accountId) {
      query += ' AND AccountId = ?';
      bindings.push(args.accountId);
    }

    query += ' ORDER BY LastModifiedDate DESC LIMIT ?';
    bindings.push(limit);

    const result = await this.db.prepare(query).bind(...bindings).all<SFContact>();
    return result.results || [];
  }

  private async updateContact(args: { Id: string; [key: string]: any }): Promise<SFContact> {
    const { Id, ...updates } = args;
    const allowedFields = ['FirstName', 'LastName', 'Email', 'Phone', 'Title', 'Department'];

    const setClauses: string[] = [];
    const bindings: any[] = [];

    Object.entries(updates).forEach(([key, value]) => {
      if (allowedFields.includes(key)) {
        setClauses.push(`${key} = ?`);
        bindings.push(value);
      }
    });

    if (setClauses.length === 0) {
      throw new Error('No valid fields to update');
    }

    bindings.push(Id, this.tenantId);

    await this.db
      .prepare(`UPDATE sf_contacts SET ${setClauses.join(', ')}, LastModifiedDate = datetime('now') WHERE Id = ? AND tenant_id = ?`)
      .bind(...bindings)
      .run();

    // Invalidate cache
    await this.cache.delete(`contact:${Id}`);

    // Return updated contact
    return (await this.getContact({ Id }))!;
  }

  // ========================================================================
  // ACCOUNT OPERATIONS
  // ========================================================================

  private async createAccount(args: Partial<SFAccount>): Promise<SFAccount> {
    const id = this.generateSalesforceId('001');
    const now = new Date().toISOString();

    const account: SFAccount = {
      Id: id,
      tenant_id: this.tenantId,
      Name: args.Name!,
      Industry: args.Industry,
      AnnualRevenue: args.AnnualRevenue,
      NumberOfEmployees: args.NumberOfEmployees,
      Website: args.Website,
      Phone: args.Phone,
      CreatedDate: now,
      LastModifiedDate: now,
    };

    await this.db
      .prepare(
        `INSERT INTO sf_accounts (Id, tenant_id, Name, Industry, AnnualRevenue, NumberOfEmployees, Website, Phone)
         VALUES (?, ?, ?, ?, ?, ?, ?, ?)`
      )
      .bind(
        account.Id,
        account.tenant_id,
        account.Name,
        account.Industry,
        account.AnnualRevenue,
        account.NumberOfEmployees,
        account.Website,
        account.Phone
      )
      .run();

    await this.cache.put(`account:${id}`, JSON.stringify(account), { expirationTtl: 300 });

    return account;
  }

  private async getAccount(args: { Id: string }): Promise<SFAccount | null> {
    const cached = await this.cache.get(`account:${args.Id}`, 'json');
    if (cached) return cached as SFAccount;

    const result = await this.db
      .prepare('SELECT * FROM sf_accounts WHERE Id = ? AND tenant_id = ? AND IsDeleted = 0')
      .bind(args.Id, this.tenantId)
      .first<SFAccount>();

    if (result) {
      await this.cache.put(`account:${args.Id}`, JSON.stringify(result), { expirationTtl: 300 });
    }

    return result;
  }

  private async searchAccounts(args: { name?: string; industry?: string; limit?: number }): Promise<SFAccount[]> {
    const limit = args.limit || 10;
    let query = 'SELECT * FROM sf_accounts WHERE tenant_id = ? AND IsDeleted = 0';
    const bindings: any[] = [this.tenantId];

    if (args.name) {
      query += ' AND Name LIKE ?';
      bindings.push(`%${args.name}%`);
    }
    if (args.industry) {
      query += ' AND Industry = ?';
      bindings.push(args.industry);
    }

    query += ' ORDER BY LastModifiedDate DESC LIMIT ?';
    bindings.push(limit);

    const result = await this.db.prepare(query).bind(...bindings).all<SFAccount>();
    return result.results || [];
  }

  // ========================================================================
  // OPPORTUNITY OPERATIONS
  // ========================================================================

  private async createOpportunity(args: Partial<SFOpportunity>): Promise<SFOpportunity> {
    const id = this.generateSalesforceId('006');
    const now = new Date().toISOString();

    const opportunity: SFOpportunity = {
      Id: id,
      tenant_id: this.tenantId,
      Name: args.Name!,
      StageName: args.StageName!,
      CloseDate: args.CloseDate!,
      AccountId: args.AccountId,
      Amount: args.Amount,
      Probability: args.Probability,
      Type: args.Type,
      CreatedDate: now,
      LastModifiedDate: now,
    };

    await this.db
      .prepare(
        `INSERT INTO sf_opportunities (Id, tenant_id, AccountId, Name, StageName, Amount, Probability, CloseDate, Type)
         VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)`
      )
      .bind(
        opportunity.Id,
        opportunity.tenant_id,
        opportunity.AccountId,
        opportunity.Name,
        opportunity.StageName,
        opportunity.Amount,
        opportunity.Probability,
        opportunity.CloseDate,
        opportunity.Type
      )
      .run();

    return opportunity;
  }

  private async getOpportunity(args: { Id: string }): Promise<SFOpportunity | null> {
    return await this.db
      .prepare('SELECT * FROM sf_opportunities WHERE Id = ? AND tenant_id = ? AND IsDeleted = 0')
      .bind(args.Id, this.tenantId)
      .first<SFOpportunity>();
  }

  private async updateOpportunityStage(args: { Id: string; StageName: string; notes?: string }): Promise<SFOpportunity> {
    await this.db
      .prepare(`UPDATE sf_opportunities SET StageName = ?, LastModifiedDate = datetime('now') WHERE Id = ? AND tenant_id = ?`)
      .bind(args.StageName, args.Id, this.tenantId)
      .run();

    // Mark as closed if stage is Closed Won or Closed Lost
    if (args.StageName === 'Closed Won') {
      await this.db
        .prepare('UPDATE sf_opportunities SET IsClosed = 1, IsWon = 1 WHERE Id = ? AND tenant_id = ?')
        .bind(args.Id, this.tenantId)
        .run();
    } else if (args.StageName === 'Closed Lost') {
      await this.db
        .prepare('UPDATE sf_opportunities SET IsClosed = 1, IsWon = 0 WHERE Id = ? AND tenant_id = ?')
        .bind(args.Id, this.tenantId)
        .run();
    }

    return (await this.getOpportunity({ Id: args.Id }))!;
  }

  private async searchOpportunities(args: {
    accountId?: string;
    stage?: string;
    minAmount?: number;
    limit?: number;
  }): Promise<SFOpportunity[]> {
    const limit = args.limit || 20;
    let query = 'SELECT * FROM sf_opportunities WHERE tenant_id = ? AND IsDeleted = 0';
    const bindings: any[] = [this.tenantId];

    if (args.accountId) {
      query += ' AND AccountId = ?';
      bindings.push(args.accountId);
    }
    if (args.stage) {
      query += ' AND StageName = ?';
      bindings.push(args.stage);
    }
    if (args.minAmount) {
      query += ' AND Amount >= ?';
      bindings.push(args.minAmount);
    }

    query += ' ORDER BY CloseDate ASC LIMIT ?';
    bindings.push(limit);

    const result = await this.db.prepare(query).bind(...bindings).all<SFOpportunity>();
    return result.results || [];
  }

  // ========================================================================
  // TASK OPERATIONS
  // ========================================================================

  private async createTask(args: Partial<SFTask>): Promise<SFTask> {
    const id = this.generateSalesforceId('00T');
    const now = new Date().toISOString();

    const task: SFTask = {
      Id: id,
      tenant_id: this.tenantId,
      Subject: args.Subject!,
      WhoId: args.WhoId,
      WhatId: args.WhatId,
      Status: args.Status || 'Not Started',
      Priority: args.Priority || 'Normal',
      ActivityDate: args.ActivityDate,
      Description: args.Description,
      CreatedDate: now,
    };

    await this.db
      .prepare(
        `INSERT INTO sf_tasks (Id, tenant_id, WhoId, WhatId, Subject, Status, Priority, ActivityDate, Description)
         VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)`
      )
      .bind(
        task.Id,
        task.tenant_id,
        task.WhoId,
        task.WhatId,
        task.Subject,
        task.Status,
        task.Priority,
        task.ActivityDate,
        task.Description
      )
      .run();

    return task;
  }

  private async getTasks(args: { status?: string; limit?: number }): Promise<SFTask[]> {
    const limit = args.limit || 20;
    let query = 'SELECT * FROM sf_tasks WHERE tenant_id = ? AND IsDeleted = 0';
    const bindings: any[] = [this.tenantId];

    if (args.status) {
      query += ' AND Status = ?';
      bindings.push(args.status);
    }

    query += ' ORDER BY ActivityDate ASC LIMIT ?';
    bindings.push(limit);

    const result = await this.db.prepare(query).bind(...bindings).all<SFTask>();
    return result.results || [];
  }

  // ========================================================================
  // HELPER METHODS
  // ========================================================================

  private generateSalesforceId(prefix: string): string {
    const chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789';
    let id = prefix;
    for (let i = 0; i < 15; i++) {
      id += chars.charAt(Math.floor(Math.random() * chars.length));
    }
    return id;
  }

  private async cacheContact(contact: SFContact): Promise<void> {
    await this.cache.put(`contact:${contact.Id}`, JSON.stringify(contact), {
      expirationTtl: 300, // 5 minutes
    });
  }

  private async logUsage(toolName: string, statusCode: number, responseTimeMs: number): Promise<void> {
    try {
      await this.db
        .prepare(
          `INSERT INTO api_usage (tenant_id, tool_name, status_code, response_time_ms)
           VALUES (?, ?, ?, ?)`
        )
        .bind(this.tenantId, toolName, statusCode, responseTimeMs)
        .run();
    } catch (error) {
      console.error('Failed to log usage:', error);
    }
  }

  private createResponse(id: number | string, result: any): MCPResponse {
    return {
      jsonrpc: '2.0',
      id,
      result,
    };
  }

  private createErrorResponse(id: number | string, code: number, message: string): MCPResponse {
    return {
      jsonrpc: '2.0',
      id,
      error: {
        code,
        message,
      },
    };
  }

  private jsonResponse(data: any, status: number = 200, headers: Record<string, string> = {}): Response {
    return new Response(JSON.stringify(data), {
      status,
      headers: {
        'Content-Type': 'application/json',
        ...headers,
      },
    });
  }
}
