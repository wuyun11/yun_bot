# LangChain 功能覆盖分析报告

> 基于 **Agent智能体项目案例** 与 **LangchainStudy** 两个项目的代码分析

---

## 一、项目概览

| 项目 | 路径 | 定位 |
|------|------|------|
| **Agent智能体项目案例** | `Agent智能体项目案例/` | 面向业务的完整 Agent 应用（扫地/扫拖机器人智能客服） |
| **LangchainStudy** | `LangchainStudy/` | LangChain 学习与示例项目（教程式） |

---

## 二、当前已涉及的 LangChain 功能

### 2.1 模型 I/O（Model I/O）

| 功能 | Agent项目 | LangchainStudy | 涉及文件/示例 |
|------|:--------:|:--------------:|---------------|
| **Chat 模型** | ✅ | ✅ | ChatTongyi（通义千问） |
| **LLM（纯文本）** | ❌ | ✅ | P3-01/02：Tongyi、OllamaLLM |
| **流式输出** | ✅ | ✅ | P3-03：`model.stream()`；P5-02：`agent.stream()` |
| **消息格式** | ✅ | ✅ | P3-04/05/06：Chat 消息、简写形式 |
| **提示词模板** | | | |
| └ PromptTemplate | ✅ | ✅ | rag_service.py；P3-09 |
| └ ChatPromptTemplate | ❌ | ✅ | P3-11；P4 rag.py |
| └ FewShotPromptTemplate | ❌ | ✅ | P3-10 |
| └ MessagesPlaceholder | ❌ | ✅ | P3-11/17/18；P4 rag.py |
| **输出解析器** | | | |
| └ StrOutputParser | ✅ | ✅ | rag_service.py；P3-14 |
| └ JsonOutputParser | ❌ | ✅ | P3-15 |

### 2.2 数据连接（Retrieval / Data Connection）

| 功能 | Agent项目 | LangchainStudy | 涉及文件/示例 |
|------|:--------:|:--------------:|---------------|
| **Embedding 模型** | ✅ | ✅ | DashScopeEmbeddings、OllamaEmbeddings |
| **文档加载器** | | | |
| └ PyPDFLoader | ✅ | ✅ | file_handler.py；P3-21 |
| └ TextLoader | ✅ | ✅ | file_handler.py；P3-22 |
| └ CSVLoader | ❌ | ✅ | P3-19 |
| └ JSONLoader | ❌ | ✅ | P3-20 |
| **文本分割器** | ✅ | ✅ | RecursiveCharacterTextSplitter |
| **向量存储** | | | |
| └ Chroma | ✅ | ✅ | vector_store.py；P3-23/24/25；P4 |
| └ InMemoryVectorStore | ❌ | ✅ | P3-23/24/25 |
| **检索器** | ✅ | ✅ | VectorStoreRetriever；RAG 链中的 retriever |

### 2.3 组合（Composition）

| 功能 | Agent项目 | LangchainStudy | 涉及文件/示例 |
|------|:--------:|:--------------:|---------------|
| **LCEL 链** | ✅ | ✅ | `prompt \| model \| parser` |
| **RunnableLambda** | ✅ | ✅ | rag_service.py；P3-16/25；P4 |
| **RunnablePassthrough** | ❌ | ✅ | P3-25；P4 rag.py |
| **Tools** | ✅ | ✅ | `@tool` 装饰器 |
| **Agents** | ✅ | ✅ | `create_agent`（ReAct 式 Agent） |
| **RAG 流程** | ✅ | ✅ | 向量检索 → 构建提示词 → LLM 生成 |

### 2.4 记忆（Memory）

| 功能 | Agent项目 | LangchainStudy | 涉及文件/示例 |
|------|:--------:|:--------------:|---------------|
| **InMemoryChatMessageHistory** | ❌ | ✅ | P3-17 |
| **FileChatMessageHistory** | ❌ | ✅ | P3-18；P4 file_history_store |
| **RunnableWithMessageHistory** | ❌ | ✅ | P3-17/18；P4 rag.py |
| **Agent 会话记忆** | ❌ | ❌ | 两个项目均未在 Agent 中显式使用 memory/checkpointer |

### 2.5 中间件与扩展

| 功能 | Agent项目 | LangchainStudy | 涉及文件/示例 |
|------|:--------:|:--------------:|---------------|
| **Agent 中间件** | ✅ | ✅ | wrap_tool_call, before_model, dynamic_prompt 等 |
| **LangGraph Runtime** | ✅ | ✅ | `langgraph.runtime.Runtime`；Agent 项目还用 `Command` |
| **动态 Prompt** | ✅ | ❌ | middleware 中的 `dynamic_prompt`（客服 vs 报告生成） |

### 2.6 业务功能对比

| 业务功能 | Agent项目 | LangchainStudy |
|----------|:--------:|:--------------:|
| 多工具 Agent（天气、用户、RAG、报告等） | ✅ | 简单演示工具 |
| RAG 知识库问答 | ✅ | ✅（P4 客服问答） |
| 文件上传与知识库增量写入 | ✅ | ✅（P4 app_file_uploader） |
| Streamlit Web 界面 | 有 | ✅（P4 app_qa） |
| 中间件监控与动态 prompt 切换 | ✅ | 基础示例 |

