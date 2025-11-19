# GoHighLevel (GHL) Integration Master Guide for MCP Brain Server

## Core Understanding: GHL as CRM & Marketing Automation Infrastructure

GoHighLevel is evolving from a marketing tool to an **API-First Platform** with their V2 API migration. The platform provides CRM, marketing automation, sales pipeline management, and communications infrastructure. **API V1 deprecates September 30, 2025** - all development MUST use V2.

## Authentication & Setup

### API Key (Current - Private Integration Token)
```
GHL_API_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJsb2NhdGlvbl9pZCI6IlBNZ2JRMzc1VEVHT3lHWHNLejdlIiwidmVyc2lvbiI6MSwiaWF0IjoxNzU3NDU2NTUwMTIyLCJzdWIiOiJ5OXFxZjNIV0FYVGk5Nk1wZXVqZiJ9.nbuFjgIZ1hnsHLPDj5IsiUlxR5DgecMw1l56LCEZEjo
GHL_LOCATION_ID=PMgbQ375TEGOyGXsKz7e
```

### API Endpoints
```
Base URL: https://rest.gohighlevel.com/v1
V2 Base: https://services.leadconnectorhq.com
Marketplace API: https://marketplace.gohighlevel.com/api/app
```

## V1 vs V2 Critical Differences

### Authentication Models
- **V1**: Static Bearer token (deprecated)
- **V2**: OAuth 2.0 or Private Integration Tokens (PITs)

### For MCP Integration: Use PIT (Private Integration Token)
PITs are the correct choice for internal servers:
- Generate in GHL Settings → Private Integrations
- Select specific scopes (principle of least privilege)
- Long-lived, no refresh needed
- Use as Bearer token in Authorization header

## Available MCP Tools for GHL Operations

### 1. ghl_search_contact
Searches contacts using powerful V2 endpoint
```json
{
  "query": "search term",
  "email": "email@example.com",
  "phone": "+1234567890",
  "tags": ["tag1", "tag2"]
}
```
Note: Uses POST /contacts/search (V2) - GET /contacts is DEPRECATED

### 2. ghl_get_contact
Retrieves full contact details
```json
{
  "contact_id": "contact_xxx"
}
```

### 3. ghl_update_contact
Updates contact fields
```json
{
  "contact_id": "contact_xxx",
  "first_name": "John",
  "last_name": "Doe",
  "email": "john@example.com",
  "tags": ["updated"],
  "custom_fields": {}
}
```

### 4. ghl_create_contact
Creates new contact with all fields
```json
{
  "first_name": "Jane",
  "last_name": "Smith",
  "email": "jane@example.com",
  "phone": "+1234567890",
  "tags": ["new_lead"],
  "source": "MCP Brain"
}
```

### 5. ghl_create_appointment
Books calendar appointment
```json
{
  "calendar_id": "cal_xxx",
  "contact_id": "contact_xxx",
  "start_time": "2025-01-15T10:00:00Z",
  "end_time": "2025-01-15T11:00:00Z",
  "title": "Sales Call",
  "location_id": "loc_xxx"
}
```

### 6. ghl_get_calendar_slots
Finds available appointment times
```json
{
  "calendar_id": "cal_xxx",
  "start_date": "2025-01-15",
  "end_date": "2025-01-20",
  "timezone": "America/New_York"
}
```

### 7. ghl_create_task
Creates follow-up task
```json
{
  "contact_id": "contact_xxx",
  "title": "Follow up call",
  "body": "Check on proposal status",
  "due_date": "2025-01-20T15:00:00Z",
  "assigned_to": "user_xxx"
}
```

### 8. ghl_add_note
Adds note to contact
```json
{
  "contact_id": "contact_xxx",
  "note": "Spoke with client, interested in premium package"
}
```

### 9. ghl_create_opportunity
Creates sales opportunity
```json
{
  "contact_id": "contact_xxx",
  "title": "Premium Package Sale",
  "pipeline_id": "pipeline_xxx",
  "pipeline_stage_id": "stage_xxx",
  "monetary_value": 5000,
  "status": "open"
}
```

### 10. ghl_move_opportunity
Moves opportunity through pipeline
```json
{
  "opportunity_id": "opp_xxx",
  "stage_id": "stage_closed_won"
}
```

