"""工具注册表。

新增工具：实现 BaseTool 子类并在文件末尾 register()，智能体即自动获得该能力，
无需修改编排或接口代码。
"""
from __future__ import annotations

from app.agent.tools.base import BaseTool
from app.agent.tools.calculator import CalculatorTool
from app.agent.tools.clock import ClockTool
from app.agent.tools.files import FileListTool, FileReadTool, FileWriteTool
from app.agent.tools.search import WebSearchTool
from app.agent.tools.text import TextStatsTool

_TOOLS: dict[str, BaseTool] = {}


def register(tool: BaseTool) -> None:
    _TOOLS[tool.name] = tool


def unregister(name: str) -> None:
    _TOOLS.pop(name, None)


def get_tool(name: str) -> BaseTool | None:
    return _TOOLS.get(name)


def all_tools() -> list[BaseTool]:
    return list(_TOOLS.values())


def tool_names() -> list[str]:
    return sorted(_TOOLS)


def specs() -> list[dict]:
    return [tool.spec() for tool in _TOOLS.values()]


register(CalculatorTool())
register(ClockTool())
register(FileWriteTool())
register(FileReadTool())
register(FileListTool())
register(TextStatsTool())
register(WebSearchTool())
