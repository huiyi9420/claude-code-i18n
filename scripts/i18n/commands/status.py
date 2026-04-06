"""Enhanced status command with localization detection and map info.

STATUS-01: Outputs JSON with version, localized state, entry count, backup integrity.
STATUS-03: All commands output JSON format for script integration.
"""

import json
from pathlib import Path

from scripts.i18n.cli import output_json
from scripts.i18n.config.constants import MAP_FILE, BACKUP_NAME, HASH_NAME
from scripts.i18n.io.translation_map import load_translation_map

# Default paths for translation data (scripts/ directory)
_SCRIPTS_DIR = Path(__file__).resolve().parent.parent.parent.parent  # scripts/

# Markers to detect localization (Chinese strings present in cli.js)
_LOCALIZATION_MARKERS = ["绕过权限", "规划模式", "自动模式", "接受编辑"]


def cmd_status() -> None:
    """Show enhanced i18n status as JSON.

    Output fields:
    - ok: bool
    - cli_found: bool
    - version: str (from package.json)
    - backup_exists: bool
    - backup_valid: bool (if backup exists)
    - localized: bool (True if Chinese markers detected in cli.js)
    - lang_entries: int (translation map entry count)
    - lang_version: str (_meta.cli_version from translation map)
    - detection_method: str (how CLI was found)
    """
    from scripts.i18n.config.paths import find_cli_install_dir

    cli_dir, method = find_cli_install_dir()
    if cli_dir is None:
        output_json({
            "ok": False,
            "cli_found": False,
            "version": "unknown",
            "backup_exists": False,
            "error": "Claude Code CLI not found",
            "hint": "Install Claude Code first: npm install -g @anthropic-ai/claude-code",
        })
        return

    # Read version from package.json
    version = "unknown"
    pkg_json = cli_dir / 'package.json'
    if pkg_json.exists():
        try:
            meta = json.loads(pkg_json.read_text(encoding='utf-8'))
            version = meta.get('version', 'unknown')
        except (json.JSONDecodeError, OSError):
            pass

    # Check backup status
    backup_path = cli_dir / BACKUP_NAME
    hash_path = cli_dir / HASH_NAME
    backup_exists = backup_path.exists()

    result = {
        "ok": True,
        "cli_found": True,
        "version": version,
        "backup_exists": backup_exists,
        "cli_dir": str(cli_dir),
        "detection_method": method,
    }

    if backup_exists:
        from scripts.i18n.io.backup import BackupManager
        bm = BackupManager(cli_dir)
        result["backup_valid"] = bm._verify_integrity()
        if hash_path.exists():
            result["backup_hash"] = hash_path.read_text(encoding='utf-8').strip()[:16] + "..."

    # Check localization state (STATUS-01)
    cli_js = cli_dir / 'cli.js'
    if cli_js.exists():
        try:
            content = cli_js.read_text(encoding='utf-8')
            result["localized"] = sum(
                1 for m in _LOCALIZATION_MARKERS if m in content
            ) >= 2
        except OSError:
            result["localized"] = False

    # Translation map info (STATUS-01)
    map_path = _SCRIPTS_DIR / MAP_FILE
    if map_path.exists():
        try:
            map_data = load_translation_map(map_path)
            result["lang_entries"] = len(map_data["translations"])
            result["lang_version"] = map_data["meta"].get("cli_version", "")
        except (json.JSONDecodeError, OSError):
            result["lang_entries"] = 0

    output_json(result)
