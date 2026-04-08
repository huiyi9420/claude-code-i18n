"""Version detection for Claude Code i18n engine.

Reads CLI version from package.json and compares with translation map's
_meta.cli_version. Handles version changes by deleting stale backup and
recreating from the new cli.js.

VER-01: Engine reads CLI version from package.json.
VER-02: Engine compares CLI version with translation map's _meta.cli_version.
VER-03: On version mismatch, engine deletes stale backup and re-creates from new cli.js.
VER-04: Version change reported with old->new version numbers.
"""

import json
import stat
from pathlib import Path

from scripts.i18n.io.backup import BackupManager


def get_cli_version(cli_dir: Path) -> str:
    """Read CLI version from package.json (VER-01).

    Args:
        cli_dir: Path to the Claude Code installation directory.

    Returns:
        Version string (e.g. "2.1.92"), or "unknown" if not determinable.
    """
    pkg = cli_dir / "package.json"
    if not pkg.exists():
        return "unknown"
    try:
        data = json.loads(pkg.read_text(encoding="utf-8"))
        return data.get("version", "unknown")
    except (json.JSONDecodeError, OSError):
        return "unknown"


def check_version_change(cli_dir: Path, map_meta: dict) -> dict:
    """Compare CLI version with translation map's _meta.cli_version (VER-02).

    Args:
        cli_dir: Path to the Claude Code installation directory.
        map_meta: The _meta dict from the translation map, expected to contain
                  a 'cli_version' key.

    Returns:
        dict with:
        - changed: True if versions differ (and current is not "unknown")
        - old: The version from the translation map
        - new: The current CLI version
    """
    current = get_cli_version(cli_dir)
    expected = map_meta.get("cli_version", "unknown")
    changed = current != expected and current != "unknown"
    return {
        "changed": changed,
        "old": expected,
        "new": current,
    }


def handle_version_change(cli_dir: Path, map_meta: dict) -> dict:
    """Handle version mismatch: delete stale backup, re-create (VER-03/04).

    If the CLI version has changed:
    1. Delete old backup file and hash file
    2. Re-create backup from current cli.js via BackupManager

    Args:
        cli_dir: Path to the Claude Code installation directory.
        map_meta: The _meta dict from the translation map.

    Returns:
        dict with:
        - changed: Whether version changed
        - old: Previous version (from map)
        - new: Current CLI version
        - backup_recreated: Whether backup was successfully recreated
        - error: Error message if backup recreation failed (only on failure)
    """
    check = check_version_change(cli_dir, map_meta)
    if not check["changed"]:
        check["backup_recreated"] = False
        return check

    # Version changed: delete old backup and hash
    bm = BackupManager(cli_dir)
    if bm.backup.exists():
        bm._make_writable(bm.backup)
        bm.backup.unlink()
    if bm.hash_file.exists():
        bm.hash_file.unlink()

    # Re-create from new cli.js (will fail if cli.js is already localized)
    result = bm.ensure_backup()
    check["backup_recreated"] = result["ok"]
    if not result["ok"]:
        check["error"] = result.get("error", "backup recreation failed")
        # If cli.js is localized, we can't create a clean backup.
        # User must reinstall Claude Code first.
        if result.get("error") == "source_not_pristine":
            check["error"] = (
                "CLI has been updated but current cli.js is already localized. "
                "Reinstall Claude Code to get pristine files."
            )
    return check
