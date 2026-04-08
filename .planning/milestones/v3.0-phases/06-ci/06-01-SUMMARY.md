---
phase: 06-ci
plan: 01
subsystem: ci
tags: [github-actions, coverage-regression, translation-baseline]

requires:
  - phase: 05-quality
    provides: "翻译映射表 zh-CN.json (2,657 条目)"

provides:
  - "CI 覆盖率回归检测脚本 (ci_check_coverage.py)"
  - "翻译覆盖率基线文件 (coverage-baseline.json)"
  - "GitHub Actions coverage-regression job"

affects: [ci, translation-workflow]

tech-stack:
  added: []
  patterns: [baseline-comparison-ci, pure-file-io-coverage-check]

key-files:
  created:
    - scripts/ci_check_coverage.py
    - tests/unit/test_ci_check_coverage.py
    - .planning/coverage-baseline.json
  modified:
    - .github/workflows/ci.yml

key-decisions:
  - "CI 覆盖率检查使用独立脚本，不依赖 cli.js，仅统计翻译条目数量"
  - "基线不存在时 ok=true（首次运行场景）"
  - "coverage-regression job 与 test job 并行运行，使用单一 Python 3.12"

patterns-established:
  - "Baseline-comparison: 存储翻译条目数量基线到 JSON 文件，CI 时对比当前值"
  - "Pure-file-io coverage: 覆盖率检查不依赖 Node.js 或 cli.js 扫描"

requirements-completed: [COV-04]

duration: 6min
completed: 2026-04-08
---

# Phase 6 Plan 1: CI 覆盖率回归检测 Summary

**独立 CI 覆盖率回归脚本 + GitHub Actions job，翻译条目数低于基线时自动失败**

## Performance

- **Duration:** 6 分钟
- **Started:** 2026-04-08T02:04:54Z
- **Completed:** 2026-04-08T02:11:12Z
- **Tasks:** 2
- **Files modified:** 4

## Accomplishments
- CI 覆盖率检查脚本：读取 zh-CN.json 统计翻译条目并按长度分类，与基线对比
- 17 个单元测试覆盖所有核心函数（count_translations / load_baseline / compare_coverage / main）
- GitHub Actions coverage-regression job：PR/push 时自动运行，覆盖率下降则 CI 失败
- 覆盖率基线文件：2,657 条目（1,260L/1,120M/277S）

## Task Commits

每个任务独立提交：

1. **Task 1 (RED): CI 覆盖率检查测试** - `0cb666e` (test)
2. **Task 1 (GREEN): CI 覆盖率检查脚本 + 基线** - `55fe7ca` (feat)
3. **Task 2: CI workflow 新增覆盖率回归检测 job** - `516068e` (feat)

## Files Created/Modified
- `scripts/ci_check_coverage.py` - 独立覆盖率检查脚本（count_translations / load_baseline / compare_coverage / main）
- `tests/unit/test_ci_check_coverage.py` - 17 个单元测试
- `.planning/coverage-baseline.json` - 覆盖率基线（2,657 entries）
- `.github/workflows/ci.yml` - 新增 coverage-regression job

## Decisions Made
- CI 覆盖率检查使用独立 Python 脚本，不依赖 cli.js 或 Node.js（纯文件读取 + JSON 解析）
- 基线文件不存在时视为首次运行，ok=true 不阻塞（避免新仓库初始化问题）
- coverage-regression job 使用单一 Python 3.12，无需矩阵（纯 I/O 操作无版本兼容风险）

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

- .planning/ 目录在 .gitignore 中，需使用 `git add -f` 强制添加 coverage-baseline.json

## Next Phase Readiness
- Phase 06（CI 覆盖率回归检测）已完成
- 所有计划均已执行完毕，v3.1 milestone 的 CI 相关需求 COV-04 已满足

## Self-Check: PASSED

- All 5 files verified present: scripts/ci_check_coverage.py, tests/unit/test_ci_check_coverage.py, .planning/coverage-baseline.json, .github/workflows/ci.yml, 06-01-SUMMARY.md
- All 3 commits verified in git log: 0cb666e, 55fe7ca, 516068e

---
*Phase: 06-ci*
*Completed: 2026-04-08*
