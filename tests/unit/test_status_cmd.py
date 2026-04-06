"""Tests for enhanced status command: localization detection and map info."""

import json
from pathlib import Path
from unittest.mock import patch

import pytest


class TestStatusEnhancedFields:
    """Status should include localization detection and translation map info."""

    def test_status_enhanced_fields(self, mock_cli_dir, tmp_path, capsys):
        """Enhanced status should include localized, lang_entries, lang_version."""
        from scripts.i18n.commands.status import cmd_status

        # Create translation map in tmp_path
        map_file = tmp_path / 'zh-CN.json'
        map_data = {
            "_meta": {"cli_version": "2.1.92"},
            "translations": {
                "Permission denied": "权限被拒绝",
                "OK": "确定",
            },
        }
        map_file.write_text(json.dumps(map_data, ensure_ascii=False), encoding='utf-8')

        with patch('scripts.i18n.config.paths.find_cli_install_dir', return_value=(mock_cli_dir, 'test')):
            with patch('scripts.i18n.commands.status._SCRIPTS_DIR', tmp_path):
                cmd_status()

        captured = capsys.readouterr()
        result = json.loads(captured.out)
        assert result["ok"] is True
        assert "localized" in result
        assert result["localized"] is False  # sample_cli.js has no Chinese
        assert result["lang_entries"] == 2
        assert result["lang_version"] == "2.1.92"

    def test_status_localized_detected(self, mock_cli_dir, tmp_path, capsys):
        """Status should detect localized cli.js (Chinese markers present)."""
        from scripts.i18n.commands.status import cmd_status

        # Add Chinese markers to cli.js
        cli_js = mock_cli_dir / 'cli.js'
        original = cli_js.read_text(encoding='utf-8')
        cli_js.write_text(original + '绕过权限;规划模式;自动模式;接受编辑;', encoding='utf-8')

        map_file = tmp_path / 'zh-CN.json'
        map_data = {"_meta": {}, "translations": {}}
        map_file.write_text(json.dumps(map_data), encoding='utf-8')

        with patch('scripts.i18n.config.paths.find_cli_install_dir', return_value=(mock_cli_dir, 'test')):
            with patch('scripts.i18n.commands.status._SCRIPTS_DIR', tmp_path):
                cmd_status()

        captured = capsys.readouterr()
        result = json.loads(captured.out)
        assert result["localized"] is True


class TestStatusNoCLI:
    """Status when CLI is not installed."""

    def test_status_no_cli(self, capsys):
        """CLI not found should output ok=False with hint."""
        from scripts.i18n.commands.status import cmd_status

        with patch('scripts.i18n.config.paths.find_cli_install_dir', return_value=(None, 'not_found')):
            cmd_status()

        captured = capsys.readouterr()
        result = json.loads(captured.out)
        assert result["ok"] is False
        assert result["cli_found"] is False
        assert "error" in result
        assert "hint" in result


class TestStatusBackupInfo:
    """Status should report backup integrity."""

    def test_status_with_valid_backup(self, mock_cli_dir, tmp_path, capsys):
        """Status should report backup_valid when backup exists and is valid."""
        from scripts.i18n.commands.status import cmd_status
        from scripts.i18n.io.backup import BackupManager

        bm = BackupManager(mock_cli_dir)
        bm.ensure_backup()

        map_file = tmp_path / 'zh-CN.json'
        map_data = {"_meta": {}, "translations": {}}
        map_file.write_text(json.dumps(map_data), encoding='utf-8')

        with patch('scripts.i18n.config.paths.find_cli_install_dir', return_value=(mock_cli_dir, 'test')):
            with patch('scripts.i18n.commands.status._SCRIPTS_DIR', tmp_path):
                cmd_status()

        captured = capsys.readouterr()
        result = json.loads(captured.out)
        assert result["backup_exists"] is True
        assert result["backup_valid"] is True
        assert "backup_hash" in result
