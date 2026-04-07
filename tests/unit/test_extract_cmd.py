"""Tests for extract command: string extraction from pristine backup."""

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest


class TestExtractNoCLI:
    """Extract when CLI is not installed."""

    def test_extract_no_cli(self, capsys):
        """CLI not found should trigger output_error (sys.exit)."""
        from scripts.i18n.commands.extract import cmd_extract

        with patch('scripts.i18n.commands.extract.get_cli_dir') as mock_get:
            mock_get.side_effect = SystemExit(1)
            with pytest.raises(SystemExit) as exc_info:
                cmd_extract()
            assert exc_info.value.code == 1


class TestExtractReadsBackup:
    """Extract must read from pristine backup, not cli.js."""

    def test_extract_reads_backup(self, mock_cli_dir, tmp_path, capsys):
        """Extract should read from backup file, not cli.js."""
        from scripts.i18n.commands.extract import cmd_extract

        # Ensure backup exists via BackupManager
        from scripts.i18n.io.backup import BackupManager
        bm = BackupManager(mock_cli_dir)
        bm.ensure_backup()

        # No existing translation map
        with patch('scripts.i18n.commands.extract.get_cli_dir', return_value=mock_cli_dir):
            with patch('scripts.i18n.commands.extract.get_data_dir', return_value=tmp_path):
                with patch('scripts.i18n.commands.extract.scan_candidates') as mock_scan:
                    mock_scan.return_value = [
                        {"en": "Permission denied", "count": 1, "score": 3, "type": "strong"},
                    ]

                    cmd_extract()

        # Verify scan_candidates was called with backup content
        call_args = mock_scan.call_args
        assert call_args is not None
        # First arg is content read from backup
        content_arg = call_args[0][0]
        assert "Claude Code" in content_arg  # sample_cli.js content


class TestExtractOutputFormat:
    """Extract output JSON structure."""

    def test_extract_output_format(self, mock_cli_dir, tmp_path, capsys):
        """Extract output should have strong_count, weak_count, strong, weak arrays."""
        from scripts.i18n.commands.extract import cmd_extract
        from scripts.i18n.io.backup import BackupManager

        bm = BackupManager(mock_cli_dir)
        bm.ensure_backup()

        with patch('scripts.i18n.commands.extract.get_cli_dir', return_value=mock_cli_dir):
            with patch('scripts.i18n.commands.extract.get_data_dir', return_value=tmp_path):
                with patch('scripts.i18n.commands.extract.scan_candidates') as mock_scan:
                    mock_scan.return_value = [
                        {"en": "Permission denied", "count": 1, "score": 3, "type": "strong"},
                        {"en": "Loading text", "count": 2, "score": 1, "type": "weak"},
                    ]

                    cmd_extract()

        captured = capsys.readouterr()
        result = json.loads(captured.out)
        assert result["ok"] is True
        assert "strong_count" in result
        assert "weak_count" in result
        assert "strong" in result
        assert "weak" in result
        assert result["strong_count"] == 1
        assert result["weak_count"] == 1
        assert len(result["strong"]) == 1
        assert len(result["weak"]) == 1


class TestExtractExcludesExisting:
    """Extract should exclude already-translated strings."""

    def test_extract_excludes_existing(self, mock_cli_dir, tmp_path, capsys):
        """Already-translated strings should be passed to scan_candidates as 'existing'."""
        from scripts.i18n.commands.extract import cmd_extract
        from scripts.i18n.io.backup import BackupManager

        bm = BackupManager(mock_cli_dir)
        bm.ensure_backup()

        # Create a map with existing translation
        map_file = tmp_path / 'zh-CN.json'
        map_data = {
            "_meta": {},
            "translations": {"Permission denied": "权限被拒绝"},
        }
        map_file.write_text(json.dumps(map_data, ensure_ascii=False), encoding='utf-8')

        with patch('scripts.i18n.commands.extract.get_cli_dir', return_value=mock_cli_dir):
            with patch('scripts.i18n.commands.extract.get_data_dir', return_value=tmp_path):
                with patch('scripts.i18n.commands.extract.scan_candidates') as mock_scan:
                    mock_scan.return_value = []

                    cmd_extract()

        # Verify existing set was passed
        call_args = mock_scan.call_args
        existing_arg = call_args[0][1]  # second positional arg
        assert "Permission denied" in existing_arg