---

## 三、尚未涉及的 LangChain 功能

### 3.1 调试与可观测性

| 功能 | 说明 |
|------|------|
| **Callbacks** | 未使用 `BaseCallbackHandler` 等记录中间步骤、token 消耗 |
| **LangSmith** | 未集成 LangSmith 做链/Agent 的追踪、调试和监控 |

### 3.2 输出与结构化

| 功能 | 说明 |
|------|------|
| **StructuredOutputParser** | 未使用 Pydantic 结构化输出 |
| **PydanticOutputParser** | 未使用 Pydantic 定义输出 schema |
| **ListParser / 其他 Parser** | 未涉及更复杂的解析器 |

### 3.3 Agent 与编排

| 功能 | 说明 |
|------|------|
| **其他 Agent 类型** | 仅用 ReAct；未涉及 Plan-and-Execute、Tool Calling Agent 等 |
| **Human-in-the-Loop** | 未使用人工审核/介入节点 |
| **Checkpointer** | Agent 未使用 MemorySaver / SqliteSaver 等持久化会话 |
| **多 Agent 协作** | 未涉及多 Agent 协同工作流 |
| **LangGraph 图编排** | 未手写 LangGraph 图，仅用 `create_agent` 的默认图 |

### 3.4 文档与检索

| 功能 | 说明 |
|------|------|
| **更多 Document Loader** | 未用 Unstructured、SitemapLoader、WebBaseLoader、GitLoader 等 |
| **更多 Text Splitter** | 未用 TokenTextSplitter、语义分割、按代码分割等 |
| **更多向量库** | 未用 Pinecone、Weaviate、Qdrant、Milvus、FAISS 等 |
| **Hybrid 检索** | 未结合关键词 + 向量检索 |
| **重排序（Reranker）** | 未对检索结果做 rerank |
| **图 RAG / Graph RAG** | 未涉及知识图谱或图数据库增强 |

### 3.5 高级 RAG 与评估

| 功能 | 说明 |
|------|------|
| **Parent Document Retriever** | 未使用父子文档检索 |
| **Self-RAG / Reflexion** | 未使用自反思式 RAG |
| **评估（Evaluation）** | 未使用 LangChain 的评估工具（如 QAEvalChain、自定义评估链） |

### 3.6 其他能力

| 功能 | 说明 |
|------|------|
| **SQL / 数据库 Chain** | 未使用 SQL 查询链或 DB 相关工具 |
| **API / 外部工具** | 有 fetch_external_data 等，但未系统使用 LangChain 的 API/HTTP 工具封装 |
| **Guardrails** | 未使用输出内容安全校验、格式约束 |
| **缓存** | 未使用 LangChain 的 InMemory / Redis 缓存 |
| **批处理** | 未使用 `batch` / `abatch` 等批量调用 |

---

## 四、汇总表

### 已覆盖的 LangChain 核心模块

| 模块 | 覆盖情况 |
|------|----------|
| Model I/O（Prompts、Chat、LLM、Output Parsers） | ✅ 大部分覆盖 |
| Document Loaders | ✅ 部分（PDF、TXT、CSV、JSON） |
| Text Splitters | ✅ 基础（RecursiveCharacterTextSplitter） |
| Embeddings | ✅ DashScope、Ollama |
| Vector Stores | ✅ Chroma、InMemory |
| Retrievers | ✅ 基础向量检索 |
| Chains（LCEL） | ✅ 已使用 |
| Runnables | ✅ Lambda、Passthrough、WithMessageHistory |
| Tools | ✅ 已使用 |
| Agents | ✅ ReAct 式 Agent |
| Memory | ⚠️ 仅 RAG 链中有，Agent 无 |
| Middleware | ✅ 已使用 |
| LangGraph | ✅ Runtime、Command |

### 未覆盖或待拓展的模块

| 模块/能力 | 说明 |
|-----------|------|
| Callbacks | 调试与监控 |
| LangSmith | 链/Agent 追踪 |
| 更多 Output Parsers | 结构化、Pydantic |
| 更多 Document Loaders | Web、Sitemap、Unstructured 等 |
| 更多 Vector Stores | Pinecone、Weaviate、Qdrant 等 |
| 高级检索 | Hybrid、Reranker、Parent Document |
| 其他 Agent 类型 | Plan-and-Execute 等 |
| Human-in-the-Loop | 人工介入 |
| Checkpointer | Agent 会话持久化 |
| 评估与 Guardrails | 质量与安全控制 |

---

## 五、建议学习路径

若希望继续拓展 LangChain 能力，可按以下方向补充：

1. **Callbacks + LangSmith**：为现有链/Agent 增加可观测性。
2. **Checkpointer**：为 Agent 增加会话记忆与持久化（可参考 yun_bot 文档中的 SqliteSaver 方案）。
3. **StructuredOutputParser**：在需要结构化输出时使用 Pydantic。
4. **高级 RAG**：Hybrid 检索、Reranker、Parent Document Retriever。
5. **多 Agent / LangGraph 图**：手写 LangGraph 图实现更复杂工作流。

---

*文档生成日期：2025-02-26*
