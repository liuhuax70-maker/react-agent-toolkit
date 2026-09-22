"""依赖装配：把能力层组装成用例服务，注入到路由。"""
from __future__ import annotations

from functools import lru_cache

from app.config import get_settings
from app.llm import get_llm
from app.services.agent import AgentService


@lru_cache
def get_agent_service() -> AgentService:
    return AgentService(get_llm(), get_settings())
