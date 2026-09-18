<div align="center">

# Code Primitives

<p><b>Curated lab of self-contained, production-grade, and verified engineering primitives for human developers and AI agents.</b></p>
<p><i>面向多语言工程实践的高价值代码原语与自包含模式资产库</i></p>

<p>
  <a href="LICENSE"><img src="https://img.shields.io/badge/License-MIT-blue.svg" alt="License"></a>
  <a href="AGENTS.md"><img src="https://img.shields.io/badge/AI--Friendly-Yes-success.svg" alt="AI-Friendly"></a>
  <a href="#-domains"><img src="https://img.shields.io/badge/Polyglot-Go%20%7C%20Python%20%7C%20TS%20%7C%20Rust-orange.svg" alt="Polyglot"></a>
  <a href="catalog.json"><img src="https://img.shields.io/badge/Catalog-Self--Indexed-blueviolet.svg" alt="Catalog"></a>
</p>

<p>
  <a href="README.md">简体中文</a> | <a href="README.en.md"><b>English</b></a>
</p>

</div>

---

`code-primitives` is a polyglot engineering asset repository for **reusable code building blocks (Primitives) and self-contained architectural patterns**.

Rather than trivial boilerplate or business-specific glue, this repository archives high-value, decoupled, and thoroughly tested implementations extracted from complex real-world challenges—including anti-scraping, streaming protocols, cryptography, and concurrency control.

Designed with native AI-friendliness, it enables autonomous retrieval, borrowing, maintenance, and verification by AI agents.

---

## 🤖 Agent Collaboration Examples

In daily cross-project development, you can directly prompt AI assistants (Codex, Claude Code, Cursor, etc.) to borrow or deposit assets:

### 1. 🔍 Retrieve Asset
> **Example Prompt:**
> 
> "Check `catalog.json` in my GitHub repository `b1mango/code-primitives` for modules handling streaming tool calls, and implement a Python version referencing its state machine design."

- **Agent Action Chain**:
  1. Fetch `catalog.json` or `llms.txt` in a single request (<200 tokens);
  2. Pinpoint the primitive path based on keywords and summary;
  3. Inspect the code and test fixtures to reproduce the pattern in the target project.

---

### 2. 📥 Ingest Asset
> **Example Prompt:**
> 
> "Distill this code snippet / repository into my GitHub `b1mango/code-primitives`. Strictly adhere to the root `AGENTS.md` guidelines for decoupling, test suite creation, registry updates, and push."

- **Agent Action Chain**:
  1. **Gatekeeping**: Review against inclusion criteria to filter out trivial business logic;
  2. **Decoupling**: Strip vendor-specific dependencies and environment locks;
  3. **Verification**: Implement test cases and run `test_cmd` to ensure 100% pass rate;
  4. **Registration**: Generate Frontmatter documentation and update `catalog.json` and `llms.txt`.

---

## 📥 Inclusion Criteria

To be accepted into this library, a pattern must satisfy at least 3 of the following conditions:

1. **Non-trivial Problem**: Solves complex technical edge cases (e.g. non-standard protocol state machines, WAF fingerprint cloaking, streaming tag leaks, concurrency lock contention), rather than off-the-shelf library calls.
2. **Craftsmanship & Performance**: Demonstrates clear architectural or efficiency advantages (e.g., zero-allocation hot loops, state pre-absorption, lossless fallback mechanisms).
3. **Zero-Coupling**: Free from business-specific domain entities, relying primarily on standard libraries or ubiquitous foundational primitives.
4. **Self-Contained & Verified**: Accompanied by executable unit tests and benchmarks that run autonomously in isolation.

## 🚫 Exclusion Criteria

- Business-specific domain entities or proprietary API wrappers.
- Trivial CRUD logic, basic routing, or general config files.
- Code snippets that cannot be tested in a self-contained local environment.

---

## 🧭 Quick Access

- **Human Reading**: Explore subdirectories and review each module's `README.md` for architectural breakdowns and design choices.
- **AI Agent Reading**:
  - Read [`llms.txt`](llms.txt) for an ultra-compact summary index.
  - Read [`catalog.json`](catalog.json) for structured machine-readable registry metadata.

---

## 📂 Domains

- [`crypto/`](crypto/): Cryptographic algorithms, hashing variants, PoW solvers
- [`streaming/`](streaming/): Streaming protocols, SSE parsing, tool call sieves, state machines
- [`network/`](network/): Network transport, TLS fingerprint emulation, anti-bot bypass
- [`concurrency/`](concurrency/): Concurrency primitives, worker pools, slot scheduling

---

## 🛠️ Contribution & Maintenance

All additions and maintenance must strictly follow [`AGENTS.md`](AGENTS.md).
