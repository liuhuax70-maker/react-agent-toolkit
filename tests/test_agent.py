"""ReAct 循环测试（使用脚本化假 LLM，无需网络）。"""
from app.agent.graph import ReActAgent
from app.config import get_settings


def _tool_call(name: str, arguments: str, call_id: str = "call_1") -> dict:
    return {
        "role": "assistant",
        "content": "",
        "tool_calls": [
            {
                "id": call_id,
                "type": "function",
                "function": {"name": name, "arguments": arguments},
            }
        ],
    }


class ScriptedLLM:
    """按脚本依次返回消息，模拟多轮推理。"""

    def __init__(self, script: list[dict]) -> None:
        self.script = list(script)
        self.calls = 0

    def _next(self) -> dict:
        message = self.script[min(self.calls, len(self.script) - 1)]
        self.calls += 1
        return message

    def complete(self, messages, tools=None) -> dict:
        return self._next()

    def stream_complete(self, messages, tools=None):
        message = self._next()
        for char in message.get("content") or "":
            yield {"type": "token", "content": char}
        yield {"type": "message", "message": message}


class AlwaysToolLLM:
    """永远要求调用工具，用于验证步数上限。"""

    def complete(self, messages, tools=None) -> dict:
        return _tool_call("calculator", '{"expression": "1+1"}')

    def stream_complete(self, messages, tools=None):
        yield {"type": "message", "message": _tool_call("calculator", '{"expression": "1+1"}')}


def test_agent_calls_tool_then_answers():
    llm = ScriptedLLM(
        [
            _tool_call("calculator", '{"expression": "(12+8)*3"}'),
            {"role": "assistant", "content": "结果是 60。"},
        ]
    )
    result = ReActAgent(llm, get_settings()).run("算一下 (12+8)*3")
    assert result["answer"] == "结果是 60。"
    assert result["steps"] == 1
    call = result["tool_calls"][0]
    assert call["name"] == "calculator"
    assert call["ok"] is True
    assert "60" in call["result"]


def test_agent_stops_at_max_steps():
    agent = ReActAgent(AlwaysToolLLM(), get_settings(), max_steps=2)
    result = agent.run("无论问什么都调用工具")
    assert "最大步数" in result["answer"]
    assert result["steps"] == 2


def test_agent_tool_error_is_reported_not_raised():
    llm = ScriptedLLM(
        [
            _tool_call("calculator", '{"expression": "1 +"}'),
            {"role": "assistant", "content": "表达式有误，已换用其它方式。"},
        ]
    )
    result = ReActAgent(llm, get_settings()).run("算一个坏表达式")
    assert result["tool_calls"][0]["ok"] is False
    assert result["answer"] == "表达式有误，已换用其它方式。"


def test_stream_emits_tool_events_and_final():
    llm = ScriptedLLM(
        [
            _tool_call("current_time", "{}"),
            {"role": "assistant", "content": "现在时间已获取。"},
        ]
    )
    events = list(ReActAgent(llm, get_settings()).stream("现在几点"))
    types = [event["type"] for event in events]
    assert types[0] == "step"
    assert "tool_call" in types
    assert "tool_result" in types
    assert types[-1] == "final"
    assert events[-1]["content"] == "现在时间已获取。"
