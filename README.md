# yun_bot

一个基于 NoneBot + QQ 官方适配器的 QQ 机器人项目，现在已经补上了一套最小可玩的 `infra + RAG` 骨架。

## 现在有的能力

- 群聊里 `@机器人` 走“按群隔离 + 群共享历史”的 RAG 聊天
- `/chat` 或 `/rag` 基于本群知识库做检索问答
- `/收录 文本` 将显式文本写入本群知识库
- `/ingest` 将 `data/groups/<group_id>/refs` 下资料灌入本群知识库
- `/我的名称` 查看本群中的当前名称
- `/设置名称 xxx` 设置本群中的显示名称
- RAG 同时提供两种入口：NoneBot 直接调用、Agent Tool 调用

## 目录

- `config/app.yml`: RAG 基础配置
- `config/model.yml`: agent 模型、rag 模型、embedding 模型配置
- `src/langchain_app/infra`: 配置、日志、模型、prompt 加载
- `src/langchain_app/rag`: 向量库、灌库、RAG chain
- `src/langchain_app/tools`: 给 agent 用的 tools
- `src/plugins/rag.py`: NoneBot 命令入口

## 快速开始

1. 安装依赖：`pip install -e .`
2. 在 `.env` 里准备 `DASHSCOPE_API_KEY`，或者把 `config/model.yml` 改成 `ollama`
3. 群资料放到 `data/groups/<group_id>/refs`
4. 启动机器人：`nb run`
5. 在群里先执行 `/收录 一段文本` 或 `/ingest`
6. 再执行 `/chat 你的问题` 或直接 `@机器人`

## 后续可继续长

这次先搬了基础设施和 RAG 部分，下一步如果你要继续做成真正的 `agent + tools + memory`，可以直接在 `src/langchain_app` 上继续叠。

当前模型分工：

- `agent_model_name`: 给普通聊天和后续 agent 使用
- `rag_chain_model_name`: 给 RAG 总结链使用，适合配更省钱的模型
- `embedding_model_name`: 给向量化和检索使用
