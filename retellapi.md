# Retell.ai API comprehensive guide for MCP server integration

Retell.ai provides a robust REST API ecosystem for building and managing AI voice agents programmatically. The platform combines **real-time WebSocket connections**, comprehensive webhook systems, and traditional REST endpoints to enable sophisticated voice agent deployments at scale. With official SDKs for Python and Node.js, the API supports everything from basic agent creation to complex multi-stage conversation flows with custom LLM integrations.

## Complete API documentation and endpoints

The Retell.ai API operates on a RESTful architecture with JSON payloads, accessible at `https://api.retellai.com`. Authentication uses **Bearer token format** with API keys obtained from the dashboard. The API provides comprehensive endpoints across five major categories:

**Agent Management** forms the core of the API with endpoints for creating (`POST /create-agent`), retrieving (`GET /get-agent/{agent_id}`), updating (`PATCH /update-agent/{agent_id}`), and deleting agents (`DELETE /delete-agent/{agent_id}`). The list endpoint (`GET /list-agents`) supports pagination for managing large agent fleets. Notably, Retell maintains agent versioning through `GET /get-agent-versions/{agent_id}`, enabling rollback capabilities for production deployments.

**Call Management** endpoints handle the entire call lifecycle. The `POST /create-phone-call` initiates outbound calls while `POST /create-web-call` handles browser-based interactions. The critical `POST /register-phone-call` endpoint establishes WebSocket connections for real-time communication. Call retrieval (`GET /get-call/{call_id}`) returns comprehensive analytics including **latency metrics**, transcripts with word-level timestamps, and cost breakdowns. The `POST /list-calls` endpoint supports complex filtering for call history analysis.

**Phone Number Management** provides full control over telephony resources. Beyond basic CRUD operations (`/create-phone-number`, `/update-phone-number`, `/delete-phone-number`), the API supports number importation (`POST /import-phone-number`) for existing telephony infrastructure. Each number can have distinct inbound and outbound agents with separate webhook configurations.

**LLM Configuration** endpoints (`/create-retell-llm`, `/update-retell-llm`) manage the conversational intelligence layer. These endpoints support **multi-state conversation flows**, dynamic tool definitions, and prompt templates with variable injection using `{{variable_name}}` syntax. The maximum prompt length is **8,192 tokens**, with support for state-based transitions and custom function calling.

**Additional Capabilities** include batch calling (`POST /create-batch-call`), conversation flow management (`POST /create-conversation-flow`), knowledge base creation (`POST /create-knowledge-base`), and concurrency monitoring (`GET /get-concurrency`). The **WebSocket endpoint** at `/llm-websocket/{call_id}` enables real-time custom LLM integration with configurable auto-reconnection and ping-pong monitoring.

## Best practices for voice agent management

Creating robust voice agents programmatically requires careful attention to configuration patterns and lifecycle management. The **agent object model** supports over 40 configurable parameters, but effective agents focus on five critical areas:

**Response Engine Configuration** determines the conversational intelligence. For Retell LLM, specify the `llm_id` and version. Custom LLM integrations require WebSocket server setup with proper message handling for `config`, `response_required`, and `update_only` events. Always configure fallback mechanisms for LLM failures.

**Voice Optimization** involves selecting primary and fallback voices across providers (ElevenLabs, OpenAI, PlayHT, Cartesia). Set `voice_temperature` between 0.5-1.5 for variability, `voice_speed` from 0.5-2.0 for pacing, and configure `interruption_sensitivity` (0.1-1.0) based on conversation style. Enable `backchannel` with appropriate frequency (0.8-1.0) for natural conversation flow.

**Call Behavior Settings** require careful tuning of `responsiveness` (0.1-1.0) for latency versus accuracy tradeoff, `end_call_after_silence_ms` (typically 600000 for 10-minute timeout), and `reminder_trigger_ms` for handling user silence. Configure `max_call_duration_ms` appropriately - default is 3600000 (1 hour).

**Error Recovery Patterns** should include webhook URL configuration with signature verification, pronunciation dictionary setup for domain-specific terms, and `boosted_keywords` for improved speech recognition accuracy. Always implement `opt_out_sensitive_data_storage` for compliance requirements.

**Deployment strategies** leverage agent versioning for A/B testing and gradual rollouts. Create template agents for consistent configurations across similar use cases. Use dynamic variables for personalization without creating duplicate agents. Monitor the `last_modification_timestamp` to track configuration drift.

## Webhook configurations and event handling

Retell's webhook system provides **three primary events**: `call_started`, `call_ended`, and `call_analyzed`, each delivering complete call objects with transcripts, analytics, and metadata. Webhook URLs are configured at the agent level and support both synchronous responses and asynchronous processing patterns.

**Authentication and Security** relies on the `x-retell-signature` header for request verification. Implement signature validation using HMAC-SHA256 with your API key. Whitelist Retell's server IPs: **13.248.202.14**, **3.33.169.178**, and **100.20.5.228**. The SDK provides built-in verification functions that should be used in production.

