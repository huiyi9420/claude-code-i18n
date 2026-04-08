---
phase: 05-translation-expansion
plan: 01
subsystem: i18n-quality
tags: [validation, regex, translation-quality, cli-command]

# Dependency graph
requires:
  - phase: 04-context-aware-arch
    provides: load_translation_map (v4/v5/v6 format support)
provides:
  - validate 命令 — 翻译质量自动检测工具
  - check_chinese_english_mixing — 中英混杂检测函数
  - check_synonym_inconsistency — 同义不一致检测函数
  - check_placeholder_missing — 格式占位符丢失检测函数
  - validate_translations — 完整验证报告生成
affects: [05-02, 05-03, CI-pipeline]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "质量检测采用独立命令模式，不在 apply 时实时检测"
    - "白名单机制过滤技术术语避免误报"

key-files:
  created:
    - scripts/i18n/commands/validate.py
    - tests/unit/test_validate.py
  modified:
    - scripts/i18n/cli.py

key-decisions:
  - "白名单包含 30+ 常见技术缩写（API/CLI/MCP/SSH/Git 等），避免中英混杂误报"
  - "同义不一致检测使用标准化（小写+去标点）作为 canonical key"
  - "占位符检测覆盖 printf(%s)、template(${var})、brace({0}/{name}) 三种风格"
  - "validate 不依赖 CLI 安装目录，仅读取翻译映射表"

patterns-established:
  - "质量检测命令模式: 独立命令 + JSON 报告输出 + 可被 CI 集成"
  - "白名单模式: 维护技术术语白名单避免检测误报"

requirements-completed: [CTX-04]

# Metrics
duration: 5min
completed: 2026-04-07
---

# Phase 05 Plan 01: 翻译质量验证命令 Summary

**validate 命令实现三类翻译质量检测：中英混杂、同义不一致、格式占位符丢失，输出 JSON 报告**

## Performance

- **Duration:** 5 min
- **Started:** 2026-04-07T10:55:30Z
- **Completed:** 2026-04-07T11:00:39Z
- **Tasks:** 1 (TDD: RED + GREEN)
- **Files modified:** 3

## Accomplishments
- validate 命令可检测三类翻译质量问题，输出结构化 JSON 报告
- 对现有 zh-CN.json (835 条) 实测发现 236 个潜在问题，工具实际有效
- CLI 已注册 validate 子命令，可通过 `python3 scripts/engine.py validate` 调用
- 10 个单元测试覆盖所有检测逻辑，包括正向检测和误报规避

## Task Commits

Each task was committed atomically:

1. **Task 1 (TDD RED): 失败测试** - `5de8e11` (test)
2. **Task 1 (TDD GREEN): validate 命令实现** - `4942f4c` (feat)

_Note: TDD task executed with RED (failing tests) -> GREEN (implementation) flow_

## Files Created/Modified
- `scripts/i18n/commands/validate.py` - 翻译质量验证命令模块（205 行）
- `tests/unit/test_validate.py` - validate 命令单元测试（252 行）
- `scripts/i18n/cli.py` - 新增 validate 子命令注册

## Decisions Made
- 白名单包含 30+ 常见技术缩写，避免将技术术语误报为中英混杂
- 同义不一致使用标准化 canonical key（小写+去标点）检测，而非语义分析
- 占位符检测覆盖三种主流格式：printf(%s/%d)、template(${var})、brace({0}/{name})
- validate 命令不依赖 CLI 安装目录，仅读取翻译映射表

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness
- validate 命令已就绪，可供 Plan 02/03 翻译扩充时使用
- 可直接集成到 CI 流程中做翻译质量回归检测
- 当前 zh-CN.json 有 236 个检测问题，后续翻译扩充时需关注

## Self-Check: PASSED

- scripts/i18n/commands/validate.py: FOUND
- tests/unit/test_validate.py: FOUND
- scripts/i18n/cli.py: FOUND
- 05-01-SUMMARY.md: FOUND
- 5de8e11 (RED commit): FOUND
- 4942f4c (GREEN commit): FOUND

---
*Phase: 05-translation-expansion*
*Completed: 2026-04-07*
