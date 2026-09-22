"""应用配置。

所有可变参数集中在 Settings 中，从环境变量 / .env 读取；
API Key 只在这里出现，其他模块不接触硬编码密钥。
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent

load_dotenv(BASE_DIR / ".env", override=False)


def _env(name: str, default: str) -> str:
    return os.getenv(name, default)


def _env_int(name: str, default: str) -> int:
    return int(os.getenv(name, default))


def _env_float(name: str, default: str) -> float:
    return float(os.getenv(name, default))


def _env_path(name: str, default: str) -> Path:
    value = Path(os.getenv(name, default))
    return value if value.is_absolute() else BASE_DIR / value


@dataclass(frozen=True)
class Settings:
    app_name: str = "多工具 ReAct 智能体"
    api_prefix: str = "/api/v1"

    # LLM
    llm_api_key: str = field(default_factory=lambda: _env("DEEPSEEK_API_KEY", ""))
    llm_base_url: str = field(default_factory=lambda: _env("DEEPSEEK_BASE_URL", "https://api.deepseek.com"))
    llm_model: str = field(default_factory=lambda: _env("LLM_MODEL", "deepseek-chat"))
    llm_temperature: float = field(default_factory=lambda: _env_float("LLM_TEMPERATURE", "0.2"))

    # Agent
    max_steps: int = field(default_factory=lambda: _env_int("MAX_STEPS", "6"))
    tool_retries: int = field(default_factory=lambda: _env_int("TOOL_RETRIES", "2"))
    tool_timeout: float = field(default_factory=lambda: _env_float("TOOL_TIMEOUT", "10"))

    # 工具工作目录
    workspace_dir: Path = field(default_factory=lambda: _env_path("WORKSPACE_DIR", "data/workspace"))

    # 日志
    log_level: str = field(default_factory=lambda: _env("LOG_LEVEL", "INFO").upper())

    def missing_llm_key(self) -> bool:
        return not self.llm_api_key or self.llm_api_key.startswith("sk-your")


@lru_cache
def get_settings() -> Settings:
    return Settings()
