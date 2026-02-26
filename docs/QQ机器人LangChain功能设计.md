# QQ 机器人 + LangChain 功能设计

> yun_bot 项目设计文档  
> 基于 NoneBot 框架，以 LangChain 覆盖学习为目标

---

## 一、项目定位

- **用途**：个人娱乐 / 学习
- **框架**：NoneBot + LangChain
- **目标**：尽量覆盖 LangChain 知识点，边做边学
- **不考虑**：流量、成本、高并发

---

## 二、整体架构

```
QQ 消息
    │
    ▼
┌─────────────────────────────────────────────────────────┐
│  NoneBot 入口层                                          │
│  ① 显式指令（/加知识、/清空记忆 等）→ 对应插件处理         │
│  ② 其他消息 → 主聊天插件                                 │
└─────────────────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────────────────┐
│  主 Agent（create_agent）                                │
│  - 理解用户意图（自然语言）                               │
│  - 自主选择工具：发图、天气、RAG、翻译、时间等             │
│  - 无需用户背指令                                        │
└─────────────────────────────────────────────────────────┘
    │
    ├── RAG 工具（内部是 Chain：检索 →  prompt → 模型 → 解析）
    ├── 天气工具
    ├── 发图工具
    ├── 翻译工具
    ├── 时间工具
    └── ...
```

---

## 三、路由策略：Agent 优先 + 显式指令辅助

### 3.1 原则

| 路由方式 | 适用场景 | 说明 |
|----------|----------|------|
| **Agent 理解意图** | 发图、天气、RAG、翻译、聊天等 | 用户自然说话，Agent 决定调用哪个工具 |
| **显式指令** | 加知识、清空记忆、敏感操作等 | NoneBot 层识别 `/xxx`，直接走对应插件 |

### 3.2 为什么这样分？

- **Agent 优先**：充分利用 LangChain 的 ReAct、工具选择、意图理解，交互自然。
- **显式指令**：敏感/管理类操作需要明确表达，便于权限控制和审计。

### 3.3 流程示意

```
用户：「帮我找张猫的图」
    → 主 Agent 理解 → 调用发图工具 → 返回图片

用户：「北京天气怎么样」
    → 主 Agent 理解 → 调用天气工具 → 返回天气

用户：「/加知识 扫地机器人每周清理尘盒」
    → NoneBot 识别 /加知识 → 知识库插件处理 → 写入向量库
    （不经过 Agent）
```

---

## 四、功能设计（按 LangChain 知识点）

### 4.1 主 Agent 能力（自然语言驱动）

| 用户说法示例 | Agent 调用的工具 | LangChain 涉及 |
|--------------|------------------|----------------|
| 「找张猫的图」「发个猫的图片」 | 发图工具 | Tool、Agent |
| 「北京天气怎么样」「上海下雨吗」 | 天气工具 | Tool |
| 「现在几点」「今天几号」 | 时间工具 | Tool |
| 「xxx 是什么意思」「查一下 xxx」 | RAG / 百科工具 | RAG 链、Tool |
| 「把这句话翻译成英文」 | 翻译工具 | Chain、Tool |
| 普通聊天 | 直接回复 | Chat 模型、流式输出 |

### 4.2 显式指令（NoneBot 层路由）

| 指令 | 功能 | LangChain 涉及 |
|------|------|----------------|
| `/加知识 [内容]` | 将内容加入个人知识库 | Document Loader、向量库 |
| `/清空记忆` | 清空当前会话记忆 | Checkpointer / Memory |
| `/切换模型 [名称]` | 切换 Chat 模型（可选） | 模型工厂 |

### 4.3 知识点与功能对照表

