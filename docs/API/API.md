# RevOps OS API Documentation

AI-native outreach CRM API built on Cloudflare Workers.

## Base URL

**Development:** `https://revopsOS-dev.aijesusbro-brain.workers.dev`

## Authentication

All protected endpoints require a JWT token in the Authorization header:

```
Authorization: Bearer <your-jwt-token>
```

## Endpoints

### Health Check

**GET** `/health`

Check API status.

**Response:**
```json
{
  "status": "ok",
  "environment": "dev"
}
```

### Account Management

#### Create Account

**POST** `/api/accounts`

Create a new account and user.

**Request Body:**
```json
{
  "name": "My Company",
  "email": "user@example.com",
  "password": "securepassword123"
}
```

**Response:**
```json
{
  "account_id": "acc_1234567890",
  "user_id": "user_1234567890",
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "account": {
    "id": "acc_1234567890",
    "name": "My Company"
  }
}
```

**Status Codes:**
- `201` - Account created successfully
- `400` - Missing required fields
- `409` - Email already registered
- `500` - Server error

#### Login

**POST** `/api/login`

Authenticate user and get JWT token.

**Request Body:**
```json
{
  "email": "user@example.com",
  "password": "securepassword123"
}
```

**Response:**
```json
{
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "user_id": "user_1234567890",
  "account_id": "acc_1234567890",
  "account": {
    "id": "acc_1234567890",
    "name": "My Company"
  }
}
```

**Status Codes:**
- `200` - Login successful
- `400` - Missing required fields
- `401` - Invalid credentials
- `500` - Server error

#### Get Account

**GET** `/api/accounts/:id`

Get account details.

**Headers:**
- `Authorization: Bearer <token>`

**Response:**
```json
{
  "id": "acc_1234567890",
  "name": "My Company",
  "settings": {},
  "created_at": 1703123456789
}
```

**Status Codes:**
- `200` - Success
- `403` - Forbidden (not your account)
- `404` - Account not found

### Campaign Management

#### List Campaigns

**GET** `/api/campaigns`

Get all campaigns for the authenticated account.

**Headers:**
- `Authorization: Bearer <token>`

**Response:**
```json
{
  "campaigns": [
    {
      "id": "camp_1234567890",
      "account_id": "acc_1234567890",
      "name": "Q1 Outreach",
      "status": "active",
      "config": {
        "value_proposition": "We help B2B SaaS companies...",
        "differentiators": "Fully autonomous, learns what works...",
        "sender_name": "Alex Morgan",
        "sender_email": "alex@company.com",
        "company_name": "RevOps OS"
      },
      "created_at": 1703123456789,
      "started_at": 1703123456789,
      "completed_at": null
    }
  ]
}
```

#### Create Campaign

**POST** `/api/campaigns`

Create a new campaign.

**Headers:**
- `Authorization: Bearer <token>`
- `Content-Type: application/json`

**Request Body:**
```json
{
  "name": "Q1 Outreach",
  "config": {
    "value_proposition": "We help B2B SaaS companies close more deals with AI-powered outreach",
    "differentiators": "Fully autonomous, learns what works, adapts in real-time",
    "sender_name": "Alex Morgan",
    "sender_email": "alex@company.com",
    "company_name": "RevOps OS"
  }
}
```

**Response:**
```json
{
  "campaign": {
    "id": "camp_1234567890",
    "account_id": "acc_1234567890",
    "name": "Q1 Outreach",
    "status": "draft",
    "config": { /* same as request */ },
    "created_at": 1703123456789,
    "started_at": null,
    "completed_at": null
  }
}
```

#### Get Campaign

**GET** `/api/campaigns/:id`

Get specific campaign details.

**Headers:**
- `Authorization: Bearer <token>`

**Response:**
```json
{
  "campaign": {
    "id": "camp_1234567890",
    "account_id": "acc_1234567890",
    "name": "Q1 Outreach",
    "status": "active",
    "config": { /* campaign config */ },
    "created_at": 1703123456789,
    "started_at": 1703123456789,
    "completed_at": null
  }
}
```

#### Update Campaign

**PATCH** `/api/campaigns/:id`

Update campaign fields.

**Headers:**
- `Authorization: Bearer <token>`
- `Content-Type: application/json`

