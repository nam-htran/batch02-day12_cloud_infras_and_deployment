import os
import json
import logging
import signal
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, Depends, Request, HTTPException
import redis
import uvicorn

from .config import settings
from .auth import verify_api_key
from .rate_limiter import check_rate_limit
from .cost_guard import check_budget

from src.module_rag_core.rag_engine import RAGCoreEngine
from system_contracts import RAGConfig

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

is_ready = False
redis_client = None
rag_engine = RAGCoreEngine()

@asynccontextmanager
async def lifespan(app: FastAPI):
    global is_ready, redis_client
    
    logger.info("Initializing Agent...")
    try:
        redis_client = redis.from_url(settings.redis_url, decode_responses=True)
        redis_client.ping()
        rag_engine.configure(RAGConfig(gemini_api_key=os.getenv("GEMINI_API_KEY", "")))
        is_ready = True
        logger.info("Connected to Redis successfully.")
    except Exception as e:
        logger.error(f"Failed to connect to Redis: {e}")
        
    yield
    
    # Graceful Shutdown
    is_ready = False
    logger.info("Shutting down safely...")
    if redis_client:
        redis_client.close()

app = FastAPI(title=settings.app_name, version=settings.app_version, lifespan=lifespan)

# Health Checks
@app.get("/health")
def health():
    return {"status": "ok", "message": "Container is alive"}

@app.get("/ready")
def ready():
    if not is_ready:
        raise HTTPException(status_code=503, detail="Agent is not ready to serve traffic")
    return {"status": "ready"}

# Main Agent Endpoint
@app.post("/ask")
async def ask_agent(
    request: Request,
    user_id: str = Depends(verify_api_key)
):
    body = await request.json()
    question = body.get("question")
    if not question:
        raise HTTPException(status_code=422, detail="Thiếu trường 'question'")
        
    # Check Rate Limit
    check_rate_limit(user_id, redis_client)
    
    # Giả lập tính toán chi phí (VD mỗi request tốn 0.01$)
    estimated_cost = 0.01
    check_budget(user_id, estimated_cost, redis_client)
    
    # Gọi LLM xử lý
    try:
        rag_ans = rag_engine.generate_answer("api_user", question, [])
        answer = rag_ans.answer
    except Exception as e:
        answer = f"System Error: {str(e)}"
    
    # Lưu History xuống Redis (Stateless design)
    history_key = f"history:{user_id}"
    history_entry = json.dumps({"q": question, "a": answer})
    redis_client.rpush(history_key, history_entry)
    
    return {
        "question": question,
        "answer": answer,
        "platform": "Docker/Cloud",
        "estimated_cost": estimated_cost
    }

def handle_sigterm(*args):
    logger.info("Received SIGTERM. Stop accepting traffic...")

signal.signal(signal.SIGTERM, handle_sigterm)

if __name__ == "__main__":
    uvicorn.run("app.main:app", host=settings.host, port=settings.port)
