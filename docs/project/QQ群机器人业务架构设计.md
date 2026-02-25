# QQ 群机器人业务架构设计

本文档描述「同学群 QQ 机器人」中**除 QQ 协议对接以外**的业务架构，包括会话与多租户、知识库、RAG 问答、**对话记忆与记忆优化**（含超阈值时由模型总结前 N 条）等。QQ 机器人协议与消息收发请参考对应官方/社区文档，本架构假定已有适配层将「群消息/私聊/上传文件」转为内部事件。

---

## 1. 目标与范围

| 在架构内 | 不在架构内（你自行对接） |
|----------|---------------------------|
| 会话与 session 管理（按群/人隔离） | QQ 登录、收消息、发消息、收文件等协议细节 |
| 群友上传内容 → 知识库入库 | QQ 侧「谁可上传、审核策略」等产品规则 |
| 基于知识库的 RAG 问答（带对话历史） | 具体 QQ 框架选型（如 NoneBot2 + go-cqhttp） |
| **对话记忆存储 + 记忆优化**（超阈值时 LLM 总结前 N 条，避免无限截断） | 部署、运维、监控 |

---

## 2. 整体架构示意

```
                    +------------------+
                    |  QQ 协议/官方     |
                    |  收消息、收文件   |
                    +--------+---------+
                             | 事件（消息/文件）
                             v
+-------------------------------------------------------------------------------+
|                          QQ 适配层（你实现）                                   |
|  解析事件 → 区分「文本提问 / 上传文件」→ 生成 session_id → 调用下方业务层      |
+-------------------------------------------------------------------------------+
                             |
         +-------------------+-------------------+
         |                   |                   |
         v                   v                   v
+----------------+  +----------------+  +----------------------------------------+
| 会话与租户      |  | 知识库服务      |  | 对话记忆 + 记忆优化                     |
| session_id =   |  | 上传 → 解析     |  | 按 session 存历史；超阈值时对「前 N 条」|
| f(group_id,    |  | → 分块 → 向量   |  | 调用 LLM 总结 → 替换为 1 条摘要再保留   |
|   user_id)     |  | → 入库(MD5去重) |  | 剩余消息，避免简单截断丢上下文           |
+----------------+  +----------------+  +----------------------------------------+
         |                   |                   |
         +-------------------+-------------------+
                             |
                             v
                    +------------------+
                    |  RAG 服务        |
                    |  检索 + 历史     |
                    |  + 总结 prompt   |
                    |  → LLM 回复     |
                    +--------+---------+
                             |
                    可选：Agent（工具调用）
                             |
                             v
                    +------------------+
                    |  回复内容        |
                    |  → 回传给 QQ 层 |
                    +------------------+
```

---

## 3. 模块划分

### 3.1 QQ 适配层（约定接口，具体你按官方文档实现）

- **职责**：接收 QQ 事件（群消息、私聊、文件上传等），解析出「文本内容 / 文件 URL 或二进制」、`group_id`、`user_id`（及可选 `message_id`）。
- **与业务层约定**：
  - **session_id**：由适配层按业务规则生成并传入后续模块，建议 `session_id = f"{group_id}_{user_id}"` 或仅 `f"{group_id}"`（群共用一个会话），便于「对话记忆」和「知识库」按会话/群隔离。
  - **两类调用**：
    - **文本消息**：视为用户提问 → 调用「RAG 服务」（传入 `session_id` + 用户输入）→ 将返回文本交给 QQ 层发送。
    - **文件消息**：视为上传资料 → 调用「知识库服务」上传接口（传入 `session_id`、文件内容或路径）→ 按需返回「已入库 / 跳过」等提示，由 QQ 层发给用户。
- 本架构不实现具体 QQ 协议，只约定上述**入参与调用关系**。

### 3.2 会话与多租户

- **session_id** 唯一标识一个「对话会话」，建议由 QQ 适配层根据 `group_id`、`user_id` 生成（例如同群同人一个 session）。
- **知识库**可按需选择：
  - **按群隔离**：每个 `group_id` 一个向量集合（或同一 Chroma 下不同 `collection_name`），检索时只查该群知识库；
  - **全局共享**：所有群共用一个知识库（当前 Agent 项目做法）。
