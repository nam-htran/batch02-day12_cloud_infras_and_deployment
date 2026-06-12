# Deployment Information

## Public URL
https://batch02-day12cloudinfrasanddeployment-production-32e0.up.railway.app

## Platform
Railway

## Test Commands

### Health Check
```bash
curl https://batch02-day12cloudinfrasanddeployment-production-32e0.up.railway.app/health
# Expected: {"status": "ok", "message": "Container is alive"}
```

### API Test (with authentication)
```bash
curl -X POST https://batch02-day12cloudinfrasanddeployment-production-32e0.up.railway.app/ask \
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
- [Deployment dashboard](assets/dashboard.png)
- [Service running](assets/running.png)
- [Test results](assets/test.png)
