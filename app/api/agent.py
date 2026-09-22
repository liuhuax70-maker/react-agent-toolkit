"""智能体接口。"""
from __future__ import annotations

import json

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse

from app.agent import tools
from app.api.deps import get_agent_service
from app.schemas import RunRequest, RunResult
from app.services.agent import AgentService

router = APIRouter(prefix="/agent", tags=["agent"])


def _sse(payload: dict) -> str:
    return f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"


@router.post("/run", response_model=RunResult, summary="同步执行任务")
def run(request: RunRequest, service: AgentService = Depends(get_agent_service)) -> RunResult:
    return RunResult(**service.run(request.question, request.max_steps))


@router.post("/stream", summary="流式执行任务（SSE）")
def stream(request: RunRequest, service: AgentService = Depends(get_agent_service)):
    def event_stream():
        for event in service.stream(request.question, request.max_steps):
            yield _sse(event)
        yield "data: [DONE]\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")


@router.get("/tools", summary="已注册工具列表")
def list_tools() -> dict:
    return {
        "tools": [
            {"name": tool.name, "description": tool.description}
            for tool in tools.all_tools()
        ]
    }
