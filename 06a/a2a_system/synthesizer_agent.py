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

from common.llm import get_llm
from langchain_core.messages import SystemMessage, HumanMessage

app = FastAPI(title="A2A Synthesizer Agent")

class ChatRequest(BaseModel):
    query: str
    history: list = []
    context: str = ""

@app.post("/generate")
def generate(request: ChatRequest):
    context = request.context.strip()
    offline_mode = os.getenv("RAG_FORCE_OFFLINE", "").strip() in {"1", "true", "yes", "on"}
    if offline_mode or not os.getenv("OPENROUTER_API_KEY", "").strip():
        return {
            "answer": context or "Xin chào, bạn có thể hỏi mình về pháp luật phòng chống ma túy.",
            "sources": [],
            "trace": ["Synthesizer ➡️ Trả lời bằng context sẵn có vì LLM tổng hợp chưa khả dụng"]
        }

    try:
        llm = get_llm()
        if context:
            system_prompt = (
                "Bạn là Tổng hợp viên (Synthesizer). Chỉ dùng dữ liệu đã thu "
                "thập bên dưới để viết câu trả lời cuối cùng. Không tự thêm "
                "căn cứ pháp lý, số liệu, hoặc nguồn mới. Giữ lại citation "
                "trong ngoặc vuông nếu có. Nếu dữ liệu cho biết đang dùng "
                "nguồn dữ liệu cục bộ hoặc dịch vụ ngoài chưa khả dụng, diễn đạt trung thực và ngắn gọn.\n\n"
                f"[Dữ liệu thu thập]:\n{context}"
            )
        else:
            system_prompt = (
                "Bạn là trợ lý hội thoại cho hệ thống tư vấn pháp lý. Với câu "
                "chào hỏi hoặc trao đổi thông thường, trả lời ngắn gọn và mời "
                "người dùng hỏi về pháp luật phòng chống ma túy. Nếu câu hỏi "
                "cần kiến thức chuyên môn nhưng chưa có context, nói rằng cần "
                "chuyển tới worker phù hợp."
            )
        sys_msg = SystemMessage(content=system_prompt)
        response = llm.invoke([sys_msg, HumanMessage(content=request.query)])
        answer = response.content.strip()
        if not answer:
            answer = context or "Xin chào, bạn có thể hỏi mình về pháp luật phòng chống ma túy."
        return {
            "answer": answer,
            "sources": [],
            "trace": ["Synthesizer ➡️ Tổng hợp đáp án cuối cùng"]
        }
    except Exception as e:
        fallback_answer = context or f"Lỗi Synthesizer: {e}"
        return {
            "answer": fallback_answer,
            "sources": [],
            "trace": [f"Synthesizer ❌ Lỗi tổng hợp ({e})"]
        }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=10103)
