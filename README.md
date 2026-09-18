# Code Primitives

> A curated lab of self-contained, production-grade, and verified engineering primitives for human developers and AI agents.

`code-primitives` 是一个面向多语言工程实践的**代码原语（Primitives）与核心模式资产库**。

这里沉淀的不是平庸的业务代码片段，而是在复杂系统、反爬逆向、流式解析、密码学计算、高并发控制等场景中提炼出的**最小可用、经过完备测试、零业务耦合**的高价值实现。

本仓库采用原生 AI 友好设计（AI-Friendly），支持 AI Agent 自主检索、借用、维护与验证。

---

## 📥 准入标准 (Inclusion Criteria)

一段代码或模式要被收录进本库，必须至少满足以下条件中的 3 条：

1. **解决硬痛点（Non-trivial Problem）**：解决了特定领域的技术死角（如非标协议状态机、WAF 指纹伪装、流式标签闪烁泄漏、并发锁优化等），而非调库开箱即得的代码。
2. **设计/算法巧思（Craftsmanship & Performance）**：具备显著的架构或性能优势（如热循环零内存分配、前缀状态预吸收、无损回退机制）。
3. **极简零耦合（Zero-Coupling）**：剥离业务专有依赖与命名空间，优先使用语言标准库或通用基础库，可独立移植。
4. **自包含可运行（Self-Contained & Verified）**：必须附带能够独立跑通的单元测试（Test）与基准测试（Benchmark）。

## 🚫 排除标准 (Exclusion Criteria)

- 带有业务属性的业务逻辑或私有 API 封装。
- 常见的 CRUD、路由挂载、常规配置文件。
- 无法在单机隔离环境下执行测试的片段。

---

## 🧭 快速检索与使用 (Quick Access)

- **人类阅读**：浏览各分类目录下的子文件夹，阅读 `README.md` 查看模式解析与核心解题思路。
- **AI Agent 读取**：
  - 读取 [`llms.txt`](llms.txt) 获取全局精简大纲（极低 Token 消耗）。
  - 读取 [`catalog.json`](catalog.json) 获取机器可读的结构化模式注册表。

---

## 📂 领域分类 (Domains)

- [`crypto/`](crypto/)：密码学算法、哈希变种、PoW 求解器
- [`streaming/`](streaming/)：流式传输、SSE 解析、流式标签过滤、状态机
- [`network/`](network/)：网络传输、TLS 指纹模拟、反爬与协议适配
- [`concurrency/`](concurrency/)：高并发控制、工作池、队列与槽位调度

---

## 🛠️ 维护规范

所有对本仓库的新增、更新与维护工作，请严格遵照 [`AGENTS.md`](AGENTS.md) 执行。
