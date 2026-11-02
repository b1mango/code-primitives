# README 模板库

按风格收集可复用的 README 模板。每个模板一个子目录，包含生成器或模板文件、可直接查看的示例，以及来源说明。

| 模板 | 风格 | 适合 | 形式 |
|---|---|---|---|
| [retro-panel](retro-panel/README.md) | 千禧年米色机箱：像素字体、面板章节标题、键帽链接，日夜双套 SVG | 想在首屏建立辨识度的个人项目、工具、Bot | Python 生成器 + Markdown 模板，3 套配色 |

## 选用

1. 先看各模板 README 顶部的封面和 `example/`，按项目气质挑选风格。
2. 按模板说明复制配置或模板文件到目标仓库，再生成或填写。
3. 章节内容（简介、功能、安装、开发、许可证）仍按项目自身的 README 规范编写，模板只负责视觉。

## 收录约定

- 目录：`readme/<kebab-case-style-name>/`，README 带标准 Frontmatter（`domain: readme`），并登记到根目录 `catalog.json` 与 `llms.txt`，同时更新上表。
- 必须附 `example/`：一份可直接在 GitHub 上查看效果的示例 README。
- 有暗色模式问题的视觉（浅色底图、深色文字）须提供日夜两套资产，或说明只适配一种主题。
- 参考了他人 README 的，写明来源仓库；不直接复制他人的图片、插画或字体文件。
- 含生成器的模板须带测试，按根目录 [AGENTS.md](../AGENTS.md) 的门禁执行。
