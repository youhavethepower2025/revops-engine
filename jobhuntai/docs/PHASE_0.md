# Phase 0: Foundations

## Goal
Build stable, deployable, multi-tenant infrastructure with complete observability substrate.

## Checklist

### Infrastructure
- [x] Project directory created
- [x] wrangler.toml configured
- [x] Complete D1 schema with event sourcing
- [ ] D1 databases created (dev, staging, production)
- [ ] Schema deployed to databases
- [ ] Vectorize index created
- [ ] Queues configured

### Auth System
- [ ] JWT generation utility
- [ ] Auth middleware (validates JWT, extracts account_id)
- [ ] Account creation endpoint
- [ ] Login endpoint

### API Scaffolding
- [ ] Hono router setup
- [ ] Account endpoints (stubs)
- [ ] Campaign endpoints (stubs)
- [ ] Lead endpoints (stubs)
- [ ] Conversation endpoints (stubs)
- [ ] Analytics endpoints (stubs)
- [ ] All endpoints filter by account_id

### Event System
- [ ] Trace ID generation
- [ ] Event emission utility
- [ ] Event log viewer (simple HTML page)

### Developer Tools
- [ ] Wrangler dashboard access confirmed
- [ ] D1 query scripts
- [ ] Event viewer deployed

## Exit Criteria
- Can create account via API
- Can get JWT token
- Can make authenticated API call
- Can view events in real-time
- All infrastructure deployed and accessible

## Next Steps
After Phase 0 completes, move to Phase 1: Core Runtime + Basic Resilience
