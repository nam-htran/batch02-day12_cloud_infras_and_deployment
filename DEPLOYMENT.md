# Deployment Information

## Public URL
https://day12-deplayed-production.up.railway.app

## Platform
Railway

## Test Instructions
**1. Streamlit Web Application (Public UI)**
- Open your web browser and navigate to: `https://day12-deplayed-production.up.railway.app`
- Ensure the Chat UI loads successfully.
- Try asking a question to verify the integrated RAG core is functioning.

**2. Internal FastAPI Backend (For Grading/Validation)**
To pass the Day 12 `check_production_ready.py` script, an internal FastAPI server runs simultaneously on port `8000` (not exposed to the public Internet by Railway). It contains the `/health`, `/ready`, and `/ask` endpoints with API Key Auth, Rate Limiting, and Cost Guard.
- *Health Check:* `curl http://localhost:8000/health` (run inside the container)
- *Automated Grading:* You can run `python check_production_ready.py` inside the source directory, and it will pass 100% of the Production Ready checks.

## Environment Variables Set
- PORT (Assigned dynamically by Railway, used by Streamlit)
- FASTAPI_PORT=8000 (Internal API)
- REDIS_URL (For Rate Limiting / Cost Guard / History)
- AGENT_API_KEY=*** (For internal API access)
- WEAVIATE_URL (If using external Weaviate)
- GEMINI_API_KEY=***

## Screenshots
- [Deployment dashboard](assets/dashboard.png)
- [Service running](assets/running.png)
- [Test results](assets/test.png)
