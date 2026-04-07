---
phase: 01-foundation-safety
plan: 01
subsystem: infra
tags: [pathlib, shutil.which, subprocess, volta, npm, cascading-detection]

# Dependency graph
requires: []
provides:
  - find_cli_install_dir() - 5-level cascading CLI path detection
  - validate_cli_dir() - CLI installation directory validation
  - constants.py - PKG_NAME, BACKUP_NAME, HASH_NAME
  - Test infrastructure (conftest.py, fixtures, test patterns)
affects: [01-02, 01-03, 02-apply-engine, 02-extract, 03-install]

# Tech tracking
tech-stack:
  added: [pytest 9.0.2 (dev only)]
  patterns: [cascading-strategy, mock-factory-fixture, tdd-red-green]

key-files:
  created:
    - scripts/i18n/config/paths.py
    - scripts/i18n/config/constants.py
    - tests/conftest.py
    - tests/unit/test_paths.py
    - tests/fixtures/sample_cli.js
    - tests/fixtures/sample_package.json
  modified: []

key-decisions:
  - "5-level cascading detection: env_var > config_file > volta > npm_global > common_path"
  - "validate_cli_dir only checks structure + package name, not content purity"
  - "All subprocess calls use timeout=5 and exception handling"
  - "Created Python venv for isolated pytest execution (.venv/)"

patterns-established:
  - "Cascading strategy: try methods in priority order, return first success"
  - "Mock factory fixtures: conftest.py returns factory functions for flexible mocking"
  - "TDD red-green: write failing tests first, implement to pass"

requirements-completed: [PATH-01, PATH-02, PATH-03, PATH-04, PATH-05]

# Metrics
duration: 5min
completed: 2026-04-05
---

# Phase 1 Plan 01: CLI Path Detection Summary

**5-level cascading CLI path detection with env var, config file, Volta, npm global, and common path fallback strategies, plus directory validation**

## Performance

- **Duration:** 5 min
- **Started:** 2026-04-05T11:37:10Z
- **Completed:** 2026-04-05T11:42:35Z
- **Tasks:** 2
- **Files modified:** 10

## Accomplishments
- Implemented find_cli_install_dir() with 5-level cascading detection strategy
- Implemented validate_cli_dir() checking directory structure and package identity
- Created complete test infrastructure (conftest.py, fixtures, 12 unit tests)
- All 12 tests GREEN, zero external runtime dependencies

## Task Commits

Each task was committed atomically:

1. **Task 1: Create test infrastructure + path resolver constants** - `2bf0554` (test) - TDD RED state
2. **Task 2: Implement Path Resolver** - `e17d8ed` (feat) - TDD GREEN state

_Note: TDD tasks have multiple commits (test -> feat)_

## Files Created/Modified
- `scripts/i18n/config/paths.py` - 5-level cascading path detection + validation
- `scripts/i18n/config/constants.py` - PKG_NAME, BACKUP_NAME, HASH_NAME constants
- `scripts/i18n/__init__.py` - Package marker
- `scripts/i18n/config/__init__.py` - Package marker
- `tests/__init__.py` - Test package marker
- `tests/conftest.py` - Shared fixtures (mock_cli_dir, mock_volta, mock_npm_root, clean_env)
- `tests/unit/__init__.py` - Unit test package marker
- `tests/unit/test_paths.py` - 12 tests covering PATH-01 through PATH-05
- `tests/fixtures/sample_cli.js` - Mock CLI JS file (~500 bytes)
- `tests/fixtures/sample_package.json` - Mock package.json with correct PKG_NAME

## Decisions Made
- Used 5-level cascading detection (env_var > config_file > volta > npm_global > common_path) to handle all known installation methods
- validate_cli_dir only checks structural validity (files exist + package name), not content purity -- content checking is a separate concern for the backup manager
- All subprocess.run calls wrapped with timeout=5 and (TimeoutExpired, OSError) exception handling to prevent hangs
- Created .venv/ for isolated pytest installation, added to .gitignore

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
- pytest not installed system-wide due to PEP 668 restrictions -- resolved by creating a Python venv (.venv/) for development dependencies
- Path typos in initial Write tool calls (zhaolu instead of zhaolulu) -- caught and corrected immediately

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Path detection module ready for consumption by backup manager (Plan 02) and CLI entry point (Plan 03)
- Test infrastructure (conftest.py, fixtures) reusable for subsequent plans
- Constants (PKG_NAME, BACKUP_NAME, HASH_NAME) shared across all plans

---
*Phase: 01-foundation-safety*
*Completed: 2026-04-05*
