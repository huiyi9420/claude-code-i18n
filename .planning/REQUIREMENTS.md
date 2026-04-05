# Requirements: Claude Code i18n (Complete Rewrite)

**Defined:** 2026-04-05
**Core Value:** 用户运行一条命令，Claude Code CLI 的全部用户可见界面变成准确、自然的中文，版本更新后自动适配。

## v1 Requirements

### Path Resolution (PATH)

- [x] **PATH-01**: Engine auto-detects CLI installation path via `which claude` symlink resolution
- [x] **PATH-02**: Engine supports explicit path via environment variable `CLAUDE_I18N_CLI_DIR`
- [x] **PATH-03**: Engine supports config file `~/.claude/i18n.json` with custom `cli_path`
- [x] **PATH-04**: Engine validates detected path exists and contains `cli.js` + `package.json`
- [x] **PATH-05**: Engine reports clear error message when CLI not found (with install instructions)

### Backup Integrity (BAK)

- [x] **BAK-01**: First apply creates backup from pristine cli.js (no Chinese characters present)
- [x] **BAK-02**: Backup creation computes SHA-256 hash stored in `.backup.hash`
- [x] **BAK-03**: Every restore/apply validates backup hash before use; mismatch triggers re-extraction
- [x] **BAK-04**: Backup purity check: scan for CJK characters, reject if found (>0 CJK chars)
- [x] **BAK-05**: Atomic write for all file operations (write to temp, then os.rename)
- [x] **BAK-06**: Backup file set read-only after creation (chmod 444) to prevent accidental modification
- [x] **BAK-07**: Restore command returns cli.js to 100% pure English with zero Chinese characters

### Apply Engine (APPLY)

- [ ] **APPLY-01**: Apply reads from pristine backup (not current cli.js) as source
- [ ] **APPLY-02**: Long strings (>20 chars) use global replacement with exact match
- [ ] **APPLY-03**: Medium strings (10-20 chars) use quote-boundary constrained replacement
- [ ] **APPLY-04**: Short strings (<10 chars) use word-boundary + whitelist + frequency cap (default skip)
- [ ] **APPLY-05**: All replacements proceed longest-first to prevent partial matches
- [ ] **APPLY-06**: Replacement count tracked per category (long/medium/short/skipped)
- [ ] **APPLY-07**: After all replacements, `node --check` validates syntax
- [ ] **APPLY-08**: On syntax validation failure, automatic rollback to backup
- [ ] **APPLY-09**: Hook/template string patterns replaced via precise context-aware sed (not blind global)
- [ ] **APPLY-10**: Apply outputs JSON result with ok/replacements/stats/entries

### Extract (EXTRACT)

- [ ] **EXTRACT-01**: Extract reads from pristine backup only (never from translated cli.js)
- [ ] **EXTRACT-02**: Extract uses strong/weak signal indicator system to score candidates
- [ ] **EXTRACT-03**: Extract filters out code-like strings (identifiers, URLs, protocol keywords)
- [ ] **EXTRACT-04**: Extract outputs JSON with strong/weak candidates, scores, and occurrence counts
- [ ] **EXTRACT-05**: Extract correctly excludes already-translated and already-skipped strings
- [ ] **EXTRACT-06**: Extract never outputs strings containing Chinese characters

### Version Detection (VER)

- [ ] **VER-01**: Engine reads CLI version from package.json
- [ ] **VER-02**: Engine compares CLI version with translation map's `_meta.cli_version`
- [ ] **VER-03**: On version mismatch, engine deletes stale backup and re-creates from new cli.js
- [ ] **VER-04**: Version change reported to user with old→new version numbers

### Status & Output (STATUS)

- [ ] **STATUS-01**: `status` command outputs JSON with version, localized state, entry count, backup integrity
- [ ] **STATUS-02**: `version` command outputs current CLI version
- [ ] **STATUS-03**: All commands output JSON format for script integration
- [ ] **STATUS-04**: Human-readable summary printed after apply (version, replacements, verification result)

### Translation Map (MAP)

- [ ] **MAP-01**: Translation map uses JSON format with `_meta` header (version, cli_version, description)
- [ ] **MAP-02**: Map loaded from `~/.claude/scripts/i18n/zh-CN.json` by default
- [ ] **MAP-03**: Skip words loaded from `~/.claude/scripts/i18n/skip-words.json`
- [ ] **MAP-04**: Map entries with identical en/zh values are automatically skipped

### Cross-Platform (PLATFORM)

- [ ] **PLAT-01**: All file paths use `pathlib.Path` (no hardcoded OS-specific separators)
- [ ] **PLAT-02**: No hardcoded user paths — all resolved dynamically
- [ ] **PLAT-03**: `sed -i` in Hook replacements uses platform-appropriate syntax (macOS vs Linux)

### Installation (INSTALL)

- [ ] **INST-01**: `install.sh` copies engine + map + skip-words + skill command to `~/.claude/`
- [ ] **INST-02**: Skill command (`commands/zcf/i18n.md`) stays in sync with engine capabilities
- [ ] **INST-03**: Install script verifies Python 3 and Node.js availability

### Testing (TEST)

