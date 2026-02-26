# LangChain 知识点大全

> 基于 **Agent智能体项目案例** 与 **LangchainStudy** 的学习覆盖情况整理  
> 已涉及 ✅ | 未涉及 ❌

---

## 一、模型 I/O（Model I/O）

### 1.1 模型接口

| 知识点 | 覆盖 | 说明 |
|--------|:----:|------|
| **Chat 模型** | ✅ | 以「消息」为输入输出的对话模型（如 ChatTongyi、OpenAI Chat），支持多轮对话 |
| **LLM（纯文本）** | ✅ | 以「字符串」为输入输出的基础模型（如 Tongyi、OllamaLLM），无消息结构 |
| **流式输出** | ✅ | `model.stream()` 或 `agent.stream()`，逐 token 返回，用于实时展示 |
| **批量调用** | ❌ | `batch()` / `abatch()`：对多个输入批量调用，`abatch` 支持异步，用于高并发场景 |
| **绑定与配置** | ❌ | `model.bind()` 绑定 stop 词等；`RunnableConfig` 传递配置、callbacks、metadata |

### 1.2 提示词模板

| 知识点 | 覆盖 | 说明 |
|--------|:----:|------|
| **PromptTemplate** | ✅ | 单轮文本模板，`{var}` 占位符，用于简单 LLM 调用 |
| **ChatPromptTemplate** | ✅ | 多消息模板，支持 `SystemMessage`、`HumanMessage`、`AIMessage`、`MessagesPlaceholder` |
| **FewShotPromptTemplate** | ✅ | 少样本提示：在模板中嵌入若干示例，让模型模仿格式或风格 |
| **MessagesPlaceholder** | ✅ | 在 ChatPrompt 中预留消息槽，用于注入历史消息（会话记忆） |
| **PipelinePrompt** | ❌ | 组合多个子提示为一个管道，用于模块化复杂提示 |

### 1.3 输出解析器

| 知识点 | 覆盖 | 说明 |
|--------|:----:|------|
| **StrOutputParser** | ✅ | 将 LLM 输出解析为字符串 |
| **JsonOutputParser** | ✅ | 将 LLM 输出解析为 JSON 对象 |
| **PydanticOutputParser / StructuredOutputParser** | ❌ | 见下方「未涉及知识点详解」 |
| **ListParser / 其他 Parser** | ❌ | 解析列表、XML、正则等格式，用于特定输出结构 |

---

## 二、数据连接（Retrieval / Data Connection）

### 2.1 文档加载器

| 知识点 | 覆盖 | 说明 |
|--------|:----:|------|
| **TextLoader** | ✅ | 加载纯文本文件 |
| **PyPDFLoader** | ✅ | 加载 PDF |
| **CSVLoader** | ✅ | 加载 CSV |
| **JSONLoader** | ✅ | 加载 JSON，可配置 JSONPath 抽取字段 |
| **WebBaseLoader** | ❌ | 加载网页 HTML 内容，用于网页抓取类 RAG |
| **SitemapLoader** | ❌ | 按 sitemap 批量加载站点页面 |
| **UnstructuredLoader** | ❌ | 加载 Word、PPT、HTML 等多种格式，依赖 unstructured 库 |
| **GitLoader** | ❌ | 加载 Git 仓库文件，用于代码库问答 |
| **DirectoryLoader** | ❌ | 扫描目录下多种类型文件并批量加载 |

### 2.2 文本分割器

| 知识点 | 覆盖 | 说明 |
|--------|:----:|------|
| **RecursiveCharacterTextSplitter** | ✅ | 按字符递归分割，可配置 separators（如 `\n\n`、`\n`、空格），最常用 |
| **TokenTextSplitter** | ❌ | 按 token 数量分割，保证不截断 token，适合严格控制上下文长度 |
| **MarkdownHeaderTextSplitter** | ❌ | 按 Markdown 标题分割，保留层级结构 |
| **语义分割** | ❌ | 按语义边界分割，需要额外模型，适合长文档精细化切分 |

