<div align="center">

  <p>
  <a href="#"><picture><source media="(prefers-color-scheme: dark)" srcset="assets/readme/lang-zh-night.svg"><img src="assets/readme/lang-zh-day.svg" alt="中文"></picture></a>
  <a href="#"><picture><source media="(prefers-color-scheme: dark)" srcset="assets/readme/lang-en-night.svg"><img src="assets/readme/lang-en-day.svg" alt="English"></picture></a>
  </p>

  <picture><source media="(prefers-color-scheme: dark)" srcset="assets/readme/hero-night.svg"><img src="assets/readme/hero-day.svg" alt="Retro README Kit：让你的 README 在千篇一律中被一眼认出" width="100%"></picture>

  <p>
  <img src="https://img.shields.io/badge/Python-3.8%2B-8fd6a0?style=flat-square&amp;labelColor=5a544a" alt="Python 3.8+">
  <img src="https://img.shields.io/badge/Deps-zero-ffd84a?style=flat-square&amp;labelColor=5a544a" alt="Deps zero">
  <img src="https://img.shields.io/github/license/b1mango/code-primitives?label=License&amp;color=f08a5d&amp;style=flat-square&amp;labelColor=5a544a" alt="License">
  <img src="https://img.shields.io/github/stars/b1mango/code-primitives?label=Stars&amp;color=8fd6a0&amp;style=flat-square&amp;labelColor=5a544a" alt="Stars">
  </p>

  <p>
  <a href="#快速开始"><picture><source media="(prefers-color-scheme: dark)" srcset="assets/readme/key-get-night.svg"><img src="assets/readme/key-get-day.svg" alt="快速开始"></picture></a>
  <a href="../README.md"><picture><source media="(prefers-color-scheme: dark)" srcset="assets/readme/key-docs-night.svg"><img src="assets/readme/key-docs-day.svg" alt="文档"></picture></a>
  <a href="../README.md#主题"><picture><source media="(prefers-color-scheme: dark)" srcset="assets/readme/key-themes-night.svg"><img src="assets/readme/key-themes-day.svg" alt="主题"></picture></a>
  </p>

</div>

<picture><source media="(prefers-color-scheme: dark)" srcset="assets/readme/sec-intro-night.svg"><img src="assets/readme/sec-intro-day.svg" alt="简介 · INTRO" width="100%"></picture>

Retro README Kit 把 README 的每一块视觉（封面、章节标题、按键链接）都做成日夜两套 SVG，用 `<picture>` 跟随 GitHub 主题自动切换。  
<sub><sup>Every visual block of the README is a day/night SVG pair that follows the GitHub theme through <code>&lt;picture&gt;</code>.</sup></sub>

- **像素字体转路径**：英文标签直接画成 `<path>`，任何机器上看起来都一样。  
  <sub><sup><strong>Pixel font as paths</strong>: English labels are drawn as paths and look the same everywhere.</sup></sub>
- **一份配置生成全套**：改 JSON，重新生成，不用手调 SVG。  
  <sub><sup><strong>One config</strong>: edit JSON, regenerate, never hand-tune SVG.</sup></sub>

<picture><source media="(prefers-color-scheme: dark)" srcset="assets/readme/sec-start-night.svg"><img src="assets/readme/sec-start-day.svg" alt="快速开始 · QUICK START" width="100%"></picture>

```bash
python3 readme_kit.py readme-kit.json --template README.template.md --readme README.md
```

<picture><source media="(prefers-color-scheme: dark)" srcset="assets/readme/sec-idea-night.svg"><img src="assets/readme/sec-idea-day.svg" alt="设计理念 · IDEA" width="100%"></picture>

> **像一件实物，而不是一页文档。**  
> <sub><sup>Make it feel like an object, not a document.</sup></sub>

<picture><source media="(prefers-color-scheme: dark)" srcset="assets/readme/sec-notice-night.svg"><img src="assets/readme/sec-notice-day.svg" alt="许可证 · LICENSE" width="100%"></picture>

**License**: MIT
