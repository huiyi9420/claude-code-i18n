---
phase: 01-foundation-safety
plan: 03
subsystem: cli
tags: [argparse, json, cli, subcommands, restore, status]

# Dependency graph
requires:
  - phase: 01-01
    provides: "Path resolver (find_cli_install_dir, validate_cli_dir)"
  - phase: 01-02
    provides: "BackupManager (ensure_backup, restore), atomic file I/O"
provides:
  - "CLI entry point (engine.py) with argparse subcommand routing"
  - "restore command: path detection + backup restore + purity verification"
  - "status command: CLI version + backup integrity + detection method"
  - "version command: CLI version from package.json"
  - "JSON output utilities (output_json, output_error)"
  - "apply/extract skeleton commands for Phase 2"
affects: [02-apply-engine, 02-extract, 03-installation]

# Tech tracking
tech-stack:
  added: [argparse]
  patterns: [subcommand-routing, json-stdout-stderr-split, hash-mismatch-autofix]

key-files:
  created:
    - scripts/engine.py
    - scripts/i18n/cli.py
    - scripts/i18n/commands/__init__.py
    - scripts/i18n/commands/restore.py
    - tests/unit/test_cli.py
  modified: []

key-decisions:
  - "engine.py adds project root to sys.path (not scripts/) for proper package imports"
  - "restore command auto-recreates backup on hash mismatch before retrying"
  - "status/version commands handle CLI-not-found gracefully without sys.exit"
  - "apply/extract output error via output_error (Phase 2 skeletons)"

patterns-established:
  - "Subcommand pattern: each command in scripts/i18n/commands/<name>.py exporting cmd_<name>"
  - "Output pattern: output_json for success to stdout, output_error for failure to stderr"
  - "Path resolution: get_cli_dir() wraps find_cli_install_dir() with error handling"

requirements-completed: [PATH-01, PATH-04, PATH-05, BAK-01, BAK-03, BAK-05, BAK-07]

# Metrics
duration: 4min
completed: 2026-04-05
---

# Phase 1 Plan 3: CLI Entry Point + Restore Command Summary

**argparse CLI framework with restore/status/version commands, JSON output, and hash mismatch auto-recovery**

## Performance

- **Duration:** 4 min
- **Started:** 2026-04-05T12:28:33Z
- **Completed:** 2026-04-05T12:32:33Z
- **Tasks:** 1 (TDD: RED + GREEN)
- **Files modified:** 5

## Accomplishments
- CLI entry point (engine.py) with 5 subcommands: status, restore, version, apply, extract
- restore command with hash mismatch auto-recovery and BAK-07 post-restore purity verification
- status command outputs comprehensive JSON: CLI version, backup status, detection method
- All 45 Phase 1 tests passing (paths: 9, backup: 12, file_io: 6, cli: 15)

## Task Commits

Each task was committed atomically:

1. **Task 1: CLI framework + restore/status/version + tests** - TDD flow
   - RED: `1100a57` (test) - 15 failing test cases for CLI framework
   - GREEN: `1fe64e6` (feat) - Full implementation making all tests pass

## Files Created/Modified
- `scripts/engine.py` - CLI entry point with sys.path setup for project root
- `scripts/i18n/cli.py` - argparse router, JSON output utils, status/version/apply/extract commands
- `scripts/i18n/commands/__init__.py` - Package marker
- `scripts/i18n/commands/restore.py` - Restore command with auto-recovery logic
- `tests/unit/test_cli.py` - 15 test cases: output, parser, restore, status, version, entry point

## Decisions Made
- **engine.py sys.path strategy**: Added project root (parent of scripts/) to sys.path rather than scripts/ itself. This ensures `from scripts.i18n.*` imports work correctly from any working directory.
- **restore auto-recovery**: On hash mismatch, restore command automatically recreates backup from current cli.js before retrying. This handles the common case of version updates invalidating the hash.
- **status/version graceful degradation**: These commands output `{"ok": false}` JSON instead of calling sys.exit when CLI is not found. Only restore (which requires CLI to exist) triggers sys.exit via get_cli_dir().

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed engine.py sys.path for correct module resolution**
- **Found during:** Task 1 (GREEN phase)
- **Issue:** Initial engine.py added `scripts/` to sys.path but imports use `scripts.i18n.cli`, requiring the project root in the path
- **Fix:** Changed sys.path.insert to add `Path(__file__).resolve().parent.parent` (project root) instead of `Path(__file__).parent` (scripts/)
- **Files modified:** scripts/engine.py
- **Verification:** `python3 scripts/engine.py --help` works from project root
- **Committed in:** 1fe64e6 (Task 1 GREEN commit)

**2. [Rule 1 - Bug] Simplified test_restore_no_cli test structure**
- **Found during:** Task 1 (GREEN phase)
- **Issue:** Original test nested multiple `with pytest.raises(SystemExit)` and patches incorrectly, not testing actual restore flow
- **Fix:** Simplified to mock `get_cli_dir` directly in restore module namespace with SystemExit side effect
- **Files modified:** tests/unit/test_cli.py
- **Verification:** test_restore_no_cli passes
- **Committed in:** 1fe64e6 (Task 1 GREEN commit)

---

**Total deviations:** 2 auto-fixed (2 bugs)
**Impact on plan:** Both fixes necessary for correct behavior. No scope creep.

## Issues Encountered
None

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Phase 1 complete: Path detection, backup management, CLI framework all functional
- Ready for Phase 2: Apply engine (APPLY-01~10), Extract (EXTRACT-01~06), Version detection (VER-01~04)
- apply and extract skeleton commands already registered in argparse, just need implementation
- All Phase 1 requirements (PATH-01~05, BAK-01~07) have test coverage

## Self-Check: PASSED

All 6 created files verified present. Both task commits (1100a57, 1fe64e6) verified in git log.

---
*Phase: 01-foundation-safety*
*Completed: 2026-04-05*
