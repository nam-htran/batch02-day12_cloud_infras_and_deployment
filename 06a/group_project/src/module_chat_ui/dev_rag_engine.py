from typing import List

from system_contracts import ChatMessage, Document, RAGAnswer, RAGConfig, RAGCoreInterface


class DevelopmentRAGCore(RAGCoreInterface):
    """Contract-compatible local engine used only if the configured engine cannot load."""

    def __init__(self) -> None:
        self.config = RAGConfig(gemini_api_key="")
        self.sessions: dict[str, list[ChatMessage]] = {}

    def configure(self, config: RAGConfig) -> None:
        self.config = config

    def generate_answer(
        self,
        session_id: str,
        user_query: str,
        chat_history: List[ChatMessage],
    ) -> RAGAnswer:
        self.sessions.setdefault(session_id, [])
        answer = (
            "The configured RAG engine could not be loaded, so this local contract "
            "engine is returning a diagnostic response. "
            f"Your question was: {user_query}\n\n"
            "Check the import error shown in the Streamlit sidebar before using this "
            "session as a live retrieval demo."
        )
        source = Document(
            id="ui-local-contract-source",
            content=(
                "Diagnostic source emitted by DevelopmentRAGCore when the configured "
                "RAG engine cannot be imported."
            ),
            metadata={
                "title": "Development fallback",
                "model": self.config.llm_model_name,
                "top_k": self.config.top_k,
                "reranker": self.config.use_reranker,
                "history_turns": len(chat_history),
            },
            score=1.0,
        )
        self.sessions[session_id].extend(
            [
                ChatMessage(role="user", content=user_query),
                ChatMessage(role="assistant", content=answer),
            ]
        )
        return RAGAnswer(answer=answer, sources=[source], standalone_query=user_query)

    def clear_session(self, session_id: str) -> None:
        self.sessions.pop(session_id, None)
