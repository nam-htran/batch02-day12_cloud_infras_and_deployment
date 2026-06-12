# Deployment Information

## Public URL
https://day12-deplayed-production.up.railway.app

## Platform
Railway

## Test Instructions
This is a Streamlit Web Application. To test the deployment:
1. Open your web browser and navigate to: `https://day12-deplayed-production.up.railway.app`
2. Ensure the Chat UI loads successfully.
3. Try asking a question to verify the integrated RAG core is functioning.

*(Note: Streamlit apps do not have standard `/health` or `/ask` API endpoints. You interact with it directly via the UI)*

## Environment Variables Set
- PORT (Assigned by Railway)
- WEAVIATE_URL (If using external Weaviate)
- GEMINI_API_KEY=***
- OPENROUTER_API_KEY=***

## Screenshots
- [Deployment dashboard](assets/dashboard.png)
- [Service running](assets/running.png)
- [Test results](assets/test.png)
