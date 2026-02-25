# 会话记忆实施方案：checkpointer + 截断

本文说明在采用 **create_agent + checkpointer（SqliteSaver 单文件）+ 截断** 方案时，需要**新增、删除、修改**的代码与配置。存储使用本地单个 `.db` 文件（与向量库类似），无需安装独立数据库服务。

---

## 方案回顾

- **存**：由 LangGraph 的 checkpointer 负责，使用 `SqliteSaver`，落盘为一个 SQLite 文件（如 `data/agent_checkpoints.db`）。
- **记多少**：通过截断（如 `trim_messages` 按条数/ token）控制发给模型的上下文长度；截断可在图内（reducer / 调用模型前）实现。
- **调用**：每轮只传本轮用户消息，并传 `config={"configurable": {"thread_id": session_id}}`，图会自动恢复/保存该线程的 state。

---

## 一、新增

### 1. 依赖

在 `require/requirements.txt`（或当前使用的依赖文件）中增加：

```text
langgraph-checkpoint-sqlite>=2.0.0
```

安装：

```bash
pip install langgraph-checkpoint-sqlite
```

### 2. checkpointer 的创建与注入方式

两种常见做法（二选一）：

- **在应用入口创建并传入 ReactAgent**  
  在启动 bot 的入口（如 `bot.py` 或加载 agent 的模块）里：
  - 使用 `SqliteSaver.from_conn_string("...")` 创建 checkpointer（若 API 要求 `with`，则在入口的 with 块内创建图，或保存为可长期持有的对象并传入）。
  - 将 checkpointer 传给 `ReactAgent(checkpointer=...)`。
- **在 ReactAgent 内部创建**  
  在 `ReactAgent.__init__` 里根据项目根路径拼出 SQLite 文件路径（如 `get_abs_path("data/agent_checkpoints.db")`），创建 `SqliteSaver` 并保存为实例属性，再在 `create_agent(..., checkpointer=self.checkpointer)` 时传入。

新增内容要点：

- 使用 `agent_app.utils.path_tool.get_abs_path` 拼出持久化路径，例如：`get_abs_path("data/agent_checkpoints.db")`，并确保 `data/` 目录存在或由 SqliteSaver 自动创建（视具体 API 而定）。
- 若采用「入口创建并传入」，则需在入口文件中**新增**：创建 `SqliteSaver`、实例化 `ReactAgent(checkpointer=...)` 的逻辑。

### 3. `react_agent.py` 中与 checkpointer、thread_id 相关的逻辑

- **create_agent 增加参数**  
  `create_agent(..., checkpointer=checkpointer)`，其中 `checkpointer` 来自上一步（传入或内部创建）。
- **execute_stream 增加 session_id，并传 config**  
  - 方法签名增加参数，例如：`execute_stream(self, query: str, session_id: str | None = None)`。  
  - 调用 `self.agent.stream(...)` 时：
    - `inputs` 仍为 `{"messages": [{"role": "user", "content": query}]}`（只传本轮用户消息）。
    - 当 `session_id` 不为空时，传入 `config={"configurable": {"thread_id": session_id}}`，这样图会按 thread 恢复/保存 state；若 `session_id` 为空，可不传 config（无多轮记忆）。
- **流式循环**  
  保持现有 `stream_mode="values"` 与对 `chunk["messages"][-1]` 的 yield 逻辑不变；无需再在流式结束后“写回历史”（由 checkpointer 自动完成）。

以上为**必须新增**的部分。

### 4. 截断（可选，建议先实现「最近 N 条」）

- **目标**：避免 state 中 `messages` 无限增长，控制发给模型的上下文长度。
- **可选实现位置**（选一处即可）：
  - **图内 reducer**：若 create_agent 支持自定义 state 的 reducer，在合并 `messages` 时只保留最近 N 条（或按 token 的 trim）。
  - **图内「调用模型前」**：若能在 middleware（如 `before_model`）或调用 LLM 的节点内拿到当前 `state["messages"]`，则用 LangChain 的 `trim_messages()` 按条数/ token 截断后再调用模型；注意此时 checkpoint 里可能仍保存完整 state，只是“发给模型”的变少。
