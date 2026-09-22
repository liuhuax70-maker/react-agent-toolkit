"""工具执行：参数解析、错误重试与兜底。

任何失败都转成字符串返回，保证 ReAct 循环不会因单个工具异常而中断。
"""
from __future__ import annotations

import json
import logging

from app.agent import tools

logger = logging.getLogger(__name__)


def execute(name: str, arguments: str, retries: int = 0) -> dict:
    """执行工具并返回结构化结果。

    返回 {"ok": bool, "content": str, "result": str, "error": str | None}
    content 用于回填给模型的 tool 消息。
    """
    tool = tools.get_tool(name)
    if tool is None:
        error = f"未知工具：{name}（可用：{', '.join(tools.tool_names())}）"
        return {"ok": False, "content": error, "result": "", "error": error}

    try:
        kwargs = json.loads(arguments) if arguments else {}
        if not isinstance(kwargs, dict):
            raise ValueError("参数必须是 JSON 对象")
    except (json.JSONDecodeError, ValueError) as exc:
        error = f"参数解析失败：{exc}；收到的参数为 {arguments!r}"
        return {"ok": False, "content": error, "result": "", "error": error}

    last_error = ""
    for attempt in range(retries + 1):
        try:
            result = str(tool.run(**kwargs))
            return {"ok": True, "content": result, "result": result, "error": None}
        except Exception as exc:
            last_error = f"{type(exc).__name__}: {exc}"
            logger.warning("工具 %s 第 %d 次执行失败：%s", name, attempt + 1, last_error)

    error = f"工具 {name} 执行失败（已尝试 {retries + 1} 次）：{last_error}"
    return {"ok": False, "content": error, "result": "", "error": error}
