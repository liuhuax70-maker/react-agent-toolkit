"""接口层测试（离线）。"""
import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from app.config import get_settings
from app.main import app
from app.schemas import RunRequest

client = TestClient(app)


def test_health_lists_tools():
    r = client.get("/health")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "ok"
    assert "calculator" in body["tools"]


def test_ready():
    r = client.get("/ready")
    assert r.status_code == 200
    assert r.json()["tools"] >= 1


def test_tools_endpoint():
    r = client.get("/api/v1/agent/tools")
    assert r.status_code == 200
    names = [tool["name"] for tool in r.json()["tools"]]
    assert "calculator" in names
    assert "web_search" in names


def test_schema_rejects_empty_question():
    with pytest.raises(ValidationError):
        RunRequest(question="")


def test_run_without_api_key_returns_503():
    if not get_settings().missing_llm_key():
        pytest.skip("已配置 Key，跳过未配置场景")
    r = client.post("/api/v1/agent/run", json={"question": "1+1"})
    assert r.status_code == 503
