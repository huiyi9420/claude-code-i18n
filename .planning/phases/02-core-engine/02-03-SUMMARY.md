---
phase: 02-core-engine
plan: 03
subsystem: core-engine
tags: [node-check, syntax-verification, version-detection, subprocess, pathlib]

# Dependency graph
requires:
  - phase: 01-foundation
    provides: BackupManager, atomic_write_text, PKG_NAME, find_cli_install_dir
provides:
  - verify_syntax() -- node --check JS syntax validation with timeout/error handling
  - get_cli_version() -- read CLI version from package.json
  - check_version_change() -- compare CLI version vs translation map _meta.cli_version
  - handle_version_change() -- delete stale backup and recreate on version mismatch
affects: [02-core-engine/02-04, apply-command, status-command]

# Tech tracking
tech-stack:
  added: [subprocess.run with node --check]
  patterns: [verifier-pattern, version-change-handler-pattern]

key-files:
  created:
    - scripts/i18n/core/verifier.py
    - scripts/i18n/core/version.py
    - tests/unit/test_verifier.py
    - tests/unit/test_version.py

key-decisions:
  - "verify_syntax returns dict with ok+error for consistent error handling"
  - "handle_version_change uses BackupManager._make_writable before unlink to handle chmod 444"
  - "check_version_change treats unknown CLI version as unchanged to avoid false positives"

patterns-established:
  - "Verification pattern: subprocess.run([list], capture_output, text, timeout) -- never shell=True"
  - "Version detection: json.loads + Path.read_text for package.json parsing"
  - "Error recovery: version mismatch triggers backup deletion + BackupManager.ensure_backup recreation"

requirements-completed: [APPLY-07, APPLY-08, VER-01, VER-02, VER-03, VER-04, PLAT-01, PLAT-02]

# Metrics
duration: 3min
completed: 2026-04-05
---

# Phase 2 Plan 3: Verification + Version Detection Summary

**node --check syntax verifier with automatic rollback support and package.json version detection with stale backup recreation**

## Performance

- **Duration:** 3 min
- **Started:** 2026-04-05T13:02:59Z
- **Completed:** 2026-04-05T13:05:00Z
- **Tasks:** 1
- **Files modified:** 4

## Accomplishments
- verify_syntax() validates JS via node --check with timeout, missing-file, and node-not-found handling (APPLY-07)
- Version detection reads package.json, compares with translation map _meta.cli_version (VER-01, VER-02)
- Version mismatch triggers automatic stale backup deletion and recreation from new cli.js (VER-03, VER-04)
- All paths use pathlib.Path throughout (PLAT-01, PLAT-02)
- 20 unit tests (7 verifier + 13 version) all passing

## Task Commits

Each task was committed atomically:

1. **Task 1 (RED): Failing tests for verifier and version modules** - `d6fb250` (test)
2. **Task 1 (GREEN): Implement verifier and version detection modules** - `af41d1e` (feat)

_Note: TDD task with RED-GREEN commits_

## Files Created/Modified
- `scripts/i18n/core/__init__.py` - Core module package init
- `scripts/i18n/core/verifier.py` - JS syntax verification via node --check (APPLY-07/08)
- `scripts/i18n/core/version.py` - CLI version detection and change handling (VER-01~04)
- `tests/unit/test_verifier.py` - 7 tests for verify_syntax
- `tests/unit/test_version.py` - 13 tests for get_cli_version, check_version_change, handle_version_change

## Decisions Made
- verify_syntax returns a consistent dict `{"ok": bool, "error": str|None}` for all code paths (success, syntax error, timeout, node-not-found, file-not-found)
- handle_version_change calls `BackupManager._make_writable()` before `unlink()` because backups are chmod 444 from Phase 1
- check_version_change treats CLI version "unknown" as unchanged to avoid false-positive version mismatch triggers when package.json is unreadable
- Error messages are descriptive and user-facing (e.g., "node not found -- is Node.js installed?")

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
None.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- verifier.py ready for import by Plan 02-04 apply command (rollback-on-failure integration)
- version.py ready for import by Plan 02-04 apply command (pre-apply version check)
- All core engine modules for the apply pipeline are now complete

## Self-Check: PASSED

All files verified present:
- scripts/i18n/core/verifier.py
- scripts/i18n/core/version.py
- tests/unit/test_verifier.py
- tests/unit/test_version.py
- .planning/phases/02-core-engine/02-03-SUMMARY.md

All commits verified:
- d6fb250: test(02-03): add failing tests for verifier and version modules
- af41d1e: feat(02-03): implement verifier and version detection modules

---
*Phase: 02-core-engine*
*Completed: 2026-04-05*
