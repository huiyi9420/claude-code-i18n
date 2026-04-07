---
phase: 04-context-aware-arch
plan: 01
subsystem: infra
tags: [context-aware, translation-map, v6-format, pattern-matching, regex]

# Dependency graph
requires:
  - phase: 01-core-engine
    provides: "translation_map.py 加载/保存基础设施"
provides:
  - "v6 格式翻译映射表加载/保存（带 contexts 的翻译条目）"
  - "resolve_translation 函数按上下文优先级选择翻译"
  - "context_detector.py 模块（build_context_index + detect_context）"
  - "10 种上下文标签的 cli.js 功能区块识别"
affects: [04-02-PLAN, 04-03-PLAN, replacer.py, scanner.py, extract.py]

# Tech tracking
tech-stack:
  added: []
  patterns: [context-tag-priority, sliding-window-region, region-merge]

key-files:
  created:
    - scripts/i18n/core/context_detector.py
    - tests/unit/test_context_detector.py
  modified:
    - scripts/i18n/io/translation_map.py
    - tests/unit/test_translation_map.py

key-decisions:
  - "load_translation_map 返回三层结构：meta + translations(展平) + raw_translations(完整)"
  - "resolve_translation 按 context_tags 列表顺序匹配，先匹配先返回"
  - "billing 模式不包含 token（与 auth 歧义），billing 仅匹配 cost|usage|billing"
  - "build_context_index 一次构建 + detect_context 多次查询的设计适合 13MB 文件场景"
  - "滑动窗口 512 字符扩展 + 2048 字符合并阈值的区块识别策略"

patterns-established:
  - "v6 翻译条目格式: {zh: str, contexts: {tag: str}}"
  - "上下文检测两阶段: build_context_index(content) -> detect_context(index, position)"
  - "raw_translations 保留完整结构，translations 展平为 {en: zh} 兼容旧代码"

requirements-completed: [CTX-01]

# Metrics
duration: 8min
completed: 2026-04-07
---

# Phase 04 Plan 01: 翻译映射表 v6 格式 + 上下文检测模块 Summary

**v6 格式翻译映射表支持同一英文多翻译（带 contexts），上下文检测模块通过正则模式匹配识别 cli.js 中 10 种功能区块**

## Performance

- **Duration:** 8 min
- **Started:** 2026-04-07T09:48:42Z
- **Completed:** 2026-04-07T09:56:49Z
- **Tasks:** 2
- **Files modified:** 4

## Accomplishments
- 翻译映射表 v6 格式：同一英文字符串可定义多个上下文翻译，v4/v5 完全向后兼容
- resolve_translation 函数：按上下文标签优先级选择最精确翻译
- 上下文检测模块：基于 10 种正则模式识别 cli.js 功能区块（tools/auth/mcp/status/config/permission/agent/git/mode/billing）
- 测试从 214 增加到 225（+11 新测试），全部通过

## Task Commits

Each task was committed atomically (TDD: RED + GREEN):

1. **Task 1 RED: v6 格式测试** - `c4ebef5` (test)
2. **Task 1 GREEN: v6 格式实现** - `91d5393` (feat)
3. **Task 2 RED: 上下文检测测试** - `5242d7f` (test)
4. **Task 2 GREEN: 上下文检测实现** - `509ee41` (feat)

## Files Created/Modified
- `scripts/i18n/io/translation_map.py` - 新增 raw_translations 返回、resolve_translation 函数，v6 格式保存
- `scripts/i18n/core/context_detector.py` - 上下文检测模块（build_context_index + detect_context）
- `tests/unit/test_translation_map.py` - 新增 12 个 v6 格式测试
- `tests/unit/test_context_detector.py` - 新增 11 个上下文检测测试

## Decisions Made
- load_translation_map 返回三层结构：translations（展平兼容）+ raw_translations（完整 v6）+ meta，避免破坏现有调用方
- resolve_translation 采用线性扫描 context_tags 列表（先匹配先返回），简单可靠，条目数不大无需优化
- billing 模式不包含 token 关键词，避免与 auth 模式产生歧义（token 在 auth 上下文中更常见）
- 上下文检测采用 build-once-query-many 模式，因 cli.js 13MB 不可每次替换重新扫描
- 滑动窗口 512 字符（每个方向）+ 2048 字符合并阈值，平衡精确性和区块连续性

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
None.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- v6 格式基础设施就绪，Plan 02 可基于此实现替换引擎的上下文感知翻译选择
- context_detector 模块就绪，Plan 02/03 可在 replacer 和 extract 流程中集成
- 所有现有测试（225 个）通过，无回归

## Self-Check: PASSED

- All 4 created/modified files verified present
- All 4 task commits verified in git history (c4ebef5, 91d5393, 5242d7f, 509ee41)
- 225 tests pass, 0 regressions

---
*Phase: 04-context-aware-arch*
*Completed: 2026-04-07*
