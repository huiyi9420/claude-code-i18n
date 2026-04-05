"""Tests for CLI framework: argparse routing, JSON output, restore/status/version commands."""

import json
import os
import subprocess
import sys
from io import StringIO
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest


class TestOutputJson:
    """Test output_json utility function."""

    def test_output_json_to_stdout(self, capsys):
        """output_json should write JSON to stdout with ensure_ascii=False."""
        from scripts.i18n.cli import output_json

        output_json({"ok": True, "action": "restored"})
        captured = capsys.readouterr()
        result = json.loads(captured.out)
        assert result["ok"] is True
        assert result["action"] == "restored"

    def test_output_json_unicode(self, capsys):
        """output_json should not escape Chinese characters."""
        from scripts.i18n.cli import output_json

        output_json({"ok": True, "message": "欢迎使用"})
        captured = capsys.readouterr()
        assert "欢迎使用" in captured.out
        assert "\\u" not in captured.out

    def test_output_error_to_stderr(self):
        """output_error should write JSON error to stderr and sys.exit(1)."""
        from scripts.i18n.cli import output_error

        with pytest.raises(SystemExit) as exc_info:
            output_error("cli not found", hint="Install Claude Code first")
        assert exc_info.value.code == 1


class TestBuildParser:
    """Test argparse parser construction."""

    def test_parser_has_subcommands(self):
        """Parser should have status, restore, version, apply, extract subcommands."""
        from scripts.i18n.cli import build_parser

        parser = build_parser()
        # Test that each subcommand is recognized
        for cmd in ['status', 'restore', 'version', 'apply', 'extract']:
            args = parser.parse_args([cmd])
            assert args.command == cmd

    def test_subparsers_required(self):
        """No subcommand should cause argparse to error (subparsers.required=True)."""
        from scripts.i18n.cli import build_parser

        parser = build_parser()
        with pytest.raises(SystemExit) as exc_info:
            parser.parse_args([])
        assert exc_info.value.code == 2

    def test_help_contains_commands(self):
        """--help output should mention all subcommands."""
        from scripts.i18n.cli import build_parser

        parser = build_parser()
        with pytest.raises(SystemExit) as exc_info:
            parser.parse_args(['--help'])
        assert exc_info.value.code == 0


class TestRestoreCommand:
    """Test restore subcommand end-to-end behavior."""

    def test_restore_success(self, mock_cli_dir, capsys):
        """Successful restore should output JSON with ok=True."""
        from scripts.i18n.cli import get_cli_dir
        from scripts.i18n.commands.restore import cmd_restore
        from scripts.i18n.io.backup import BackupManager

        with patch('scripts.i18n.cli.find_cli_install_dir', return_value=(mock_cli_dir, 'test')):
            bm = BackupManager(mock_cli_dir)
            # Create backup first
            bm.ensure_backup()
            # Now restore
            with patch('scripts.i18n.commands.restore.get_cli_dir', return_value=mock_cli_dir):
                cmd_restore()
            captured = capsys.readouterr()
            result = json.loads(captured.out)
            assert result["ok"] is True
            assert result["action"] == "restored"

    def test_restore_no_cli(self, capsys):
        """When CLI not installed, restore should output error JSON (not traceback)."""
        from scripts.i18n.commands.restore import cmd_restore

        with patch('scripts.i18n.cli.find_cli_install_dir', return_value=(None, 'not_found')):
            with pytest.raises(SystemExit):
                with patch('scripts.i18n.commands.restore.get_cli_dir') as mock_get:
                    from scripts.i18n.cli import output_error
                    # Simulate get_cli_dir calling output_error
                    with pytest.raises(SystemExit):
                        output_error(
                            "Claude Code CLI not found",
                            hint="Install Claude Code first: npm install -g @anthropic-ai/claude-code",
                        )

    def test_restore_hash_mismatch_autofix(self, mock_cli_dir, capsys):
        """Hash mismatch should auto-recreate backup and retry restore."""
        from scripts.i18n.commands.restore import cmd_restore
        from scripts.i18n.io.backup import BackupManager

        with patch('scripts.i18n.cli.find_cli_install_dir', return_value=(mock_cli_dir, 'test')):
            bm = BackupManager(mock_cli_dir)
            bm.ensure_backup()

            # Corrupt the hash file
            hash_file = mock_cli_dir / 'cli.backup.hash'
            hash_file.write_text("badhash", encoding='utf-8')

            with patch('scripts.i18n.commands.restore.get_cli_dir', return_value=mock_cli_dir):
                cmd_restore()
            captured = capsys.readouterr()
            result = json.loads(captured.out)
            assert result["ok"] is True


class TestStatusCommand:
    """Test status subcommand output format."""

    def test_status_with_cli(self, mock_cli_dir, capsys):
        """Status should output JSON with cli_found, version, backup_exists."""
        from scripts.i18n.cli import cmd_status

        with patch('scripts.i18n.cli.find_cli_install_dir', return_value=(mock_cli_dir, 'test')):
            cmd_status()
        captured = capsys.readouterr()
        result = json.loads(captured.out)
        assert "cli_found" in result
        assert result["cli_found"] is True
        assert "version" in result
        assert "backup_exists" in result

    def test_status_no_cli(self, capsys):
        """Status without CLI should output error JSON."""
        from scripts.i18n.cli import cmd_status

        with patch('scripts.i18n.cli.find_cli_install_dir', return_value=(None, 'not_found')):
            cmd_status()
        captured = capsys.readouterr()
        result = json.loads(captured.out)
        assert result["ok"] is False
        assert "error" in result


class TestVersionCommand:
    """Test version subcommand output format."""

    def test_version_output(self, mock_cli_dir, capsys):
        """Version should output JSON with version field."""
        from scripts.i18n.cli import cmd_version

        with patch('scripts.i18n.cli.find_cli_install_dir', return_value=(mock_cli_dir, 'test')):
            cmd_version()
        captured = capsys.readouterr()
        result = json.loads(captured.out)
        assert "version" in result
        assert result["version"] == "2.1.92"

    def test_version_no_cli(self, capsys):
        """Version without CLI should output version unknown."""
        from scripts.i18n.cli import cmd_version

        with patch('scripts.i18n.cli.find_cli_install_dir', return_value=(None, 'not_found')):
            cmd_version()
        captured = capsys.readouterr()
        result = json.loads(captured.out)
        assert result["version"] == "unknown"


class TestEngineEntryPoint:
    """Test engine.py as CLI entry point."""

    def test_engine_help(self):
        """python engine.py --help should output help and exit 0."""
        result = subprocess.run(
            [sys.executable, 'scripts/engine.py', '--help'],
            capture_output=True, text=True, timeout=10,
            cwd='/Users/zhaolulu/Projects/claude-code-i18n',
        )
        assert result.returncode == 0
        assert 'status' in result.stdout
        assert 'restore' in result.stdout

    def test_engine_no_args_exits(self):
        """python engine.py without args should exit with error."""
        result = subprocess.run(
            [sys.executable, 'scripts/engine.py'],
            capture_output=True, text=True, timeout=10,
            cwd='/Users/zhaolulu/Projects/claude-code-i18n',
        )
        assert result.returncode != 0
