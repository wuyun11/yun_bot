# QQ 机器人：官方 API、go-cqhttp、NoneBot 分别是什么

网上常说的「QQ 机器人官方 API」「go-cqhttp」「NoneBot」是三层不同东西：**官方对接方式**、**开源协议实现**、**Python 业务框架**。下面分别说明是什么、怎么配合、怎么选。

---

## 1. QQ 官方 API（腾讯官方对接方式）

### 是什么

- **腾讯官方**提供的 QQ 机器人开放能力，用于**合规、可上架**的机器人开发。
- 入口与文档：
  - 机器人开放平台：<https://open.qq.com/bot/>
  - QQ 机器人开发文档：<https://bot.q.qq.com/wiki/>（API v2 等）
- 使用 **AppID + AppSecret** 获取 AccessToken，请求头带 `Authorization: QQBot {ACCESS_TOKEN}`，接口基地址一般为 `https://api.sgroup.qq.com`。

### 特点

- **合规**：官方支持，符合平台规范，适合正式/长期运营。
- **流程**：注册开发者 → 创建应用 → 选择场景（频道/群聊/单聊）→ 开发与调试 → **提交审核** → 通过后发布。
- **SDK**：官方提供多语言 SDK，如 Go（botgo）、Python（botpy）、Node.js（bot-node-sdk）等。

### 小结

| 项目     | 说明                         |
|----------|------------------------------|
| 是什么   | 腾讯官方提供的机器人接口与平台 |
| 谁提供   | 腾讯                         |
| 合规性   | 官方认可，需审核后上线       |
| 典型用途 | 正式产品、需要稳定与合规时   |

---

## 2. go-cqhttp（GitHub 开源项目，协议层）

### 是什么

