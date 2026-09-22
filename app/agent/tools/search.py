"""联网搜索工具。

使用 DuckDuckGo 的 HTML 端点，无需 API Key。需要外网访问；
请求失败会抛异常，由 executor 统一处理并返回可读错误。
"""
from __future__ import annotations

import re

import httpx

from app.agent.tools.base import BaseTool
from app.config import get_settings

_ENDPOINT = "https://html.duckduckgo.com/html/"
_RESULT_RE = re.compile(
    r'<a[^>]*class="result__a"[^>]*href="([^"]+)"[^>]*>(.*?)</a>', re.S
)
_TAG_RE = re.compile(r"<[^>]+>")


class WebSearchTool(BaseTool):
    name = "web_search"
    description = "联网搜索关键词，返回若干条标题与链接。需要最新或外部信息时使用。"
    parameters = {
        "type": "object",
        "properties": {
            "query": {"type": "string", "description": "搜索关键词"},
            "limit": {"type": "integer", "description": "返回条数，默认 5"},
        },
        "required": ["query"],
    }

    def run(self, query: str, limit: int = 5) -> str:
        response = httpx.post(
            _ENDPOINT,
            data={"q": query},
            timeout=get_settings().tool_timeout,
            headers={"User-Agent": "Mozilla/5.0"},
            follow_redirects=True,
        )
        response.raise_for_status()
        matches = _RESULT_RE.findall(response.text)[: max(1, int(limit))]
        if not matches:
            return f"未找到与「{query}」相关的结果"
        lines = [
            f"{index}. {_TAG_RE.sub('', title).strip()} — {url}"
            for index, (url, title) in enumerate(matches, start=1)
        ]
        return "\n".join(lines)