**Request Body:**
```json
{
  "name": "Updated Campaign Name",
  "status": "paused",
  "config": {
    "value_proposition": "Updated value prop"
  }
}
```

**Response:**
```json
{
  "campaign": {
    "id": "camp_1234567890",
    "name": "Updated Campaign Name",
    "status": "paused",
    "config": { /* updated config */ }
  }
}
```

#### Get Campaign Stats

**GET** `/api/campaigns/:id/stats`

Get detailed campaign statistics.

**Headers:**
- `Authorization: Bearer <token>`

**Response:**
```json
{
  "campaign": {
    "id": "camp_1234567890",
    "name": "Q1 Outreach",
    "status": "active",
    "started_at": 1703123456789
  },
  "leads": {
    "total": 150,
    "new": 25,
    "contacted": 100,
    "replied": 15,
    "qualified": 8,
    "unqualified": 2,
    "reply_rate": 0.15
  },
  "conversations": {
    "total": 15
  },
  "activity": {
    "agents_active": true,
    "last_activity": 1703123456789,
    "recent_events": {
      "research_completed": 5,
      "outreach_generated": 3,
      "decision_made": 8
    }
  }
}
```

#### Get Campaign Activity

**GET** `/api/campaigns/:id/activity`

Get human-readable activity feed for a campaign.

**Headers:**
- `Authorization: Bearer <token>`

**Query Parameters:**
- `limit` (optional): Number of activities to return (default: 20)

**Response:**
```json
{
  "activities": [
    {
      "id": "event_1234567890",
      "icon": "🔍",
      "description": "Researched Anthropic",
      "event_type": "research_completed",
      "entity_type": "lead",
      "entity_id": "lead_1234567890",
      "payload": {
        "company": "Anthropic"
      },
      "timestamp": 1703123456789,
      "trace_id": "trace_1234567890"
    }
  ]
}
```

#### Start Campaign

**POST** `/api/campaigns/:id/start`

Start a campaign - triggers research for all new leads.

**Headers:**
- `Authorization: Bearer <token>`

**Response:**
```json
{
  "campaign_id": "camp_1234567890",
  "triggered": 25,
  "results": [
    {
      "success": true,
      "lead_id": "lead_1234567890",
      "research": { /* research results */ },
      "strategy": { /* strategy decision */ },
      "timing": { /* timing calculation */ },
      "outreach": { /* outreach generation */ }
    }
  ]
}
```

#### Pause Campaign

**POST** `/api/campaigns/:id/pause`

Pause an active campaign.

**Headers:**
- `Authorization: Bearer <token>`

**Response:**
```json
{
  "status": "paused"
}
```

### Lead Management

#### List Leads

**GET** `/api/leads`

Get leads for the authenticated account.

**Headers:**
- `Authorization: Bearer <token>`

**Query Parameters:**
- `campaign_id` (optional): Filter by campaign

**Response:**
```json
{
  "leads": [
    {
      "id": "lead_1234567890",
      "account_id": "acc_1234567890",
      "campaign_id": "camp_1234567890",
      "name": "John Doe",
      "email": "john@anthropic.com",
      "phone": "+1-555-0123",
      "company": "anthropic.com",
      "metadata": {
        "research": {
          "company": {
            "companyName": "Anthropic",
            "description": "AI safety and research company...",
            "industry": "Artificial Intelligence",
            "employeeCount": "100-500"
          }
        }
      },
      "status": "contacted",
      "score": 85.5,
      "created_at": 1703123456789,
      "updated_at": 1703123456789
    }
  ]
}
```

#### Create Leads

**POST** `/api/leads`

Add multiple leads to a campaign.

**Headers:**
- `Authorization: Bearer <token>`
- `Content-Type: application/json`

**Request Body:**
```json
{
  "campaign_id": "camp_1234567890",
  "leads": [
    {
      "name": "John Doe",
      "email": "john@anthropic.com",
      "phone": "+1-555-0123",
      "company": "anthropic.com"
    },
    {
      "name": "Jane Smith",
      "email": "jane@openai.com",
      "company": "openai.com"
    }
  ]
}
```