### 11. ghl_trigger_workflow
Triggers automation workflow
```json
{
  "workflow_id": "workflow_xxx",
  "contact_id": "contact_xxx"
}
```

### 12. ghl_send_message
Sends SMS/Email through GHL
```json
{
  "contact_id": "contact_xxx",
  "type": "SMS",
  "message": "Your appointment is confirmed for tomorrow at 10 AM"
}
```

### 13. ghl_webhook_received
Processes incoming webhook
```json
{
  "event_type": "contact_created",
  "payload": {}
}
```

## Webhook Configuration

### Webhook Events (50+ Types)
- Contact: created, updated, deleted
- Appointment: booked, cancelled, confirmed
- Opportunity: created, status_changed, stage_changed
- Form: submitted
- Message: inbound_sms, inbound_email

### Webhook Security
```python
# Verify webhook signature
import hmac
import hashlib

def verify_ghl_webhook(payload, signature, secret):
    expected = hmac.new(
        secret.encode(),
        payload.encode(),
        hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(expected, signature)
```

### Webhook Processing Pattern
```python
@app.post("/webhooks/ghl/{location_id}")
async def handle_ghl_webhook(location_id: str, request: Request):
    data = await request.json()
    event_type = data.get("event")

    if event_type == "contact.created":
        # New contact added
        await process_new_contact(data["contact"])

    elif event_type == "appointment.booked":
        # Appointment scheduled
        await sync_to_calendar(data["appointment"])

    elif event_type == "opportunity.stage_changed":
        # Deal moved in pipeline
        await update_deal_status(data["opportunity"])
```

## API Rate Limits

### V2 Rate Limits (Per App, Per Location)
- **Burst**: 100 requests per 10 seconds
- **Daily**: 200,000 requests per 24 hours

### Rate Limit Headers
```
X-RateLimit-Limit-Daily: 200000
X-RateLimit-Daily-Remaining: 199950
X-RateLimit-Max: 100
X-RateLimit-Remaining: 95
X-RateLimit-Interval-Milliseconds: 10000
```

### Rate Limit Strategy
```python
async def rate_limited_request(client, endpoint, **kwargs):
    response = await client.request(endpoint, **kwargs)

    if response.status_code == 429:
        retry_after = int(response.headers.get('Retry-After', 60))
        await asyncio.sleep(retry_after)
        return await rate_limited_request(client, endpoint, **kwargs)

    remaining = int(response.headers.get('X-RateLimit-Remaining', 100))
    if remaining < 10:
        await asyncio.sleep(1)  # Slow down near limit

    return response
```

## CRM Patterns

### Contact Enrichment Flow
```python
async def enrich_contact_after_call(call_data):
    # After Retell call ends
    contact = await ghl_get_contact(call_data["metadata"]["contact_id"])

    # Update with call insights
    await ghl_update_contact(
        contact_id=contact["id"],
        custom_fields={
            "last_call_date": datetime.now(),
            "call_sentiment": call_data["sentiment"],
            "qualification_score": calculate_score(call_data)
        },
        tags=determine_tags(call_data)
    )

    # Add call notes
    await ghl_add_note(
        contact_id=contact["id"],
        note=f"Call Summary: {call_data['summary']}\nDuration: {call_data['duration']}s"
    )

    # Move through pipeline if qualified
    if call_data["qualified"]:
        await ghl_move_opportunity(
            opportunity_id=contact["opportunity_id"],
            stage_id="qualified_lead"
        )
```

### Pipeline Automation
```python
PIPELINE_STAGES = {
    "new": "stage_001",
    "contacted": "stage_002",
    "qualified": "stage_003",
    "proposal": "stage_004",
    "negotiation": "stage_005",
    "closed_won": "stage_006",
    "closed_lost": "stage_007"
}

async def advance_pipeline(contact_id, action):
    opportunity = await get_contact_opportunity(contact_id)
    current_stage = opportunity["pipeline_stage_id"]

    next_stage = determine_next_stage(current_stage, action)

    if next_stage:
        await ghl_move_opportunity(
            opportunity_id=opportunity["id"],
            stage_id=next_stage
        )

        # Trigger stage-specific workflow
        await ghl_trigger_workflow(
            workflow_id=STAGE_WORKFLOWS[next_stage],
            contact_id=contact_id
        )
```

## Calendar & Scheduling

