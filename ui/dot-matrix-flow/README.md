---
id: ui-dot-matrix-flow
domain: ui
title: 点阵粒子流（ultracode 紫色抖动点阵进度/状态底纹）
language: javascript
tags: [ui, canvas, particles, dot-matrix, progress, animation, web-component, reduced-motion, theming]
source: "复刻 Claude Code「ultracode」档位的紫色抖动点阵观感；实现提炼自 觅音 SongSeek web/src/RowFlow.tsx（原创）"
test_cmd: "node --test dot_flow_test.js"
dependencies: []
created: 2026-11-10
---

# 点阵粒子流 · Dot Matrix Flow

> 来源：视觉上复刻 Claude Code 思考档位 **ultracode** 的紫色动态粒子（细小方点、各自抖动、向前沿聚密增亮）。实现最早写在 觅音 SongSeek 的「下载中整行粒子进度」（`web/src/RowFlow.tsx`），这里剥离 React/store/业务文案，抽成零依赖的 Canvas 原语。

把任意一个盒子（进度条、表格整行、按钮胶囊、卡片底纹）变成一片会呼吸的点阵：

| 状态 | 用途 | 观感 |
| --- | --- | --- |
| `progress` | 确定进度（0–1） | 从左向右抖动填充，越靠前沿越密越亮，前沿外溢出少量光点；显示值平滑追赶目标值 |
| `sweep` | 未知进度（只知道在下、不知道总大小） | 一颗彗星从左扫到右循环，尾部渐隐 |
| `pulse` | 收尾处理 / 高强度思考 / ultracode 开启 | 整片铺满，叠加一道行进波，抖动节奏加快 |
| `idle` | 空闲底纹 | 稀疏暗淡的光点 |

`progress` 传 `null`/非数字时自动退化为 `sweep`。

## 1. 痛点

- 进度条本身信息量低，长任务里一根实心色块看不出"还活着"；常见的 shimmer 扫光又太模板化。
- 想要 ultracode 那种"颗粒感+抖动"的质感，但 CSS 背景图做不出"每个点独立闪烁、密度随位置变化"。
- 列表里同时有十几行在下载时，每行一个动画很容易吃 CPU，且离屏行也在白跑。

## 2. 设计要点

- **独立节拍抖动**：每个点用 `hash(i, j)` 得到固定种子，按 `floor(t · rate · (0.6 + seed) + seed·7)` 换拍后再掷一次骰子决定亮灭。各点节奏不同，整片是"抖"而不是"同步闪"。整个帧由 `(i, j, t)` 确定，可复现、可测试。
- **密度场**：填充区内密度 `0.08 + 0.7·u^2.2`（u 为尾→前沿 0→1）叠一层正弦涟漪；前沿 10px 内强制高密高亮；前沿外按 `exp(-ahead/14)` 衰减溢出光点。行上下边缘降透明度，文字落在更安静的中带。
- **同色相渐变**：底部淡紫 wash 的透明端用"同 RGB、alpha=0"，而不是 `transparent`（= 透明黑），避免渐变经过灰色。颜色先交给 canvas 规范化，所以 CSS 变量里写任何合法颜色都行。
- **性能**：画布按 DPR 缩放；动画按 30fps 节流（保留余数，60Hz 屏上严格隔帧）；`IntersectionObserver` 离屏暂停；单帧 720×40 约 0.04ms（mock ctx，见测试里的 benchmark）。
- **主题**：读取 `--dot-flow`（点色）与 `--dot-flow-soft`（底色）CSS 变量；`<html>/<body>` 的 `class`/`data-theme`/`style` 变化或系统深浅色切换时自动重新取色，无需业务派发事件。
- **无障碍**：`prefers-reduced-motion: reduce` 时不启动循环，只在状态/进度变化时画一帧静态图；元素带 `aria-hidden`，进度文字请另行提供。

## 3. 使用

### Web Component（最省事）

```html
<link rel="stylesheet" href="dot-flow.css" />
<script src="dot-flow.js"></script>

<div class="dot-flow-host" style="height:40px">
  <dot-flow state="progress" progress="0.35"></dot-flow>
  下载中 35%
</div>
```

`<dot-flow>` 绝对定位铺满包含块、`z-index:-1` 垫在内容下面，所以父元素需要 `position: relative; isolation: isolate`（即 `.dot-flow-host`）。

属性：`state`、`progress`、`palette`（这三个可动态改，也可用 `el.state = 'pulse'` / `el.progress = 0.5`）；`pitch`（点间距，默认 4）、`size`（点边长，默认 2）、`alpha`（默认 0.8）、`fps`（默认 30）、`color`、`soft`、`host`（只在挂载时读取）。

### 表格整行作为进度（SongSeek 用法）

