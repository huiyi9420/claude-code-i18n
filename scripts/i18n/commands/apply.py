"""Apply command: apply Chinese localization to Claude Code CLI.

Flow:
1. Detect CLI installation + load translation map + skip words
2. Check version change (handle stale backup if needed)
3. Ensure pristine backup exists
4. Restore from backup (clean state)
5. Read cli.js, apply translations
6. Write via atomic_write_text
7. Verify with node --check
8. On failure: restore from backup
9. Output JSON result

APPLY-01: Reads from pristine backup (via restore) as source.
APPLY-07: node --check validates syntax after replacements.
APPLY-08: On syntax failure, automatic rollback to backup.
APPLY-10: Outputs JSON result with ok/replacements/stats/entries.
"""

from pathlib import Path

from scripts.i18n.cli import get_cli_dir, output_json, output_error
from scripts.i18n.config.constants import MAP_FILE, SKIP_FILE
from scripts.i18n.io.backup import BackupManager
from scripts.i18n.io.file_io import atomic_write_text
from scripts.i18n.io.translation_map import load_translation_map, load_skip_words
from scripts.i18n.core.replacer import apply_translations
from scripts.i18n.core.verifier import verify_syntax
from scripts.i18n.core.version import handle_version_change, get_cli_version
from scripts.i18n.config.paths import get_data_dir
from scripts.i18n.core.context_detector import build_context_index



def cmd_apply() -> None:
    """Apply Chinese localization to Claude Code CLI."""
    cli_dir = get_cli_dir()

    # Load translation data
    map_path = get_data_dir() / MAP_FILE
    skip_path = get_data_dir() / SKIP_FILE

    if not map_path.exists():
        output_error(f"Translation map not found: {map_path}")
        return

    map_data = load_translation_map(map_path)
    skip_words = load_skip_words(skip_path) if skip_path.exists() else set()
    translations = map_data["translations"]
    raw_translations = map_data.get("raw_translations", {})

    # Version change detection (VER-01~04)
    version_result = handle_version_change(cli_dir, map_data["meta"])

    # Ensure pristine backup
    bm = BackupManager(cli_dir)
    backup_result = bm.ensure_backup()
    if not backup_result["ok"]:
        output_error(
            f"Backup creation failed: {backup_result.get('error', 'unknown')}",
            hint=backup_result.get('hint', ''),
        )
        return

    # Restore from backup (clean state for apply, APPLY-01)
    restore_result = bm.restore()
    if not restore_result["ok"]:
        output_error(
            f"Restore from backup failed: {restore_result.get('error', 'unknown')}",
            hint=restore_result.get('hint', ''),
        )
        return

    # Read cli.js content
    cli_js = cli_dir / 'cli.js'
    content = cli_js.read_text(encoding='utf-8')

    # Build context index only when there may be context-tagged entries
    context_index = build_context_index(content) if raw_translations else None

    # Apply translations (context-aware when context_index is available)
    modified, stats = apply_translations(
        content, translations, skip_words,
        raw_translations=raw_translations,
        context_index=context_index,
    )

    # Write via atomic operation
    atomic_write_text(cli_js, modified)

    # Verify syntax (APPLY-07)
    verify_result = verify_syntax(cli_js)

    if not verify_result["ok"]:
        # Rollback on failure (APPLY-08)
        bm.restore()
        output_json({
            "ok": False,
            "error": f"Syntax validation failed, rolled back: {verify_result['error']}",
            "stats": stats,
            "rollback": True,
        })
        return

    # Success output (APPLY-10, STATUS-04)
    total = stats["long"] + stats["medium"] + stats["short"]
    output_json({
        "ok": True,
        "action": "applied",
        "replacements": total,
        "stats": stats,
        "entries": len(translations),
        "version": get_cli_version(cli_dir),
        "verification": "passed",
    })
