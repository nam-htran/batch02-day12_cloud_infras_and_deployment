# Production AI Agent

A production-ready AI agent with FastAPI, Redis, rate limiting, and cost guarding.

## Setup Instructions

### 1. Clone the repository
```bash
git clone <repository_url>
cd 06-lab-complete
```

### 2. Configure Environment
Copy the environment template:
```bash
cp .env.example .env.local
```

### 3. Run with Docker Compose
```bash
docker compose up --build
```
The API will be available at `http://localhost:8000`.

### 4. Endpoints
- `GET /health`: Liveness check
- `GET /ready`: Readiness check
- `POST /ask`: Chat with the agent (Requires `X-API-Key` header)
