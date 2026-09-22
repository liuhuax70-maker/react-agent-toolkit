"""文件工具：读写限定在工作目录内，防止目录穿越。"""
from __future__ import annotations

from pathlib import Path

from app.agent.tools.base import BaseTool
from app.config import get_settings


def _resolve(name: str) -> Path:
    root = get_settings().workspace_dir
    root.mkdir(parents=True, exist_ok=True)
    target = (root / name).resolve()
    if target != root.resolve() and root.resolve() not in target.parents:
        raise ValueError("只能访问工作目录内的文件")
    return target


class FileWriteTool(BaseTool):
    name = "write_file"
    description = "把文本写入工作目录中的文件（不存在则创建，已存在则覆盖）。"
    parameters = {
        "type": "object",
        "properties": {
            "path": {"type": "string", "description": "相对工作目录的文件名"},
            "content": {"type": "string", "description": "要写入的文本"},
        },
        "required": ["path", "content"],
    }

    def run(self, path: str, content: str) -> str:
        target = _resolve(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
        return f"已写入 {path}（{len(content)} 字符）"


class FileReadTool(BaseTool):
    name = "read_file"
    description = "读取工作目录中文件的文本内容。"
    parameters = {
        "type": "object",
        "properties": {
            "path": {"type": "string", "description": "相对工作目录的文件名"}
        },
        "required": ["path"],
    }

    def run(self, path: str) -> str:
        target = _resolve(path)
        if not target.exists():
            raise FileNotFoundError(f"文件不存在：{path}")
        return target.read_text(encoding="utf-8", errors="ignore")


class FileListTool(BaseTool):
    name = "list_files"
    description = "列出工作目录中的文件。"
    parameters = {"type": "object", "properties": {}, "required": []}

    def run(self) -> str:
        root = get_settings().workspace_dir
        root.mkdir(parents=True, exist_ok=True)
        names = sorted(p.name for p in root.iterdir() if p.is_file())
        return "\n".join(names) if names else "（工作目录为空）"
