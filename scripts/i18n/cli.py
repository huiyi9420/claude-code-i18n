"""CLI framework for Claude Code i18n Engine.

Provides:
- output_json / output_error: JSON output utilities (stdout/stderr)
- get_cli_dir: CLI installation path resolution with error handling
- build_parser: argparse subcommand router
- cmd_status / cmd_version: Phase 1 commands
- main: Entry point called by engine.py
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Optional

from scripts.i18n.config.paths import find_cli_install_dir


def output_json(data: dict) -> None:
    """Output structured JSON to stdout.

    Uses ensure_ascii=False to preserve Chinese characters.
    """
    print(json.dumps(data, ensure_ascii=False, indent=2))


def output_error(message: str, hint: str = "", exit_code: int = 1) -> None:
    """Output error JSON to stderr and exit.

    Args:
        message: Error description.
        hint: Suggested resolution.
        exit_code: Non-zero exit code (default 1).
    """
    error_data = {"ok": False, "error": message}
    if hint:
        error_data["hint"] = hint
    print(json.dumps(error_data, ensure_ascii=False, indent=2), file=sys.stderr)
    sys.exit(exit_code)


def get_cli_dir() -> Optional[Path]:
    """Resolve CLI installation directory.

    Calls find_cli_install_dir() and handles the not_found case
    by outputting an error and exiting.

    Returns:
        Path to CLI installation directory.

    Raises:
        SystemExit: If CLI is not found.
    """
    cli_dir, method = find_cli_install_dir()
    if cli_dir is None:
        output_error(
            "Claude Code CLI not found",
            hint="Install Claude Code first: npm install -g @anthropic-ai/claude-code",
        )
    return cli_dir


def build_parser() -> argparse.ArgumentParser:
    """Build argparse parser with subcommands.

    Subcommands: status, restore, version, apply (skeleton), extract (skeleton).
    subparsers.required = True (Pitfall 7 from RESEARCH.md).
    """
    parser = argparse.ArgumentParser(
        prog='engine',
        description='Claude Code i18n Engine',
    )
    sub = parser.add_subparsers(dest='command', help='Available commands')
    sub.required = True

    # Phase 1: fully implemented commands
    sub.add_parser('status', help='Show current i18n status')
    sub.add_parser('restore', help='Restore original English CLI')
    sub.add_parser('version', help='Show CLI version')

    # Phase 2: skeleton commands
    sub.add_parser('apply', help='Apply Chinese localization')
    sub.add_parser('extract', help='Extract translatable strings')

    return parser


def cmd_status() -> None:
    """Show current i18n status as JSON.

    Output fields:
    - ok: bool
    - cli_found: bool
    - version: str (from package.json or "unknown")
    - backup_exists: bool
    - backup_valid: bool (if backup exists)
    - detection_method: str (how CLI was found)
    """
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
    from scripts.i18n.config.constants import BACKUP_NAME, HASH_NAME
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
        integrity = bm._verify_integrity()
        result["backup_valid"] = integrity
        if hash_path.exists():
            result["backup_hash"] = hash_path.read_text(encoding='utf-8').strip()[:16] + "..."

    output_json(result)


def cmd_version() -> None:
    """Show CLI version as JSON."""
    cli_dir, method = find_cli_install_dir()
    if cli_dir is None:
        output_json({"ok": False, "version": "unknown"})
        return

    version = "unknown"
    pkg_json = cli_dir / 'package.json'
    if pkg_json.exists():
        try:
            meta = json.loads(pkg_json.read_text(encoding='utf-8'))
            version = meta.get('version', 'unknown')
        except (json.JSONDecodeError, OSError):
            pass

    output_json({"ok": True, "version": version})


def cmd_apply() -> None:
    """Skeleton: Apply Chinese localization (Phase 2)."""
    output_error("not implemented in this version", exit_code=1)


def cmd_extract() -> None:
    """Skeleton: Extract translatable strings (Phase 2)."""
    output_error("not implemented in this version", exit_code=1)


def main() -> None:
    """Main entry point: parse args and route to subcommand."""
    parser = build_parser()
    args = parser.parse_args()

    # Import command handlers
    from scripts.i18n.commands.restore import cmd_restore

    commands = {
        'status': cmd_status,
        'restore': cmd_restore,
        'version': cmd_version,
        'apply': cmd_apply,
        'extract': cmd_extract,
    }

    cmd_func = commands.get(args.command)
    if cmd_func:
        cmd_func()
    else:
        parser.print_help()
        sys.exit(1)
