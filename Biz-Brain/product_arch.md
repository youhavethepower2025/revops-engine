# 02 PRODUCT ARCHITECTURE

## THE "SOVEREIGN STACK" (Standard Deployment)
**Status:** Production Ready (Reference: Medtainer Deploy)
**Infrastructure:** DigitalOcean Droplet (Ubuntu 22.04 LTS)
**Containerization:** Docker Compose (Multi-container orchestration)

### 1. THE BRAIN (The Router)
* **Framework:** Python 3.11 + FastAPI (ASGI) + Uvicorn
* **Protocol:** MCP over SSE (Server-Sent Events)
* **Routing Logic:** Centralized `handle_mcp_request` dispatcher that routes JSON-RPC requests to the Tool Registry.
* **Tool Registry:** Singleton pattern. Auto-registers tools on startup. Decouples the API layer from the Execution layer.

### 2. THE SECURITY LAYER (Custom OAuth 2.1)
**We do NOT use third-party auth providers.**
* **Protocol:** OAuth 2.1 + PKCE (RFC 9728).
* **Token Storage:** Redis (In-Memory).
    * *Access Tokens:* 1-hour TTL. Opaque random hex (NOT JWTs).
    * *Refresh Tokens:* 7-day TTL.
* **Why No JWT?** Immediate revocation capabilities (delete from Redis = instant kill).
* **The Handshake:**
    1.  Claude Discovery (`/.well-known/oauth-protected-resource`)
    2.  Redirect to `/authorize` (PKCE Challenge)
    3.  Code Exchange for Token (stored in Redis)
    4.  Authenticated SSE Stream

### 3. THE DATA LAYER (Persistence)
* **Hot Data (Tokens/Sessions):** Redis 7 (Alpine). Persisted via AOF/RDB.
* **Cold Data (Logs/Context):** PostgreSQL 16.
    * *Volume Strategy:* Local Docker volumes (`/var/lib/docker/volumes/...`). Survives container restarts.
    * *Encryption:* Fernet (AES-256) for sensitive long-term storage.

### 4. THE NETWORK BRIDGE (Cloudflare Tunnel)
**We do NOT open port 443.**
* **Mechanism:** `cloudflared` daemon creates an encrypted tunnel to Cloudflare Edge.
* **WAF Rule (Critical):** Custom rule to **SKIP** "Super Bot Fight Mode" for the `/mcp` endpoint (Fixes Claude Electron User-Agent blocking).
* **Benefits:** DDoS protection, Free SSL, No attack surface on the Droplet IP.

### 5. DEPLOYMENT PROTOCOL
* **Method:** `rsync` code to server -> `docker-compose restart mcp`.
* **Philosophy:** "Push to Prod." No complex CI/CD pipelines.
* **Monitoring:** `docker logs -f` (The truth is in the logs).

---

## THE "NO JANITOR" BOUNDARIES
**What We Build:**
* The Docker Container ("The Brain").
* The API Bridges (Stripe, GHL, etc.).
* The Auth Tunnel.

**What We Do Not Build:**
* Custom UI Dashboards (Claude Desktop is the UI).
* Data Cleaning Scripts (Garbage In, Garbage Out).
* Network Debugging for Client's Local Wi-Fi.