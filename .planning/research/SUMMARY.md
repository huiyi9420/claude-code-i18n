# Project Research Summary

**Project:** Claude Code CLI i18n Tool (claude-code-i18n)
**Domain:** Post-build localization of minified JavaScript CLI via enhanced regex string replacement
**Researched:** 2026-04-05
**Confidence:** HIGH

## Executive Summary

这是一个独特的技术挑战：在不修改源代码、不依赖上游支持的前提下，对 13MB 的 minified JavaScript 文件（Claude Code CLI）进行安全的字符串级本地化。业界常规做法（源码级 i18n、AST 解析、React 组件 patch）在此场景下均不可行。研究表明，**增强型 regex + 引号上下文感知**是唯一可行的技术路线。核心架构由三层组成：备份完整性保证层（确保可恢复）、分级替换引擎层（长/中/短字符串差异化策略）、验证门控层（node --check 语法验证）。

推荐方案是纯 Python 标准库实现，零外部依赖。关键技术决策包括：逆序替换避免偏移重算、三级替换策略平衡覆盖率与安全性、从纯净备份提取字符串而非从已汉化文件。翻译映射表从简单键值对升级为带 context/scope 字段的结构化 JSON，为 Phase 2 的上下文感知翻译预留空间。

最大风险是**备份污染**和**短字符串误替换**。当前 v3.0 的备份文件已含 12,224 个中文字符，restore 功能名存实亡。短字符串（<10 字符）在 minified 代码中同时出现在 UI 文本和代码逻辑中，regex 无法可靠区分。缓解策略：备份创建时即锁定为只读并计算 SHA-256 校验和；MVP 阶段默认跳过短字符串翻译，仅在白名单中显式标记的条目才处理。

## Key Findings

### Recommended Stack

纯 Python 标准库方案，零外部依赖，目标兼容 Python 3.8+。Node.js 仅用于 `node --check` 语法验证（Claude Code 本身依赖 Node，无需额外安装）。

**Core technologies:**
- **Python `re` (标准库):** 正则引擎 -- 支持本项目所需的全部特性（lookbehind/lookahead/word boundary），无需第三方 `regex` 库
- **Python `pathlib` + `shutil`:** 文件路径与复制 -- 跨平台路径操作，备份创建/恢复的核心工具
- **Python `hashlib.sha256`:** 校验和 -- 备份完整性验证，分块读取避免大文件内存问题
- **Python `subprocess` + `os.rename`:** 外部调用与原子写入 -- `node --check` 验证 + 临时文件写入后原子替换
- **Python `argparse`:** CLI 子命令路由 -- 6 个子命令（apply/restore/extract/status/coverage/version），argparse 完全够用
- **JSON (翻译映射表):** `zh-CN.json` -- 标准库原生支持，所有编辑器可直接编辑，无额外依赖

### Expected Features

**Must have (table stakes -- P1):**
- **一键汉化 (apply):** 核心价值，三级替换策略（长/中/短），逆序替换，30 秒内完成
- **一键恢复 (restore):** 从纯净备份恢复，SHA-256 校验 + CJK 污染检测，不可绕过的安全门
- **自动路径检测:** 支持 volta/npm/nvm/fnm 安装，`which claude` + 环境变量 + 配置文件覆盖
- **备份完整性保证:** 创建时锁定只读 + 哈希校验 + 纯净性检测（零 CJK 字符）
- **语法验证 (node --check):** 替换后强制验证，失败则从备份回滚
- **原子写入:** 先写临时文件，验证通过后 `os.rename()` 原子替换
- **版本检测:** 读取 package.json version 与映射表 `_meta.cli_version` 对比
- **字符串提取 (extract):** 从纯净备份提取可翻译字符串候选，噪声过滤 + UI 评分

**Should have (competitive -- P2):**
- **上下文感知翻译:** 映射表增加 context/scope 字段，同一英文在不同 UI 位置可有不同翻译
- **增量覆盖率报告 (coverage):** 已翻译/未翻译/跳过三类统计
- **dry-run 预览模式:** 替换前展示所有将被修改的位置及上下文
- **短字符串翻译:** 白名单机制 + 逐条审核，覆盖率从 1.4% 提升到 80%+ 时启用

**Defer (v2+ -- P3):**
- **版本更新智能适配:** 自动 diff 新旧版本提取结果，分类为 new/changed/removed
- **多模式验证:** `node --check` 之外的语义级验证
- **CI 集成:** 自动化回归检测
- **Aho-Corasick 优化:** 翻译条目超 2000 且性能不够时引入

### Architecture Approach