**Response:**
```json
{
  "created": 2,
  "leads": [
    {
      "id": "lead_1234567890",
      "name": "John Doe",
      "email": "john@anthropic.com",
      "phone": "+1-555-0123",
      "company": "anthropic.com"
    },
    {
      "id": "lead_1234567891",
      "name": "Jane Smith",
      "email": "jane@openai.com",
      "company": "openai.com"
    }
  ]
}
```

#### Get Lead

**GET** `/api/leads/:id`

Get specific lead details.

**Headers:**
- `Authorization: Bearer <token>`

**Response:**
```json
{
  "lead": {
    "id": "lead_1234567890",
    "account_id": "acc_1234567890",
    "campaign_id": "camp_1234567890",
    "name": "John Doe",
    "email": "john@anthropic.com",
    "phone": "+1-555-0123",
    "company": "anthropic.com",
    "metadata": { /* research data */ },
    "status": "contacted",
    "score": 85.5,
    "created_at": 1703123456789,
    "updated_at": 1703123456789
  }
}
```

#### Update Lead

**PATCH** `/api/leads/:id`

Update lead fields.

**Headers:**
- `Authorization: Bearer <token>`
- `Content-Type: application/json`

**Request Body:**
```json
{
  "name": "John Smith",
  "status": "qualified",
  "score": 95.0
}
```

**Response:**
```json
{
  "lead": {
    "id": "lead_1234567890",
    "name": "John Smith",
    "status": "qualified",
    "score": 95.0,
    "updated_at": 1703123456789
  }
}
```

### Conversation Management

#### List Conversations

**GET** `/api/conversations`

Get conversations for the authenticated account.

**Headers:**
- `Authorization: Bearer <token>`

**Query Parameters:**
- `campaign_id` (optional): Filter by campaign
- `lead_id` (optional): Filter by lead

**Response:**
```json
{
  "conversations": [
    {
      "id": "conv_1234567890",
      "account_id": "acc_1234567890",
      "lead_id": "lead_1234567890",
      "campaign_id": "camp_1234567890",
      "channel": "email",
      "messages": [
        {
          "id": "msg_1234567890",
          "from": "alex@company.com",
          "to": "john@anthropic.com",
          "subject": "Quick question about AI safety",
          "body": "Hi John,\n\nI noticed Anthropic is doing...",
          "sent_at": 1703123456789,
          "type": "outbound"
        }
      ],
      "embedding_id": "vec_1234567890",
      "status": "active",
      "created_at": 1703123456789,
      "updated_at": 1703123456789
    }
  ]
}
```

### Analytics & Observability

#### Get Decision Logs

**GET** `/api/decision_logs`

Get AI decision logs for debugging and analysis.

**Headers:**
- `Authorization: Bearer <token>`

**Query Parameters:**
- `entity_id` (optional): Filter by entity
- `entity_type` (optional): Filter by entity type
- `agent_type` (optional): Filter by agent type
- `limit` (optional): Number of logs to return (default: 10)

**Response:**
```json
{
  "decision_logs": [
    {
      "id": "log_1234567890",
      "trace_id": "trace_1234567890",
      "agent_type": "strategy",
      "lead_id": "lead_1234567890",
      "input_context": {
        "lead": {
          "name": "John Doe",
          "company": "anthropic.com"
        },
        "research": { /* research data */ }
      },
      "reasoning": "Company shows strong AI focus, high confidence in ROI angle",
      "decision": {
        "action": "send_now",
        "messaging_angle": "roi_focused",
        "confidence": 85
      },
      "outcome": {
        "conversation_id": "conv_1234567890"
      },
      "timestamp": 1703123456789
    }
  ]
}
```

#### Get Events

**GET** `/api/events`

Get system events for debugging and monitoring.

**Headers:**
- `Authorization: Bearer <token>`

**Query Parameters:**
- `limit` (optional): Number of events to return (default: 100)
- `event_type` (optional): Filter by event type

**Response:**
```json
{
  "events": [
    {
      "id": "event_1234567890",
      "trace_id": "trace_1234567890",
      "parent_span_id": null,
      "account_id": "acc_1234567890",
      "event_type": "research_completed",
      "entity_type": "lead",
      "entity_id": "lead_1234567890",
      "payload": {
        "company": "Anthropic"
      },
      "timestamp": 1703123456789
    }
  ]
}
```

### Testing Endpoints

#### Test AI

**GET** `/test/ai`

Test Cloudflare Workers AI integration.

