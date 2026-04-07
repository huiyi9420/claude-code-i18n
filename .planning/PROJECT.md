# Claude Code i18n

## What This Is

Claude Code CLI 的中文汉化工具，将终端界面从英文翻译为中文。面向中文用户群体，提供一键汉化/恢复体验。v3.0 完全重写已完成，工具达到可发布质量。

## Core Value

用户运行一条命令，Claude Code CLI 的全部用户可见界面变成准确、自然的中文，版本更新后自动适配。

## Current State

**已发布:** v3.0 (2026-04-07)

- 3 个 Phase，10 个计划，全部完成
- 202 个测试通过，86% 代码覆盖率
- 1,301 条翻译条目，48.0% 翻译覆盖率
- 中字符串 100%，短字符串 92.3%
- GitHub Actions CI（Python 3.10/3.12/3.14）
- 一键安装脚本 (install.sh)

## Requirements

### Validated

- ✓ 一键汉化/恢复工作流 — v3.0 已验证
- ✓ 三级替换策略（长/中/短字符串分级处理）— v3.0 已实现
- ✓ 版本检测 + 自动更新流程 — v3.0 已实现（auto-update 命令）
- ✓ 安全回滚机制 — v3.0 已实现（SHA-256 + node --check + 原子写入）
- ✓ 不可变备份管理 — v3.0 已实现（chmod 444 + CJK 纯净性检查）
- ✓ 覆盖率量化能力 — v3.0 已实现（coverage 子命令）
- ✓ 安装脚本一键部署 — v3.0 已实现（install.sh）
- ✓ CI 自动化测试 — v3.0 已实现（GitHub Actions）

### Active — v3.1

- [ ] 翻译覆盖率 ≥ 80%（用户可见 UI 字符串）— 当前 48.0%
- [ ] 上下文感知翻译（同一英文在不同组件可有不同中文）
- [ ] CI 翻译覆盖率回归检测

### Deferred

- [ ] Aho-Corasick 多模式匹配（翻译条目 >2000 时性能优化）
- [ ] 多语言支持（日/韩）— 架构已预留

### Out of Scope

- 二进制版本兼容 — 用户明确要求最后考虑
- AST 解析引擎 — 13MB minified 文件不适合 AST
- React 组件运行时 patch — 风险过高
- 翻译管理后台/Web UI — 规模不需要

## Context

### 技术环境

- 目标文件：`cli.js`（~13MB，minified）
- CLI 通过 Volta/npm 安装
- CLI 更新频率约每周一次
- 当前翻译条目：1,301（834 初始 + 467 本会话新增）

### 翻译现状

- 长字符串(>20): 826 已翻译
- 中等字符串(10-20): 384 已翻译 (100%)
- 短字符串(<10): 84 已翻译 (92.3%)
- 跳过词: 45
- 未翻译: 1,418（主要是低频内部错误消息）

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| 完全重写而非修补 | 备份污染是架构级 bug，修补无法根治 | ✓ Good — 备份纯净性 100% 保证 |
| Python 作为主引擎 | 现有用户已安装 Python，保持一致性 | ✓ Good — 零外部依赖 |
| 不使用 AST parser | cli.js 是 minified 的超大文件（13MB） | ✓ Good — regex 方案 30 秒内完成 |
| 翻译映射表保持 JSON 格式 | 可读性好，用户可直接编辑 | ✓ Good |
| 三级替换策略 | 长/中/短字符串风险不同 | ✓ Good — 中字符串 100% 覆盖 |
| 规则引擎自动翻译 | 无外部 API 依赖 | ⚠ Revisit — prefix_suffix_match 质量差 |
| 覆盖率独立命令 | 与 pytest 覆盖率区分 | ✓ Good — 表格+JSON 双输出 |

## Current Milestone: v3.1 翻译增强

**Goal:** 将翻译覆盖率从 48% 提升到 80%+，并引入上下文感知翻译能力

**Target features:**
- 大幅扩充翻译条目（1,301 → 2,500+）
- 上下文感知翻译架构（同一英文在不同组件可有不同中文）
- CI 翻译覆盖率回归检测
- 翻译质量验证机制

## Evolution

This document evolves at phase transitions and milestone boundaries.

---
*Last updated: 2026-04-07 after v3.0 milestone*
