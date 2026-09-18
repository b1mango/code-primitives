---
id: streaming-sse-tool-sieve
domain: streaming
title: 流式输出工具调用防泄漏状态机 (Tool Sieve)
language: go
tags: [streaming, sse, tool-call, markdown-fence, sliding-window]
source: "CJackHwang/ds2api"
test_cmd: "go test -v ./..."
dependencies: []
created: 2026-09-18
---

# 流式输出工具调用防泄漏状态机 (Tool Sieve)

本模块提供了一种在 LLM 流式输出（SSE）过程中，实时拦截、隔离和提取 XML/DSML 工具调用，同时彻底防止标签闪烁与 Markdown 误判的状态机实现。

### 1. 核心技术痛点
在将开源模型（或网页端逆向模型）封装为标准 OpenAI Tool Calling API 时，通常通过 Prompt 引导模型输出 `<tool_call>...</tool_call>` 标签。
- **标签泄漏**：在流式输出中，若逐 chunk 推送给前端，用户会看到一闪而过的 `<tool_call>` 脏标签；
- **Markdown 误判**：当模型在 Markdown 代码块（如 ````xml <tool_call>... </tool_call>````）中向用户展示示例时，简陋的正则拦截器会误把示例当成真实调用吃掉；
- **截断丢字**：当模型吐出未闭合的伪标签或在标签中间遭遇连接中断时，死板的缓冲池会造成正文丢字。

### 2. 状态机核心机制
- **滑动窗口切分（Safe/Hold）**：遇到可能构成标签前缀的字符（如 `<`）时，安全前缀立刻向下游推送，可疑片段暂存入 `hold` 缓冲；
- **Markdown 上下文跟踪**：实时计算反引号（``` 及 `）状态。在代码块内部的标签直接视为合法正文透传；
- **无损回退 Flush**：流结束时若捕获内容无法闭合成有效工具调用，一律无损释放回普通 Content。

### 3. 运行测试
```bash
go test -v ./...
```