| LangChain 知识点 | 对应功能 | 说明 |
|------------------|----------|------|
| **Chat 模型** | 主对话 | 通义 / Ollama 等 |
| **流式输出** | 回复逐步输出 | `agent.stream()` |
| **PromptTemplate** | 翻译、摘要 Chain | `{input}` 等占位符 |
| **ChatPromptTemplate** | 多轮对话 | 配合 MessagesPlaceholder |
| **FewShotPromptTemplate** | 反义词等示例任务 | 少样本 |
| **StrOutputParser** | 普通文本回复 | 链输出解析 |
| **JsonOutputParser** | 天气等结构化输出 | 工具返回 JSON |
| **PydanticOutputParser** | 抽签等结构化输出 | 严格 schema |
| **Document Loaders** | 知识库 | PDF、TXT、Web 等 |
| **Text Splitter** | 知识库分块 | RecursiveCharacterTextSplitter |
| **Chroma / InMemoryVectorStore** | 向量存储 | RAG |
| **RAG 链** | 知识库问答 | retriever \| prompt \| model \| parser |
| **RunnablePassthrough** | RAG 链 | 注入检索上下文 |
| **@tool** | 发图、天气、RAG 等 | Agent 工具 |
| **create_agent** | 主 Agent | ReAct |
| **@wrap_tool_call** | 工具调用日志 | 中间件 |
| **@dynamic_prompt** | 群聊/私聊不同 prompt | 中间件 |
| **RunnableWithMessageHistory** | 链级会话记忆 | 多轮对话 |
| **Checkpointer** | Agent 会话记忆 | 按 QQ 号做 session_id |
| **Callbacks** | Token、耗时统计 | 可观测性 |
| **LangSmith** | 调试追踪（可选） | 可观测性 |
| **Human-in-the-Loop** | 敏感操作确认（可选） | 人工审批 |

---

## 五、实现阶段建议

### 阶段 1：基础对话（约 1～2 周）

- [ ] NoneBot 接入，主聊天插件
- [ ] Chat 模型 + 流式输出
- [ ] PromptTemplate、StrOutputParser
- [ ] 简单 Chain：`prompt | model | parser`
- [ ] 普通聊天可用

### 阶段 2：Agent + 工具（约 2 周）

- [ ] `create_agent`
- [ ] 工具：天气、时间、翻译（基础）
- [ ] `@wrap_tool_call` 日志
- [ ] `@dynamic_prompt`（群聊 / 私聊不同 prompt）
- [ ] 自然语言驱动天气、时间、翻译

### 阶段 3：RAG 知识库（约 2 周）

- [ ] Document Loaders（TXT、PDF、Web）
- [ ] Text Splitter、Chroma
- [ ] RAG 链 + RunnablePassthrough
- [ ] RAG 作为 Agent 工具
- [ ] `/加知识 [内容]` 显式指令

### 阶段 4：记忆与进阶（约 2 周）

- [ ] RunnableWithMessageHistory / FileChatMessageHistory
- [ ] Checkpointer（Agent 会话记忆）
- [ ] FewShotPromptTemplate、JsonOutputParser、PydanticOutputParser
- [ ] `/清空记忆` 显式指令

### 阶段 5：可选拓展（按兴趣）

- [ ] 发图工具（调用 API）
- [ ] Hybrid 检索、Reranker
- [ ] Agent 调 Agent（主 Agent + 专家 Agent）
- [ ] Human-in-the-Loop
- [ ] Callbacks、LangSmith
- [ ] SQL Chain、缓存、评估

---

## 六、主 Agent System Prompt 要点

建议在 system prompt 中明确：

1. **角色**：QQ 群/私聊助手
2. **可用工具**：发图、天气、时间、RAG、翻译 等，及各工具适用场景
3. **输出规则**：简洁、贴合 QQ 场景
4. **意图理解**：根据用户自然语言自主选择工具，无需用户使用 `/xxx` 指令

---

## 七、目录结构建议（yun_bot）

```
yun_bot/
├── src/
│   ├── plugins/
│   │   ├── chat.py          # 主聊天插件（调用 Agent）
│   │   ├── knowledge.py     # /加知识、/清空记忆
│   │   └── ...
│   ├── langchain_app/       # LangChain 相关
│   │   ├── agent/
│   │   │   ├── react_agent.py
│   │   │   └── tools/
│   │   ├── rag/
│   │   ├── model/
│   │   └── utils/
│   └── ...
├── config/
├── prompts/
├── data/
└── docs/
    └── QQ机器人LangChain功能设计.md
```

---

## 八、技术栈

| 组件 | 选型 |
|------|------|
| QQ 机器人框架 | NoneBot |
| LLM | 通义 / Ollama |
| Agent | LangChain create_agent |
| 向量库 | Chroma |
| 会话记忆 | RunnableWithMessageHistory + Checkpointer |

---

*文档更新日期：2025-02-26*
