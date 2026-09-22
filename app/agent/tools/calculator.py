"""计算器工具：仅允许算术表达式的安全求值。"""
from __future__ import annotations

import ast
import operator

from app.agent.tools.base import BaseTool

_BINARY_OPS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.FloorDiv: operator.floordiv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
}
_UNARY_OPS = {ast.UAdd: operator.pos, ast.USub: operator.neg}


def _eval(node: ast.AST):
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return node.value
    if isinstance(node, ast.BinOp) and type(node.op) in _BINARY_OPS:
        return _BINARY_OPS[type(node.op)](_eval(node.left), _eval(node.right))
    if isinstance(node, ast.UnaryOp) and type(node.op) in _UNARY_OPS:
        return _UNARY_OPS[type(node.op)](_eval(node.operand))
    raise ValueError(f"不支持的表达式片段：{type(node).__name__}")


def safe_eval(expression: str) -> float:
    """解析并求值算术表达式，拒绝函数调用、属性访问等一切非算术语法。"""
    tree = ast.parse(expression, mode="eval")
    return _eval(tree.body)


class CalculatorTool(BaseTool):
    name = "calculator"
    description = "计算数学表达式，支持 + - * / // % ** 与括号。涉及数值计算时必须使用。"
    parameters = {
        "type": "object",
        "properties": {
            "expression": {
                "type": "string",
                "description": "要计算的算术表达式，例如 (12+8)*3/4",
            }
        },
        "required": ["expression"],
    }

    def run(self, expression: str) -> str:
        value = safe_eval(expression)
        if isinstance(value, float) and value.is_integer():
            value = int(value)
        return f"{expression} = {value}"
