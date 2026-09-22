"""工具执行器：未知工具、参数错误与重试。"""
from app.agent import executor, tools
from app.agent.tools.base import BaseTool


class FlakyTool(BaseTool):
    """前两次失败、第三次成功的工具，用于验证重试。"""

    name = "flaky"
    description = "测试用工具"
    parameters = {"type": "object", "properties": {}, "required": []}

    def __init__(self, fail_times: int = 2) -> None:
        self.fail_times = fail_times
        self.calls = 0

    def run(self, **kwargs) -> str:
        self.calls += 1
        if self.calls <= self.fail_times:
            raise RuntimeError(f"第 {self.calls} 次失败")
        return "成功"


def test_unknown_tool_returns_error():
    outcome = executor.execute("no_such_tool", "{}")
    assert outcome["ok"] is False
    assert "未知工具" in outcome["error"]


def test_invalid_arguments_returns_error():
    outcome = executor.execute("calculator", "{not json")
    assert outcome["ok"] is False
    assert "参数解析失败" in outcome["error"]


def test_retry_until_success():
    tool = FlakyTool(fail_times=2)
    tools.register(tool)
    try:
        outcome = executor.execute("flaky", "{}", retries=2)
        assert outcome["ok"] is True
        assert outcome["result"] == "成功"
        assert tool.calls == 3
    finally:
        tools.unregister("flaky")


def test_exhausted_retries_returns_error():
    tool = FlakyTool(fail_times=5)
    tools.register(tool)
    try:
        outcome = executor.execute("flaky", "{}", retries=1)
        assert outcome["ok"] is False
        assert "执行失败" in outcome["error"]
        assert tool.calls == 2
    finally:
        tools.unregister("flaky")
