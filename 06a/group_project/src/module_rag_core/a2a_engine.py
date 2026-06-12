import os
import requests
from typing import List, Sequence
from system_contracts import RAGCoreInterface, RAGConfig, RAGAnswer, ChatMessage, Document

class A2ARAGCoreEngine(RAGCoreInterface):
    """
    RAG Core Engine that acts as an API client to the A2A Supervisor.
    """
    
    def __init__(self):
        self.supervisor_url = os.getenv("A2A_SUPERVISOR_URL", "http://localhost:10100/generate")
        self.config = None

    def configure(self, config: RAGConfig) -> None:
        self.config = config

    def clear_session(self, session_id: str) -> None:
        # The A2A supervisor is stateless; UI state owns the conversation history.
        return None

    def generate_answer(
        self, session_id: str, user_query: str, chat_history: List[ChatMessage]
    ) -> RAGAnswer:
        
        history_dicts = [{"role": msg.role, "content": msg.content} for msg in chat_history]
        
        try:
            resp = requests.post(
                self.supervisor_url,
                json={"query": user_query, "history": history_dicts},
                timeout=60
            )
            resp.raise_for_status()
            data = resp.json()
            
            final_ans = data.get("answer", "Lỗi: Không có câu trả lời")
            sources_data = data.get("sources", [])
            trace = data.get("trace", [])
            
            sources = []
            for s in sources_data:
                sources.append(Document(
                    id=s.get("id", ""),
                    content=s.get("content", ""),
                    metadata=s.get("metadata", {}),
                    score=s.get("score", 1.0)
                ))
            
            flow_lines = []
            route_node = ""
            for t in trace:
                if "legal_rag" in t and "Định tuyến" in t:
                    flow_lines.append("`[👤 Người dùng]` ➜ `[🧠 Supervisor]` ➜ Định tuyến tới ➜ `[⚖️ Legal RAG]`")
                    route_node = "Legal RAG"
                elif "web_search" in t and "Định tuyến" in t:
                    flow_lines.append("`[👤 Người dùng]` ➜ `[🧠 Supervisor]` ➜ Định tuyến tới ➜ `[🌐 Web Search]`")
                    route_node = "Web Search"
                elif "synthesizer" in t and "Định tuyến" in t:
                    flow_lines.append("`[👤 Người dùng]` ➜ `[🧠 Supervisor]` ➜ Định tuyến tới ➜ `[✍️ Synthesizer]`")
                    route_node = "Synthesizer"
                elif "Weaviate" in t:
                    flow_lines.append(f"`[{route_node}]` ➜ 🔍 Tra cứu ➜ `[📚 Weaviate DB]`")
                elif "MCP" in t:
                    flow_lines.append(f"`[{route_node}]` ➜ 🔌 Gọi Tool ➜ `[MCP Server]`")
                elif "Synthesizer" in t and "Tổng hợp" in t:
                    if route_node and route_node != "Synthesizer":
                        flow_lines.append(f"`[{route_node}]` ➜ Trả dữ liệu về ➜ `[✍️ Synthesizer]`")
                    flow_lines.append("`[✍️ Synthesizer]` ➜ 💬 Trả kết quả cuối cùng ➜ `[👤 Người dùng]`")
            
            flow_str = "\n\n".join(flow_lines)
            display_answer = f"### 🧠 Luồng thực thi A2A\n{flow_str}\n\n---\n### 💡 Kết quả\n{final_ans}"
            
            return RAGAnswer(
                answer=display_answer,
                sources=sources,
                standalone_query=user_query
            )
            
        except Exception as e:
            return RAGAnswer(
                answer=f"Lỗi khi gọi A2A Supervisor (chắc bạn chưa bật Terminal chạy Server): {e}",
                sources=[],
                standalone_query=user_query
            )
