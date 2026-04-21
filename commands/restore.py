"""Restore command: restore cli.js from pristine backup.

Flow:
1. Detect CLI installation directory
2. Initialize BackupManager
3. If hash mismatch, auto-recreate backup and retry
4. Verify restored cli.js has zero CJK characters (BAK-07)
5. Output JSON result
"""

import sys

from scripts.i18n.cli import get_cli_dir, output_json, output_error
from scripts.i18n.io.backup import BackupManager


def _progress(*args, **kwargs) -> None:
    """Print progress message to stderr (keeps stdout clean for JSON output)."""
    print(*args, **kwargs, file=sys.stderr, flush=True)


def cmd_restore() -> None:
    """Restore cli.js from pristine backup."""
    cli_dir = get_cli_dir()
    bm = BackupManager(cli_dir)

    _progress("▶ 恢复原始英文 cli.js...", end="")
    result = bm.restore()

    if not result['ok']:
        # Hash mismatch: auto-recreate backup from current cli.js
        if result.get('error') == 'hash_mismatch':
            _progress(" 哈希不匹配，重建备份...")
            create_result = bm.ensure_backup()
            if create_result['ok']:
                _progress("▶ 重新恢复...", end="")
                result = bm.restore()
                if result['ok']:
                    if not bm._is_pristine_file(bm.cli_js):
                        _progress(" 失败!")
                        output_error(
                            "restore verification failed",
                            hint="cli.js still contains CJK characters after restore",
                        )
                    _progress(" 完成")
                    output_json(result)
                    return
            _progress(" 失败!")
            output_error(
                result.get('error', 'restore_failed'),
                hint=result.get('hint', ''),
            )
            return
        _progress(f" 失败! ({result.get('error', 'unknown')})")
        output_error(
            result.get('error', 'unknown'),
            hint=result.get('hint', ''),
        )
    else:
        if not bm._is_pristine_file(bm.cli_js):
            _progress(" 失败! (验证未通过)")
            output_error(
                "restore verification failed",
                hint="cli.js still contains CJK characters after restore",
            )
        else:
            _progress(" 完成")
        output_json(result)