- **对话记忆**严格按 `session_id` 隔离：每个 session 一份历史（见下节），RAG 请求时只加载该 session 的历史。

### 3.3 知识库服务

- **职责**：接收「上传内容」（文本或文件路径/二进制），解析 → 分块 → 向量化 → 写入向量库，并做 MD5 去重。
- **可复用**：
  - **Agent 项目**：`VectorStoreService`（Chroma + 分块 + 持久化）、`file_handler`（PDF/TXT 解析、MD5）、`load_document` 的「按文件 MD5 去重」逻辑；
  - **P4_RAG**：`KnowledgeBaseService.upload_by_str`（字符串入库、MD5、分块、metadata）。
- **扩展**：提供「单条上传」接口（供 QQ 适配层在收到文件后调用）：保存临时文件 → 解析为 Document → 分块 → 写入向量库（可选：metadata 中记录 `group_id`/`user_id`/上传时间）→ 记录 MD5 防重复。

### 3.4 RAG 服务（带对话历史）

- **职责**：给定 `session_id` 与用户问题，加载该 session 的**对话历史**，检索知识库得到参考资料，将「历史 + 当前问题 + 参考资料」拼进 prompt，调用 LLM 生成回复；并将本轮「用户问 + 模型答」写回对话记忆。
- **可复用**：
  - **P4_RAG**：`RagService` 的链式结构（`RunnablePassthrough` + retriever + `format_documents` + `ChatPromptTemplate` 含 `MessagesPlaceholder("chat_history")` + `RunnableWithMessageHistory`）；
  - **Agent 项目**：`RagSummarizeService` 的检索 + 总结模板 + `chat_model`，以及 `vector_store.get_retriever()`。
- **与记忆的衔接**：历史由「对话记忆」模块提供（见下节）；RAG 服务只负责「读历史、拼 prompt、调用 LLM、写回新消息」。记忆的**截断与总结**在记忆模块内部完成，RAG 无感。

### 3.5 对话记忆与记忆优化（核心）

- **职责**：
  - 按 `session_id` 持久化对话历史（LangChain 的 `BaseChatMessageHistory` 形态，便于 `RunnableWithMessageHistory` 使用）。
  - **当历史条数超过设定阈值时**，不再简单「只保留最后 N 条」截断，而是：**取「前 SUMMARY_CHUNK_SIZE 条」交给 LLM 做一次总结，得到一条「摘要消息」**，然后将历史替换为 **「摘要消息 + 剩余消息」**，从而在控制条数的同时保留长期上下文。
- **与 P4 的对应**：对应 P4 的 `file_history_store.FileChatMessageHistory` 与配置中的 `MAX_HISTORY_MESSAGES`、`SUMMARY_CHUNK_SIZE`；P4 当前在超阈值时仍是简单截断，本架构把「总结前 N 条」设计完整并落到实现约定上。详见第 4 节。

### 3.6 可选：Agent 层

- 若希望支持「多步推理 + 工具调用」（如先查天气再结合知识库回答），可在 RAG 之上再包一层 `create_agent`，将 RAG 作为其中一个 tool；此时「对话历史」可仍由当前 RAG 链的 `RunnableWithMessageHistory` 管理，或改为 Agent 的 message 历史，二选一、避免重复。
- 若先只做「群资料库 + 基于资料的问答」，可仅用 RAG 服务 + 对话记忆，不引入 Agent。

---

## 4. 对话记忆优化设计（详细）

### 4.1 目标

- 历史消息不能无限增长（token 与存储都受限）。
- 简单截断「只保留最后 N 条」会丢失早期重要信息（如用户之前说过偏好、前提条件）。
- **方案**：超过阈值时，对「前若干条」做一次 LLM 总结，用**一条摘要消息**替代这段历史，再拼接剩余消息，这样总条数下降，但关键信息通过摘要保留。

### 4.2 配置参数（建议放入 config，与 P4 对齐命名）

