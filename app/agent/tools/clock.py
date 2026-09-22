"""时间工具。"""
from __future__ import annotations

from datetime import datetime

from app.agent.tools.base import BaseTool

_WEEKDAYS = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]


class ClockTool(BaseTool):
    name = "current_time"
    description = "获取当前日期与时间（本地时区）。涉及'今天''现在'的问题应先调用它。"
    parameters = {"type": "object", "properties": {}, "required": []}

    def run(self) -> str:
        now = datetime.now()
        return f"{now:%Y-%m-%d %H:%M:%S}（{_WEEKDAYS[now.weekday()]}）"
