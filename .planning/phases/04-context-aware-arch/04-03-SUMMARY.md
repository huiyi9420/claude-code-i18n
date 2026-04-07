---
phase: 04-context-aware-arch
plan: 03
subsystem: infra
tags: [context-aware, scanner, extract, component-source, position-tracking]

# Dependency graph
requires:
  - phase: 04-context-aware-arch/01
    provides: "context_detector.py (build_context_index + detect_context)"
provides:
  - "scan_candidates 输出包含 contexts 字段（组件来源标签）"
  - "extract 命令 JSON 输出包含组件来源信息"
  - "向后兼容：不传 context_index 时 contexts 为空列表"
affects: [05-translation-expansion, extract-output-consumers]

# Tech tracking
tech-stack:
  added: []
patterns: [finditer-position-tracking, context-tag-aggregation]

key-files:
  created: []
  modified:
    - scripts/i18n/core/scanner.py
    - scripts/i18n/commands/extract.py
    - tests/unit/test_scanner.py

key-decisions:
  - "scan_candidates 新增可选 context_index 参数，向后兼容（默认 None -> contexts=[]）"
  - "使用 re.finditer 替代 re.findall 保留位置信息用于上下文检测"
  - "contexts 字段去重排序，不在任何区域时返回 ['default']"

patterns-established:
  - "Optional parameter pattern: 新功能通过可选参数扩展，保持向后兼容"
  - "Position-based context lookup: 从正则匹配位置查询预构建的上下文索引"

requirements-completed: [CTX-03]

# Metrics
duration: 10min
completed: 2026-04-07
---

# Phase 4 Plan 3: extract 命令组件来源标注 Summary

**scan_candidates 和 extract 命令集成上下文检测，输出每个候选字符串的组件来源标签（如 tools、auth、mcp）**

## Performance

- **Duration:** 10 min
- **Started:** 2026-04-07T10:04:38Z
- **Completed:** 2026-04-07T10:14:44Z
- **Tasks:** 1 (TDD: RED + GREEN + REFACTOR)
- **Files modified:** 3

## Accomplishments
- scan_candidates 函数新增 context_index 可选参数，输出 contexts 字段
- extract 命令集成 build_context_index，自动为候选项标注组件来源
- 完整 TDD 流程：5 个新测试用例覆盖上下文检测各种场景
- 230 个单元测试全部通过，零回归

## Task Commits

Each task was committed atomically:

1. **Task 1 (RED): 上下文感知扫描测试** - `59442d7` (test)
2. **Task 1 (GREEN+REFACTOR): scanner + extract 上下文检测实现** - `8cb231f` (feat)

_Note: TDD 任务包含 RED 测试提交和 GREEN+REFACTOR 实现提交_

## Files Created/Modified
- `scripts/i18n/core/scanner.py` - 新增 context_index 参数，使用 finditer 保留位置信息，输出 contexts 字段
- `scripts/i18n/commands/extract.py` - 集成 build_context_index，传入 context_index 到 scan_candidates
- `tests/unit/test_scanner.py` - 新增 TestScanContextDetection 测试类（5 个测试用例）

## Decisions Made
- 使用 `Optional[list] = None` 作为 context_index 参数类型，保持向后兼容
- 将正则匹配改为 `re.finditer` 以获取匹配位置，同时预编译为模块级常量 `_CANDIDATE_RE`
- contexts 为空列表 `[]` 表示未启用上下文检测，`["default"]` 表示无匹配区域
- 同一字符串出现在多个区域时，contexts 收集所有唯一标签并排序

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
None.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- extract 命令现在输出包含组件来源信息的候选字符串
- 下一步可直接利用 contexts 字段指导人工翻译（同一英文在不同组件可有不同中文）
- Plan 04-02 (replacer 上下文感知替换) 与本 plan 共同完成上下文感知架构

---
*Phase: 04-context-aware-arch*
*Completed: 2026-04-07*

## Self-Check: PASSED

- FOUND: scripts/i18n/core/scanner.py
- FOUND: scripts/i18n/commands/extract.py
- FOUND: tests/unit/test_scanner.py
- FOUND: .planning/phases/04-context-aware-arch/04-03-SUMMARY.md
- FOUND: 59442d7 (test commit)
- FOUND: 8cb231f (feat commit)
