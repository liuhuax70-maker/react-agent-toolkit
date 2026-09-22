# 设计文档

本文档描述 ReAct 循环、事件协议、工具契约与错误处理策略。

## 1. ReAct 循环

```
        ┌──────────────────────────────┐
        │                              │
   [agent] ──有 tool_calls──▶ [tools] ─┘
        │
        └──无 tool_calls / 达到 MAX_STEPS──▶ END
```

- `agent` 节点：调用模型，产出思考内容与（可能有的）工具调用
- `tools` 节点：执行本轮的**全部**工具调用，把结果作为 `tool` 消息回填，`steps + 1`
- 条件边：有工具调用且未超步数 → 回到 `agent`；否则结束

状态（`AgentState`）：`messages`（对话与工具结果）、`steps`（工具轮次）、`tool_calls`（轨迹记录）。

## 2. 接口契约

### GET /health
```json
{ "status": "ok", "version": "0.1.0", "tools": ["calculator", "..."] }
```

### GET /ready
```json
{ "status": "ready", "llm_configured": true, "tools": 7 }
```

### POST /api/v1/agent/run
请求：`{ "question": "...", "max_steps": 6 }`（`max_steps` 可选）
响应：
```json
{
  "answer": "最终答案",
  "steps": 2,
  "tool_calls": [
    { "name": "calculator", "arguments": "{\"expression\": \"1+1\"}",
      "ok": true, "result": "1+1 = 2", "error": null }
  ]
}
```

### POST /api/v1/agent/stream（SSE）
```
data: {"type":"step","index":1}
data: {"type":"token","content":"我先查一下时间"}
data: {"type":"tool_call","name":"current_time","arguments":"{}"}
data: {"type":"tool_result","name":"current_time","ok":true,"result":"2026-09-22 20:26:44（周二）","error":null}
data: {"type":"step","index":2}
data: {"type":"token","content":"现在是"}
data: {"type":"final","content":"现在是 20:26。"}
data: [DONE]
```

事件类型：`step` / `token` / `tool_call` / `tool_result` / `final` / `error`。

## 3. 工具契约

每个工具是 `BaseTool` 的子类，提供 `name`、`description`、`parameters`（JSON Schema）与 `run(**kwargs) -> str`。

`spec()` 把三者转成 OpenAI function calling 的格式：

```json
{ "type": "function",
  "function": { "name": "calculator",
                "description": "计算数学表达式…",
                "parameters": { "type": "object", "properties": {...}, "required": [...] } } }
```

安全约束：

- `calculator` 用 AST 白名单求值，拒绝函数调用、属性访问、下标等语法
- 文件工具限定在 `WORKSPACE_DIR` 内，路径解析后校验是否越界

## 4. 错误处理与重试

| 场景 | 处理 |
|---|---|
| 未知工具 | 返回错误文本，模型可见并据此调整 |
| 参数不是合法 JSON | 返回错误文本，附上原始参数 |
| 工具内部异常 | 按 `TOOL_RETRIES` 重试，仍失败则返回错误文本 |
| 模型调用失败 | 同步接口返回 5xx；流式推送 `{"type":"error"}` |
| 达到最大步数 | 结束循环，返回"已达最大步数"的说明 |

原则：**工具失败不抛给调用方**，而是转成模型可读的消息，让 ReAct 循环自行纠错。

## 5. 参数

| 参数 | 默认 | 说明 |
|---|---|---|
| MAX_STEPS | 6 | 最大工具轮次 |
| TOOL_RETRIES | 2 | 单工具重试次数 |
| TOOL_TIMEOUT | 10 | 工具请求超时（秒） |
| LLM_MODEL | deepseek-chat | 对话模型 |
| LLM_TEMPERATURE | 0.2 | 生成温度 |

## 6. 安全

- `.env` 不入库；`.gitignore` 覆盖 `.env` 与 `data/workspace`
- 无硬编码密钥；密钥仅在 `config.py` 读取
- 文件工具防目录穿越；计算器禁用任意代码执行
