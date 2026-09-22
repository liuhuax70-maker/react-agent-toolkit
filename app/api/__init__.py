"""API 路由聚合。"""
from fastapi import APIRouter

from app.api import agent
from app.config import get_settings

api_router = APIRouter(prefix=get_settings().api_prefix)
api_router.include_router(agent.router)
