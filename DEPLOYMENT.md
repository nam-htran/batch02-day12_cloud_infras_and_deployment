# Deployment Information

## Public URL
https://vinai-day12-production-6dac.up.railway.app

## Platform
Railway

## Test Commands

### Health Check
```bash
curl https://vinai-day12-production-6dac.up.railway.app/health
# Expected: {"status": "ok", "message": "Container is alive"}
```

### API Test (with authentication)
```bash
curl -X POST https://vinai-day12-production-6dac.up.railway.app/ask \
  -H "X-API-Key: secret-key-123" \
  -H "Content-Type: application/json" \
  -d '{"question": "Hello"}'
```

## Environment Variables Set
- PORT=8000
- REDIS_URL=redis://localhost:6379/0 (Using internal Railway Redis)
- AGENT_API_KEY=secret-key-123
- RATE_LIMIT_PER_MINUTE=10
- MONTHLY_BUDGET_USD=10.0

## Screenshots
- [Deployment dashboard](screenshots/dashboard.png)
- [Service running](screenshots/running.png)
- [Test results](screenshots/test.png)
