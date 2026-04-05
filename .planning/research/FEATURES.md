# Feature Research

**Domain:** CLI i18n -- Post-build localization of minified JavaScript (Claude Code CLI)
**Researched:** 2026-04-05
**Confidence:** HIGH (table stakes & differentiators) / MEDIUM (anti-features boundary)

---

## Feature Landscape

### Table Stakes (Users Expect These)

Features users assume exist. Missing these = product feels incomplete or untrustworthy.

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| **一键汉化 (apply)** | Core value proposition. User runs one command, entire CLI becomes Chinese. | MEDIUM | 三级替换策略（长/中/短），按长度降序，逆序替换。当前 v3.0 已有骨架，需重写核心逻辑增加上下文感知。 |
| **一键恢复 (restore)** | 用户信任底线。必须能无损恢复到纯英文。当前 v3.0 的备份已污染（含 12,224 中文字符），这是本次重写的首要原因。 | LOW | 从纯净备份复制回 cli.js。需增加 SHA-256 校验和验证 + CJK 污染检测。 |
| **备份完整性保证** | restore 可靠性的前提。备份文件不可被后续操作污染。 | MEDIUM | 创建时计算 hash + 只读保护 + 每次使用前验证纯净性。PITFALLS.md Pitfall 1 是此功能的直接驱动。 |
| **语法验证 (node --check)** | 替换后 CLI 必须能启动。一个引号截断就导致完全不可用。 | LOW | subprocess.run() 调用 node --check，失败则从备份回滚。v3.0 已实现，保留。 |
| **自动路径检测** | 不同用户用 Volta/npm/nvm/fnm 安装 Claude Code，硬编码路径意味着 90% 用户无法使用。当前代码硬编码了作者路径。 | MEDIUM | 检查 `which claude`、遍历常见安装路径、支持环境变量覆盖、支持配置文件 `~/.claude/i18n.json`。 |
| **版本检测** | Claude Code 约每周更新一次。用户需要知道翻译是否匹配当前版本。 | LOW | 读取 package.json 的 version 字段，与翻译映射表的 _meta.cli_version 对比。v3.0 已有基础实现。 |
| **JSON 格式输出** | 所有命令结果以 JSON 输出，便于脚本集成和 Claude Code skill 调用。 | LOW | v3.0 已实现，保留并标准化输出格式。 |
| **跨平台支持 (macOS/Linux)** | 用户群体同时使用两个平台。 | LOW | 纯 Python 实现，路径用 pathlib.Path，避免平台特定逻辑。主要差异在路径检测逻辑。 |

### Differentiators (Competitive Advantage)

