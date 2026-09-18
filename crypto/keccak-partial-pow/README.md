---
id: crypto-keccak-partial-pow
domain: crypto
title: 跳步 Keccak-f[1600] 零堆分配 PoW 求解器
language: go
tags: [crypto, pow, keccak, zero-allocation, sha3]
source: "CJackHwang/ds2api"
test_cmd: "go test -v -bench=. ./..."
dependencies: []
created: 2026-09-18
---

# 跳步 Keccak-f[1600] 零堆分配 PoW 求解器

本模块是 DeepSeek 网页端工作量证明（PoW）`DeepSeekHashV1` 挑战的高性能纯 Go 解法与哈希还原。

### 1. 核心技术痛点
DeepSeek 采用了自研的非标 SHA3 哈希变种（`DeepSeekHashV1`）：其参数等同于 SHA3-256（`rate=136`, `padding=0x06...0x80`, 输出 32 字节），但其底层的 **Keccak-f[1600] 置换跳过了 round 0（仅执行 round 1..23）**。普通密码学标准库无法直接计算，依赖浏览器 WASM 计算又极其低效。

### 2. 算法与架构设计亮点
- **纯 Go 状态展开**：直接将 25 个 `uint64` 内部状态解构成独立局部变量（`a0..a24`, `b0..b24`），纯位运算展开 23 轮置换，性能逼近编译后的 C 代码。
- **前缀状态预吸收（Prefix State Pre-absorbing）**：输入格式为 `prefix + str(nonce)`。在循环前将不变的 `prefix` 预先吸收进 Keccak 状态，遍历循环中每次只需处理尾部数字，哈希耗时立减 50% 以上。
- **热循环零堆分配（0 B/op）**：
  - 栈上使用 `[20]byte` 逆向格式化整数，杜绝 `strconv.Itoa` 的内存逃逸。
  - 目标匹配直接基于 4 个 `uint64` 整数（即 32 字节）在 CPU 寄存器层面比对，无需任何 Hex 编码转换。

### 3. 运行测试
```bash
go test -v -bench=. ./...
```
