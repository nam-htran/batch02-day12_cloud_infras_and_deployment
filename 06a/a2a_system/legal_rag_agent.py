import uvicorn
from fastapi import FastAPI
from pydantic import BaseModel
import sys, os
from pathlib import Path
from dotenv import load_dotenv
load_dotenv()

# Add root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
DAY08_ROOT = Path(__file__).resolve().parents[1]
if str(DAY08_ROOT) not in sys.path:
    sys.path.insert(0, str(DAY08_ROOT))
GROUP_PROJECT = DAY08_ROOT / "group_project"
if str(GROUP_PROJECT) not in sys.path:
    sys.path.insert(0, str(GROUP_PROJECT))

from src.module_rag_core.rag_engine import RAGCoreEngine
from system_contracts import ChatMessage, RAGConfig

app = FastAPI(title="A2A Legal RAG Agent")
engine = RAGCoreEngine()
ENGINE_STATUS = "not configured"


def _float_env(name: str, default: float) -> float:
    try:
        return float(os.getenv(name, default))
    except (TypeError, ValueError):
        return default


def _int_env(name: str, default: int) -> int:
    try:
        return int(os.getenv(name, default))
    except (TypeError, ValueError):
        return default


def _bool_env(name: str, default: bool) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def _configure_engine() -> None:
    """Configure the real RAG engine when keys/services are available.

    If live configuration fails, RAGCoreEngine still has deterministic local
    source documents. The response trace will make that visible instead of
    claiming a successful Weaviate lookup.
    """
    global ENGINE_STATUS
    config = RAGConfig(
        gemini_api_key=os.getenv("GEMINI_API_KEY", ""),
        llm_model_name=os.getenv("RAG_LLM_MODEL", os.getenv("OPENROUTER_MODEL", "google/gemini-2.5-flash")),
        temperature=_float_env("RAG_TEMPERATURE", 0.2),
        top_k=_int_env("RAG_TOP_K", 5),
        use_reranker=_bool_env("RAG_USE_RERANKER", True),
    )
    try:
        engine.configure(config)
        ENGINE_STATUS = "configured"
    except Exception as exc:
        ENGINE_STATUS = f"local fallback: {exc}"


def _trace_for_sources(sources: list) -> str:
    using_local_docs = any(str(getattr(source, "id", "")).startswith("local_") for source in sources)
    if using_local_docs:
        if ENGINE_STATUS.startswith("local fallback"):
            return f"LegalRAG ➡️ Dùng bộ tài liệu cục bộ ({ENGINE_STATUS})"
        return "LegalRAG ➡️ Dùng bộ tài liệu cục bộ vì vector store chưa khả dụng"
    return "LegalRAG ➡️ Truy vấn Weaviate DB thành công"


_configure_engine()

class ChatRequest(BaseModel):
    query: str
    history: list = []

@app.post("/generate")
def generate(request: ChatRequest):
    try:
        hist = [ChatMessage(**m) for m in request.history]
        ans = engine.generate_answer("default", request.query, hist)
        return {
            "answer": f"Thông tin từ cơ sở dữ liệu luật:\n{ans.answer}",
            "sources": [s.model_dump() for s in ans.sources],
            "trace": [_trace_for_sources(ans.sources)]
        }
    except Exception as e:
        return {
            "answer": f"Lỗi RAG: {e}",
            "sources": [],
            "trace": [f"LegalRAG ❌ Lỗi tra cứu ({e})"]
        }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=10101)