Features that set this tool apart from generic approaches and competitor tools.

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| **上下文感知翻译** | 同一英文词在不同 UI 位置可有不同中文翻译。例如 "Running" 在状态栏译为"运行中"，在进程管理译为"正在执行"。纯文本替换无法实现这一点。 | HIGH | 翻译映射表增加 context/scope 字段。替换引擎根据上下文标签选择翻译。当前 v3.0 完全不具备此能力。 |
| **三级替换安全策略** | 13MB minified 文件中约 23,651 个大写开头字符串，其中约 74% 是代码逻辑而非 UI 文本。不分级的替换必然破坏代码。 | MEDIUM | 长字符串(>20)精确替换；中等(10-20)引号边界约束；短字符串(<10)词边界+白名单+频率上限。v3.0 已有骨架，重写时需强化短字符串策略。 |
| **字符串提取与评分 (extract)** | 从 6000+ 候选字符串中自动筛选最值得翻译的 UI 文本。使用强信号/弱信号双层评分机制，减少人工筛选工作量。 | MEDIUM | 正则提取 + NOISE_RE 噪声过滤 + STRONG_INDICATORS/WEAK_INDICATORS 评分。v3.0 已实现核心逻辑，需改为从纯净备份提取。 |
| **增量覆盖率报告 (coverage)** | 用户需要知道翻译进度：哪些已翻译、哪些未翻译、哪些被跳过。百分比 + 分类明细。 | MEDIUM | 扫描 cli.js 中所有 UI 候选字符串，与翻译映射表交叉对比，输出已翻译/未翻译/跳过三类统计。当前 v3.0 无此功能。 |
| **版本更新智能适配** | CLI 更新后，自动检测新增/变更/移除的 UI 字符串，增量更新翻译映射表而非全量重建。 | HIGH | 对比新旧版本的提取结果，分类为 new/changed/unchanged/removed。changed 条目标记需人工审核。对 v3.0 的 _meta.cli_version 机制的全面升级。 |
| **dry-run 预览模式** | 替换前展示所有将被修改的位置及其上下文，用户确认后才执行。对短字符串尤其重要。 | MEDIUM | `--dry-run` 参数，输出每条替换的行号、周围上下文、替换前后对比。不写入文件。 |
| **备份纯净性检测** | 启动时自动检测备份文件是否被中文污染（含 CJK 字符），被污染则拒绝 restore 并提示重新下载。 | LOW | 正则扫描 `[\u4e00-\u9fff]`，count > 0 即判定污染。这是解决 PITFALLS.md Pitfall 1 的检测手段。 |
| **原子写入** | 写入操作先写临时文件，验证通过后原子性 rename 到目标路径。崩溃安全。 | LOW | tempfile + os.rename 模式。防止写入中断导致文件损坏。PITFALLS.md Pitfall 11 的解决方案。 |

### Anti-Features (Deliberately NOT Build)

Features that seem appealing but create problems, are out of scope, or contradict core design.

| Anti-Feature | Why Requested | Why Problematic | What to Do Instead |
|--------------|---------------|-----------------|-------------------|
| **AST 解析引擎** | "精确"替换的理想方案。AST 理论上能区分字符串字面量的语义角色。 | 13MB minified 文件上 AST 解析耗时 5-15 秒、内存消耗 65-130MB，且每次替换后需重新解析验证。更关键的是：Acorn/Babel/Tree-sitter 都无法稳定处理如此巨大的单文件。 | 使用增强型 regex + 引号上下文约束。对短字符串增加 surrounding-code-context 匹配。这是 PROJECT.md 明确认定的 Key Decision。 |
| **多语言支持（日文/韩文等）** | 扩大用户群体的自然延伸。架构上看起来只需替换翻译映射表。 | 每种语言需要独立的映射表 + 翻译维护团队。CIG 日韩文字符处理在 regex 中有额外边界问题。当前项目资源不足以维护多语言。 | 架构上预留空间（Translation Map 是独立 JSON 文件），但仅实现中文。PROJECT.md Out of Scope 明确列出。 |
| **二进制版本兼容** | 很多用户通过 Homebrew 或直接下载二进制安装 Claude Code。 | 二进制文件的字符串提取和替换策略完全不同（需要 ELF/Mach-O 解析），复杂度是 CLI 版本的 3-5 倍。 | PROJECT.md Out of Scope：用户明确要求先确保 CLI 版本质量，二进制兼容最后考虑。 |
| **翻译管理后台/Web UI** | 可视化管理翻译映射表、审核状态、多人协作。 | 项目规模不需要。翻译映射表约 1000-2000 条，JSON 文件可直接编辑。Web UI 的开发和维护成本远超收益。 | JSON 文件 + 用户直接编辑。提供 extract 命令辅助发现新字符串。 |
| **React 运行时 Patch** | 直接修改 React 组件的渲染逻辑，在运行时拦截并翻译字符串。 | 需要注入代码到 Claude Code 进程，风险极高。可能触发安全检测，破坏 React 虚拟 DOM 对比机制，导致不可预测的 UI 行为。 | 构建后静态替换，不修改任何运行时逻辑。 |
| **自动推送版本更新通知** | 用户知道何时有新版本可用。 | 超出工具职责范围。Claude Code 自身有更新机制。i18n 工具只需在新版本上正确工作。 | 版本检测 + mismatch 警告，不主动推送通知。 |
| **AI 自动翻译** | 提取新字符串后自动调用 LLM 翻译，减少人工工作量。 | 翻译质量难以控制。CLI UI 文本需要精确、简洁、一致的术语。AI 翻译的"过度创意"会导致 UI 不统一。 | 由维护者人工审核翻译。extract 命令输出候选列表，人工添加到 zh-CN.json。 |
| **sed/awk 级别的简单替换** | 最快的实现方式，Unix 工具链标准。 | sed 不理解引号边界，会替换引号外的代码逻辑。已证明导致 CLI 崩溃（v3.0 早期版本的 Hook UI 替换问题）。 | Python 引擎 + 引号边界 regex + node --check 验证。 |