### Appointment Booking Pattern
```python
async def book_appointment_with_availability(contact_id, calendar_id, preferences):
    # Get available slots
    slots = await ghl_get_calendar_slots(
        calendar_id=calendar_id,
        start_date=preferences["earliest_date"],
        end_date=preferences["latest_date"],
        timezone=preferences["timezone"]
    )

    # Select optimal slot
    selected_slot = select_best_slot(slots, preferences)

    # Book appointment
    appointment = await ghl_create_appointment(
        calendar_id=calendar_id,
        contact_id=contact_id,
        start_time=selected_slot["start"],
        end_time=selected_slot["end"],
        title=f"Meeting with {contact['name']}",
        location_id=GHL_LOCATION_ID
    )

    # Send confirmation
    await ghl_send_message(
        contact_id=contact_id,
        type="SMS",
        message=f"Your appointment is confirmed for {format_time(selected_slot)}"
    )

    return appointment
```

## Workflow Integration

### Triggering Workflows with Data
```python
async def trigger_workflow_with_context(workflow_id, contact_id, context_data):
    # Workflows can receive data via webhook trigger
    # First, update contact with context
    await ghl_update_contact(
        contact_id=contact_id,
        custom_fields=context_data
    )

    # Then trigger workflow
    await ghl_trigger_workflow(
        workflow_id=workflow_id,
        contact_id=contact_id
    )
```

### Inbound Webhook Pattern
Use "Inbound Webhook" trigger in GHL workflow builder:
1. Create workflow with Inbound Webhook trigger
2. Get webhook URL from workflow
3. POST data directly to trigger with payload

## Multi-Location Support

### Managing Multiple GHL Accounts
```python
GHL_ACCOUNTS = {
    "client_001": {
        "api_key": "xxx",
        "location_id": "loc_001"
    },
    "client_002": {
        "api_key": "yyy",
        "location_id": "loc_002"
    }
}

async def get_client_ghl(client_id):
    config = GHL_ACCOUNTS[client_id]
    return GHLClient(
        api_key=config["api_key"],
        location_id=config["location_id"]
    )
```

## Common Issues & Solutions

### Issue: 404 on contact endpoints
**Solution**: Ensure using V2 endpoints and correct location_id

### Issue: Webhook not firing
**Solution**: Check app installation, webhook URL configuration, and event subscriptions

### Issue: Rate limit hit
**Solution**: Implement exponential backoff, use batch operations where available

### Issue: OAuth token expired
**Solution**: Use PIT for internal servers, implement refresh token logic for marketplace apps

### Issue: Contact search not working
**Solution**: Use POST /contacts/search (V2), not deprecated GET /contacts

## SDK Recommendations

### Official SDK
```javascript
npm install @gohighlevel/api-client
```

### Community SDK (More Features)
```javascript
npm install @gnosticdev/highlevel-sdk
```
- Fully typed from OpenAPI spec
- Better error handling
- Auto-generated from latest API changes

## Testing Tools

### Postman
- Build custom collection for V2 API
- No official V2 collection yet

### Webhook.site
- Test webhook payloads before implementation
- Essential for understanding event structure

## Security Best Practices

1. **Use PIT for internal servers** (not OAuth)
2. **Request minimum scopes** needed
3. **Validate webhook signatures** always
4. **Store tokens securely** (environment variables)
5. **Log full requests/responses** for debugging
6. **Implement circuit breakers** for API failures
7. **Monitor rate limit headers** proactively

## Migration from V1 to V2

### Key Changes
1. Replace static API keys with PITs
2. Update endpoints to V2 URLs
3. Add scope handling
4. Update search to POST method
5. Handle new error formats

### Deadline: September 30, 2025
All V1 integrations will stop working after this date.

## Success Metrics

- Contact creation: < 1 second
- Search response: < 2 seconds
- Webhook processing: < 500ms
- Appointment booking: < 3 seconds
- Workflow trigger: < 1 second

## CRITICAL RULES

1. **NEVER** use V1 API for new development
2. **ALWAYS** use Private Integration Tokens for internal servers
3. **ALWAYS** validate webhook signatures
4. **NEVER** exceed rate limits (monitor headers)
5. **ALWAYS** use V2 search endpoint (POST)
6. **NEVER** store sensitive data in custom fields
7. **ALWAYS** handle 429 rate limit responses gracefully

This is THE definitive GoHighLevel V2 API integration guide for MCP Brain Server.