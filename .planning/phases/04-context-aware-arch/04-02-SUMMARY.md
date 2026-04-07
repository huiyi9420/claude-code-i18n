---
phase: 04-context-aware-arch
plan: 02
subsystem: i18n-engine
tags: [context-aware, replacement-engine, tdd, backward-compatible]

# Dependency graph
requires:
  - phase: 04-01
    provides: "v6 translation map format + context_detector module (build_context_index, detect_context)"
provides:
  - "上下文感知替换引擎 (apply_translations with raw_translations + context_index)"
  - "apply 命令集成上下文检测流程"
  - "per-position context resolution: 同一英文在不同区域可有不同翻译"
affects: [04-03, extract, coverage]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "pre-plan replacement: 先在原始 content 上计算所有匹配位置和上下文翻译，再统一逆序替换"
    - "overlap suppression: 长字符串匹配覆盖短字符串重叠匹配"

key-files:
  created: []
  modified:
    - "scripts/i18n/core/replacer.py"
    - "scripts/i18n/commands/apply.py"
    - "tests/unit/test_replacer.py"

key-decisions:
  - "pre-plan 替换架构: 先收集所有匹配位置，过滤重叠，再统一逆序替换，解决跨 tier 偏移问题"
  - "lazy import context_detector.detect_context: 避免循环导入，仅在需要时加载"

patterns-established:
  - "Pre-plan replacement: 收集所有匹配 -> 过滤重叠 -> 逆序替换，避免跨 tier 偏移问题"
  - "Context resolution per-position: 每个 match 独立判断上下文，使用 _resolve_contextual 辅助函数"

requirements-completed: [CTX-02]

# Metrics
duration: 8min
completed: 2026-04-07
---

# Phase 4 Plan 2: 上下文感知替换引擎 Summary

**per-position 上下文感知替换引擎，根据字符串在 cli.js 中的位置选择上下文翻译，无上下文参数时完全兼容 v3.0**

## Performance

- **Duration:** 8 min
- **Started:** 2026-04-07T10:02:51Z
- **Completed:** 2026-04-07T10:10:53Z
- **Tasks:** 1 (TDD: RED -> GREEN -> REFACTOR)
- **Files modified:** 3

## Accomplishments
- apply_translations 支持 raw_translations + context_index 参数，按位置上下文选择翻译
- apply 命令集成 build_context_index，有上下文条目时自动构建上下文索引
- 重构为 pre-plan 替换架构：先在原始 content 上收集所有匹配，过滤重叠，再统一逆序替换
- 新增 8 个上下文感知测试，全部 238 个测试通过，零回归

## Task Commits

Each task was committed atomically:

1. **Task 1 (RED): 添加失败测试** - `98a8ad9` (test)
2. **Task 1 (GREEN+REFACTOR): 实现上下文感知替换引擎** - `ca9d65c` (feat)

## Files Created/Modified
- `scripts/i18n/core/replacer.py` - 新增 _find_all_positions, _resolve_contextual 辅助函数；apply_translations 新增 raw_translations/context_index 参数；pre-plan 替换架构（收集匹配 -> 过滤重叠 -> 逆序替换）
- `scripts/i18n/commands/apply.py` - 集成 build_context_index，传入 raw_translations 和 context_index
- `tests/unit/test_replacer.py` - 新增 TestContextAwareReplacement 类（8 个测试用例）

## Decisions Made
- **Pre-plan 替换架构**: 原始架构按 tier 逐个处理（长 -> 中 -> 短），但长字符串替换会改变后续 tier 的匹配位置偏移。新架构先在原始 content 上统一收集所有匹配位置和对应的翻译，然后过滤重叠（长字符串优先），最后统一逆序替换。这保证了 context_index 的位置始终基于原始 content。
- **Lazy import**: `_resolve_contextual` 中 lazy import `detect_context` 避免循环导入风险，且只在实际需要上下文检测时才执行。

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] 修复跨 tier 位置偏移导致上下文错误替换**
- **Found during:** Task 1 (GREEN 阶段)
- **Issue:** 原始实现按 tier 顺序处理（长 -> 中 -> 短），长字符串替换后 content 偏移变化导致中/短 tier 的匹配位置与原始 context_index 不对应，test_apply_mixed_context_and_plain 失败
- **Fix:** 重构为 pre-plan 替换架构：先在原始 content 上收集所有匹配位置和对应翻译，再统一逆序替换。同时引入重叠过滤机制（APPLY-05 增强），确保长字符串匹配优先覆盖短字符串重叠匹配
- **Files modified:** scripts/i18n/core/replacer.py
- **Verification:** 全部 36 个 replacer 测试通过，包括 test_longest_first 和 test_no_partial_corruption 排序测试
- **Committed in:** ca9d65c (Task 1 commit)

---

**Total deviations:** 1 auto-fixed (1 bug)
**Impact on plan:** 架构改进使替换引擎更健壮，同时修复了原有的 APPLY-05 长字符串优先逻辑的一个潜在边界问题

## Issues Encountered
None

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- 上下文感知替换引擎已完成，可与 Plan 01 的 translation_map v6 + context_detector 协同工作
- Plan 03 可扩展 extract 命令输出组件来源信息（scanner.py 的 signal 评分系统）
- 当前 238 个测试全部通过，覆盖率保持 86%+

---
*Phase: 04-context-aware-arch*
*Completed: 2026-04-07*
