"""请求 / 响应模型（API 契约）。"""
from __future__ import annotations

from pydantic import BaseModel, Field


class RunRequest(BaseModel):
    question: str = Field(..., min_length=1, description="交给智能体处理的任务")
    max_steps: int | None = Field(None, ge=1, le=20, description="本次运行的最大步数")


class ToolCallRecord(BaseModel):
    name: str
    arguments: str = ""
    ok: bool = True
    result: str = ""
    error: str | None = None


class RunResult(BaseModel):
    answer: str
    tool_calls: list[ToolCallRecord] = Field(default_factory=list)
    steps: int = 0


class HealthResult(BaseModel):
    status: str
    version: str
    tools: list[str] = Field(default_factory=list)


class ReadyResult(BaseModel):
    status: str
    llm_configured: bool
    tools: int = 0