- **建议**：先实现「按条数保留最近 N 条」或「按 token 数 trim_messages」，总结逻辑可后续再加。具体 API 以当前使用的 `create_agent` / LangGraph 版本为准（可查 `trim_messages`、state reducer 文档）。

新增内容小结：依赖 `langgraph-checkpoint-sqlite`；创建并注入 checkpointer；在 `react_agent.py` 中为 create_agent 传入 checkpointer、为 execute_stream 增加 session_id 与 config；可选在图内增加截断逻辑。

---

## 二、删除

- **当前项目**：若从未接入过「图外 JSON 存储」（如 `file_history_store`、`get_history` 等），则**无需删除**任何现有代码。
- **若之前接入了「图外 JSON 拼接」**：可删除对 `get_history` / `FileChatMessageHistory` 的引用，以及 `execute_stream` 里“从历史加载 messages、流式结束后写回”的逻辑；不再使用 JSON 文件作为对话存储。

---

## 三、修改

### 1. `agent_app/agent/react_agent.py`

| 位置 | 修改内容 |
|------|----------|
| 文件头 | 如需在 ReactAgent 内创建 SqliteSaver，则增加：`from langgraph.checkpoint.sqlite import SqliteSaver`，以及 `from agent_app.utils.path_tool import get_abs_path`（若在内部拼路径）。 |
| `ReactAgent.__init__` | 增加参数 `checkpointer`（或改为在内部创建）；在 `create_agent(...)` 调用中增加 `checkpointer=checkpointer`。 |
| `execute_stream` | 增加参数 `session_id: str | None = None`；在调用 `self.agent.stream(input_dict, ...)` 时，若 `session_id` 非空，则增加关键字参数 `config={"configurable": {"thread_id": session_id}}`。 |

### 2. 调用 `execute_stream` 的地方（如 QQ 插件、Streamlit、API）

- 将“当前用户/会话”的 id 作为 `session_id` 传入，例如：  
  `execute_stream(query, session_id=event.get_user_id())` 或 `execute_stream(query, session_id=user_id)`。  
- 不传 `session_id` 时行为与当前一致（无多轮记忆）。

### 3. 可选：截断相关

- 若在图内做截断：需修改或扩展 create_agent 所用到的 state / middleware（如增加 reducer 或 before_model 中对 `state["messages"]` 的 trim），具体取决于当前 LangChain/LangGraph 版本是否支持以及项目结构。

---

## 四、文件与配置清单（汇总）

| 类型 | 文件/位置 | 操作 |
|------|-----------|------|
| 依赖 | `require/requirements.txt`（或当前依赖文件） | **新增**一行：`langgraph-checkpoint-sqlite>=2.0.0` |
| 存储路径 | 使用 `get_abs_path("data/agent_checkpoints.db")` 或等价路径 | 确保目录存在；可将 `data/` 加入 `.gitignore`（若尚未） |
| Agent | `agent_app/agent/react_agent.py` | **修改**：create_agent 增加 checkpointer；execute_stream 增加 session_id 与 config |
| 应用入口 | 若在入口创建 checkpointer 并注入 ReactAgent | **新增**：创建 SqliteSaver、传入 ReactAgent 的代码 |
| 调用方 | 所有调用 `execute_stream` 的地方 | **修改**：传入 `session_id`（如 QQ user_id） |
| 图外 JSON 存储 | 若曾使用 file_history_store / get_history 等 | **删除**：相关引用与“加载/写回”逻辑（可选） |
| 截断 | 图内 reducer 或调用模型前 | **新增**（可选）：trim_messages 或“最近 N 条”逻辑 |

按上述清单逐项完成即可在本项目中落地「checkpointer（Sqlite 单文件）+ 截断」的会话记忆方案，且无需单独安装数据库服务。
