from html.parser import HTMLParser
import sys
from pathlib import Path
from urllib.parse import parse_qs, unquote, urlparse

import requests
import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI
from pydantic import BaseModel

load_dotenv()

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

app = FastAPI(title="A2A Web Search Agent")


class ChatRequest(BaseModel):
    query: str
    history: list = []


class DuckDuckGoHTMLParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.results: list[dict[str, str]] = []
        self._current: dict[str, str] | None = None
        self._capture: str | None = None

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attr = dict(attrs)
        css = attr.get("class", "") or ""
        if tag == "a" and "result__a" in css:
            href = self._clean_url(attr.get("href", "") or "")
            self._current = {"title": "", "url": href, "snippet": ""}
            self._capture = "title"
        elif self._current is not None and "result__snippet" in css:
            self._capture = "snippet"

    def handle_data(self, data: str) -> None:
        if self._current is not None and self._capture:
            existing = self._current.get(self._capture, "")
            self._current[self._capture] = (existing + " " + data.strip()).strip()

    def handle_endtag(self, tag: str) -> None:
        if self._current is not None and tag == "a" and self._capture == "title":
            self.results.append(self._current)
            self._capture = None
        elif self._capture == "snippet":
            self._capture = None

    @staticmethod
    def _clean_url(url: str) -> str:
        parsed = urlparse(url)
        if parsed.path.startswith("/l/"):
            uddg = parse_qs(parsed.query).get("uddg", [""])[0]
            if uddg:
                return unquote(uddg)
        return url


def web_search(query: str, limit: int = 5) -> list[dict[str, str]]:
    response = requests.get(
        "https://duckduckgo.com/html/",
        params={"q": query},
        headers={"User-Agent": "Mozilla/5.0"},
        timeout=12,
    )
    response.raise_for_status()

    parser = DuckDuckGoHTMLParser()
    parser.feed(response.text)
    results = [
        result
        for result in parser.results
        if result.get("title") and result.get("url")
    ]
    return results[:limit]


@app.post("/generate")
def generate(request: ChatRequest):
    try:
        results = web_search(request.query)
    except Exception as exc:
        return {
            "answer": f"Không thể tìm kiếm web ở thời điểm này: {exc}",
            "sources": [],
            "trace": [f"WebSearch ❌ Lỗi tìm kiếm web ({exc})"],
        }

    if not results:
        return {
            "answer": "Không tìm thấy kết quả web phù hợp cho câu hỏi này.",
            "sources": [],
            "trace": ["WebSearch ➡️ Tìm kiếm web không có kết quả phù hợp"],
        }

    lines = ["Kết quả web liên quan:"]
    sources = []
    for index, result in enumerate(results, start=1):
        title = result["title"]
        url = result["url"]
        snippet = result.get("snippet", "")
        lines.append(f"{index}. {title}\n   {snippet}\n   Nguồn: {url}")
        sources.append(
            {
                "id": f"web_{index}",
                "content": snippet or title,
                "metadata": {"title": title, "source": url, "type": "web"},
                "score": None,
            }
        )

    return {
        "answer": "\n\n".join(lines),
        "sources": sources,
        "trace": ["WebSearch ➡️ Tìm kiếm web trực tiếp qua DuckDuckGo HTML"],
    }


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=10102)