### 2.3 嵌入模型

| 知识点 | 覆盖 | 说明 |
|--------|:----:|------|
| **DashScopeEmbeddings** | ✅ | 阿里云通义 Embedding |
| **OllamaEmbeddings** | ✅ | 本地 Ollama Embedding |

### 2.4 向量存储

| 知识点 | 覆盖 | 说明 |
|--------|:----:|------|
| **Chroma** | ✅ | 轻量向量库，本地持久化 |
| **InMemoryVectorStore** | ✅ | 内存向量存储，适合演示和小数据 |
| **Pinecone / Weaviate / Qdrant / Milvus / FAISS** | ❌ | 云或本地向量库，用于大规模、生产级检索 |
| **pgvector** | ❌ | PostgreSQL 向量扩展，数据与向量同库 |

### 2.5 检索器

| 知识点 | 覆盖 | 说明 |
|--------|:----:|------|
| **VectorStoreRetriever** | ✅ | 向量相似度检索，`as_retriever(search_kwargs={"k": n})` |
| **BM25Retriever** | ❌ | 见下方「未涉及知识点详解」 |
| **EnsembleRetriever** | ❌ | 见下方「未涉及知识点详解」 |
| **ParentDocumentRetriever** | ❌ | 见下方「未涉及知识点详解」 |
| **ContextualCompressionRetriever** | ❌ | 对检索结果做压缩/摘要，减少无关内容输入 LLM |

---

## 三、组合（Composition）

### 3.1 LCEL 与 Runnables

| 知识点 | 覆盖 | 说明 |
|--------|:----:|------|
| **LCEL 链** | ✅ | `prompt \| model \| parser` 的管道式组合 |
| **RunnableLambda** | ✅ | 将任意 Python 函数包装为 Runnable，用于链中自定义逻辑 |
| **RunnablePassthrough** | ✅ | 透传输入或合并上下文（如 `{"context": retriever, "question": RunnablePassthrough()}`） |
| **RunnableWithMessageHistory** | ✅ | 为链注入会话历史，用于多轮对话 |
| **RunnableParallel** | ❌ | 并行执行多个 Runnable，合并结果 |
| **RunnableBranch** | ❌ | 根据条件选择分支执行 |
| **RunnableSequence** | ❌ | 显式定义顺序链，等价于 `a \| b \| c` |

### 3.2 工具与 Agent

| 知识点 | 覆盖 | 说明 |
|--------|:----:|------|
| **@tool 装饰器** | ✅ | 将函数声明为工具，供 Agent 调用 |
| **create_agent（ReAct）** | ✅ | ReAct 式 Agent：思考 → 选工具 → 执行 → 观察 → 循环 |
| **Plan-and-Execute Agent** | ❌ | 见下方「未涉及知识点详解」 |
| **Tool Calling Agent** | ❌ | 利用模型原生 function calling 的 Agent，依赖模型支持 |
| **多 Agent 协作** | ❌ | 多个 Agent 协同工作，如主 Agent 路由到专家 Agent |

### 3.3 中间件

| 知识点 | 覆盖 | 说明 |
|--------|:----:|------|
| **wrap_tool_call** | ✅ | 包装工具调用，可加日志、审批等 |
| **before_model / after_model** | ✅ | 模型调用前后钩子 |
| **before_agent / after_agent** | ✅ | Agent 执行前后钩子 |
| **dynamic_prompt** | ✅ | 动态切换 system prompt |
| **Human-in-the-Loop Middleware** | ❌ | 见下方「未涉及知识点详解」 |

---

## 四、记忆（Memory）

| 知识点 | 覆盖 | 说明 |
|--------|:----:|------|
| **InMemoryChatMessageHistory** | ✅ | 内存会话历史，进程重启丢失 |
| **FileChatMessageHistory** | ✅ | 文件持久化会话历史 |
| **RunnableWithMessageHistory** | ✅ | 链级会话记忆，配合 `get_session_history` |
| **Checkpointer（MemorySaver / SqliteSaver）** | ❌ | 见下方「未涉及知识点详解」 |
| **对话摘要 / 对话截断** | ❌ | 长对话压缩为摘要或滑动窗口，控制上下文长度 |

