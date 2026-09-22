"""领域异常。

服务层只抛领域异常，由 API 层统一映射为 HTTP 状态码。
"""
from __future__ import annotations


class AppError(Exception):
    status_code = 400

    def __init__(self, message: str, status_code: int | None = None) -> None:
        super().__init__(message)
        self.message = message
        if status_code is not None:
            self.status_code = status_code


class ToolNotFound(AppError):
    """调用了未注册的工具。"""


class ToolExecutionError(AppError):
    """工具执行失败且重试后仍未成功。"""


class BackendUnavailable(AppError):
    """依赖的后端不可用（如未配置模型 Key）。"""

    status_code = 503
