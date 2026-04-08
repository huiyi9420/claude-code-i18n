# Phase 2: Core Engine - Context

**Gathered:** 2026-04-05
**Status:** Ready for planning
**Mode:** Auto-generated (autonomous mode)

<domain>
## Phase Boundary

用户运行一条命令即可安全地将 Claude Code CLI 界面汉化为中文，替换后语法正确、失败自动回滚，且能从纯净源提取新的可翻译字符串。

</domain>

<decisions>
## Implementation Decisions

### Claude's Discretion
All implementation choices are at Claude's discretion — autonomous execution mode. Use ROADMAP phase goal, success criteria, Phase 1 established patterns, and codebase conventions to guide decisions.

**Key constraints:**
- Python 3.8+, zero external dependencies
- Enhanced regex (NOT AST) for string replacement
- All output as JSON
- Atomic writes for all file operations
- Must use Path Resolver and Backup Manager from Phase 1
- Translation map format: JSON with _meta header

</decisions>

<code_context>
## Existing Code Insights

### Reusable Assets (from Phase 1)
- `scripts/i18n/config/paths.py` — find_cli_install_dir(), validate_cli_dir()
- `scripts/i18n/config/constants.py` — PKG_NAME, BACKUP_NAME, HASH_NAME
- `scripts/i18n/io/backup.py` — BackupManager (create/verify/restore/check_purity)
- `scripts/i18n/io/file_io.py` — atomic_write_text(), atomic_copy()
- `scripts/i18n/cli.py` — build_parser(), output_json(), output_error()
- `scripts/engine.py` — CLI entry point

### Established Patterns
- TDD workflow (RED → GREEN → commit)
- pytest fixtures in conftest.py
- JSON output for all commands
- Atomic file operations throughout
- Error handling via output_error() to stderr

### Integration Points
- BackupManager must be used by apply command (restore from backup, apply translations, verify)
- Path resolver used by all commands to locate cli.js
- CLI framework (argparse) needs new subcommands: apply, extract
- Translation map (zh-CN.json) loaded by new scanner module

</code_context>

<specifics>
## Specific Ideas

No specific requirements — autonomous mode. Refer to ROADMAP phase description and success criteria.

</specifics>

<deferred>
## Deferred Ideas

None — autonomous execution.
</deferred>
