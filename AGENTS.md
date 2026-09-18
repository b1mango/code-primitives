# Instructions for AI Agents (Agent SOP)

你是本代码资产库的维护者与使用者。当你被授权维护、更新或查询本仓库时，必须严格遵守以下规范。

---

## 🔍 场景一：查询与借用模式 (Retrieval)

1. **第一入口**：优先读取根目录下的 `catalog.json` 或 `llms.txt`，根据关键词（keywords/domain）进行语义匹配。
2. **定向读取**：定位到目标路径 `<domain>/<pattern-name>/` 后，按需只读取该目录下的实现与测试文件，避免无谓遍历。
3. **安全复用**：借用代码时，参考对应 `*_test.*` 中的调用范式进行移植与集成。

---

## 📥 场景二：录入与新增模式 (Ingestion)

当用户要求你“将某段代码/某项目有价值的解法沉淀到 code-primitives”时，必须按以下标准步骤执行，严禁跳步：

1. **准入审查**：严格对照根目录 `README.md` 的准入标准。若属于平庸 CRUD 或强业务代码，坚决拒绝并向用户说明原因。
2. **纯化解耦**：
   - 移除任何上游私有依赖、专有日志库、公司业务命名空间。
   - 优先替换为语言标准库；如必须引入外部库，选择社区公认的标准库。
3. **建立目录**：
   - 路径规范：`<domain>/<kebab-case-pattern-name>/`
4. **交付三件套**：
   - **核心实现**：如 `keccak.go`、`sieve.py` 等，要求逻辑纯粹。
   - **自动化测试**：如 `pow_test.go`、`test_sieve.py` 等，必须包含正常流 + 边缘 Case；算法类必须包含 Benchmark。
   - **说明文档**：编写本目录的 `README.md`，必须包含标准 YAML Frontmatter（格式见下方）。
5. **本地验证（硬性门禁）**：
   - 在子目录下执行其测试命令（如 `go test -v ./...`）。**测试未通过前严禁提交**。
6. **同步注册表**：
   - 将新模式追加到根目录 `catalog.json`，保持结构规范。
   - 将新模式追加到根目录 `llms.txt`。
7. **Git 提交规范**：
   - Commit message: `feat(<domain>): add <pattern-name> (<language>)`

---

## 📋 子模块 README Frontmatter 规范

每个子模块的 `README.md` 顶部必须包含标准 YAML Frontmatter，格式如下：

```yaml
---
id: <domain>-<pattern-name>
domain: <domain>
title: <简短标题>
language: <go|python|typescript|rust|c++>
tags: [tag1, tag2]
source: "<上游项目名或原创>"
test_cmd: "<该目录下执行测试的单行命令，如 go test -v ./...>"
dependencies: []
created: YYYY-MM-DD
---
```
