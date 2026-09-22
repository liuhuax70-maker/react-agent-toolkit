"""pytest 全局配置：把工具工作目录指向临时目录，避免污染开发数据。"""
import os
import tempfile
from pathlib import Path

_tmp = Path(tempfile.mkdtemp(prefix="agent_test_"))

os.environ["WORKSPACE_DIR"] = str(_tmp / "workspace")
os.environ["MAX_STEPS"] = "4"