**Response:**
```json
{
  "llama": "Here's a compelling subject line: 'Quick question about your AI strategy'",
  "qwen": "Acme Corp"
}
```

#### Test Scraping

**GET** `/test/scrape?domain=anthropic.com`

Test website scraping functionality.

**Response:**
```json
{
  "title": "Anthropic",
  "description": "AI safety and research company...",
  "emails": ["contact@anthropic.com"],
  "phones": [],
  "url": "https://anthropic.com",
  "domain": "anthropic.com"
}
```

#### Test Research Agent

**GET** `/test/research?company=anthropic.com`

Test the research agent with a sample lead.

**Response:**
```json
{
  "result": {
    "success": true,
    "lead_id": "lead_1234567890",
    "company_info": {
      "companyName": "Anthropic",
      "description": "AI safety and research company...",
      "industry": "Artificial Intelligence",
      "employeeCount": "100-500"
    }
  },
  "lead": {
    "id": "lead_1234567890",
    "name": "John Doe",
    "email": "john@example.com",
    "company": "anthropic.com",
    "metadata": {
      "research": {
        "company": { /* extracted company info */ }
      }
    }
  }
}
```

#### Test Outreach Agent

**GET** `/test/outreach`

Test the outreach agent with a sample lead and campaign.

**Response:**
```json
{
  "result": {
    "success": true,
    "lead_id": "lead_1234567890",
    "conversation_id": "conv_1234567890",
    "subject": "Quick question about your AI strategy",
    "preview": "Hi Sarah,\n\nI noticed Anthropic is doing incredible work in AI safety..."
  },
  "conversation": {
    "id": "conv_1234567890",
    "messages": [
      {
        "id": "msg_1234567890",
        "from": "alex@aijesusbro.com",
        "to": "sarah@example.com",
        "subject": "Quick question about your AI strategy",
        "body": "Hi Sarah,\n\nI noticed Anthropic is doing incredible work...",
        "sent_at": 1703123456789,
        "type": "outbound"
      }
    ]
  }
}
```

## Error Responses

All endpoints return errors in this format:

```json
{
  "error": "Error message describing what went wrong"
}
```

**Common Status Codes:**
- `400` - Bad Request (missing/invalid parameters)
- `401` - Unauthorized (invalid/missing token)
- `403` - Forbidden (access denied)
- `404` - Not Found
- `409` - Conflict (resource already exists)
- `500` - Internal Server Error

## Rate Limits

Currently no rate limits are implemented, but they will be added as the system scales.

## Webhooks

### Email Events

**POST** `/webhooks/email`

Webhook endpoint for email provider events (opens, clicks, replies, etc.).

**Headers:**
- `Content-Type: application/json`

**Request Body:**
```json
{
  "event": "email_opened",
  "message_id": "msg_1234567890",
  "timestamp": 1703123456789,
  "data": {
    "recipient": "john@anthropic.com",
    "ip_address": "192.168.1.1"
  }
}
```

## SDKs and Examples

### cURL Examples

**Create Account:**
```bash
curl -X POST https://revopsOS-dev.aijesusbro-brain.workers.dev/api/accounts \
  -H "Content-Type: application/json" \
  -d '{"name":"My Company","email":"user@example.com","password":"securepass123"}'
```

**Start Campaign:**
```bash
curl -X POST https://revopsOS-dev.aijesusbro-brain.workers.dev/api/campaigns/camp_123/start \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

**Add Leads:**
```bash
curl -X POST https://revopsOS-dev.aijesusbro-brain.workers.dev/api/leads \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"campaign_id":"camp_123","leads":[{"name":"John Doe","email":"john@example.com","company":"example.com"}]}'
```

### JavaScript Examples

**Login and Get Campaigns:**
```javascript
// Login
const loginResponse = await fetch('https://revopsOS-dev.aijesusbro-brain.workers.dev/api/login', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    email: 'user@example.com',
    password: 'securepass123'
  })
});

const { token } = await loginResponse.json();

// Get campaigns
const campaignsResponse = await fetch('https://revopsOS-dev.aijesusbro-brain.workers.dev/api/campaigns', {
  headers: { 'Authorization': `Bearer ${token}` }
});

const { campaigns } = await campaignsResponse.json();
```

## Support

For API support or questions, check the main README or create an issue in the repository.
