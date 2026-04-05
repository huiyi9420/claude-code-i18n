# Claude Code i18n — 完全重写

## What This Is

Claude Code CLI 的中文汉化工具，将终端界面从英文翻译为中文。面向中文用户群体，提供一键汉化/恢复体验。当前版本存在严重的架构问题（备份污染、低覆盖率、无上下文感知），需要完全重写核心引擎以从根本上解决质量问题。

## Core Value

用户运行一条命令，Claude Code CLI 的全部用户可见界面变成准确、自然的中文，版本更新后自动适配。

## Requirements

### Validated

- ✓ 一键汉化/恢复工作流 — 现有 v3.0 已验证用户需要这种体验
- ✓ 三级替换策略（长/中/短字符串分级处理）— 概念正确但实现需改进
- ✓ 版本检测 + 自动更新流程 — 用户依赖此功能
- ✓ 安全回滚机制 — 用户信任此保障

### Active

- [ ] 基于 AST 的精确定位引擎，替换纯文本匹配
- [ ] 翻译覆盖率 ≥ 90%（用户可见 UI 字符串）
- [ ] 上下文感知翻译（同一英文在不同组件可有不同中文）
- [ ] 备份完整性保证（英文备份零中文污染）
- [ ] 完全可配置路径（无硬编码，支持 Volta/npm/其他安装方式）
- [ ] 跨平台支持（macOS/Linux）
- [ ] 单元测试覆盖率 ≥ 80%
- [ ] 增量式覆盖率报告（显示已翻译/未翻译/跳过占比）
- [ ] 翻译映射表支持上下文标签
- [ ] CI 集成（自动化回归检测）
- [ ] Hook UI 消息的精确替换（替代 sed 裸替换）
- [ ] extract 命令从纯净英文源提取，正确过滤已翻译条目

### Out of Scope

- 二进制版本兼容 — 用户明确要求最后考虑，当前仅支持 CLI（Volta/npm）版本
- 其他语言支持（日文/韩文等）— 当前仅中文
- 翻译管理后台/Web UI — 规模不需要
- 自动检测 claude code 版本更新并推送通知 — 超出工具范围
- React 组件运行时 patch（修改渲染逻辑）— 风险过高

## Context

### 现有架构问题

1. **备份污染（严重）**：`cli.bak.en.js` 包含 12,224 个中文字符，restore 无法恢复纯英文
2. **覆盖率低**：834 条翻译仅覆盖约 1.4% 的 UI 文本出现次数（实际体验覆盖更高，因为高频字符串已翻译）
3. **无上下文感知**：纯文本替换，同一英文词在不同位置可能需要不同翻译
4. **extract bug**：从被污染的备份提取，会把已翻译的中文当作"新字符串"
5. **sed 裸替换**：Hook UI 消息替换（步骤 6）容易误伤非目标文本
6. **硬编码路径**：`CLI_DIR` 写死为 `/Users/zhaolulu/.volta/...`

### 技术环境

- 目标文件：`cli.js`（~13MB，16,938 行，minified）
- 包含约 23,651 个大写开头双引号字符串
- 其中约 6,062 个是 UI 文本候选（含 5,998 个未翻译）
- CLI 通过 Volta 安装，路径结构固定
- CLI 更新频率约每周一次，每次可能新增/修改 UI 文本

### 翻译现状

- 长字符串(>20字符): 603 条已翻译
- 中等字符串(10-20): 131 条已翻译
- 短字符串(<10): 100 条已翻译（风险最高）
- 跳过词: 45 条

## Constraints

- **Tech Stack**: Python 3.6+（主引擎），Node.js（语法验证），shell（安装脚本）
- **Compatibility**: 必须兼容 macOS 和 Linux
- **Safety**: 每次替换后必须 `node --check` 验证，失败自动回滚
- **Performance**: 汉化整个 cli.js（13MB）应在 30 秒内完成
- **Reversibility**: restore 必须恢复到 100% 纯英文，零残留
- **Non-destructive**: 不可修改代码逻辑，只替换用户可见的显示文本

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| 完全重写而非修补 | 备份污染是架构级 bug，修补无法根治 | — Pending |
| Python 作为主引擎 | 现有用户已安装 Python，保持一致性 | — Pending |
| 不使用 AST parser（如 acorn/babel） | cli.js 是 minified 的超大文件（13MB），AST 解析耗时长且不稳定 | — Pending |
| 翻译映射表保持 JSON 格式 | 可读性好，用户可直接编辑 | — Pending |
| 二进制版本兼容延后 | 用户明确要求先确保 CLI 版本质量 | — Pending |

## Evolution

This document evolves at phase transitions and milestone boundaries.

**After each phase transition** (via `/gsd:transition`):
1. Requirements invalidated? → Move to Out of Scope with reason
2. Requirements validated? → Move to Validated with phase reference
3. New requirements emerged? → Add to Active
4. Decisions to log? → Add to Key Decisions
5. "What This Is" still accurate? → Update if drifted

**After each milestone** (via `/gsd:complete-milestone`):
1. Full review of all sections
2. Core Value check — still the right priority?
3. Audit Out of Scope — reasons still valid?
4. Update Context with current state

---
*Last updated: 2026-04-05 after initialization*
