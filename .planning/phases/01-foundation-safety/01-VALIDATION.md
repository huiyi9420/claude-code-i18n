---
phase: 1
slug: foundation-safety
status: draft
nyquist_compliant: true
wave_0_complete: true
created: 2026-04-05
---

# Phase 1 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 8.x |
| **Config file** | pyproject.toml (if exists) or default |
| **Quick run command** | `python -m pytest tests/ -x -q` |
| **Full suite command** | `python -m pytest tests/ -v --tb=short` |
| **Estimated runtime** | ~5 seconds |

---

## Sampling Rate

- **After every task commit:** Run `python -m pytest tests/ -x -q`
- **After every plan wave:** Run `python -m pytest tests/ -v --tb=short`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 5 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 01-01-T1 | 01 | 1 | PATH-01~03 | unit | `python -m pytest tests/test_paths.py::test_resolve_via_which -x` | ✅ W0 | ⬜ pending |
| 01-01-T2 | 01 | 1 | PATH-04, PATH-05 | unit | `python -m pytest tests/test_paths.py::test_validate_cli_dir -x` | ✅ W0 | ⬜ pending |
| 01-02-T1 | 02 | 2 | BAK-05 | unit | `python -m pytest tests/test_file_io.py::test_atomic_write -x` | ✅ W0 | ⬜ pending |
| 01-02-T2 | 02 | 2 | BAK-01~04, BAK-06, BAK-07 | unit | `python -m pytest tests/test_backup.py -x` | ✅ W0 | ⬜ pending |
| 01-03-T1 | 03 | 3 | PATH/BAK integration | unit | `python -m pytest tests/test_cli.py -x` | ✅ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [x] `tests/test_paths.py` — stubs for PATH-01~05
- [x] `tests/test_backup.py` — stubs for BAK-01~07
- [x] `tests/test_file_io.py` — stubs for BAK-05 (atomic write)
- [x] `tests/test_cli.py` — stubs for CLI integration
- [x] `tests/conftest.py` — shared fixtures (mock_cli_dir, mock_backup)

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Volta shim path resolution on real system | PATH-01 | Requires actual Volta installation | Run `python engine.py status` and verify auto-detected path |
| chmod 444 on backup file | BAK-06 | File permission check needs real filesystem | Run apply, check `ls -la cli.bak.en.js` shows read-only |

---

## Validation Sign-Off

- [x] All tasks have automated verify or Wave 0 dependencies
- [x] Sampling continuity: no 3 consecutive tasks without automated verify
- [x] Wave 0 covers all MISSING references
- [x] No watch-mode flags
- [x] Feedback latency < 5s
- [x] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
