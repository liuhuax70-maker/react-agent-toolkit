"""智能体用例。"""
from __future__ import annotations

import logging
from typing import Iterator

from app.agent.graph import ReActAgent
from app.config import Settings, get_settings
from app.llm import LLMClient

logger = logging.getLogger(__name__)


class AgentService:
    def __init__(self, llm: LLMClient, settings: Settings | None = None) -> None:
        self.llm = llm
        self.settings = settings or get_settings()

    def _agent(self, max_steps: int | None = None) -> ReActAgent:
        return ReActAgent(self.llm, self.settings, max_steps)

    def run(self, question: str, max_steps: int | None = None) -> dict:
        """同步执行一次任务，返回答案与工具调用轨迹。"""
        result = self._agent(max_steps).run(question)
        logger.info(
            "任务完成：%d 次工具调用，%d 步",
            len(result["tool_calls"]),
            result["steps"],
        )
        return result

    def stream(self, question: str, max_steps: int | None = None) -> Iterator[dict]:
        """流式执行，产出 step / token / tool_call / tool_result / final / error 事件。"""
        return self._agent(max_steps).stream(question)