`<tr>` 不能做定位容器，所以把元素放进首个单元格，用 `host="tr"` 让它按整行尺寸绘制：

```html
<table class="dot-flow-table">
  <tr class="is-flowing">
    <td>02<dot-flow host="tr" state="progress" progress="0.62"></dot-flow></td>
    <td>Song B</td><td>下载中 62%</td>
  </tr>
</table>
```

`.dot-flow-table` 给表格 `isolation`，并把流动行的单元格背景设透明，否则画布会被单元格背景盖住。

### React

```tsx
import "./dot-flow.css";
import "./dot-flow.js"; // 注册 <dot-flow>

export function RowProgress({ fraction, finishing }: { fraction: number | null; finishing: boolean }) {
  return <dot-flow host="tr" state={finishing ? "pulse" : "progress"} progress={fraction ?? ""} />;
}
```

TS 下需声明一次：`declare global { namespace JSX { interface IntrinsicElements { "dot-flow": any } } }`。

或者直接用命令式控制器，自己管画布（文件是 UMD 风格：CommonJS 下走 `module.exports`，浏览器/Vite 源码里挂到 `window.DotFlow`）：

```tsx
import "./dot-flow.js";
const { createDotFlow } = (window as any).DotFlow;

useEffect(() => {
  const flow = createDotFlow(canvasRef.current!, { host: canvasRef.current!.closest("tr")! });
  flowRef.current = flow;
  return () => flow.destroy();
}, []);
useEffect(() => flowRef.current?.set({ progress: fraction, state: finishing ? "pulse" : "progress" }), [fraction, finishing]);
// <canvas ref={canvasRef} className="dot-flow-canvas" aria-hidden />
```

### API

| 导出 | 说明 |
| --- | --- |
| `createDotFlow(canvas, opts)` | 返回 `{ set({state?, progress?, palette?}), resize(), recolor(), paint(), destroy(), state, shown, colors }`。`opts`：`host`、`state`、`progress`、`palette`、`pitch`、`size`、`alpha`、`fps`、`ease`、`wash`、`color`、`soft`、`reducedMotion` |
| `paintFrame(ctx, w, h, frame, opts)` | 纯绘制一帧（`frame = {state, shown, t, color, soft}`），返回绘制的点数；可用于离屏渲染、导出静帧或接入自己的循环 |
| `DOT_FLOW_PALETTES` / `paletteColors(name, scheme)` | 内置配色表与取色 |
| `columnField` / `flowGeometry` / `hash` | 密度场、填充几何、整数哈希，便于移植到 WebGL/Swift/WPF 等其他渲染层 |
| `DotFlowElement` | `<dot-flow>` 的类，SSR 环境下为 `null` |

## 4. 配色

三套内置配色，亮/暗各一组值：

| palette | 亮色 点 / 底 | 暗色 点 / 底 | 说明 |
| --- | --- | --- | --- |
| `purple`（默认） | `#7b4fd8` / `#ebe2fb` | `#a98bff` / `#261d3d` | ultracode 紫 |
| `orange` | `#bd5230` / `#f9e1d4` | `#ec9672` / `#3a2219` | Claude 橙；亮色版压暗到与紫色同等明度，2px 小点在浅底上才立得住 |
| `claude` | 同 orange | 同 purple | 亮色用橙、暗色用紫 |

切换方式（按需选一种）：

```html
<!-- 整页或任意子树：改的是 --dot-flow / --dot-flow-soft，未指定 palette 的实例都跟着变 -->
<html data-dot-flow="claude">

<!-- 单个实例固定配色，不受页面切换影响 -->
<dot-flow palette="orange" state="progress" progress="0.4"></dot-flow>
```

```js
createDotFlow(canvas, { palette: 'orange' });
flow.set({ palette: 'claude' }); // 运行时切换
```

取色优先级：`color`/`soft` 显式参数 → 指定了 palette 时读 `--dot-flow-<palette>(-soft)`，否则读 `--dot-flow(-soft)` → 内置表 `DOT_FLOW_PALETTES`（不引 CSS 也能用）。想微调某套配色，覆盖 `--dot-flow-orange` 等变量即可；暗色由 `prefers-color-scheme` 或 `<html>` 上的 `data-theme="dark"` / `.dark` 决定，切换时自动重新取色。

同一行的文字标签（如百分比）建议用 `color: var(--dot-flow)`，与粒子同色。

## 5. 验证

```bash
node --test dot_flow_test.js   # 16 项：配色表与取色优先级、哈希分布、几何、密度场单调性、同色相透明、帧确定性、控制器、30fps 节流、benchmark
python3 -m http.server         # 打开 index.html 看全部状态 + 亮暗切换
```
