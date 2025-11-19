# Cloudflare Tools Reference

**Complete guide to all Cloudflare tools in CursorMCP**

---

## 🚀 Workers Tools

### `cloudflare_list_workers`
List all Cloudflare Workers in your account.

**Input:**
```json
{}
```

**Output:**
```json
{
  "workers": [
    {
      "id": "jobhuntai-dev",
      "name": "jobhuntai-dev",
      "created_on": "2024-01-01T00:00:00Z"
    }
  ],
  "count": 1
}
```

---

### `cloudflare_get_worker`
Get detailed information about a specific Worker.

**Input:**
```json
{
  "script_name": "jobhuntai-dev"
}
```

**Output:**
```json
{
  "id": "jobhuntai-dev",
  "script": "...",
  "bindings": [],
  "created_on": "2024-01-01T00:00:00Z"
}
```

---

### `cloudflare_deploy_worker`
Deploy or update a Cloudflare Worker.

**Input:**
```json
{
  "script_name": "my-worker",
  "script_content": "export default {\n  async fetch(request) {\n    return new Response('Hello World')\n  }\n}",
  "bindings": [
    {
      "type": "kv_namespace",
      "name": "MY_KV",
      "namespace_id": "abc123"
    }
  ]
}
```

**Output:**
```json
{
  "success": true,
  "script_name": "my-worker",
  "result": {...},
  "url": "https://my-worker.aijesusbro-brain.workers.dev"
}
```

---

### `cloudflare_delete_worker`
Delete a Cloudflare Worker.

**Input:**
```json
{
  "script_name": "my-worker"
}
```

**Output:**
```json
{
  "success": true,
  "script_name": "my-worker",
  "result": {...}
}
```

---

### `cloudflare_get_worker_logs`
Get logs for a Cloudflare Worker (may require Workers Analytics Engine).

**Input:**
```json
{
  "script_name": "my-worker",
  "start_time": "2024-01-01T00:00:00Z",
  "end_time": "2024-01-01T23:59:59Z"
}
```

**Output:**
```json
{
  "script_name": "my-worker",
  "logs": [...],
  "count": 10
}
```

---

## 💾 D1 Database Tools

### `cloudflare_list_d1_databases`
List all D1 databases in your account.

**Input:**
```json
{}
```

**Output:**
```json
{
  "databases": [
    {
      "uuid": "abc123",
      "name": "jobhuntai-db-dev",
      "created_at": "2024-01-01T00:00:00Z"
    }
  ],
  "count": 1
}
```

---

### `cloudflare_create_d1_database`
Create a new D1 database.

**Input:**
```json
{
  "name": "my-database"
}
```

**Output:**
```json
{
  "success": true,
  "database": {
    "uuid": "abc123",
    "name": "my-database"
  }
}
```

---

### `cloudflare_query_d1`
Execute a SQL query on a D1 database.

**Input:**
```json
{
  "database_id": "abc123",
  "query": "SELECT * FROM users WHERE id = ?",
  "params": ["user123"]
}
```

**Output:**
```json
{
  "success": true,
  "result": {
    "results": [
      {"id": "user123", "name": "John"}
    ],
    "meta": {...}
  }
}
```

---

## 🔑 KV Storage Tools

### `cloudflare_list_kv_namespaces`
List all KV namespaces.

**Input:**
```json
{}
```

**Output:**
```json
{
  "namespaces": [
    {
      "id": "abc123",
      "title": "my-kv-namespace"
    }
  ],
  "count": 1
}
```

---

### `cloudflare_create_kv_namespace`
Create a new KV namespace.

**Input:**
```json
{
  "title": "my-kv-namespace"
}
```

**Output:**
```json
{
  "success": true,
  "namespace": {
    "id": "abc123",
    "title": "my-kv-namespace"
  }
}
```

---

### `cloudflare_get_kv_value`
Get a value from KV storage.

**Input:**
```json
{
  "namespace_id": "abc123",
  "key": "user:123"
}
```

**Output:**
```json
{
  "key": "user:123",
  "value": "{\"name\": \"John\"}",
  "found": true
}
```

---

### `cloudflare_set_kv_value`
Set a value in KV storage.

**Input:**
```json
{
  "namespace_id": "abc123",
  "key": "user:123",
  "value": "{\"name\": \"John\"}"
}
```

**Output:**
```json
{
  "success": true,
  "key": "user:123",
  "result": {"success": true}
}
```

---

### `cloudflare_delete_kv_value`
Delete a value from KV storage.

**Input:**
```json
{
  "namespace_id": "abc123",
  "key": "user:123"
}
```

**Output:**
```json
{
  "success": true,
  "key": "user:123",
  "result": {...}
}
```

---

## 🎯 Usage Examples

### Deploy a Simple Worker

```
User: "Deploy a worker that returns 'Hello from CursorMCP'"

AI calls:
- cloudflare_deploy_worker({
    "script_name": "hello-cursormcp",
    "script_content": "export default { async fetch() { return new Response('Hello from CursorMCP') } }"
  })
```

### Query D1 Database

```
User: "Get all companies from jobhuntai database"

AI calls:
- cloudflare_query_d1({
    "database_id": "jobhuntai-db-id",
    "query": "SELECT * FROM organizations LIMIT 10"
  })
```

### Store Configuration in KV

```
User: "Store my API key in KV"

AI calls:
- cloudflare_set_kv_value({
    "namespace_id": "config-namespace-id",
    "key": "api_key",
    "value": "secret-key-123"
  })
```

---

## 🔧 Configuration

Make sure your `.env` file has:

```env
CLOUDFLARE_API_TOKEN=your_token_here
CLOUDFLARE_ACCOUNT_ID=your_account_id_here
```

Get these from:
- API Token: https://dash.cloudflare.com/profile/api-tokens
- Account ID: https://dash.cloudflare.com/ (in URL or Workers dashboard)

---

## 🚨 Error Handling

All tools return errors in this format:

```json
{
  "error": "Error message here",
  "success": false
}
```

Common errors:
- `Cloudflare API token not configured` - Check `.env` file
- `HTTP 401` - Invalid API token
- `HTTP 404` - Resource not found
- `HTTP 429` - Rate limit exceeded

---

## 📚 Next Steps

1. Test tools with your Cloudflare account
2. Build application MCP servers (see MULTI_MCP_VISION.md)
3. Connect apps through orchestrator
4. Create distributed workflows

---

**Ready to orchestrate Cloudflare!** 🚀