---

## Feature Dependencies

```
[一键恢复 (restore)]
    └──requires──> [备份完整性保证]
                       └──requires──> [备份纯净性检测]
                       └──requires──> [原子写入]

[一键汉化 (apply)]
    └──requires──> [自动路径检测]
    └──requires──> [备份完整性保证]
    └──requires──> [三级替换安全策略]
    └──requires──> [语法验证 (node --check)]
    └──requires──> [原子写入]

[三级替换安全策略]
    └──requires──> [翻译映射表格式（含上下文标签）]

[上下文感知翻译]
    └──requires──> [三级替换安全策略]
    └──requires──> [翻译映射表格式（含 context/scope 字段）]

[字符串提取与评分 (extract)]
    └──requires──> [备份完整性保证]（必须从纯净源提取）
    └──requires──> [自动路径检测]

[增量覆盖率报告 (coverage)]
    └──requires──> [字符串提取与评分]
    └──requires──> [翻译映射表加载]

[版本更新智能适配]
    └──requires──> [版本检测]
    └──requires──> [字符串提取与评分]
    └──requires──> [增量覆盖率报告]

[dry-run 预览模式]
    └──requires──> [三级替换安全策略]
    └──enhances──> [一键汉化 (apply)]

[上下文感知翻译] ──conflicts──> [简单键值对映射格式]
```

### Dependency Notes

- **apply requires 备份完整性保证:** apply 的第一步是从备份恢复干净状态。如果备份被污染，apply 的结果不可预测。
- **extract requires 备份完整性保证:** extract 必须从纯净英文源提取。从已汉化的 cli.js 提取会导致把中文当作"新字符串"（v3.0 的已知 bug）。
- **上下文感知翻译 requires 翻译映射表格式变更:** 当前 zh-CN.json 是简单键值对 `{"en": "zh"}`，需要升级为带 context/scope 字段的结构化格式。这是破坏性变更，影响所有现有翻译条目。
- **dry-run enhances apply:** dry-run 是 apply 的 `--dry-run` 参数变体，共享替换逻辑但不写入文件。
- **上下文感知翻译 conflicts 简单键值对:** 格式不兼容，必须选择一种。建议新格式向后兼容（简单条目可省略 context 字段，默认全局匹配）。

---

## MVP Definition

### Launch With (v1 -- Phase 1+2)

Minimum viable product -- what's needed to deliver the core value "一键汉化，可靠恢复"。

- [ ] **一键汉化 (apply)** -- 核心价值，用户运行一条命令即可汉化
- [ ] **一键恢复 (restore)** -- 信任基础，必须可靠恢复纯英文
- [ ] **备份完整性保证** -- restore 可靠性的技术前提（hash + 纯净性检测 + 只读）
- [ ] **自动路径检测** -- 所有用户能开箱即用
- [ ] **三级替换安全策略** -- 长字符串精确替换 + 中等字符串引号边界 + 短字符串保守策略
- [ ] **语法验证 (node --check)** -- 最基本的安全门
- [ ] **原子写入** -- 防止写入中断导致文件损坏
- [ ] **版本检测** -- 用户知道翻译是否匹配当前版本
- [ ] **JSON 格式输出** -- 所有命令输出 JSON
- [ ] **字符串提取 (extract)** -- 从纯净源提取可翻译字符串候选

