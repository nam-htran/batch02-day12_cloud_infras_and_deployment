import json
import os
import sys
from pathlib import Path

import requests
import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI
from langchain_core.messages import HumanMessage, SystemMessage
from pydantic import BaseModel

load_dotenv()

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from common.llm import get_llm

app = FastAPI(title="A2A Supervisor Agent")

VALID_ROUTES = {"legal_rag", "web_search", "synthesizer"}
URLS = {
    "legal_rag": os.getenv("RAG_URL", "http://localhost:10101/generate"),
    "web_search": os.getenv("WEB_URL", "http://localhost:10102/generate"),
    "synthesizer": os.getenv("SYNTH_URL", "http://localhost:10103/generate"),
}


class ChatRequest(BaseModel):
    query: str
    history: list = []


def _normalize_route(raw_route: str) -> str | None:
    route = raw_route.strip().lower().strip("`'\" ")
    if route in VALID_ROUTES:
        return route

    if route.startswith("{"):
        try:
            parsed = json.loads(route)
            parsed_route = str(parsed.get("route", "")).strip().lower()
            if parsed_route in VALID_ROUTES:
                return parsed_route
        except json.JSONDecodeError:
            pass

    matches = [candidate for candidate in VALID_ROUTES if candidate in route]
    if len(matches) == 1:
        return matches[0]
    return None


def _route_with_llm(query: str) -> tuple[str, str]:
    prompt = """Bạn là Supervisor của hệ thống tư vấn pháp lý.
Phân loại ý định của người dùng vào đúng một route:
- legal_rag: câu hỏi cần tra cứu corpus luật phòng chống ma túy / quy định pháp luật Việt Nam.
- web_search: câu hỏi yêu cầu thông tin mới, tin tức, sự kiện, hoặc dữ liệu ngoài corpus.
- synthesizer: chào hỏi, cảm ơn, trò chuyện ngắn, hoặc câu không cần worker chuyên môn.

Chỉ trả về JSON hợp lệ dạng: {"route": "legal_rag" | "web_search" | "synthesizer"}"""

    if os.getenv("RAG_FORCE_OFFLINE", "").strip().lower() in {"1", "true", "yes", "on"}:
        return "legal_rag", "Supervisor LLM routing skipped because RAG_FORCE_OFFLINE is enabled"
    if not os.getenv("OPENROUTER_API_KEY", "").strip():
        return "legal_rag", "Supervisor LLM routing skipped because OPENROUTER_API_KEY is not configured"

    try:
        response = get_llm().invoke(
            [SystemMessage(content=prompt), HumanMessage(content=query)]
        )
        route = _normalize_route(response.content)
        if route:
            return route, ""
        return "legal_rag", "Supervisor LLM returned an invalid route; defaulting to legal_rag"
    except Exception as exc:
        return "legal_rag", f"Supervisor LLM routing failed ({exc}); defaulting to legal_rag"


@app.post("/generate")
def generate(request: ChatRequest):
    next_route, routing_note = _route_with_llm(request.query)
    trace = [f"Supervisor ➡️ Định tuyến tới {next_route}"]
    if routing_note:
        trace.append(routing_note)

    try:
        url = URLS[next_route]
        resp = requests.post(url, json=request.model_dump(), timeout=60)
        resp.raise_for_status()
        data = resp.json()

        if next_route in {"legal_rag", "web_search"}:
            trace.append(f"{next_route} ➡️ Chuyển dữ liệu cho Synthesizer tổng hợp")
            synth_payload = request.model_dump()
            synth_payload["context"] = data.get("answer", "")

            synth_resp = requests.post(
                URLS['synthesizer'],
                json=synth_payload,
                timeout=60,
            )
            synth_resp.raise_for_status()
            synth_data = synth_resp.json()

            return {
                "answer": synth_data.get("answer", ""),
                "sources": data.get("sources", []),
                "trace": trace + data.get("trace", []) + synth_data.get("trace", []),
            }

        return {
            "answer": data.get("answer", ""),
            "sources": data.get("sources", []),
            "trace": trace + data.get("trace", []),
        }
    except Exception as exc:
        trace.append(f"Lỗi gọi {next_route} ({exc}) ➡️ Fallback to synthesizer")
        if next_route != "synthesizer":
            try:
                resp = requests.post(
                    URLS['synthesizer'],
                    json=request.model_dump(),
                    timeout=60,
                )
                resp.raise_for_status()
                data = resp.json()
                return {
                    "answer": data.get("answer", ""),
                    "sources": data.get("sources", []),
                    "trace": trace + data.get("trace", []),
                }
            except Exception as fallback_exc:
                return {
                    "answer": f"Lỗi hệ thống: {fallback_exc}",
                    "sources": [],
                    "trace": trace,
                }
        return {"answer": f"Lỗi hệ thống: {exc}", "sources": [], "trace": trace}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=10100)