| 参数 | 含义 | 示例 |
|------|------|------|
| `MAX_HISTORY_MESSAGES` | 历史消息条数上限（含摘要与普通消息）；超过即触发「总结」逻辑 | 20 |
| `SUMMARY_CHUNK_SIZE` | 每次参与总结的「前缀」消息条数；这 N 条会被总结成 1 条摘要 | 10 |
| `SUMMARY_PROMPT_PATH` 或内联 | 总结用的 prompt 模板路径或内容 | 见下 |

### 4.3 触发条件

- 在 **写入新消息之后** 检查：若 `len(all_messages) > MAX_HISTORY_MESSAGES`，则执行一次「总结并压缩」。
- 可选扩展：再加「定时总结」（例如每累积 M 条就总结一次），与「超阈值总结」二选一或并存；首版建议只做「超阈值」即可。

### 4.4 总结流程（单次）

1. 取当前历史列表 `messages`（已包含本轮新加的消息）。
2. 若 `len(messages) <= MAX_HISTORY_MESSAGES`，直接持久化，结束。
3. 否则：
   - 取「前 `SUMMARY_CHUNK_SIZE` 条」：`to_summarize = messages[:SUMMARY_CHUNK_SIZE]`。
   - 将这 N 条格式化为文本（如 `role: content` 逐条拼接），送入 **总结 prompt**。
   - 总结 prompt 示例（可放配置文件或 prompts 目录）：
     ```text
     请将以下对话历史总结为一段简洁的摘要，保留关键事实、用户意图与重要结论，供后续对话参考。不要编造内容，只基于给定历史概括。
     对话历史：
     {history_text}
     ```
   - 调用 LLM 得到 `summary_text`。
   - 构造一条「摘要消息」：建议用 `SystemMessage(content=summary_text)`，表示这是系统生成的上下文摘要。
   - 新历史 = `[SystemMessage(content=summary_text)] + messages[SUMMARY_CHUNK_SIZE:]`。
   - 持久化新历史（覆盖原文件或存储）。
4. 若采用「定时总结」：在达到「每 M 条」时同样执行上述 3，只是触发条件改为「当前条数 ≥ M」而非「> MAX_HISTORY_MESSAGES」。

### 4.5 存储形态

- **给 RAG/Agent 用的历史**：仍是 `Sequence[BaseMessage]`，即 LangChain 的 `messages_from_dict` / `message_to_dict` 可序列化的结构；摘要以 `SystemMessage` 形式存在，与普通 Human/AIMessage 一起参与后续 prompt。
- **UI 或轻量展示用**（若有）：可像 P4 一样单独维护一份「精简历史」（只含 role/content），且可只保留最近若干条；总结逻辑只作用于「完整历史」，精简版可按条数截断或按需同步。

### 4.6 与 P4 的对接点

- P4 的 `FileChatMessageHistory.add_messages` 中，当前逻辑是：
  - `if len(all_messages) > max_len: all_messages = all_messages[-max_len:]`
- **改造为**：在 `if len(all_messages) > max_len` 分支内，改为调用「总结函数」：
  - 取 `to_summarize = all_messages[:SUMMARY_CHUNK_SIZE]`；
  - 调用 LLM 总结 → 得到 `SystemMessage(摘要)`；
  - `all_messages = [SystemMessage(摘要)] + all_messages[SUMMARY_CHUNK_SIZE:]`；
  - 若仍 `> max_len`，可再截断尾部（或再触发一次总结，视需求而定，一般一次即可）。
- 这样 **RAG 链无需改**，仍通过 `get_history(session_id)` 拿到「可能含摘要消息」的历史；`RunnableWithMessageHistory` 行为不变。

---

## 5. 数据流简述

### 5.1 用户发一条文本（提问）