- [ ] **TEST-01**: Unit tests for path resolution (mock filesystem)
- [ ] **TEST-02**: Unit tests for backup manager (hash, purity, atomic write)
- [ ] **TEST-03**: Unit tests for string scanner (signal scoring, noise filtering)
- [ ] **TEST-04**: Unit tests for replacement engine (long/medium/short strategies)
- [ ] **TEST-05**: Unit tests for extract command (candidate scoring)
- [ ] **TEST-06**: Integration test: apply → verify → restore → verify (full round-trip)
- [ ] **TEST-07**: Test coverage ≥ 80%

## v2 Requirements

### Quality Enhancement

- **CTX-01**: Translation map supports context/scope tags per entry (e.g., `"Running" → {default: "运行中", process: "正在执行"}`)
- **CTX-02**: Replacement engine resolves context tags during apply
- **COV-01**: `coverage` command outputs translation coverage report (translated/untranslated/skipped with percentages)
- **COV-02**: Coverage report shows per-category breakdown (long/medium/short)
- **DRY-01**: `--dry-run` flag on apply shows planned replacements without writing
- **SHORT-01**: Safe short-string translation with configurable whitelist and frequency cap

### Scalability

- **SMART-01**: Version update smart diff — compare old vs new extract results, categorize as new/changed/removed
- **SMART-02**: Changed entries flagged for human review
- **PERF-01**: Evaluate Aho-Corasick multi-pattern matching for 2000+ patterns
- **PERF-02**: Batch replacement optimization for 13MB file (target <30s)
- **CI-01**: Automated regression test suite runnable in CI

## Out of Scope

| Feature | Reason |
|---------|--------|
| AST parsing engine | 13MB minified file too large/slow for AST; enhanced regex sufficient |
| Multi-language support (ja/ko/etc) | Current resources only support Chinese; architecture can be extended later |
| Binary version compatibility | User explicitly requested this as future consideration |
| Web UI / translation management backend | Scale doesn't require it; JSON files are sufficient |
| Automatic AI translation | Quality control requires human review; AI suggests, human confirms |
| Runtime React component patching | Risk of breaking rendering logic too high |
| i18n of plugins/commands | Separate concern from core CLI UI translation |

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| PATH-01 | Phase 1 | Complete |
| PATH-02 | Phase 1 | Complete |
| PATH-03 | Phase 1 | Complete |
| PATH-04 | Phase 1 | Complete |
| PATH-05 | Phase 1 | Complete |
| BAK-01 | Phase 1 | Complete |
| BAK-02 | Phase 1 | Complete |
| BAK-03 | Phase 1 | Complete |
| BAK-04 | Phase 1 | Complete |
| BAK-05 | Phase 1 | Complete |
| BAK-06 | Phase 1 | Complete |
| BAK-07 | Phase 1 | Complete |
| APPLY-01 | Phase 2 | Pending |
| APPLY-02 | Phase 2 | Pending |
| APPLY-03 | Phase 2 | Pending |
| APPLY-04 | Phase 2 | Pending |
| APPLY-05 | Phase 2 | Pending |
| APPLY-06 | Phase 2 | Pending |
| APPLY-07 | Phase 2 | Pending |
| APPLY-08 | Phase 2 | Pending |
| APPLY-09 | Phase 2 | Pending |
| APPLY-10 | Phase 2 | Pending |
| EXTRACT-01 | Phase 2 | Pending |
| EXTRACT-02 | Phase 2 | Pending |
| EXTRACT-03 | Phase 2 | Pending |
| EXTRACT-04 | Phase 2 | Pending |
| EXTRACT-05 | Phase 2 | Pending |
| EXTRACT-06 | Phase 2 | Pending |
| VER-01 | Phase 2 | Pending |
| VER-02 | Phase 2 | Pending |
| VER-03 | Phase 2 | Pending |
| VER-04 | Phase 2 | Pending |
| STATUS-01 | Phase 2 | Pending |
| STATUS-02 | Phase 2 | Pending |
| STATUS-03 | Phase 2 | Pending |
| STATUS-04 | Phase 2 | Pending |
| MAP-01 | Phase 2 | Pending |
| MAP-02 | Phase 2 | Pending |
| MAP-03 | Phase 2 | Pending |
| MAP-04 | Phase 2 | Pending |
| PLAT-01 | Phase 2 | Pending |
| PLAT-02 | Phase 2 | Pending |
| PLAT-03 | Phase 2 | Pending |
| INST-01 | Phase 3 | Pending |
| INST-02 | Phase 3 | Pending |
| INST-03 | Phase 3 | Pending |
| TEST-01 | Phase 3 | Pending |
| TEST-02 | Phase 3 | Pending |
| TEST-03 | Phase 3 | Pending |
| TEST-04 | Phase 3 | Pending |
| TEST-05 | Phase 3 | Pending |
| TEST-06 | Phase 3 | Pending |
| TEST-07 | Phase 3 | Pending |

**Coverage:**
- v1 requirements: 53 total (10 categories)
- Mapped to phases: 53
- Phase 1: 12 requirements (PATH 5 + BAK 7)
- Phase 2: 31 requirements (APPLY 10 + EXTRACT 6 + VER 4 + STATUS 4 + MAP 4 + PLAT 3)
- Phase 3: 10 requirements (INST 3 + TEST 7)
- Unmapped: 0

---
*Requirements defined: 2026-04-05*
*Last updated: 2026-04-05 after roadmap creation*
