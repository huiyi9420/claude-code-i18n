"""Restore command: restore cli.js from pristine backup.

Flow:
1. Detect CLI installation directory
2. Initialize BackupManager
3. If hash mismatch, auto-recreate backup and retry
4. Verify restored cli.js has zero CJK characters (BAK-07)
5. Output JSON result
"""

from scripts.i18n.cli import get_cli_dir, output_json, output_error
from scripts.i18n.io.backup import BackupManager


def cmd_restore() -> None:
    """Restore cli.js from pristine backup.

    Handles:
    - CLI not found (delegated to get_cli_dir)
    - No backup exists
    - Hash mismatch (auto-recreate from cli.js)
    - Backup poisoned (CJK in backup)
    - Post-restore CJK purity verification (BAK-07)
    """
    cli_dir = get_cli_dir()
    bm = BackupManager(cli_dir)
    result = bm.restore()

    if not result['ok']:
        # Hash mismatch: auto-recreate backup from current cli.js
        if result.get('error') == 'hash_mismatch':
            create_result = bm.ensure_backup()
            if create_result['ok']:
                result = bm.restore()
                if result['ok']:
                    # Verify post-restore purity (BAK-07)
                    if not bm._is_pristine_file(bm.cli_js):
                        output_error(
                            "restore verification failed",
                            hint="cli.js still contains CJK characters after restore",
                        )
                    output_json(result)
                    return
            # Recreate failed or re-restore failed
            output_error(
                result.get('error', 'restore_failed'),
                hint=result.get('hint', ''),
            )
            return
        # Other errors (no_backup, backup_poisoned)
        output_error(
            result.get('error', 'unknown'),
            hint=result.get('hint', ''),
        )
    else:
        # Verify post-restore purity (BAK-07)
        if not bm._is_pristine_file(bm.cli_js):
            output_error(
                "restore verification failed",
                hint="cli.js still contains CJK characters after restore",
            )
        output_json(result)