---

## 五、调试与可观测性

| 知识点 | 覆盖 | 说明 |
|--------|:----:|------|
| **Callbacks（BaseCallbackHandler）** | ❌ | 见下方「未涉及知识点详解」 |
| **LangSmith** | ❌ | 见下方「未涉及知识点详解」 |
| **verbose / debug 模式** | ❌ | 控制台打印中间步骤，简单调试 |

---

## 六、其他能力

| 知识点 | 覆盖 | 说明 |
|--------|:----:|------|
| **SQL Chain / 数据库工具** | ❌ | 自然语言转 SQL、执行查询，用于数据库问答 |
| **Guardrails** | ❌ | 输出内容安全校验、格式约束，防止有害或偏离格式 |
| **缓存（InMemory / Redis）** | ❌ | 对相同输入缓存 LLM 输出，降低成本和延迟 |
| **评估（Evaluation）** | ❌ | 用 LLM 或规则评估回答质量，用于迭代优化 |
| **LangGraph 手写图** | ❌ | 见下方「未涉及知识点详解」 |

---

# 未涉及知识点详解

> 对「两个学习项目尚未涉及」的知识点做简要说明：**是什么** + **用来干什么**

---

## 1. PydanticOutputParser / StructuredOutputParser

**是什么**：让 LLM 输出符合 Pydantic 模型或 JSON Schema 定义的结构（字段名、类型、校验）。

**用来干什么**：需要结构化数据时（如抽实体、填表、返回 JSON 接口），用 Pydantic 定义 schema，解析器负责把 LLM 文本解析并校验为对象。比 `JsonOutputParser` 更严格、可校验。

---

## 2. Callbacks（BaseCallbackHandler）

**是什么**：在 LLM、Chain、Tool、Retriever 等执行的各个阶段挂载钩子（如 `on_llm_start`、`on_tool_end`），记录事件。

**用来干什么**：记录 token 消耗、延迟、中间变量，做日志、监控、计费。不依赖 LangSmith 也能做自定义可观测性。

---

## 3. LangSmith

**是什么**：LangChain 官方的可观测性平台，自动追踪链/Agent 执行。

**用来干什么**：设置 `LANGSMITH_TRACING=true` 后，每次调用会生成 trace，在 Web UI 中查看每步输入输出、耗时、错误。用于调试复杂链和 Agent。

---

## 4. Checkpointer（MemorySaver / SqliteSaver）

**是什么**：LangGraph 的「检查点保存器」，在 Agent 图执行时持久化状态（消息、中间结果等）。

**用来干什么**：实现 Agent 的**会话记忆**：同一 `thread_id` 下多轮对话可恢复上下文；支持暂停、恢复、时间旅行（从某检查点重跑）。`MemorySaver` 仅内存，`SqliteSaver` 落盘 SQLite。

---

## 5. Human-in-the-Loop（HITL）

**是什么**：在执行到某个节点（如调用工具前）暂停，等待人工审核、修改或拒绝，再继续执行。

**用来干什么**：敏感操作（写文件、执行 SQL、预订等）必须经过人工审批时使用。需配合 Checkpointer 保存状态，以便暂停后稍后再恢复。

---

## 6. Plan-and-Execute Agent

**是什么**：先由 LLM 制定「步骤计划」，再按计划逐条执行（每步可能调用工具或子 Agent）。

**用来干什么**：复杂任务需要显式规划时使用（如「调研竞品 → 写报告 → 发邮件」）。计划与执行解耦，便于分步调试和优化，但会增加 LLM 调用次数和延迟。

---

## 7. BM25Retriever / EnsembleRetriever（Hybrid 检索）

**是什么**：  
- **BM25**：基于关键词的检索，类似传统搜索引擎。  
- **EnsembleRetriever**：将 BM25 与向量检索结果融合（如用 RRF 算法）。

