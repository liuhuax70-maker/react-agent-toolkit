"""ReAct 循环编排（LangGraph）。

    [agent] --有 tool_calls--> [tools] --回填结果--> [agent]
       └── 无 tool_calls / 达到步数上限 --> END

依赖（LLM）由外部注入；工具来自注册表。
同步路径走 LangGraph 图；流式路径复用同一套单步能力，逐 token 推送。
"""
from __future__ import annotations

import logging
from typing import Iterator, TypedDict

from langgraph.graph import END, StateGraph

from app.agent import tools
from app.agent.executor import execute
from app.config import Settings, get_settings
from app.llm import LLMClient
from app.prompts import AGENT_SYSTEM_PROMPT

logger = logging.getLogger(__name__)


class AgentState(TypedDict, total=False):
    messages: list
    steps: int
    tool_calls: list


def _initial_messages(question: str) -> list[dict]:
    return [
        {"role": "system", "content": AGENT_SYSTEM_PROMPT},
        {"role": "user", "content": question},
    ]


def _final_answer(messages: list[dict]) -> str:
    for message in reversed(messages):
        if message.get("role") == "assistant" and message.get("content"):
            return message["content"]
    return ""


class ReActAgent:
    def __init__(
        self,
        llm: LLMClient,
        settings: Settings | None = None,
        max_steps: int | None = None,
    ) -> None:
        self.llm = llm
        self.settings = settings or get_settings()
        self.max_steps = max_steps or self.settings.max_steps
        self._graph = None

    # ---------- 单步能力（图与流式共用） ----------

    def agent_step(self, messages: list[dict]) -> dict:
        """一次模型调用：产出思考内容与（可能有的）工具调用。"""
        return self.llm.complete(messages, tools.specs())

    def tool_step(self, message: dict, records: list[dict]) -> list[dict]:
        """执行消息中的全部工具调用，返回回填用的 tool 消息。"""
        outputs: list[dict] = []
        for call in message.get("tool_calls", []):
            name = call["function"]["name"]
            arguments = call["function"]["arguments"]
            outcome = execute(name, arguments, self.settings.tool_retries)
            records.append(
                {
                    "name": name,
                    "arguments": arguments,
                    "ok": outcome["ok"],
                    "result": outcome["result"],
                    "error": outcome["error"],
                }
            )
            outputs.append(
                {"role": "tool", "tool_call_id": call["id"], "content": outcome["content"]}
            )
        return outputs

    # ---------- 图 ----------

    def _compiled(self):
        if self._graph is None:
            self._graph = self._build_graph()
        return self._graph

    def _build_graph(self):
        def agent_node(state: AgentState) -> dict:
            message = self.agent_step(state["messages"])
            return {"messages": state["messages"] + [message]}

        def tools_node(state: AgentState) -> dict:
            records = list(state.get("tool_calls", []))
            outputs = self.tool_step(state["messages"][-1], records)
            return {
                "messages": state["messages"] + outputs,
                "steps": state.get("steps", 0) + 1,
                "tool_calls": records,
            }

        def route(state: AgentState) -> str:
            if state.get("steps", 0) >= self.max_steps:
                return END
            return "tools" if state["messages"][-1].get("tool_calls") else END

        graph = StateGraph(AgentState)
        graph.add_node("agent", agent_node)
        graph.add_node("tools", tools_node)
        graph.set_entry_point("agent")
        graph.add_conditional_edges("agent", route, {"tools": "tools", END: END})
        graph.add_edge("tools", "agent")
        return graph.compile()

    def run(self, question: str) -> dict:
        """同步执行，返回最终答案与工具调用轨迹。"""
        state = self._compiled().invoke(
            {"messages": _initial_messages(question), "steps": 0, "tool_calls": []}
        )
        answer = _final_answer(state["messages"])
        if not answer:
            answer = f"已达到最大步数（{self.max_steps}），未能得出最终结论。"
        return {
            "answer": answer,
            "tool_calls": state.get("tool_calls", []),
            "steps": state.get("steps", 0),
        }

    # ---------- 流式 ----------

    def stream(self, question: str) -> Iterator[dict]:
        """产出事件：step / token / tool_call / tool_result / final / error。"""
        messages = _initial_messages(question)
        records: list[dict] = []

        for index in range(self.max_steps):
            yield {"type": "step", "index": index + 1}
            message: dict | None = None
            try:
                for event in self.llm.stream_complete(messages, tools.specs()):
                    if event["type"] == "token":
                        yield {"type": "token", "content": event["content"]}
                    else:
                        message = event["message"]
            except Exception as exc:
                logger.exception("模型调用失败")
                yield {"type": "error", "message": str(exc)}
                return

            if message is None:
                yield {"type": "error", "message": "模型未返回内容"}
                return

            messages.append(message)
            calls = message.get("tool_calls") or []
            if not calls:
                yield {"type": "final", "content": message.get("content", "")}
                return

            for call in calls:
                name = call["function"]["name"]
                arguments = call["function"]["arguments"]
                yield {"type": "tool_call", "name": name, "arguments": arguments}
                outcome = execute(name, arguments, self.settings.tool_retries)
                records.append(
                    {
                        "name": name,
                        "arguments": arguments,
                        "ok": outcome["ok"],
                        "result": outcome["result"],
                        "error": outcome["error"],
                    }
                )
                yield {
                    "type": "tool_result",
                    "name": name,
                    "ok": outcome["ok"],
                    "result": outcome["result"],
                    "error": outcome["error"],
                }
                messages.append(
                    {"role": "tool", "tool_call_id": call["id"], "content": outcome["content"]}
                )

        yield {"type": "final", "content": f"已达到最大步数（{self.max_steps}），未能得出最终结论。"}
