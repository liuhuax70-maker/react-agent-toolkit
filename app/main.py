"""FastAPI 应用入口。"""
from __future__ import annotations

import logging
import time

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from app import __version__
from app.agent import tools
from app.api import api_router
from app.config import BASE_DIR, get_settings
from app.errors import AppError
from app.logging_conf import setup_logging
from app.schemas import HealthResult, ReadyResult

logger = logging.getLogger("app")


def create_app() -> FastAPI:
    setup_logging()
    settings = get_settings()

    app = FastAPI(
        title=settings.app_name,
        description="基于 LangGraph 的 ReAct 智能体：自主规划并调用工具完成多步任务。",
        version=__version__,
    )

    @app.middleware("http")
    async def log_requests(request: Request, call_next):
        started = time.perf_counter()
        response = await call_next(request)
        cost_ms = (time.perf_counter() - started) * 1000
        logger.info(
            "%s %s -> %s (%.0fms)",
            request.method,
            request.url.path,
            response.status_code,
            cost_ms,
        )
        return response

    @app.exception_handler(AppError)
    async def handle_app_error(_: Request, exc: AppError) -> JSONResponse:
        return JSONResponse(status_code=exc.status_code, content={"detail": exc.message})

    app.include_router(api_router)

    @app.get("/health", response_model=HealthResult, tags=["system"])
    def health() -> HealthResult:
        """存活检查：进程可用即返回 ok。"""
        return HealthResult(status="ok", version=__version__, tools=tools.tool_names())

    @app.get("/ready", response_model=ReadyResult, tags=["system"])
    def ready() -> ReadyResult:
        """就绪检查：模型已配置、工具已注册。"""
        return ReadyResult(
            status="ready",
            llm_configured=not settings.missing_llm_key(),
            tools=len(tools.all_tools()),
        )

    app.mount(
        "/",
        StaticFiles(directory=str(BASE_DIR / "app" / "static"), html=True),
        name="static",
    )
    return app


app = create_app()
