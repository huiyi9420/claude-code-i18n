---
phase: 03-integration-quality
plan: 01
subsystem: testing
tags: [coverage, i18n, cli, argparse, scanner, translation-map]

# Dependency graph
requires:
  - phase: 02-core-engine
    provides: "scanner.py, translation_map.py, backup.py, noise_filter.py"
  - phase: 01-foundation
    provides: "cli.py argparse framework, path detection, constants"
provides:
  - "coverage 子命令 (cmd_coverage)"
  - "format_coverage_table 终端友好纯文本表格"
  - "按字符串长度分组的覆盖率统计 (long/medium/short)"
  - "5 个单元测试覆盖主要场景"
affects: [03-02, 03-03]

# Tech tracking
tech-stack:
  added: []
  patterns: ["命令模式: get_cli_dir + get_data_dir + BackupManager + scan_candidates + output_json"]

key-files:
  created:
    - scripts/i18n/commands/coverage.py
    - tests/unit/test_coverage_cmd.py
  modified:
    - scripts/i18n/cli.py

key-decisions:
  - "表格先输出到 stdout，JSON 后输出 -- 测试通过 rfind 定位 JSON 起始"
  - "字符串长度分类阈值: long(>20), medium(10-20), short(<10)"

patterns-established:
  - "覆盖率命令模式: 加载映射表 + 加载 skip words + 备份扫描 + 分类统计 + 表格+JSON 输出"

requirements-completed: [COV-01, COV-02]

# Metrics
duration: 12min
completed: 2026-04-07
---

# Phase 03 Plan 01: Coverage 命令 Summary

**新增 coverage 子命令，输出终端友好的翻译覆盖率表格，按字符串长度分类显示已翻译/未翻译/跳过的条目数和百分比**

## Performance

- **Duration:** 12 min
- **Started:** 2026-04-07T06:39:48Z
- **Completed:** 2026-04-07T06:51:21Z
- **Tasks:** 1
- **Files modified:** 3

## Accomplishments
- coverage 子命令可通过 `python3 scripts/engine.py coverage` 调用
- 输出包含长/中/短字符串分类的覆盖率表格（纯文本，零外部依赖）
- 输出结构化 JSON 包含 ok, translated, untranslated, skipped, total, percentage, categories 字段
- 198 个测试全部通过（新增 5 个，无退化）

## Task Commits

Each task was committed atomically:

1. **Task 1: 实现 coverage 子命令** - `5c5e289` (feat)

_Note: TDD task -- tests and implementation committed together as all tests passed_

## Files Created/Modified
- `scripts/i18n/commands/coverage.py` - coverage 命令实现：覆盖率计算、分类统计、表格格式化
- `tests/unit/test_coverage_cmd.py` - 5 个单元测试覆盖主要场景
- `scripts/i18n/cli.py` - 注册 coverage 子命令到 build_parser 和 main commands dict

## Decisions Made
- 表格输出在前，JSON 输出在后 -- 用户先看到可视化表格，测试通过 rfind `{\n  "ok"` 定位 JSON
- 字符串长度分类使用英文字符长度：long(>20), medium(10-20), short(<10)，与现有三级替换策略一致
- 无 map 文件时 BackupManager 从 cli.js 创建备份 -- 即使内容简单也会成功，保证 graceful degradation

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
None.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- coverage 命令可用于量化翻译覆盖率，为 03-02（补充翻译条目）提供数据基础
- 198 个测试全部通过，测试覆盖率维持高水平
- 表格格式可通过 format_coverage_table 函数独立测试和扩展

## Self-Check: PASSED

- FOUND: scripts/i18n/commands/coverage.py
- FOUND: tests/unit/test_coverage_cmd.py
- FOUND: .planning/phases/03-integration-quality/03-01-SUMMARY.md
- FOUND: 5c5e289 (task commit)

---
*Phase: 03-integration-quality*
*Completed: 2026-04-07*
