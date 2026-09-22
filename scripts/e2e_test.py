"""端到端冒烟测试。

前置：先启动服务并配置 DEEPSEEK_API_KEY
    uvicorn app.main:app --port 8000
然后运行：
    python scripts/e2e_test.py
"""
from __future__ import annotations

import json
import os

import httpx

BASE = os.getenv("AGENT_BASE_URL", "http://127.0.0.1:8000")


def main() -> None:
    with httpx.Client(base_url=BASE, timeout=180) as c:
        print("health :", c.get("/health").json())
        print("ready  :", c.get("/ready").json())
        print("tools  :", [t["name"] for t in c.get("/api/v1/agent/tools").json()["tools"]])

        question = "现在几点？然后用计算器算出 (128+372)*15/4，并把结果写入 result.txt"
        result = c.post("/api/v1/agent/run", json={"question": question}).json()
        print("answer :", result.get("answer"))
        for call in result.get("tool_calls", []):
            detail = call["result"] if call["ok"] else call["error"]
            print(f"  tool : {call['name']}({call['arguments']}) -> {detail}")

        print("sse    : ", end="")
        final = ""
        with c.stream("POST", "/api/v1/agent/stream", json={"question": "用计算器算 99*99"}) as resp:
            for line in resp.iter_lines():
                if not line or not line.startswith("data:"):
                    continue
                data = line[5:].strip()
                if data == "[DONE]":
                    continue
                event = json.loads(data)
                if event["type"] == "tool_call":
                    print(f"\n  call : {event['name']} {event['arguments']}", end="")
                elif event["type"] == "final":
                    final = event["content"]
        print("\n  final:", final)


if __name__ == "__main__":
    main()