系统采用分层架构：CLI 入口 -> 命令路由层 -> 核心引擎层（Scanner/Replacer/Verifier）-> I/O 层（Backup Manager/Translation Map/Path Resolver）。核心引擎与 I/O 分离，引擎只处理字符串操作，不关心文件来源，便于单元测试不依赖真实 13MB 文件。关键架构决策：**不用 AST，用增强型 regex**。13MB minified JS 上 AST 解析耗时 5-15 秒、内存消耗 65-130MB，且每次替换后需重新解析。regex 配合引号上下文约束足以满足字符串定位需求。

**Major components:**
1. **String Scanner (core/scanner.py):** 正则提取候选字符串，配合噪声过滤和 UI 指标评分
2. **Replacement Engine (core/replacer.py):** 三级替换策略（长精确/中引号边界/短白名单），逆序替换避免偏移问题
3. **Verification Engine (core/verifier.py):** `node --check` 语法验证，失败触发回滚
4. **Backup Manager (io/backup.py):** 纯净备份保证 -- SHA-256 校验、CJK 污染检测、只读保护
5. **Path Resolver (config/paths.py):** 自动检测 cli.js 路径，支持多种安装方式
6. **Translation Map (data/zh-CN.json):** 结构化 JSON，带 context/scope/tier 字段，向后兼容简单键值对

### Critical Pitfalls

1. **备份文件污染 (CRITICAL):** 当前备份已含 12,224 中文字符。解决：创建时计算 SHA-256 + 纯净性检测 + 只读保护 + 每次使用前验证
2. **短字符串误替换 (CRITICAL):** "Error"/"Running" 同时出现在 UI 和代码逻辑中。解决：MVP 默认跳过短字符串，需在白名单显式标记 + 引号边界 + 替换次数上限
3. **替换顺序级联失败 (HIGH):** 短翻译是长翻译的子串导致覆盖。解决：按长度降序处理 + 已有的 longest-first 策略 + 逆序替换
4. **模板字符串盲区 (MEDIUM):** React 组件中 `"Loading " + variable` 拼接的 UI 文本无法匹配。解决：Phase 1 承认此限制，Phase 2 构建前缀/后缀独立翻译引擎
5. **版本更新破坏翻译 (HIGH):** Claude Code 约每周更新，字符串变更导致翻译失效。解决：版本检测 + mismatch 警告 + Phase 3 智能适配

## Implications for Roadmap

### Phase 1: Foundation & Safety

**Rationale:** 备份污染是当前最严重的问题（v3.0 备份已损坏），必须在任何翻译工作之前解决。路径检测和原子写入是所有后续操作的基础设施。

**Delivers:** 可靠的备份管理、自动路径检测、原子写入基础设施、CLI 子命令框架

**Addresses:** 备份完整性保证、自动路径检测、原子写入、版本检测、JSON 格式输出

**Avoids:** Pitfall 1 (备份污染), Pitfall 7 (硬编码路径), Pitfall 9 (编码损坏), Pitfall 11 (写入崩溃)

**Components:** Path Resolver, Backup Manager, CLI Entry Point (argparse), File I/O utilities

### Phase 2: Core Engine -- Scan & Replace

**Rationale:** 替换引擎是核心价值所在。三级策略需先有 Scanner 提供候选字符串，Replacer 按策略执行，Verifier 保证安全。extract 命令复用 Scanner 能力。

**Delivers:** 安全的字符串替换引擎、extract 命令、status 命令

**Addresses:** 一键汉化 (apply)、一键恢复 (restore)、三级替换安全策略、语法验证、字符串提取 (extract)

**Avoids:** Pitfall 2 (误替换), Pitfall 3 (短字符串地雷), Pitfall 6 (替换顺序), Pitfall 10 (regex 特殊字符), Pitfall 13 (引号风格不一致)

**Components:** String Scanner, Replacement Engine, Verification Engine, Noise Filter, UI Indicator, Translation Map I/O

**Uses:** Python `re` (预编译 pattern + 逆序替换), `subprocess` (node --check), `hashlib` (备份验证)

### Phase 3: Quality & Coverage

**Rationale:** 核心引擎稳定后，增加质量保障和覆盖率提升工具。上下文感知翻译是提升覆盖率到 30%+ 的关键能力。

**Delivers:** coverage 命令、dry-run 预览模式、上下文感知翻译支持、短字符串翻译能力

**Addresses:** 上下文感知翻译、增量覆盖率报告、dry-run 预览模式、短字符串翻译

**Avoids:** Pitfall 8 (验证不足), Pitfall 12 (性能退化), Pitfall 14 (格式锁定), Pitfall 15 (无增量 apply)

**Components:** Coverage Reporter, dry-run 模式, 结构化翻译映射表格式升级

### Phase Ordering Rationale

- **Phase 1 先行:** 备份安全和路径检测是所有操作的前提。没有可靠的备份，apply 和 restore 都不可信。没有路径检测，90% 用户无法使用。
- **Phase 2 核心:** Scanner -> Replacer -> Verifier 构成关键依赖链。extract 复用 Scanner。apply 编排全部三个引擎。
- **Phase 3 增量:** 覆盖率和上下文感知依赖 Phase 2 稳定的替换引擎。短字符串翻译必须在三级策略验证通过后才启用。

