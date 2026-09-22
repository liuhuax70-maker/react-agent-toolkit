# 运行教程

## 关于"编译"

**本项目没有编译步骤。** Python 是解释型语言，装好依赖后直接启动即可，不需要 build。

如果只想做一次语法检查（不运行）：

```bat
python -m compileall app
```

## 0. 前置条件

| 项 | 要求 |
|---|---|
| Python | 3.10 及以上（推荐 3.11） |
| 操作系统 | Windows / macOS / Linux |
| 磁盘 | 约 300 MB（依赖，无需下载模型） |
| 网络 | 安装依赖时需要；运行时需要能访问 DeepSeek（`web_search` 工具还需要能访问外网） |
| DeepSeek API Key | 必填，从 https://platform.deepseek.com 获取 |

确认 Python 可用：

```bat
python --version
```

## 1. 获取代码

```bat
git clone git@github.com:liuhuax70-maker/react-agent-toolkit.git
cd react-agent-toolkit
```

## 2. 创建虚拟环境

Windows（CMD / PowerShell）：

```bat
python -m venv .venv
.venv\Scripts\activate
```

macOS / Linux：

```bash
python3 -m venv .venv
source .venv/bin/activate
```

> 激活成功后，命令行提示符前会出现 `(.venv)`。

## 3. 安装依赖

```bat
pip install -r requirements.txt
```

国内网络建议加清华镜像：

```bat
pip install -i https://pypi.tuna.tsinghua.edu.cn/simple --trusted-host pypi.tuna.tsinghua.edu.cn -r requirements.txt
```

整个安装过程约 1 分钟，不需要下载任何模型文件。

## 4. 配置密钥

```bat
copy .env.example .env
```

打开 `.env`，填上自己的 Key：

```ini
DEEPSEEK_API_KEY=sk-你的key
MAX_STEPS=6
WORKSPACE_DIR=./data/workspace
```

`.env` 已被 `.gitignore` 忽略，不会提交到仓库。

## 5. 启动服务

```bat
uvicorn app.main:app --reload --port 8000
```

看到下面这行就说明启动成功：

```
INFO:     Application startup complete.
```

- 界面：http://localhost:8000
- 接口文档：http://localhost:8000/docs
- 停止服务：在该窗口按 `Ctrl + C`

> 如果 8000 端口被占用（报 `[Errno 10048]`），换成 `--port 8010` 即可。

## 6. 验证是否正常

另开一个命令行窗口：

```bat
curl http://127.0.0.1:8000/health
```

期望输出（`tools` 里应有 7 个工具）：

```json
{"status":"ok","version":"0.1.0","tools":["calculator","current_time","list_files","read_file","text_stats","web_search","write_file"]}
```

再看已注册工具列表：

```bat
curl http://127.0.0.1:8000/api/v1/agent/tools
```

## 7. 跑一遍完整流程

1. 浏览器打开 http://localhost:8000
2. 输入框输入多步任务：

   ```
   现在几点？再用计算器算 (128+372)*15/4，并写入 result.txt
   ```

3. 期望看到：
   - 左侧展示 7 个可用工具
   - 回答区上方展开**工具调用轨迹**，依次出现 `current_time`、`calculator`、`write_file` 三次调用及其返回值
   - 下方给出最终答案（含时间、计算结果 1875、文件已写入）
4. 确认文件真的写入了工作目录：`data/workspace/result.txt`

其他可试的任务见 `examples/sample_tasks.md`。

## 8. 运行测试

单元测试（离线，使用脚本化假 LLM，不需要 Key 和网络）：

```bat
pytest -q
```

端到端冒烟测试（需要先启动服务，且已配置 Key）：

```bat
set AGENT_BASE_URL=http://127.0.0.1:8000
python scripts/e2e_test.py
```

> macOS / Linux 用 `AGENT_BASE_URL=http://127.0.0.1:8000 python scripts/e2e_test.py`。
> 未设置该变量时脚本默认连 `http://127.0.0.1:8000`。

## 9. 用 Docker 运行（可选）

```bat
docker build -t react-agent .
docker run -p 8000:8000 -e DEEPSEEK_API_KEY=sk-你的key react-agent
```

密钥通过 `-e` 在运行时注入，不写进镜像；镜像内置 `/health` 健康检查。

## 10. 常见问题

| 现象 | 原因与解决 |
|---|---|
| `[Errno 10048] ... 8000` | 端口被占用：换端口 `--port 8010`，或关掉占用端口的程序 |
| `pip install` 卡住或超时 | 用清华镜像（见第 3 步） |
| 提问报 503 / "未配置 DEEPSEEK_API_KEY" | `.env` 没填 Key，或没从 `.env.example` 复制 |
| `web_search` 返回"执行失败" | 该工具需要外网；内网环境属于预期行为，其余工具不受影响 |
| 智能体反复调用工具直到上限 | 说明模型没收敛：调大 `MAX_STEPS`，或把问题描述得更具体 |
| 写文件报"只能访问工作目录内的文件" | 文件工具做了目录穿越防护，只允许读写 `WORKSPACE_DIR` 内 |
| `python` 命令找不到 | Windows 用 `py -3.11 -m venv .venv`，或在安装 Python 时勾选 "Add to PATH" |

## 附：默认端口与数据位置

| 项 | 位置 |
|---|---|
| 工具工作目录（文件读写） | `data/workspace/` |
| 示例任务 | `examples/sample_tasks.md` |

`data/workspace/` 内除 `.gitkeep` 外的内容均已被 `.gitignore` 忽略。