**用来干什么**：纯向量检索容易漏掉「精确匹配关键词」的文档，混合检索可兼顾语义和关键词，提升召回率和鲁棒性。

---

## 8. Reranker（重排序）

**是什么**：在向量检索拿到 top-N 结果后，用另一个模型（如 Cross-Encoder）对「查询 + 文档」对打分，重新排序。

**用来干什么**：向量检索的 top-K 不一定最相关，Reranker 做二次精排，提升最终送入 LLM 的文档质量，通常能明显改善 RAG 效果。

---

## 9. ParentDocumentRetriever（父子文档检索）

**是什么**：索引时把文档切成小块（子文档）做向量；存储时保留「父文档」引用。检索时用小块的向量相似度，返回时取对应父文档或较大块。

**用来干什么**：小块检索更精准，但上下文不足；大块信息完整但检索粗。父子文档折中：用小块召回，用父块给 LLM 提供足够上下文。

---

## 10. Graph RAG

**是什么**：先构建知识图谱（实体、关系），检索时在图上游走、聚合，再结合 LLM 生成回答。

**用来干什么**：适合关系型问题（如「A 和 B 有什么关系」「谁影响了谁」）。图结构比纯向量更能表达多跳推理和结构化关系。

---

## 11. LangGraph 手写图

**是什么**：用 `StateGraph` 定义节点和边，手写 Agent 或工作流的执行逻辑，而不是用 `create_agent` 的默认图。

**用来干什么**：需要自定义流程（如多 Agent 协作、复杂分支、人工审批节点）时，手写图可以精确控制状态流转和节点逻辑。

---

## 12. 更多 Document Loader

| Loader | 是什么 | 用来干什么 |
|--------|--------|------------|
| **WebBaseLoader** | 抓取网页 HTML | 网页、博客、文档站点的 RAG |
| **SitemapLoader** | 按 sitemap 抓站 | 批量建站内知识库 |
| **UnstructuredLoader** | 多格式解析 | Word、PPT、HTML 等非纯文本 |
| **GitLoader** | 读取 Git 仓库 | 代码库问答、文档生成 |
| **DirectoryLoader** | 按 glob 扫描目录 | 批量加载多种类型文件 |

---

## 13. 缓存

**是什么**：对「相同输入」缓存 LLM 输出，避免重复调用。

**用来干什么**：开发调试、重复问题、批量处理时减少 API 调用和成本，可配合 `InMemoryCache` 或 `RedisCache`。

---

## 14. 评估（Evaluation）

**是什么**：用 LLM 或规则对「问题 + 参考答案 + 模型输出」打分（相关性、正确性、有害性等）。

**用来干什么**：迭代优化提示词、检索策略、模型选择时，用量化指标评估效果，而不是仅靠人工感受。

---

## 15. Guardrails

**是什么**：对 LLM 输出做规则或模型级校验，过滤违规内容、保证格式。

**用来干什么**：上线前防止输出有害信息、保证 JSON/表格等格式正确，满足合规和安全要求。

---

## 16. SQL Chain / 数据库工具

**是什么**：将自然语言转成 SQL，执行查询，再把结果转成自然语言回答。

**用来干什么**：做「用自然语言查数据库」的问答系统，用户问「上个月销售额多少」，系统生成并执行 SQL，返回解读后的答案。

---

# 学习路径建议

按依赖关系，建议顺序：

1. **Model I/O** → **Prompts** → **Output Parsers** → **LCEL 链**（基础）
2. **Document Loaders** → **Text Splitter** → **Vector Store** → **RAG 链**（检索增强）
3. **Tools** → **create_agent**（Agent 基础）
4. **Middleware** → **RunnableWithMessageHistory**（链级记忆）
5. **Checkpointer**（Agent 级记忆）
6. **Callbacks** → **LangSmith**（可观测）
7. **StructuredOutputParser**、**Hybrid 检索**、**Reranker**（进阶 RAG）
8. **Plan-and-Execute**、**LangGraph 手写图**、**Human-in-the-Loop**（高阶编排）

---

*文档生成日期：2025-02-26*
