---
phase: 02-core-engine
plan: 04
status: complete
wave: 2
completed: 2026-04-05
---

# Plan 02-04 Summary: Commands + CLI Integration

## Completed

All command implementations wired together, CLI router updated.

### Files Created
- `scripts/i18n/commands/apply.py` — cmd_apply: version check → backup → replace → verify → write → JSON output
- `scripts/i18n/commands/extract.py` — cmd_extract: reads from pristine backup, outputs scored candidates
- `scripts/i18n/commands/status.py` — cmd_status: enhanced with localization detection, map info
- `tests/unit/test_apply_cmd.py` — 5 tests (no_cli, no_map, success, rollback, version_change)
- `tests/unit/test_extract_cmd.py` — 4 tests (no_cli, reads_backup, output_format, excludes_existing)
- `tests/unit/test_status_cmd.py` — 4 tests (enhanced_fields, localized_detected, no_cli, backup_info)

### Files Modified
- `scripts/i18n/config/constants.py` — Added MAP_FILE, SKIP_FILE
- `scripts/i18n/cli.py` — Replaced skeleton cmd_apply/cmd_extract with real imports, removed old cmd_status
- `tests/unit/test_cli.py` — Fixed import paths for cmd_status (now from commands.status)

## Test Results
- 145 tests passing (132 Phase 1+2 Wave 1 + 13 new command tests)
- 0 failures, 0 regressions

## Requirements Covered
- APPLY-01: Reads from pristine backup via restore (clean state)
- APPLY-07: node --check validates syntax
- APPLY-08: Automatic rollback on syntax failure
- APPLY-10: JSON output with ok/replacements/stats/entries
- EXTRACT-01: Reads from pristine backup only
- EXTRACT-04: JSON with strong/weak candidates, scores, counts
- STATUS-01: Version, localized state, entry count, backup integrity
- STATUS-02: Version via cmd_version
- STATUS-03: All commands output JSON
- STATUS-04: Human-readable summary in apply JSON output
- PLAT-03: No sed usage (pure Python replacement)
