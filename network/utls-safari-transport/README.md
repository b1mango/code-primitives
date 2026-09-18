---
id: network-utls-safari-transport
domain: network
title: Safari TLS 指纹模拟与 ALPN HTTP/1.1 强制降级
language: go
tags: [network, utls, tls-fingerprint, waf-bypass, safari]
source: "https://github.com/CJackHwang/ds2api"
test_cmd: "go test -v ./..."
dependencies: ["github.com/refraction-networking/utls"]
created: 2026-09-18
---

# Safari TLS 指纹模拟与 ALPN HTTP/1.1 强制降级

> 来源与致谢：参考并提炼自 [CJackHwang/ds2api](https://github.com/CJackHwang/ds2api)，在其 uTLS Safari 传输层配置基础上完成了独立 Client 封装、ALPN 重写机制与握手测试。

本模块提供了一个可直接替代 Go 原生 `*http.Client` 的传输层适配器，用于在 HTTP 请求中伪装 Apple Safari 浏览器的 TLS ClientHello 握手指纹（JA3/JA4），并动态将 ALPN 降级为 `HTTP/1.1`。

### 1. 核心技术痛点
- **Go 默认 TLS 特征被阻断**：Go 标准库 `crypto/tls` 的 CipherSuites 和 Extensions 具有固定的顺序和默认集，极易被 Cloudflare、Akamai、AWS WAF 等反爬与风控系统识破并直接返回 403；
- **HTTP/2 行为指纹复杂**：现代 WAF 不仅检测 TLS 握手，还会深度校验 HTTP/2 的 Settings 帧顺序、Window Update 步长、伪头（`:method`, `:path`）顺序。一旦 Go 客户端使用标准 HTTP/2，极易因 H2 行为不符合真实浏览器而暴露。

### 2. 设计巧思
- **uTLS Safari ClientHello 模拟**：通过 `utls.HelloSafari_Auto` 生成完全符合 macOS/iOS Safari 真实的扩展列表和密钥交换套件；
- **动态重写 ALPN（强制 HTTP/1.1）**：在握手构建阶段劫持 `ALPNExtension`，强制指定 `http/1.1`。这既享受了真实 Safari 的 TLS 密码学特征，又彻底规避了复杂的 HTTP/2 特征风控，大幅提升请求通过率。

### 3. 运行测试
```bash
go test -v ./...
```