### Add After Validation (v1.x -- Phase 2)

Features to add once core engine is stable and coverage is increasing.

- [ ] **上下文感知翻译** -- 翻译映射表增加 context/scope 字段，替换引擎支持上下文选择。触发条件：覆盖率从当前 1.4% 提升到 30%+ 时，短字符串和中等字符串的误替换问题变得突出。
- [ ] **增量覆盖率报告 (coverage)** -- 可视化翻译进度。触发条件：用户开始贡献翻译后需要了解覆盖情况。
- [ ] **dry-run 预览模式** -- 替换前预览。触发条件：短字符串翻译开始后，需要逐条审核。
- [ ] **短字符串翻译** -- 当前 MVP 仅处理长/中等字符串，短字符串默认跳过。触发条件：长/中等字符串覆盖率达到 80%+。

### Future Consideration (v2+ -- Phase 3)

Features to defer until product-market fit is established.

- [ ] **版本更新智能适配** -- 自动 diff 新旧版本提取结果。延后原因：需要稳定的 extract + coverage 基础，且需要积累足够多的翻译条目才能体现价值。
- [ ] **多模式验证** -- node --check 之外的语义级验证（如运行 claude --version 测试）。延后原因：需要 CI 环境支持。
- [ ] **CI 集成** -- 自动化回归检测。延后原因：先确保单用户场景稳定。
- [ ] **Aho-Corasick 多模式匹配优化** -- 翻译条目从 834 增长到 6000+ 时的性能优化。延后原因：当前 834 条替换在 30 秒预算内可完成，性能暂时不是瓶颈。

---

## Feature Prioritization Matrix

| Feature | User Value | Implementation Cost | Priority |
|---------|------------|---------------------|----------|
| 一键汉化 (apply) | HIGH | MEDIUM | P1 |
| 一键恢复 (restore) | HIGH | LOW | P1 |
| 备份完整性保证 | HIGH | MEDIUM | P1 |
| 自动路径检测 | HIGH | MEDIUM | P1 |
| 三级替换安全策略 | HIGH | MEDIUM | P1 |
| 语法验证 | HIGH | LOW | P1 |
| 原子写入 | HIGH | LOW | P1 |
| 版本检测 | MEDIUM | LOW | P1 |
| JSON 格式输出 | MEDIUM | LOW | P1 |
| 字符串提取 (extract) | MEDIUM | MEDIUM | P1 |
| 上下文感知翻译 | HIGH | HIGH | P2 |
| 增量覆盖率报告 | MEDIUM | MEDIUM | P2 |
| dry-run 预览模式 | MEDIUM | MEDIUM | P2 |
| 短字符串翻译 | HIGH | HIGH | P2 |
| 版本更新智能适配 | HIGH | HIGH | P3 |
| 多模式验证 | MEDIUM | HIGH | P3 |
| CI 集成 | MEDIUM | HIGH | P3 |
| Aho-Corasick 优化 | LOW | MEDIUM | P3 |

**Priority key:**
- P1: Must have for launch -- 核心价值交付
- P2: Should have, add when coverage expands -- 质量提升
- P3: Nice to have, future consideration -- 规模化准备

---

## Competitor Feature Analysis

