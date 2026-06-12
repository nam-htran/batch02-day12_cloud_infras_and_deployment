import os
import re
from typing import List
from system_contracts import ChatMessage
from src.module_rag_core.ports.outbound import LLMServicePort

# Langchain
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage

class OpenRouterAdapter(LLMServicePort):
    """
    OpenRouter LLM client implementing the LLMServicePort interface.
    """
    
    def __init__(self) -> None:
        self.llm = None
        self.temperature = 0.2
        
    def configure(self, api_key: str, model_name: str, temperature: float) -> None:
        """
        Configure the LLM client. Note: api_key here is meant to be gemini_api_key in config,
        but we ignore it and read OPENROUTER_API_KEY from environment instead.
        """
        self.temperature = temperature
        if os.getenv("RAG_FORCE_OFFLINE", "").strip() in {"1", "true", "yes", "on"}:
            self.llm = None
            print("RAG_FORCE_OFFLINE is enabled. Using extractive answer composer.")
            return

        openrouter_key = os.getenv("OPENROUTER_API_KEY")
        if not openrouter_key:
            self.llm = None
            print("OPENROUTER_API_KEY not found. Using extractive answer composer.")
            return
            
        self.llm = ChatOpenAI(
            api_key=openrouter_key,
            model="google/gemini-2.5-flash",
            temperature=self.temperature,
            max_tokens=int(os.getenv("OPENROUTER_MAX_TOKENS", "1200")),
            base_url="https://openrouter.ai/api/v1",
            default_headers={
                "HTTP-Referer": "http://localhost:8501",
                "X-Title": "LegalRAG",
            }
        )

    def embed_query(self, query: str) -> List[float]:
        # No OpenRouter embedding adapter is configured here. Returning an empty
        # vector lets Weaviate use lexical/hybrid text search instead of sending
        # a fake vector with the wrong dimensionality.
        return []

    def condense_query(self, chat_history: List[ChatMessage], latest_query: str) -> str:
        """Condense a multi-turn conversation and follow-up query into a standalone query."""
        if not chat_history or not self.llm:
            return latest_query
            
        history_text = "\n".join(
            f"{message.role}: {message.content}" for message in chat_history
        )
        prompt = (
            "Rewrite the latest Vietnamese message into a standalone query.\n"
            "Rules:\n"
            "1. If the message is a greeting, thanks, or small talk, return it unchanged.\n"
            "2. Return only the rewritten query, with no explanation.\n\n"
            f"History:\n{history_text}\n\nLatest message: {latest_query}"
        )
        try:
            response = self.llm.invoke([HumanMessage(content=prompt)])
            return response.content.strip()
        except Exception as e:
            print(f"OpenRouter condense_query error: {e}")
            return latest_query

    def generate_answer(self, system_prompt: str, context: str, query: str) -> str:
        """Synthesize a response with inline citations based on the provided context."""
        if not self.llm:
            return self._extractive_answer(context=context, query=query)
            
        prompt = (
            f"System: {system_prompt}\n\n"
            f"Context:\n{context}\n\n"
            f"Question: {query}\n\n"
            "Answer in Vietnamese with inline citations:"
        )
        try:
            response = self.llm.invoke([HumanMessage(content=prompt)])
            return response.content.strip()
        except Exception as e:
            print(f"OpenRouter generate_answer error: {e}")
            return self._extractive_answer(context=context, query=query)

    def _extractive_answer(self, context: str, query: str) -> str:
        blocks = self._parse_context_blocks(context)
        if not blocks:
            return "Tôi không thể xác minh thông tin này từ các tài liệu hiện có."

        bullets = []
        for source, content in blocks[:2]:
            snippet = self._first_sentence(content)
            bullets.append(f"- {snippet} [{source}]")

        return (
            "Không gọi được LLM trong môi trường hiện tại. Dưới đây là phần "
            f"trích xuất trực tiếp từ tài liệu cho câu hỏi: {query}\n\n"
            + "\n".join(bullets)
        )

    @staticmethod
    def _parse_context_blocks(context: str) -> list[tuple[str, str]]:
        blocks: list[tuple[str, str]] = []
        pattern = re.compile(r"Tai lieu \[(?P<source>[^\]]+)\]:\n(?P<body>.*?)(?=\n\nTai lieu \[|\Z)", re.S)
        for match in pattern.finditer(context):
            source = match.group("source").strip()
            body = match.group("body").strip()
            if body:
                blocks.append((source, body))
        return blocks

    @staticmethod
    def _first_sentence(text: str, limit: int = 320) -> str:
        cleaned = " ".join(text.split())
        for separator in [". ", "; ", "\n"]:
            if separator in cleaned:
                cleaned = cleaned.split(separator, 1)[0]
                break
        if len(cleaned) > limit:
            cleaned = cleaned[:limit].rstrip() + "..."
        return cleaned
