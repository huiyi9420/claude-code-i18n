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

import sys
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


def _progress(*args, **kwargs) -> None:
    """Print progress message to stderr (keeps stdout clean for JSON output)."""
    print(*args, **kwargs, file=sys.stderr, flush=True)


def cmd_apply() -> None:
    """Apply Chinese localization to Claude Code CLI."""
    cli_dir = get_cli_dir()

    # Load translation data
    _progress("▶ 加载翻译数据...", end="")
    map_path = get_data_dir() / MAP_FILE
    skip_path = get_data_dir() / SKIP_FILE

    if not map_path.exists():
        output_error(f"Translation map not found: {map_path}")
        return

    map_data = load_translation_map(map_path)
    skip_words = load_skip_words(skip_path) if skip_path.exists() else set()
    translations = map_data["translations"]
    raw_translations = map_data.get("raw_translations", {})
    _progress(f" 完成 ({len(translations)} 条翻译)")

    # Version change detection (VER-01~04)
    _progress("▶ 检查版本变更...", end="")
    version_result = handle_version_change(cli_dir, map_data["meta"])
    if version_result.get("changed"):
        _progress(f" 版本已更新 {version_result['old']} → {version_result['new']}")
    else:
        _progress(" 无变更")

    # Ensure pristine backup
    _progress("▶ 创建纯净备份...", end="")
    bm = BackupManager(cli_dir)
    backup_result = bm.ensure_backup()
    if not backup_result["ok"]:
        _progress(" 失败!")
        output_error(
            f"Backup creation failed: {backup_result.get('error', 'unknown')}",
            hint=backup_result.get('hint', ''),
        )
        return
    _progress(f" {backup_result.get('action', 'ok')}")

    # Restore from backup (clean state for apply, APPLY-01)
    _progress("▶ 恢复原始英文...", end="")
    restore_result = bm.restore()
    if not restore_result["ok"]:
        _progress(" 失败!")
        output_error(
            f"Restore from backup failed: {restore_result.get('error', 'unknown')}",
            hint=restore_result.get('hint', ''),
        )
        return
    _progress(" 完成")

    # Read cli.js content
    _progress("▶ 读取 cli.js...", end="")
    cli_js = cli_dir / 'cli.js'
    content = cli_js.read_text(encoding='utf-8')
    _progress(f" 完成 ({len(content)} 字符)")

    # Build context index only when there may be context-tagged entries
    _progress("▶ 构建上下文索引...", end="")
    context_index = build_context_index(content) if raw_translations else None
    _progress(" 完成")

    # Apply translations (context-aware when context_index is available)
    _progress("▶ 应用翻译替换...", end="")
    modified, stats = apply_translations(
        content, translations, skip_words,
        raw_translations=raw_translations,
        context_index=context_index,
    )
    total = stats["long"] + stats["medium"] + stats["short"]
    _progress(f" 完成 ({total} 处替换)")

    # Write via atomic operation
    _progress("▶ 写入 cli.js...", end="")
    atomic_write_text(cli_js, modified)

    # Ensure cli.js is writable and executable (atomic_write may preserve 444 from backup)
    cli_js.chmod(0o644)
    _progress(" 完成")

    # Verify syntax (APPLY-07)
    _progress("▶ 验证语法...", end="")
    verify_result = verify_syntax(cli_js)
    if not verify_result["ok"]:
        _progress(" 失败!")
        # Rollback on failure (APPLY-08)
        bm.restore()
        output_json({
            "ok": False,
            "error": f"Syntax validation failed, rolled back: {verify_result['error']}",
            "stats": stats,
            "rollback": True,
        })
        return
    _progress(" 通过")

    # Success output (APPLY-10, STATUS-04)
    _progress(f"\n✓ 汉化完成! {total} 处替换 (长:{stats['long']} 中:{stats['medium']} 短:{stats['short']})")
    output_json({
        "ok": True,
        "action": "applied",
        "replacements": total,
        "stats": stats,
        "entries": len(translations),
        "version": get_cli_version(cli_dir),
        "verification": "passed",
    })
