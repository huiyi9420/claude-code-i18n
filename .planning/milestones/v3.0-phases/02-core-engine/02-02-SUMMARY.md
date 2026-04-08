---
phase: 02-core-engine
plan: 02
subsystem: core-engine
tags: [regex, string-replacement, three-tier, translation-engine]

# Dependency graph
requires:
  - phase: 02-core-engine
    plan: 01
    provides: "translation_map.load_translation_map() and load_skip_words() return types"
provides:
  - "replacer.classify_entry() function for tier classification"
  - "replacer.apply_translations() function for three-tier replacement"
  - "Stats dict format with long/medium/short/skipped/skip_reasons"
affects: [02-04-PLAN.md, integration-tests]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Three-tier replacement: long str.replace / medium quote-boundary regex / short word-boundary regex"
    - "Reverse-order replacement for medium/short tiers to prevent offset corruption"
    - "Longest-first sorting to prevent partial match corruption"

key-files:
  created:
    - scripts/i18n/core/replacer.py
    - tests/unit/test_replacer.py
    - tests/fixtures/sample_replacer_content.js
  modified: []

key-decisions:
  - "TDD RED/GREEN cycle: test assertions corrected to match actual string lengths (Plan Mode=9chars is short, Permission denied=18chars is medium)"
  - "skip_reasons dict tracks both 'identical' (en==zh) and 'skip_word' reasons for auditability"

patterns-established:
  - "Pattern: Three-tier replacement strategy based on source string length"
  - "Pattern: Reverse-order (reversed(matches)) for regex-based in-place string replacement"
  - "Pattern: Stats dict with per-category counters + skip_reasons sub-dict"

requirements-completed: [APPLY-01, APPLY-02, APPLY-03, APPLY-04, APPLY-05, APPLY-06, APPLY-09, APPLY-10]

# Metrics
duration: 4min
completed: 2026-04-05
---

# Phase 2 Plan 2: Three-Tier Replacement Engine Summary

**Three-tier string replacement engine with long/medium/short strategies, reverse-order regex replacement, and per-category stats tracking**

## Performance

- **Duration:** 4 min
- **Started:** 2026-04-05T13:03:24Z
- **Completed:** 2026-04-05T13:07:33Z
- **Tasks:** 1
- **Files modified:** 3

## Accomplishments
- Implemented `classify_entry()` for tier classification by string length
- Implemented `apply_translations()` with three-tier replacement strategy
- 28 unit tests covering all requirements (APPLY-01~06, APPLY-09~10)

## Task Commits

Each task was committed atomically:

1. **Task 1 (RED): Replacement Engine Tests** - `17b6fb0` (test)
2. **Task 1 (GREEN): Replacement Engine Implementation** - `633dcec` (feat)

## Files Created/Modified
- `scripts/i18n/core/replacer.py` - Three-tier replacement engine with classify_entry() and apply_translations()
- `tests/unit/test_replacer.py` - 28 unit tests for all replacement tiers, stats, ordering, edge cases
- `tests/fixtures/sample_replacer_content.js` - Test JS fixture with realistic minified content

## Decisions Made
- Corrected test string choices to match actual tier boundaries (Plan Mode=9 chars is short, Permission denied=18 chars is medium)
- Added `skip_reasons` sub-dict for auditing why entries were skipped (identical vs skip_word)

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Test assertions used wrong tier for string lengths**
- **Found during:** Task 1 (GREEN phase)
- **Issue:** Tests expected "Plan Mode" (9 chars) to be "medium" but it's "short"; "Permission denied" (18 chars) expected "long" but it's "medium"; "Dark mode" (9 chars) expected "medium" but it's "short"
- **Fix:** Corrected test strings to use strings that actually match the tier: "Permission denied" for medium, longer strings for long. Updated longest-first test to use non-overlapping Chinese translations.
- **Files modified:** tests/unit/test_replacer.py
- **Verification:** All 28 tests pass
- **Committed in:** 633dcec (Task 1 GREEN commit)

---

**Total deviations:** 1 auto-fixed (1 bug)
**Impact on plan:** Test corrections aligned with spec. No scope creep.

## Issues Encountered
None

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- replacer.py is ready for Plan 02-04 (apply command) to import
- apply_translations() takes translations dict and skip_words set as parameters
- Returns (content, stats) tuple for downstream verification and JSON output

## Self-Check: PASSED

- scripts/i18n/core/replacer.py: FOUND
- tests/unit/test_replacer.py: FOUND
- tests/fixtures/sample_replacer_content.js: FOUND
- Commit 17b6fb0 (RED): FOUND
- Commit 633dcec (GREEN): FOUND

---
*Phase: 02-core-engine*
*Completed: 2026-04-05*
