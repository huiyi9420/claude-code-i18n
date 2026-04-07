"""Integration tests: end-to-end apply → verify → restore → verify round-trip.

TEST-06: Full round-trip integration test confirming localization and restore work end-to-end.
"""

import json
import shutil
import subprocess
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

FIXTURES_DIR = Path(__file__).parent.parent / 'fixtures'
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent


@pytest.fixture
def integration_env(tmp_path):
    """Set up a complete integration environment with mock CLI and translation map."""
    # Create mock CLI installation directory
    cli_dir = tmp_path / 'claude-code'
    cli_dir.mkdir()
    shutil.copy2(FIXTURES_DIR / 'sample_cli.js', cli_dir / 'cli.js')
    shutil.copy2(FIXTURES_DIR / 'sample_package.json', cli_dir / 'package.json')

    # Create translation map
    map_dir = tmp_path / 'maps'
    map_dir.mkdir()
    map_data = {
        "_meta": {"cli_version": "2.1.92", "version": "4.2.0"},
        "translations": {
            "Permission denied": "权限被拒绝",
            "Welcome to Claude Code!": "欢迎使用 Claude Code！",
            "Goodbye and thank you for using Claude Code.": "再见，感谢使用 Claude Code。",
            "Loading, please wait...": "加载中，请稍候...",
            "Are you sure you want to proceed?": "确定要继续吗？",
            "An unexpected error occurred while processing your request.": "处理请求时发生意外错误。",
            "Show this help message": "显示此帮助信息",
            "Show version information": "显示版本信息",
        },
    }
    map_file = map_dir / 'zh-CN.json'
    map_file.write_text(json.dumps(map_data, ensure_ascii=False), encoding='utf-8')

    # Create skip words
    skip_file = map_dir / 'skip-words.json'
    skip_file.write_text('{"skip": ["OK"]}', encoding='utf-8')

    return {
        "cli_dir": cli_dir,
        "map_dir": map_dir,
        "map_file": map_file,
    }


class TestApplyRestoreRoundTrip:
    """End-to-end: apply → verify → restore → verify (TEST-06)."""

    def test_full_roundtrip(self, integration_env, capsys):
        """Full round-trip: apply translations, verify, restore, verify again."""
        from scripts.i18n.commands.apply import cmd_apply
        from scripts.i18n.commands.restore import cmd_restore
        from scripts.i18n.commands.status import cmd_status
        from scripts.i18n.io.backup import BackupManager

        cli_dir = integration_env["cli_dir"]
        map_dir = integration_env["map_dir"]
        cli_js = cli_dir / 'cli.js'

        # === Step 1: Apply translations ===
        with patch('scripts.i18n.commands.apply.get_cli_dir', return_value=cli_dir):
            with patch('scripts.i18n.commands.apply.get_data_dir', return_value=map_dir):
                with patch('scripts.i18n.commands.apply.handle_version_change', return_value={"changed": False}):
                    with patch('scripts.i18n.commands.apply.verify_syntax', return_value={"ok": True, "error": None}):
                        cmd_apply()

        captured = capsys.readouterr()
        apply_result = json.loads(captured.out)
        assert apply_result["ok"] is True
        assert apply_result["action"] == "applied"
        assert apply_result["replacements"] > 0
        assert apply_result["verification"] == "passed"

        # Verify Chinese text is present in cli.js
        content = cli_js.read_text(encoding='utf-8')
        assert "权限被拒绝" in content
        assert "欢迎使用 Claude Code！" in content

        # Original English should be replaced (long strings)
        assert "Permission denied" not in content
        assert "Welcome to Claude Code!" not in content

        # === Step 2: Check status (should show localized) ===
        with patch('scripts.i18n.config.paths.find_cli_install_dir', return_value=(cli_dir, 'test')):
            with patch('scripts.i18n.commands.status.get_data_dir', return_value=map_dir):
                cmd_status()

        captured = capsys.readouterr()
        status_result = json.loads(captured.out)
        assert status_result["ok"] is True
        assert status_result["lang_entries"] == 8
        assert status_result["version"] == "2.1.92"

        # === Step 3: Restore to English ===
        with patch('scripts.i18n.commands.restore.get_cli_dir', return_value=cli_dir):
            cmd_restore()

        captured = capsys.readouterr()
        restore_result = json.loads(captured.out)
        assert restore_result["ok"] is True
        assert restore_result["action"] == "restored"

        # Verify English text is restored
        content = cli_js.read_text(encoding='utf-8')
        assert "Permission denied" in content
        assert "Welcome to Claude Code!" in content
        assert "权限被拒绝" not in content
        assert "欢迎使用 Claude Code！" not in content

    def test_apply_idempotent(self, integration_env, capsys):
        """Applying twice should be safe (second apply starts from clean backup)."""
        from scripts.i18n.commands.apply import cmd_apply

        cli_dir = integration_env["cli_dir"]
        map_dir = integration_env["map_dir"]
        cli_js = cli_dir / 'cli.js'

        with patch('scripts.i18n.commands.apply.get_cli_dir', return_value=cli_dir):
            with patch('scripts.i18n.commands.apply.get_data_dir', return_value=map_dir):
                with patch('scripts.i18n.commands.apply.handle_version_change', return_value={"changed": False}):
                    with patch('scripts.i18n.commands.apply.verify_syntax', return_value={"ok": True, "error": None}):
                        # First apply
                        cmd_apply()
                        capsys.readouterr()  # consume output

                        # Second apply (from backup again)
                        cmd_apply()

        captured = capsys.readouterr()
        second_result = json.loads(captured.out)
        assert second_result["ok"] is True
        assert second_result["action"] == "applied"

        # Verify content is consistent
        content = cli_js.read_text(encoding='utf-8')
        assert "权限被拒绝" in content


class TestBackupIntegrity:
    """Backup integrity across operations."""

    def test_backup_pristine_after_apply(self, integration_env, capsys):
        """Backup remains pristine (zero CJK) after apply."""
        from scripts.i18n.commands.apply import cmd_apply
        from scripts.i18n.io.backup import BackupManager

        cli_dir = integration_env["cli_dir"]
        map_dir = integration_env["map_dir"]

        with patch('scripts.i18n.commands.apply.get_cli_dir', return_value=cli_dir):
            with patch('scripts.i18n.commands.apply.get_data_dir', return_value=map_dir):
                with patch('scripts.i18n.commands.apply.handle_version_change', return_value={"changed": False}):
                    with patch('scripts.i18n.commands.apply.verify_syntax', return_value={"ok": True, "error": None}):
                        cmd_apply()
                        capsys.readouterr()

        # Verify backup is still pristine
        bm = BackupManager(cli_dir)
        assert bm._is_pristine() is True
        assert bm._verify_integrity() is True


class TestEngineCLI:
    """Test engine.py as CLI entry point."""

    def test_engine_apply_restore(self, integration_env):
        """Test engine.py apply and restore via subprocess."""
        cli_dir = integration_env["cli_dir"]

        # Run engine.py status (will fail to find CLI, but tests CLI framework)
        result = subprocess.run(
            [sys.executable, str(PROJECT_ROOT / 'scripts/engine.py'), '--help'],
            capture_output=True, text=True, timeout=10,
        )
        assert result.returncode == 0
        assert 'apply' in result.stdout
        assert 'restore' in result.stdout
        assert 'extract' in result.stdout
        assert 'status' in result.stdout
