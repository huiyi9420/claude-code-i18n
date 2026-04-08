# Phase 6: CI 覆盖率回归检测 - Context

**Gathered:** 2026-04-08
**Status:** Ready for planning
**Mode:** Claude's Discretion

<domain>
## Phase Boundary

在 GitHub Actions CI 流水线中新增翻译覆盖率检查步骤。PR 提交时自动比较覆盖率与主分支基线，覆盖率下降则 CI 失败。具体包括：
1. CI 新增覆盖率检查步骤（运行 coverage 命令获取当前覆盖率）
2. PR 提交时比较覆盖率与 main 分支基线
3. 覆盖率低于基线则 CI 失败并输出对比报告
4. 覆盖率检查 60 秒内完成

</domain>

<decisions>
## Implementation Decisions

### Claude's Discretion
所有实现选择由 Claude 自行决定 — 用户明确表示"你决定即可"。使用 ROADMAP 阶段目标、成功标准和代码库约定来指导决策。

### CI 策略（Claude 决定）
- 在现有 ci.yml 中新增 coverage job 或 step
- 利用现有 coverage 命令的 JSON 输出解析覆盖率
- 基线存储：将 main 分支的覆盖率写入文件（如 `.planning/coverage-baseline.json`），PR 时对比
- 覆盖率下降时 CI 失败，输出清晰的对比报告

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### 项目上下文
- `.planning/PROJECT.md` — 项目愿景、约束
- `.planning/REQUIREMENTS.md` — v3.1 需求（COV-04）
- `.planning/ROADMAP.md` — Phase 6 目标和成功标准

### 核心代码（必须理解）
- `.github/workflows/ci.yml` — 现有 CI 配置（Python 3.10/3.12/3.14 矩阵）
- `scripts/i18n/commands/coverage.py` — 覆盖率命令（JSON 输出包含 percentage 和 categories）
- `scripts/i18n/cli.py` — CLI 子命令注册

### 测试
- `tests/unit/` — 现有单元测试

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `coverage.py` — 已有 JSON 输出（`output_json()` 格式），包含 `percentage`、`translated`、`untranslated`、`categories` 字段
- `ci.yml` — 已有完整 CI 流水线（Python 矩阵测试 + install.sh 检查）
- `cli.py` — 子命令注册模式（argparse add_parser）

### Established Patterns
- CI：GitHub Actions，Python 矩阵测试
- 命令输出：`output_json()` 统一 JSON 格式
- 零外部依赖约束（纯 Python 标准库）

### Integration Points
- `ci.yml` 需要新增 coverage 检查步骤
- coverage 命令需要 cli.js 文件才能运行（CI 环境需要模拟或跳过）
- 基线文件需要被 git 追踪

### CI 环境约束
- CI 没有 cli.js 文件 — coverage 命令需要备份文件才能扫描候选
- 解决方案：CI 中仅检查翻译条目数量变化（不依赖 cli.js 扫描）
- 或者：将覆盖率基线存储在仓库中，CI 时比较条目数量

</code_context>

<specifics>
## Specific Ideas

No specific requirements — infrastructure phase. Refer to ROADMAP phase description and success criteria.

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

---
*Phase: 06-ci*
*Context gathered: 2026-04-08*