### Research Flags

Phases likely needing deeper research during planning:
- **Phase 2 (短字符串策略):** 短字符串翻译的白名单和上下文匹配机制需要仔细设计。当前仅 45 条 SKIP_WORDS，扩展到完整短字符串策略需要实际分析 13MB 文件中的短字符串分布
- **Phase 2 (性能验证):** 6000 条翻译 x 13MB 文件的实际替换耗时需要在真实环境中验证。预算 30 秒，估计 20-26 秒，但无实测数据
- **Phase 3 (上下文感知):** context 标签的设计和 surrounding-code-context 匹配模式需要在积累一定翻译数据后才能确定最佳实践

Phases with standard patterns (skip research-phase):
- **Phase 1:** 全部使用 Python 标准库成熟模块（argparse, hashlib, shutil, pathlib, tempfile），文档完善，模式清晰
- **Phase 2 (验证引擎):** `subprocess.run(["node", "--check", ...])` 是简单直接的模式，无需额外研究

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack | HIGH | 全部基于 Python 标准库，版本兼容性已验证（3.8+），外部依赖为零 |
| Features | HIGH | 功能需求来源于直接的 v3.0 代码分析和用户反馈，竞品分析覆盖完整 |
| Architecture | HIGH | 核心决策（regex vs AST）基于多个 parser benchmark 验证。三级替换策略已在 v3.0 中验证概念可行性 |
| Pitfalls | HIGH | 6 个 Critical/High 级别陷阱全部来自 v3.0 代码的直接分析，预防策略有具体代码示例 |

**Overall confidence:** HIGH

### Gaps to Address

- **实际性能数据缺失:** 6000 条翻译 x 13MB 的替换耗时仅为估算（20-26 秒），需在 Phase 2 实现后用真实 cli.js 验证。如果超 30 秒预算，需引入 Aho-Corasick 多模式匹配
- **短字符串实际分布未知:** 13MB 文件中 <10 字符的 UI 短字符串数量和分布需要在 Phase 2 的 extract 功能完成后才能精确统计
- **模板字符串覆盖率天花板:** React 拼接字符串（`"Loading " + e + " files"`）无法通过单字符串匹配翻译，具体影响多少 UI 文本需要在 Phase 2 extract 后评估
- **CLI 更新频率对翻译的实际影响:** Claude Code 更新约每周一次，但 UI 字符串的实际变更频率需要在 Phase 1 版本检测机制上线后积累数据

## Sources

### Primary (HIGH confidence)
- Python `re`, `hashlib`, `subprocess`, `argparse`, `pathlib` 官方文档 -- 标准库 API 和行为验证
- [localize.py v3.0 源码](file:///Users/zhaolulu/Projects/claude-code-i18n/scripts/localize.py) -- 当前实现，问题识别的直接来源
- [PROJECT.md](file:///Users/zhaolulu/Projects/claude-code-i18n/.planning/PROJECT.md) -- 项目约束和关键决策
- [Claude Code 官方 i18n 需求 Issue #7233](https://github.com/anthropics/claude-code/issues/7233) -- 上游需求确认
- [zcf i18n 模块 (UfoMiao)](https://github.com/UfoMiao/zcf/blob/main/src/i18n/CLAUDE.md) -- 竞品分析

### Secondary (MEDIUM confidence)
- [Acorn vs Babel Parser 对比 (PkgPulse 2026)](https://www.pkgpulse.com/blog/acorn-vs-babel-parser-vs-espree-javascript-ast-parsers-2026) -- AST 性能基准
- [Tree-sitter 大文件性能问题 #1277](https://github.com/tree-sitter/tree-sitter/issues/1277) -- Tree-sitter 大文件限制验证
- [FormatJS Issue #2252: 模板字符串提取问题](https://github.com/formatjs/formatjs/issues/2252) -- 拼接字符串盲区验证
- [Stack Overflow: re.compile 性能评估](https://stackoverflow.com/questions/452104/is-it-worth-using-pythons-re-compile) -- regex 预编译收益
- [Phrase: 10 Common Localization Mistakes](https://phrase.com/blog/posts/10-common-mistakes-in-software-localization/) -- 行业经验参考

### Tertiary (LOW confidence)
- [Stack Overflow: mmap vs read_text 内存效率](https://stackoverflow.com/questions/50976390/memory-and-computation-efficiency-of-finding-strings-in-large-files-with-python) -- 大文件处理策略参考
- [Dasroot: CLI 框架对比](https://dasroot.net/posts/2025/12/building-cli-tools-python-click-typer-argparse/) -- argparse vs Click 决策参考

---
*Research completed: 2026-04-05*
*Ready for roadmap: yes*
