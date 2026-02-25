# Python 项目结构学习指南

> 结合当前 LangchainStudy 学习项目，整理公认的 Python 项目架构规范与开源参考，便于在后续 Agent/RAG 项目中实践分层结构。

---

## 一、以 Agent 项目为例：原结构 → 推荐结构

**AI大模型RAG与智能体开发_Agent项目** 是他人学习项目，原结构为平铺式。下面是对照 Spring Boot 思路改造后的**推荐结构**：

### 原结构（平铺，不推荐）

```
Agent项目/
├── app.py                    # 入口
├── config/
├── agent/
├── rag/
├── model/
├── utils/
├── prompts/
├── data/
├── logs/
└── chroma_db/
```

### 推荐结构（FastAPI 风格，flat layout）

参考 [FastAPI 仓库](https://github.com/fastapi/fastapi)：**flat layout**，主包在根目录，无 `src/`，结构简单、便于学习。

```
Agent项目/
├── pyproject.toml
├── README.md
├── .env.example
├── config/                      # 配置（根目录，便于编辑）
│   ├── agent.yml
│   ├── chroma.yml
│   ├── prompts.yml
│   └── rag.yml
├── prompts/                     # 提示词模板
│   ├── main_prompt.txt
│   ├── rag_summarize.txt
│   └── report_prompt.txt
├── agent_app/                   # 主包（≈ FastAPI 的 fastapi/）
│   ├── __init__.py
│   ├── main.py                  # 启动器：仅负责启动 Streamlit
│   ├── ui/                      # Streamlit 界面层
│   │   ├── __init__.py
│   │   ├── app.py               # 主界面、布局
│   │   ├── chat.py              # 聊天区域
│   │   └── sidebar.py           # 侧边栏等
│   ├── agent/
│   │   ├── __init__.py
│   │   ├── react_agent.py
│   │   └── tools/
│   │       ├── __init__.py
│   │       ├── agent_tools.py
│   │       └── middleware.py
│   ├── rag/
│   │   ├── __init__.py
│   │   ├── rag_service.py
│   │   └── vector_store.py
│   ├── model/
│   │   ├── __init__.py
│   │   └── factory.py
│   └── utils/
│       ├── __init__.py
│       ├── config_handler.py
│       ├── path_tool.py
│       ├── file_handler.py
│       └── prompt_loader.py
├── tests/
├── data/
├── logs/                        # 运行时日志（.gitignore 排除）
├── storage/                     # 向量库等运行时数据（原 chroma_db，.gitignore 排除）
├── docs/
└── scripts/                     # 可选：脚本工具
```

**要点**：主包 `agent_app/` 在根目录；`main.py` 仅作启动器，Streamlit 界面代码拆分到 `ui/`；`config/`、`prompts/` 在根目录便于修改。

**运行**：`pip install -e .` 后执行 `streamlit run agent_app/main.py`；`main.py` 作为启动器，内部导入并运行 `ui/app.py`。

### 两种组织方式对比

当前结构是**按领域/功能划分**（一个功能一个包），你提到的是**按层级划分**（类似 Spring Boot 的 service 层）。二者对比如下：

| 方式 | 结构 | 适用 |
|------|------|------|
| **按领域** | `agent/`、`rag/`、`model/` 各一个包 | 领域多、各领域内部较复杂 |
| **按层级** | `service/` 下放 `agent_service.py`、`rag_service.py` 等 | 类似 Spring Boot，结构更直观 |

**按层级划分**的等价结构（Spring Boot 风格）：

```
agent_app/
├── main.py
├── ui/
├── api/                  # 控制层
├── service/              # 业务层：各功能 service 放一起
│   ├── __init__.py
│   ├── agent_service.py
│   ├── rag_service.py
│   └── model_factory.py
├── repository/           # 可选：数据访问层
│   └── vector_store.py
└── utils/
```

学习时可按层级划分，更贴近 Spring Boot 习惯；领域复杂后再考虑按领域拆分。

---

## 二、前后端分离结构

当前端改为传统 HTML，后端提供 REST API 时，**与前端交互的 Python 代码**应放在 `api/` 或 `routers/` 目录下，负责接收 HTTP 请求、返回 JSON。

### 目录结构

```
Agent项目/
├── pyproject.toml
├── README.md
├── .env.example
├── config/
├── prompts/
├── frontend/                    # 前端（HTML/CSS/JS）
│   ├── index.html
│   ├── css/
│   ├── js/
│   └── assets/
├── agent_app/
│   ├── __init__.py
│   ├── main.py                  # 启动器：启动 FastAPI/Flask 服务
│   ├── api/                     # 与前端交互层（≈ Spring Boot Controller）
│   │   ├── __init__.py
│   │   ├── routes.py            # 或 main.py：路由注册
│   │   ├── chat.py              # 聊天相关 API
│   │   └── health.py            # 健康检查等
│   ├── agent/
│   ├── rag/
│   ├── model/
│   └── utils/
├── tests/
├── data/
├── logs/                        # 运行时日志
├── storage/                     # 向量库等运行时数据（chroma_db）
├── docs/
└── scripts/
```

### 各层职责

| 目录 | 职责 | 与前端关系 |
|------|------|------------|
| **api/** | 接收 HTTP 请求、参数校验、返回 JSON | 直接与前端交互 |
| **agent/** | Agent 业务逻辑 | 被 api 调用 |
| **rag/** | RAG 业务逻辑 | 被 api 调用 |
| **model/** | 模型工厂 | 被 agent/rag 调用 |
| **utils/** | 通用工具 | 被各层调用 |

### 请求流

```
前端 (HTML/JS)  --HTTP-->  api/chat.py  -->  agent/react_agent  -->  返回 JSON
```

### 示例：api/chat.py

```python
# agent_app/api/chat.py
from fastapi import APIRouter

router = APIRouter(prefix="/api/chat", tags=["chat"])

@router.post("/message")
async def send_message(message: str):
    # 调用 agent 业务逻辑
    from agent_app.agent.react_agent import ReactAgent
    agent = ReactAgent()
    response = agent.execute(message)
    return {"role": "assistant", "content": response}
```

### 运行方式

- **后端**：`uvicorn agent_app.main:app --reload`（FastAPI）或 `flask run`（Flask）
- **前端**：用浏览器打开 `frontend/index.html`，或配合 nginx/静态服务器；开发时可用 `npm run dev` 或直接打开 HTML