# 架构说明

## 分层

```
        HTTP
         │
   ┌─────▼─────┐
   │    api    │  接口层：参数校验、SSE 封装、状态码映射
   └─────┬─────┘
         │ 依赖注入
   ┌─────▼─────┐
   │ services  │  用例层：执行任务（同步 / 流式）
   └─────┬─────┘
         │
   ┌─────▼──────────────┐
   │  agent  /  llm     │  能力层：ReAct 编排、工具注册表、执行器、模型
   └────────────────────┘

   config / errors / schemas / prompts / logging_conf  为横向支撑
```

依赖方向单向向下：`api → services → agent / llm`。能力层不认识 Web 框架，用例层不认识 FastAPI。

## 各层职责

| 层 | 目录 | 职责 | 不该做 |
|---|---|---|---|
| 接口层 | `app/api` | 收请求、校验、封装响应与 SSE | 写编排逻辑 |
| 用例层 | `app/services` | 组织一次任务执行、日志 | 依赖 HTTP / 具体模型实现 |
| 能力层 | `app/agent`、`app/llm` | ReAct 循环、工具、执行器、模型调用 | 读写全局状态 |
| 支撑 | `config` `errors` `schemas` `prompts` | 配置、异常、契约、提示词 | 业务逻辑 |

## 关键设计

**工具注册表**：工具是"数据 + 行为"的自描述对象，注册后自动出现在模型可见的工具列表里。

```python
register(WeatherTool())          # 模型下次运行即可调用
tools.unregister("weather")      # 需要时也能摘下
```

**依赖注入**：`ReActAgent(llm, settings, max_steps)`，测试可注入脚本化假 LLM，完全离线验证多轮推理（见 `tests/test_agent.py`）。

**执行器单点收口**：所有工具调用都经过 `executor.execute()`，在这里统一做参数解析、重试与错误转换，工具本身只管实现。

**同步与流式共用单步能力**：`run()` 走 LangGraph 图；`stream()` 复用 `agent_step` / `execute` 并逐 token 推送，两条路径行为一致。

## 扩展点

| 想做的事 | 怎么做 |
|---|---|
| 新增工具 | `app/agent/tools/` 加 `BaseTool` 子类并 `register()` |
| 换模型供应商 | `app/llm.py` 加实现，注册到 `_PROVIDERS` |
| 改 ReAct 策略（如加反思节点） | 在 `app/agent/graph.py` 增加节点与条件边 |
| 改提示词 | 只改 `app/prompts.py` |
| 新增接口 | `app/api/` 加路由 + `app/services/` 加用例 |

## 请求生命周期（流式）

```
POST /api/v1/agent/stream
  → api/agent.py            解析 RunRequest
  → deps.get_agent_service()
  → AgentService.stream()
      → ReActAgent.stream()
          → agent_step()          模型调用（流式，逐 token）
          → execute()             工具执行（重试 + 兜底）
          → 循环直到无工具调用或达到 MAX_STEPS
  → 封装为 SSE
```

## 运行与运维

- `GET /health`：存活检查，返回进程状态与已注册工具
- `GET /ready`：就绪检查，返回模型是否已配置、工具数量
- 请求日志由中间件统一输出（方法、路径、状态码、耗时）
- 日志级别通过 `LOG_LEVEL` 控制

## 约定

- 依赖单向：能力层不 import 接口层
- 工具失败不抛出：统一转成模型可读消息
- 新增能力优先"加文件"，避免修改既有实现