**Payload Processing** requires handling within a **10-second timeout window**. Failed webhooks (non-2xx responses) trigger up to **3 automatic retries** with exponential backoff. Events are delivered independently - a failed `call_started` webhook won't prevent `call_ended` delivery. Parse the `disconnection_reason` field to understand call termination causes.

**Event-specific Patterns** vary by call lifecycle stage. The `call_started` event enables real-time CRM updates and concurrent process initiation. Note that failed dial attempts trigger `call_ended` without `call_started`. The `call_analyzed` event always fires regardless of connection status, providing sentiment analysis, call summaries, and success metrics even for failed calls.

**Advanced webhook patterns** include using webhook responses to update call context mid-conversation, implementing webhook queuing for high-volume scenarios, and leveraging the `metadata` field for request tracing. Configure separate webhooks for inbound versus outbound calls when different processing logic is required.

## Authentication methods and rate limits

Retell uses **API key authentication** exclusively, with keys managed through the dashboard. Each workspace supports multiple API keys sharing identical permissions. Keys follow the format `Authorization: Bearer YOUR_API_KEY` in request headers. One key per workspace is automatically designated for webhook signature generation.

**Rate limiting** operates at multiple levels. The primary constraint is **concurrency limits** - 20 simultaneous calls for Pay-As-You-Go accounts, upgradeable through billing settings. HTTP endpoints implement request rate limiting communicated through status code **429** with retry-after headers. The SDK automatically handles rate limiting with **2 retries** using exponential backoff starting at 1 second.

**Call duration limits** default to **1 hour maximum** per call with automatic termination. Batch calling operations bypass standard concurrency limits but maintain duration restrictions. Token limits for Retell LLM prompts cap at **8,192 tokens** including system and user messages.

**Error handling** should account for status code **402** indicating insufficient funds, **422** for validation errors or quota violations, and **429** for rate limit exceeded. Implement circuit breakers for repeated 5xx errors. Monitor the `/get-concurrency` endpoint to proactively manage capacity.

## Common API patterns for core operations

**Agent Creation** follows a builder pattern with minimal required fields but extensive customization options. Essential configuration includes response engine setup, voice selection, and webhook URL:

```python
agent = client.agent.create(
    response_engine={"type": "retell-llm", "llm_id": "llm_xxx"},
    voice_id="11labs-Adrian",
    agent_name="Customer Support",
    webhook_url="https://your-domain.com/webhook",
    interruption_sensitivity=0.8,
    backchannel_frequency=0.9,
    pronunciation_dictionary=[
        {"word": "API", "phoneme": "eɪ piː aɪ", "alphabet": "ipa"}
    ]
)
```

**Prompt Management** through Retell LLM supports multi-state conversations with tool integration. Define states with specific prompts and available tools, enabling complex conversation flows:

```python
llm = client.llm.create(
    general_prompt="You are a helpful assistant...",
    states=[
        {
            "name": "greeting",
            "state_prompt": "Greet the user warmly...",
            "tools": [{"type": "end_call", "name": "end_call"}]
        }
    ]
)
```

**Call Handling** requires careful orchestration of phone number registration, call initiation, and monitoring. For programmatic calling:

```python
call = client.call.createPhoneCall(
    from_number="+14157774444",
    to_number="+12137774445",
    agent_id="agent_xxx",
    retell_llm_dynamic_variables={
        "customer_name": "John Doe",
        "account_number": "12345"
    }
)
```

**Analytics Retrieval** provides comprehensive call metrics including **latency percentiles** (p50, p90, max) for end-to-end, LLM, and TTS components. Access cost breakdowns by service and sentiment analysis through the call object's nested structures.

## Error handling patterns and edge cases

**Systematic error handling** requires understanding Retell's error taxonomy. Network errors manifest as `APIConnectionError`, while business logic errors use specific status codes. Implement retry logic with exponential backoff for transient failures:

```python
async def robust_call(client, max_retries=3):
    for attempt in range(max_retries):
        try:
            return await client.call.createPhoneCall(...)
        except retell.RateLimitError:
            await asyncio.sleep(2 ** attempt)
        except retell.APIConnectionError:
            if attempt == max_retries - 1:
                raise
            await asyncio.sleep(1)
```

**WebSocket disconnection** handling requires implementing auto-reconnection with the `config` message setting `auto_reconnect: true`. Monitor ping-pong messages (every 2 seconds) with a 5-second timeout threshold. Handle the special case where JSON parsing errors cause connection closure with code 1002.

**Edge cases** include voicemail detection timing (configurable for B2B scenarios), handling calls that exceed maximum duration with graceful termination, managing WebSocket reconnection during long-running LLM operations, and dealing with partial transcription delivery for interrupted utterances.

**Call failure scenarios** require specific handling for dial failures (busy, no answer, failed) which skip `call_started` events, WebSocket connection failures during call registration, and TTS provider failures triggering automatic fallback. Monitor the `disconnection_reason` field for detailed failure analysis.

