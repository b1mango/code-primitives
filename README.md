<div align="center">

# Code Primitives

<p><b>面向多语言工程实践的高价值代码原语与自包含模式资产库</b></p>
<p><i>A curated lab of self-contained, production-grade, and verified engineering primitives for human developers and AI agents.</i></p>

<p>
  <a href="LICENSE"><img src="https://img.shields.io/badge/License-MIT-blue.svg" alt="License"></a>
  <a href="AGENTS.md"><img src="https://img.shields.io/badge/AI--Friendly-Yes-success.svg" alt="AI-Friendly"></a>
  <a href="#-领域分类-domains"><img src="https://img.shields.io/badge/Polyglot-Go%20%7C%20Python%20%7C%20TS%20%7C%20Rust-orange.svg" alt="Polyglot"></a>
  <a href="catalog.json"><img src="https://img.shields.io/badge/Catalog-Self--Indexed-blueviolet.svg" alt="Catalog"></a>
</p>

<p>
  <a href="README.md"><b>简体中文</b></a> | <a href="README.en.md">English</a>
</p>

</div>

---

`code-primitives` 是一个面向多语言工程实践的**代码原语与核心模式资产库**。

这里沉淀的不是平庸的业务代码片段，而是在复杂系统、反爬逆向、流式解析、密码学计算、高并发控制等场景中提炼出的**最小可用、经过完备测试、零业务耦合**的高价值实现。

本仓库采用原生 AI 友好设计（AI-Friendly），支持 AI Agent 自主检索、借用、维护与验证。

---

## 🤖 与 AI Agent 协作范例

在日常多项目开发中，你可以直接向 Codex、Claude Code、Cursor 等 AI 助手发送以下 Prompt，驱动其自动查询或沉淀资产：

### 1. 🔍 调用与检索资产
> **Prompt 示例：**
> 
> “去查一下我的 GitHub 仓库 `b1mango/code-primitives` 里的 `catalog.json`，看有没有处理流式工具调用的模块，参考它的状态机设计帮我实现一个 Python 版本。”

- **Agent 动作链**：
  1. 通过 `curl` 或 GitHub API 单次拉取 `catalog.json` / `llms.txt`（消耗极少 Token）；
  2. 根据 `keywords` 与 `summary` 精准定位对应原语路径；
  3. 读取其实现代码与配套测试，吸收设计模式并在当前项目中完成集成复现。

---

### 2. 📥 纯化与录入资产
> **Prompt 示例：**
> 
> “把当前项目里的这段代码/这个仓库沉淀到我的 GitHub `b1mango/code-primitives` 中，严格遵循其根目录 `AGENTS.md` 的规范完成解耦、单测编写、注册表更新并 Push。”

- **Agent 动作链**：
  1. **准入审查**：对照准入标准过滤掉平庸业务代码；
  2. **纯化解耦**：剥离专有依赖、私有变量与环境强绑定；
  3. **单测验证**：编写测试用例并执行 `test_cmd`，确保 100% 通过；
  4. **全量登记**：生成带 Frontmatter 的说明文档，同步更新根目录 `catalog.json` 与 `llms.txt`。

---

## 📥 准入标准

一段代码或模式要被收录进本库，必须至少满足以下条件中的 3 条：

1. **解决硬痛点**：解决了特定领域的技术死角（如非标协议状态机、WAF 指纹伪装、流式标签闪烁泄漏、并发锁优化等），而非调库开箱即得的代码。
2. **设计与性能巧思**：具备显著的架构或性能优势（如热循环零内存分配、前缀状态预吸收、无损回退机制）。
3. **极简零耦合**：剥离业务专有依赖与命名空间，优先使用语言标准库或通用基础库，可独立移植。
4. **自包含可运行**：必须附带能够独立跑通的单元测试（Test）与基准测试（Benchmark）。

## 🚫 排除标准

- 带有业务属性的业务逻辑或私有 API 封装。
- 常见的 CRUD、路由挂载、常规配置文件。
- 无法在单机隔离环境下执行测试的片段。

---

## 🧭 快速检索与使用

- **人类阅读**：浏览各分类目录下的子文件夹，阅读 `README.md` 查看模式解析与核心解题思路。
- **AI Agent 读取**：
  - 读取 [`llms.txt`](llms.txt) 获取全局精简大纲（极低 Token 消耗）。
  - 读取 [`catalog.json`](catalog.json) 获取机器可读的结构化模式注册表。

---

## 📂 领域分类

- [`crypto/`](crypto/)：密码学算法、哈希变种、PoW 求解器
- [`streaming/`](streaming/)：流式传输、SSE 解析、流式标签过滤、状态机
- [`network/`](network/)：网络传输、TLS 指纹模拟、反爬与协议适配
- [`concurrency/`](concurrency/)：高并发控制、工作池、队列与槽位调度
- [`ui/`](ui/)：前端交互、Agent 执行卡片、微动效、Web Component

---

## 🛠️ 维护规范

所有对本仓库的新增、更新与维护工作，请严格遵照 [`AGENTS.md`](AGENTS.md) 执行。
