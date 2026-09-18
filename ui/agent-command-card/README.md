---
id: ui-agent-command-card
domain: ui
title: Agent 终端执行框与动态状态机卡片
language: javascript
tags: [ui, agent-card, animation, web-component, mirasim, css]
source: "Mirasim Web UI (逆向与优化)"
test_cmd: "node --test command_card_test.js"
dependencies: []
created: 2026-09-19
---

# Agent 终端执行框与动态状态机卡片

本模块复刻并优化了 **Mirasim Agent 桌面端/网页端标志性的命令卡片（Command Card）交互与执行动效**。将其封装为零外部依赖的 Web Component 与高纯度 CSS 原语，支持在 React、Vue、Svelte 或原生 HTML 中即插即用。

### 1. 痛点与设计背景
在构建面向 AI Agent 的交互界面时，工具调用和 Shell 命令的展示面临几个工程体验痛点：
- **静态缺乏即时反馈**：工具执行往往需要数秒甚至数十秒，静态占位符无法给用户提供明确的“系统正在活跃处理”的心流体验；
- **过多三方库依赖**：市面上的动效库（如 Framer Motion、Lottie）体积庞大，难以直接嵌入轻量化 Web UI 或 Webview；
- **可访问性与减弱动态（Reduced Motion）支持欠缺**：高强度发光或旋转动效在无障碍模式下容易引起视觉疲劳。

### 2. 优化与工程亮点
- **零依赖 Web Component**：直接提供 `<agent-command-card>` 自定义标签，支持 `command`、`status`（`idle` | `running` | `success` | `error`）、`effect`、`duration` 等属性的实时响应。
- **5 种硬件加速微动效（GPU-Accelerated）**：
  1. `native`：Mirasim 经典单段高精度无级旋转环（Linear Spin Ring）；
  2. `pulse`：呼吸式发光边框（Soft Pulse Glow）；
  3. `shimmer`：顶部边缘跑马灯扫光（Stream Shimmer）；
  4. `beam`：角部流动光束描边（Corner Border Beam，利用 Conic-Gradient 与 Mask）；
  5. `cursor`：终端阶梯光标闪烁（`steps(1)` Cursor Blink）。
- **无障碍（A11y）友好**：内置 ARIA 属性（`role="region"`, `aria-busy`, `aria-expanded`），支持全键盘导航（`Enter` / `Space` 展开/折叠），并在检测到 `@media (prefers-reduced-motion: reduce)` 时自动平滑回退至纯静态状态。

### 3. 使用范例

#### 原生 HTML / Web Component
```html
<link rel="stylesheet" href="command-card.css" />
<script src="command-card.js"></script>

<agent-command-card command="npm run test" status="running" effect="pulse">
  Running test suites...
</agent-command-card>
```

#### React / Next.js
```tsx
import "./command-card.css";
import "./command-card.js";

export function TerminalCard({ cmd, status, output }) {
  return (
    <agent-command-card command={cmd} status={status} effect="beam">
      {output}
    </agent-command-card>
  );
}
```

### 4. 运行验证
```bash
node --test command_card_test.js
```