| Feature | claude-init (cfrs2005) | zcf (UfoMiao) | claude-code-tool-manager | Our Approach |
|---------|------------------------|---------------|--------------------------|--------------|
| **定位** | 项目初始化套件，非汉化工具 | Claude Code 环境配置工具，含 i18n 模块 | Claude Code 工具管理器，含 i18n 扩展 | 专注 CLI 界面汉化的底层引擎 |
| **汉化方式** | 配置文件模板（.claude/ 目录），不改 cli.js | 构建时 i18n（TypeScript 源码级翻译键） | React 组件级 i18n（690 翻译键） | 构建后静态替换 minified cli.js |
| **翻译目标** | CLAUDE.md、规则文件、技能描述 | CLI 工具自身的界面文本 | 工具管理器 UI | Claude Code 核心终端 UI |
| **备份/恢复** | 无（不改源文件） | 不需要（源码级修改） | 不需要（组件级修改） | 必须（直接修改 13MB 生产文件） |
| **版本适配** | 手动更新模板 | 随版本发布更新 | 随版本发布更新 | 自动检测 + 智能适配 |
| **安全验证** | 无需（配置文件无执行风险） | TypeScript 编译检查 | React 运行时检查 | node --check + 原子写入 + hash 校验 |
| **覆盖范围** | CLAUDE.md + 规则文件 | 15 功能模块，100% 翻译覆盖 | 690 翻译键 | 目标 90% UI 字符串覆盖 |

### 竞争定位分析

本工具的独特性在于：**不修改源代码，而是在构建后直接操作 minified JavaScript 文件**。这不是传统的 i18n 方案（在源码中插入翻译键），而是对已发布产品的"补丁式"本地化。

所有竞品要么是项目初始化工具（不改 cli.js），要么是在源码级别实现 i18n（需要上游配合）。本工具填补了一个独特空白：**在上游（Anthropic）不支持 i18n 的前提下，通过安全的字符串替换实现 CLI 界面本地化**。

这也决定了本工具最大的挑战：**安全性和可维护性**。每次 CLI 更新都需要验证翻译的兼容性，这是其他工具不需要面对的问题。

---

## Sources

- [Claude Code 官方 i18n 需求 Issue #7233](https://github.com/anthropics/claude-code/issues/7233) -- HIGH confidence, Anthropic 官方仓库
- [Claude Code 中文本地化需求 Issue #22356](https://github.com/anthropics/claude-code/issues/22356) -- HIGH confidence
- [Claude Code UI 消息本地化需求 Issue #18362](https://github.com/anthropics/claude-code/issues/18362) -- HIGH confidence
- [zcf i18n 模块 (UfoMiao)](https://github.com/UfoMiao/zcf/blob/main/src/i18n/CLAUDE.md) -- HIGH confidence, 直接读取源码
- [claude-init (cfrs2005)](https://github.com/cfrs2005/claude-init) -- HIGH confidence, 直接读取 README
- [claude-code-tool-manager i18n PR #167](https://github.com/tylergraydev/claude-code-tool-manager/pull/167) -- MEDIUM confidence, PR 内容
- [i18next-cli](https://www.locize.com/blog/i18next-cli) -- MEDIUM confidence, 传统 i18n CLI 工具参考
- [FormatJS Issue #2252: 模板字符串提取问题](https://github.com/formatjs/formatjs/issues/2252) -- HIGH confidence, 验证了模板字符串盲区
- [Phrase: 10 Common Localization Mistakes](https://phrase.com/blog/posts/10-common-mistakes-in-software-localization/) -- MEDIUM confidence, 行业经验参考
- [PROJECT.md](file:///Users/zhaolulu/Projects/claude-code-i18n/.planning/PROJECT.md) -- HIGH confidence, 项目约束和决策
- [localize.py v3.0 源码](file:///Users/zhaolulu/Projects/claude-code-i18n/scripts/localize.py) -- HIGH confidence, 当前实现参考
- [ARCHITECTURE.md](file:///Users/zhaolulu/Projects/claude-code-i18n/.planning/research/ARCHITECTURE.md) -- HIGH confidence, 架构决策
- [PITFALLS.md](file:///Users/zhaolulu/Projects/claude-code-i18n/.planning/research/PITFALLS.md) -- HIGH confidence, 风险评估

---
*Feature research for: CLI i18n tool for minified JavaScript (Claude Code)*
*Researched: 2026-04-05*
