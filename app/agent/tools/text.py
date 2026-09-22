"""文本统计工具。"""
from __future__ import annotations

from app.agent.tools.base import BaseTool


class TextStatsTool(BaseTool):
    name = "text_stats"
    description = "统计一段文本的字符数（含/不含空白）、行数与词数。"
    parameters = {
        "type": "object",
        "properties": {"text": {"type": "string", "description": "要统计的文本"}},
        "required": ["text"],
    }

    def run(self, text: str) -> str:
        compact = "".join(text.split())
        lines = [line for line in text.splitlines() if line.strip()]
        return (
            f"字符数（含空白）：{len(text)}\n"
            f"字符数（去空白）：{len(compact)}\n"
            f"行数（非空）：{len(lines)}\n"
            f"词数（按空白切分）：{len(text.split())}"
        )