1. QQ 适配层收到消息 → 解析出 `group_id`、`user_id`、文本内容 → 生成 `session_id`。
2. 调用 **RAG 服务**：`rag_service.invoke(session_id, user_input)`。
3. RAG 内部：  
   - 通过 **对话记忆** 取该 `session_id` 的历史；  
   - 检索 **知识库** 得参考资料；  
   - 拼 prompt（历史 + 问题 + 参考资料）→ LLM → 得到回复；  
   - 将「用户消息 + AI 回复」交给 **对话记忆** 的 `add_messages`；记忆内部若超过 `MAX_HISTORY_MESSAGES` 则执行「总结前 SUMMARY_CHUNK_SIZE 条」再落盘。
4. RAG 将回复文本返回给 QQ 适配层 → 发送到群/私聊。

### 5.2 用户上传文件（入库）

1. QQ 适配层收到文件 → 下载或拿到路径 → 生成 `session_id`（如按群）。
2. 调用 **知识库服务**：`knowledge_base.upload(session_id, file_path_or_bytes, filename)`。
3. 知识库：解析文件 → MD5 去重 → 分块 → 向量化 → 写入对应向量集合（按 session/群隔离或全局）；返回「已入库」或「已存在」。
4. 适配层将结果文案发到群/私聊。

---

## 6. 配置项建议（汇总）

- **会话**：`session_id` 生成规则（仅群 / 群+人）。
- **知识库**：向量库路径、集合名（或按群命名规则）、分块参数、允许的文件类型、MD5 存储路径；若按群隔离，需配置「集合名与 group_id 的映射」或命名规则。
- **RAG**：检索 top_k、对话模型名、RAG 提示词路径（含 `{context}`、`{chat_history}`、`{input}`）。
- **对话记忆**：  
  - `CHAT_HISTORY_PATH`（或按 session 存文件的目录）、  
  - `MAX_HISTORY_MESSAGES`、  
  - `SUMMARY_CHUNK_SIZE`、  
  - `SUMMARY_PROMPT_PATH` 或总结 prompt 正文；  
  - 若有 UI 历史：`CHAT_UI_HISTORY_PATH`、`UI_MAX_HISTORY_MESSAGES`、`CHAT_UI_LAST_N`（与 P4 一致即可）。

---

## 7. 与现有项目的对应关系

| 能力 | P4_RAG 项目 | Agent 智能体项目 | QQ 机器人中的用法 |
|------|-------------|-------------------|--------------------|
| 对话历史存储 | `file_history_store.FileChatMessageHistory`、`get_history` | — | 直接复用；在 `add_messages` 内实现「超阈值时总结前 N 条」 |
| 历史总结（未实现） | 配置有 `SUMMARY_CHUNK_SIZE`，逻辑未实现 | — | 按第 4 节在本项目或 P4 的 history 模块中实现 |
| RAG 链（检索+历史+LLM） | `rag.RagService`（含 `RunnableWithMessageHistory`） | `rag_service.RagSummarizeService`（无历史） | 以 P4 的「带历史」链为主；检索/向量可换用 Agent 的 VectorStoreService |
| 知识库入库 | `knowledge_base.upload_by_str`、MD5、分块 | `vector_store.load_document`、file_handler | 单条上传接口可参考 P4；批量/目录逻辑可参考 Agent |
| 向量检索 | `VectorStoreService`（DashScope） | `VectorStoreService`（Ollama + Chroma） | 任选其一或统一用一套 |
| Agent/工具 | — | `create_agent`、tools、middleware | 可选；若只用 RAG 则不必引入 |

---

## 8. 小结

- **QQ 侧**：你按官方文档实现适配层，只负责生成 `session_id`、区分「文本提问」与「上传文件」，并调用下面业务接口。
- **业务侧**：会话按 `session_id` 隔离；知识库负责上传与检索；RAG 负责带历史的问答；**对话记忆**在超过 `MAX_HISTORY_MESSAGES` 时，对前 `SUMMARY_CHUNK_SIZE` 条做 LLM 总结并替换为一条摘要，再与剩余消息一起持久化，从而在控制条数的同时保留长期上下文。
- 实现时可直接在 P4 的 `file_history_store` 中补全「总结前 N 条」的逻辑（并增加 `SUMMARY_PROMPT_PATH` 与调用 LLM），RAG 与 QQ 适配层无需关心总结细节，只依赖「历史接口」即可。
