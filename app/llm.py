"""LLM 客户端：接口 + DeepSeek（OpenAI 兼容）实现。

支持 function calling（工具调用）与流式输出。
新增模型供应商时，实现同签名方法并注册到 _PROVIDERS。
"""
from __future__ import annotations

from functools import lru_cache
from typing import Iterator, Protocol

from openai import OpenAI

from app.config import get_settings
from app.errors import BackendUnavailable


class LLMClient(Protocol):
    def complete(self, messages: list[dict], tools: list[dict] | None = None) -> dict: ...

    def stream_complete(self, messages: list[dict], tools: list[dict] | None = None) -> Iterator[dict]: ...


def _normalize_message(message) -> dict:
    """把 SDK 返回的消息整理成普通 dict（便于存入状态与再次发送）。"""
    result: dict = {"role": "assistant", "content": message.content or ""}
    if message.tool_calls:
        result["tool_calls"] = [
            {
                "id": call.id,
                "type": "function",
                "function": {
                    "name": call.function.name,
                    "arguments": call.function.arguments or "{}",
                },
            }
            for call in message.tool_calls
        ]
    return result


class DeepSeekClient:
    provider = "deepseek"

    def __init__(self, api_key: str, base_url: str, model: str, temperature: float) -> None:
        self._client = OpenAI(api_key=api_key, base_url=base_url)
        self._model = model
        self._temperature = temperature

    def complete(self, messages: list[dict], tools: list[dict] | None = None) -> dict:
        response = self._client.chat.completions.create(
            model=self._model,
            messages=messages,
            tools=tools or None,
            temperature=self._temperature,
        )
        return _normalize_message(response.choices[0].message)

    def stream_complete(self, messages: list[dict], tools: list[dict] | None = None) -> Iterator[dict]:
        """流式输出。

        产出事件：
          {"type": "token", "content": str}          文本增量
          {"type": "message", "message": dict}       本轮完整消息（最后一条）
        """
        stream = self._client.chat.completions.create(
            model=self._model,
            messages=messages,
            tools=tools or None,
            temperature=self._temperature,
            stream=True,
        )

        content_parts: list[str] = []
        pending: dict[int, dict] = {}

        for chunk in stream:
            if not chunk.choices:
                continue
            delta = chunk.choices[0].delta
            if delta.content:
                content_parts.append(delta.content)
                yield {"type": "token", "content": delta.content}
            for call in delta.tool_calls or []:
                slot = pending.setdefault(call.index, {"id": "", "name": "", "arguments": ""})
                if call.id:
                    slot["id"] = call.id
                if call.function and call.function.name:
                    slot["name"] = call.function.name
                if call.function and call.function.arguments:
                    slot["arguments"] += call.function.arguments

        message: dict = {"role": "assistant", "content": "".join(content_parts)}
        if pending:
            message["tool_calls"] = [
                {
                    "id": slot["id"] or f"call_{index}",
                    "type": "function",
                    "function": {
                        "name": slot["name"],
                        "arguments": slot["arguments"] or "{}",
                    },
                }
                for index, slot in sorted(pending.items())
            ]
        yield {"type": "message", "message": message}


_PROVIDERS = {DeepSeekClient.provider: DeepSeekClient}


@lru_cache
def get_llm() -> LLMClient:
    settings = get_settings()
    if settings.missing_llm_key():
        raise BackendUnavailable("未配置 DEEPSEEK_API_KEY，无法调用大模型。")
    factory = _PROVIDERS[DeepSeekClient.provider]
    return factory(
        settings.llm_api_key,
        settings.llm_base_url,
        settings.llm_model,
        settings.llm_temperature,
    )
