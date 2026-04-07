"""CLI framework for Claude Code i18n Engine.

Provides:
- output_json / output_error: JSON output utilities (stdout/stderr)
- get_cli_dir: CLI installation path resolution with error handling
- build_parser: argparse subcommand router
- cmd_version: Version command
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

    Subcommands: status, restore, version, apply, extract.
    subparsers.required = True (Pitfall 7 from RESEARCH.md).
    """
    parser = argparse.ArgumentParser(
        prog='engine',
        description='Claude Code i18n Engine',
    )
    sub = parser.add_subparsers(dest='command', help='Available commands')
    sub.required = True

    sub.add_parser('status', help='Show current i18n status')
    sub.add_parser('restore', help='Restore original English CLI')
    sub.add_parser('version', help='Show CLI version')
    sub.add_parser('apply', help='Apply Chinese localization')
    sub.add_parser('extract', help='Extract translatable strings')
    sub.add_parser('auto-update', help='One-click: detect, translate, apply')
    sub.add_parser('coverage', help='Show translation coverage report')
    sub.add_parser('validate', help='Validate translation quality')

    return parser


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


def main() -> None:
    """Main entry point: parse args and route to subcommand."""
    parser = build_parser()
    args = parser.parse_args()

    # Import command handlers
    from scripts.i18n.commands.restore import cmd_restore
    from scripts.i18n.commands.apply import cmd_apply
    from scripts.i18n.commands.extract import cmd_extract
    from scripts.i18n.commands.status import cmd_status
    from scripts.i18n.commands.auto_update import cmd_auto_update
    from scripts.i18n.commands.coverage import cmd_coverage
    from scripts.i18n.commands.validate import cmd_validate

    commands = {
        'status': cmd_status,
        'restore': cmd_restore,
        'version': cmd_version,
        'apply': cmd_apply,
        'extract': cmd_extract,
        'auto-update': cmd_auto_update,
        'coverage': cmd_coverage,
        'validate': cmd_validate,
    }

    cmd_func = commands.get(args.command)
    if cmd_func:
        cmd_func()
    else:
        parser.print_help()
        sys.exit(1)