## Integration patterns for MCP servers

**MCP server architecture** for Retell integration follows a tool-based pattern where voice operations become accessible through the Model Context Protocol. The official `@abhaybabbar/retellai-mcp-server` npm package provides a reference implementation configurable through standard MCP server definitions.

**Tool definition patterns** map Retell operations to MCP tools with clear input/output schemas. Essential tools include agent creation/management, call initiation with dynamic variables, webhook event processing, and analytics retrieval. Each tool should handle authentication, error recovery, and response formatting:

```javascript
{
  "name": "create_voice_call",
  "description": "Initiate an AI voice call",
  "parameters": {
    "to_number": "string",
    "agent_id": "string",
    "variables": "object"
  }
}
```

**Async operation handling** in MCP context requires managing long-running voice operations. Implement call initiation as a non-blocking operation returning call_id immediately. Use webhook endpoints to update MCP server state asynchronously. Provide status polling tools for clients to check call progress.

**State management** patterns maintain conversation context across MCP tool invocations. Store active call sessions with their WebSocket connections in server memory. Implement cleanup handlers for abandoned calls. Synchronize webhook events with MCP server state updates.

**Multi-server coordination** enables complex voice workflows. Configure separate MCP servers for different Retell workspaces or agent types. Implement routing logic based on call requirements. Use MCP server composition for combining Retell with other services like CRM updates or knowledge base queries.

## Implementation patterns and code examples

**Production-ready wrapper pattern** encapsulates Retell SDK with additional capabilities:

```python
class RetellMCPWrapper:
    def __init__(self, api_key, cache_ttl=300):
        self.client = AsyncRetell(api_key=api_key)
        self.cache = TTLCache(maxsize=100, ttl=cache_ttl)
        self.metrics = defaultdict(list)
    
    async def create_agent_with_template(self, template_name, overrides):
        template = self.cache.get(f"template_{template_name}")
        if not template:
            template = await self._load_template(template_name)
        
        config = {**template, **overrides}
        agent = await self.client.agent.create(**config)
        self._record_metric('agent_created', agent.agent_id)
        return agent
    
    async def monitored_call(self, **params):
        start_time = time.time()
        try:
            call = await self.client.call.createPhoneCall(**params)
            self.metrics['call_latency'].append(time.time() - start_time)
            return call
        except Exception as e:
            self.metrics['call_failures'].append(str(e))
            raise
```

**WebSocket server implementation** for custom LLM integration follows Retell's protocol:

```javascript
class RetellLLMServer {
    constructor(port) {
        this.wss = new WebSocketServer({ port });
        this.sessions = new Map();
        
        this.wss.on('connection', (ws) => {
            ws.on('message', async (data) => {
                const message = JSON.parse(data);
                await this.handleMessage(ws, message);
            });
        });
    }
    
    async handleMessage(ws, message) {
        switch(message.type) {
            case 'config':
                ws.send(JSON.stringify({
                    type: 'config',
                    auto_reconnect: true,
                    call_details: true
                }));
                break;
            case 'response_required':
                const response = await this.generateResponse(message);
                ws.send(JSON.stringify({
                    type: 'response',
                    response_id: message.response_id,
                    content: response
                }));
                break;
        }
    }
}
```

**Monitoring and observability** implementation tracks critical metrics:

```python
class RetellObservability:
    def __init__(self, retell_client):
        self.client = retell_client
        self.prometheus_registry = CollectorRegistry()
        
        self.call_duration = Histogram(
            'retell_call_duration_seconds',
            'Call duration in seconds',
            registry=self.prometheus_registry
        )
        
        self.call_success = Counter(
            'retell_call_success_total',
            'Successful calls',
            registry=self.prometheus_registry
        )
    
    async def track_call(self, call_id):
        call = await self.client.call.retrieve(call_id)
        self.call_duration.observe(call.duration_ms / 1000)
        if call.call_analysis.call_successful:
            self.call_success.inc()
```

**Testing strategies** combine multiple approaches for comprehensive coverage. Use Retell's web simulator for agent behavior testing without consuming minutes. Implement webhook mocking with ngrok for local development. Create test doubles for API responses to enable unit testing. Deploy canary agents with limited phone numbers for production testing.

## Conclusion

Building robust MCP server integrations with Retell.ai requires understanding the interplay between REST endpoints, WebSocket connections, and webhook events. The API's comprehensive feature set enables sophisticated voice agent deployments, from simple outbound calling to complex multi-state conversations with custom LLM integration. Success depends on implementing proper error handling, monitoring concurrency limits, and leveraging the SDK's built-in retry mechanisms.

The most critical implementation considerations are **webhook signature verification** for security, **WebSocket auto-reconnection** for reliability, and **proper concurrency management** for scalability. By following the architectural patterns outlined here—particularly the wrapper pattern for enhanced functionality and the monitoring pattern for observability—developers can create production-ready voice agent systems that integrate seamlessly with MCP servers while maintaining high reliability and performance standards.