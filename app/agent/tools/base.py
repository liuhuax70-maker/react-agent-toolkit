"""工具基类。

- name / description / parameters 用于生成 function calling 的 schema
- run() 返回字符串；失败直接抛异常，由 executor 统一重试与兜底
"""
from __future__ import annotations


class BaseTool:
    name: str = ""
    description: str = ""
    parameters: dict = {"type": "object", "properties": {}, "required": []}

    def run(self, **kwargs) -> str:
        raise NotImplementedError

    def spec(self) -> dict:
        """返回 OpenAI function calling 需要的工具描述。"""
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters,
            },
        }
