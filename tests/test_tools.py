"""工具测试。"""
import pytest

from app.agent import tools
from app.agent.tools.calculator import safe_eval


def test_expected_tools_registered():
    expected = {
        "calculator",
        "current_time",
        "write_file",
        "read_file",
        "list_files",
        "text_stats",
        "web_search",
    }
    assert expected <= set(tools.tool_names())


def test_calculator_evaluates_expression():
    assert tools.get_tool("calculator").run(expression="(12+8)*3/4") == "(12+8)*3/4 = 15"


def test_calculator_rejects_non_arithmetic():
    with pytest.raises(ValueError):
        safe_eval("__import__('os').system('whoami')")


def test_file_tools_roundtrip():
    tools.get_tool("write_file").run(path="a.txt", content="你好")
    assert tools.get_tool("read_file").run(path="a.txt") == "你好"
    assert "a.txt" in tools.get_tool("list_files").run()


def test_file_tool_blocks_directory_traversal():
    with pytest.raises(ValueError):
        tools.get_tool("read_file").run(path="../../etc/passwd")


def test_text_stats_counts():
    output = tools.get_tool("text_stats").run(text="你好 世界")
    assert "字符数（含空白）：5" in output
    assert "词数（按空白切分）：2" in output


def test_clock_returns_timestamp():
    assert len(tools.get_tool("current_time").run()) >= 19