- **GitHub 开源项目**：[Mrs4s/go-cqhttp](https://github.com/Mrs4s/go-cqhttp)，用 **Go 语言**实现的 **OneBot 协议** 端，主要对接 **QQ**。
- 实现方式：**模拟 QQ 客户端**与 QQ 服务器通信；你的程序不直接连 QQ，而是通过 **HTTP 或 WebSocket** 连 **go-cqhttp**，由它转发消息、执行发消息/管理群等操作。
- 文档：<https://docs.go-cqhttp.org/>

### OneBot 协议简要

- **OneBot** 是一套**聊天机器人接口标准**（原 CQHTTP 演进而来），统一了「收消息、发消息、群管理」等 API 的格式。
- 常见版本：**OneBot 11**（原 CQHTTP，目前最常用）、**OneBot 12**（更新、跨平台）。
- go-cqhttp 是 QQ 侧对 OneBot 协议的**一种实现**：你按 OneBot 的 API 调 go-cqhttp，它就帮你在 QQ 上执行对应操作。

### 特点

- **非官方**：不经过腾讯开放平台，存在**账号风控、封号、违反使用协议**等风险，不适合对外正式商用。
- **轻量、跨平台**：单可执行文件，Windows/Linux/macOS 都能跑；支持正向/反向 HTTP、正向/反向 WebSocket。
- **能力**：收发文字/图片/文件、群管理（禁言、踢人等）、获取群/好友信息等，对个人或内部群做实验、自用机器人很常见。

### 小结

| 项目     | 说明                                   |
|----------|----------------------------------------|
| 是什么   | 实现 OneBot 协议、对接 QQ 的开源程序   |
| 谁提供   | 社区开源（GitHub）                     |
| 合规性   | 非官方，有封号与协议风险               |
| 典型用途 | 自用、学习、内部群、对合规要求不高的场景 |

---

## 3. NoneBot（Python 机器人框架，业务层）

### 是什么

- **基于 Python 的 QQ 机器人框架**，GitHub：[nonebot/nonebot](https://github.com/nonebot/nonebot)。
- 文档：<https://nonebot.dev/docs>（NoneBot2）、历史版 v1：<https://v1.nonebot.dev/>。
- 负责的是**业务逻辑**：解析消息、匹配命令、调用插件、会话管理、权限等；**不直接连 QQ**，而是和 **OneBot 实现（如 go-cqhttp）** 通信。

### 和 go-cqhttp 的关系

- **go-cqhttp**：跑在本地，登录 QQ、收消息、发消息，对外暴露 **OneBot 协议**（HTTP/WebSocket）。
- **NoneBot**：跑你的 Python 代码，通过 **反向 WebSocket**（或 HTTP）连接 go-cqhttp，收到「消息事件」后由 NoneBot 的插件/规则处理，再通过 OneBot API 让 go-cqhttp 发消息。
- 流程可以简化为：  
  **QQ 服务器 ↔ go-cqhttp（OneBot 协议）↔ NoneBot（你的业务）**。

### 特点

- **异步**：基于 asyncio，适合 I/O 多的机器人逻辑。
- **插件化**：功能按插件组织，便于维护和复用。
- **多适配器**：NoneBot2 支持多种「适配器」，其中 **OneBot（如 go-cqhttp）** 最常用；理论上也可接官方 API 的适配器（若有社区或自写）。
- **版本**：v1 对应 OneBot 11；v2 需 Python 3.9+，功能更完整。

### 小结

| 项目     | 说明                                           |
|----------|------------------------------------------------|
| 是什么   | 用 Python 写机器人逻辑的框架（消息处理、插件、会话） |
| 谁提供   | 社区开源（GitHub）                             |
| 和 QQ 的关系 | 不直接连 QQ，通过 OneBot 实现（如 go-cqhttp）连 QQ |
| 典型用途 | 用 Python 开发 QQ 机器人时，写业务代码的这一层   |

---

## 4. 三者关系简图

```
【官方路线】
  你的代码（如 botpy）──► QQ 官方 API ──► 腾讯服务器 ──► QQ 客户端/群
  合规、需审核、适合正式上线

【开源常见路线】
  你的代码（NoneBot 等）──► OneBot 协议（HTTP/WS）──► go-cqhttp ──► 模拟 QQ 客户端 ──► 腾讯服务器
  不经过官方开放平台，自用/内部群常见，有风控风险
```

- **官方 API**：和腾讯直接对接的「正规入口」。
- **go-cqhttp**：开源、非官方的「协议实现」，负责和 QQ 通信，对外暴露 OneBot 接口。
- **NoneBot**：在你的业务这边，用 Python 处理消息、命令、插件，通过 OneBot 和 go-cqhttp（或其它 OneBot 实现）对话。

---

## 5. 选型与合规建议（结合网上说法）

| 需求           | 更合适的选择                     |
|----------------|----------------------------------|
| 正式上线、商用、怕封号 | **QQ 官方 API** + 官方文档与审核  |
| 同学群/个人自用、快速试 | **go-cqhttp + NoneBot** 很常见     |
| 用 Python 写逻辑 | **NoneBot** 接 go-cqhttp（或接官方适配器若已有） |
| 只关心协议、用别的语言 | 用 **go-cqhttp** 暴露的 OneBot API，用任意语言写业务 |

网上普遍说法：**官方 API** 合规稳定但要走审核流程；**go-cqhttp** 方便、生态大，但属非官方模拟客户端，存在封号与协议风险，适合自用或内部使用。

---

## 6. 和你当前架构文档的关系

- 你写的《QQ群机器人业务架构设计.md》里的 **「QQ 适配层」**：
  - 若走**官方**：适配层可对接官方 API（如用 botpy），拿到事件后转成 `session_id`、文本/文件，再调你的 RAG、知识库、记忆等。
  - 若走 **go-cqhttp + NoneBot**：NoneBot 里写「消息事件 → 生成 session_id → 调 RAG/上传」的适配逻辑即可，底层由 go-cqhttp 通过 OneBot 协议和 QQ 通信。

上面这份说明文档放在《QQ群机器人业务架构设计》旁边，方便你在选「官方 API」还是「go-cqhttp + NoneBot」时对照查阅。
