---
phase: 02-core-engine
plan: 01
subsystem: io/filters/core
tags: [translation-map, scanner, noise-filter, ui-indicators, tdd]
dependency_graph:
  requires:
    - scripts/i18n/config/constants.py
    - scripts/i18n/config/paths.py
  provides:
    - scripts/i18n/io/translation_map.py
    - scripts/i18n/filters/noise_filter.py
    - scripts/i18n/filters/ui_indicator.py
    - scripts/i18n/core/scanner.py
  affects:
    - 02-02-PLAN (replacement engine uses translation_map)
    - 02-04-PLAN (commands use scanner + translation_map)
tech_stack:
  added:
    - re.compile for NOISE_RE and CJK_PATTERN
  patterns:
    - TDD RED-GREEN workflow
    - Compiled regex for performance in hot loops
key_files:
  created:
    - scripts/i18n/io/translation_map.py
    - scripts/i18n/filters/__init__.py
    - scripts/i18n/filters/noise_filter.py
    - scripts/i18n/filters/ui_indicator.py
    - scripts/i18n/core/__init__.py
    - scripts/i18n/core/scanner.py
    - tests/unit/test_translation_map.py
    - tests/unit/test_filters.py
    - tests/unit/test_scanner.py
    - tests/fixtures/sample_zh_cn.json
    - tests/fixtures/sample_skip.json
decisions:
  - Reused v3.0 NOISE_KW list verbatim for backward compatibility
  - score_candidate returns dict with score+type for scanner consumption
  - Scanner uses re.findall with capital-letter-start pattern for candidate extraction
  - CJK exclusion uses \u4e00-\u9fff range (covers CJK Unified Ideographs)
metrics:
  duration: 5min
  tasks: 2
  files: 11
  tests: 39
---

# Phase 2 Plan 1: Translation Map + Scanner Summary

Translation map loader with v4/v5 format support, noise filter with 62 noise patterns, UI indicator scoring (21 strong + 23 weak), and string scanner with 8 filtering rules and CJK exclusion.

## Tasks Completed

| Task | Name | Commit | Files |
|------|------|--------|-------|
| 1 | Translation Map Loader + Filters + Tests | 55224e4 | translation_map.py, noise_filter.py, ui_indicator.py, test_translation_map.py, test_filters.py, fixtures |
| 2 | String Scanner + Tests | b428e24 | scanner.py, test_scanner.py, core/__init__.py |

## What Was Built

### Translation Map Loader (`scripts/i18n/io/translation_map.py`)
- `load_translation_map(path)`: Loads JSON with `_meta` header and `translations` dict. Flattens dict values (v5 format `{"zh": "..."}`) to plain strings. Preserves identical en==zh entries for consumer to handle.
- `load_skip_words(path)`: Loads skip words from JSON `{"skip": [...]}` into a set. Returns empty set for missing `skip` key.

### Noise Filter (`scripts/i18n/filters/noise_filter.py`)
- `NOISE_RE`: Compiled regex with 62 noise patterns migrated from v3.0 `NOISE_KW` list. Matches third-party library internals, protocol keywords, and irrelevant content.
- `is_noise(s)`: Boolean check for noise pattern match. Case-insensitive.

### UI Indicator Scoring (`scripts/i18n/filters/ui_indicator.py`)
- `STRONG_INDICATORS`: 21 entries for Claude-specific signals (plan mode, claude code, extended thinking, etc.)
- `WEAK_INDICATORS`: 23 entries for general UI signals (permission, loading, session, etc.)
- `score_candidate(text, count)`: Returns `{"score": int, "type": "strong"|"weak"|"none"}`. Strong scores 1000+count, weak scores count, none scores 0.

### String Scanner (`scripts/i18n/core/scanner.py`)
- `scan_candidates(content, existing, skipped, noise_re)`: Extracts double-quoted English strings from JS source. Applies 8 filtering rules: no-space exclusion, code fragment exclusion (=>, ${, ===, etc.), URL exclusion, ALL_CAPS exclusion, noise filtering, CJK exclusion, underscore-identifier exclusion. Scores via `score_candidate()`, returns sorted list by score descending.

## Requirements Satisfied

- **MAP-01**: Translation map loaded from JSON with `_meta` header
- **MAP-02**: Map loaded from configurable path (function accepts Path parameter)
- **MAP-03**: Skip words loaded from JSON into set
- **MAP-04**: Dict values flattened; identical en==zh entries preserved for consumer handling
- **EXTRACT-01**: Scanner extracts candidates with occurrence counting
- **EXTRACT-02**: Strong/weak signal scoring with `score_candidate()`
- **EXTRACT-03**: Noise filter rejects code-like strings (identifiers, URLs, protocol keywords)
- **EXTRACT-04**: Output sorted by score descending
- **EXTRACT-05**: Existing and skipped strings excluded from results
- **EXTRACT-06**: CJK characters never appear in output

## Deviations from Plan

None - plan executed exactly as written.

## Test Coverage

- **test_translation_map.py**: 9 tests (MAP-01~04)
- **test_filters.py**: 11 tests (EXTRACT-02/03)
- **test_scanner.py**: 19 tests (EXTRACT-01~06)
- **Total**: 39 tests, all passing

## Self-Check: PASSED

- All 11 files verified present
- Commit 55224e4 (Task 1) verified
- Commit b428e24 (Task 2) verified
- All 39 tests passing
