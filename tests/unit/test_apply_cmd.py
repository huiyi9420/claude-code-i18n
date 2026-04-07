"""Tests for apply command: full orchestration flow with mocks."""

import json
from pathlib import Path
from unittest.mock import MagicMock, patch, call

import pytest


@pytest.fixture
def mock_apply_deps(mock_cli_dir, tmp_path):
    """Set up mocked dependencies for apply command tests."""
    # Create a fake translation map
    map_file = tmp_path / 'zh-CN.json'
    map_data = {
        "_meta": {"cli_version": "2.1.92"},
        "translations": {
            "Permission denied": "权限被拒绝",
            "Welcome to Claude Code!": "欢迎使用 Claude Code！",
        },
    }
    map_file.write_text(json.dumps(map_data, ensure_ascii=False), encoding='utf-8')

    # Create a fake skip words file
    skip_file = tmp_path / 'skip-words.json'
    skip_data = {"skip": ["OK"]}
    skip_file.write_text(json.dumps(skip_data), encoding='utf-8')

    return {
        "cli_dir": mock_cli_dir,
        "map_file": map_file,
        "skip_file": skip_file,
    }


class TestApplyNoCLI:
    """Apply when CLI is not installed."""

    def test_apply_no_cli(self, capsys):
        """CLI not found should trigger output_error (sys.exit)."""
        from scripts.i18n.commands.apply import cmd_apply

        with patch('scripts.i18n.commands.apply.get_cli_dir') as mock_get:
            mock_get.side_effect = SystemExit(1)
            with pytest.raises(SystemExit) as exc_info:
                cmd_apply()
            assert exc_info.value.code == 1


class TestApplyNoMap:
    """Apply when translation map is missing."""

    def test_apply_no_map(self, mock_cli_dir, tmp_path, capsys):
        """Missing translation map should output error."""
        from scripts.i18n.commands.apply import cmd_apply

        # Patch _SCRIPTS_DIR to point to tmp_path (no zh-CN.json there)
        with patch('scripts.i18n.commands.apply.get_cli_dir', return_value=mock_cli_dir):
            with patch('scripts.i18n.commands.apply.get_data_dir', return_value=tmp_path):
                with pytest.raises(SystemExit) as exc_info:
                    cmd_apply()
                assert exc_info.value.code == 1


class TestApplySuccessFlow:
    """Apply command successful orchestration."""

    def test_apply_success(self, mock_cli_dir, tmp_path, capsys):
        """Successful apply should output JSON with ok=True and replacement stats."""
        from scripts.i18n.commands.apply import cmd_apply

        # Create translation map in tmp_path
        map_file = tmp_path / 'zh-CN.json'
        map_data = {
            "_meta": {"cli_version": "2.1.92"},
            "translations": {
                "Permission denied": "权限被拒绝",
                "Welcome to Claude Code!": "欢迎使用 Claude Code！",
            },
        }
        map_file.write_text(json.dumps(map_data, ensure_ascii=False), encoding='utf-8')

        # Create skip words
        skip_file = tmp_path / 'skip-words.json'
        skip_file.write_text('{"skip": []}', encoding='utf-8')

        with patch('scripts.i18n.commands.apply.get_cli_dir', return_value=mock_cli_dir):
            with patch('scripts.i18n.commands.apply.get_data_dir', return_value=tmp_path):
                with patch('scripts.i18n.commands.apply.handle_version_change') as mock_ver:
                    mock_ver.return_value = {"changed": False, "old": "2.1.92", "new": "2.1.92"}

                    with patch('scripts.i18n.commands.apply.verify_syntax') as mock_verify:
                        mock_verify.return_value = {"ok": True, "error": None}

                        cmd_apply()

        captured = capsys.readouterr()
        result = json.loads(captured.out)
        assert result["ok"] is True
        assert result["action"] == "applied"
        assert "replacements" in result
        assert "stats" in result
        assert "entries" in result
        assert result["verification"] == "passed"


class TestApplyRollbackOnVerifyFail:
    """Apply rollback when syntax verification fails."""

    def test_apply_rollback(self, mock_cli_dir, tmp_path, capsys):
        """Syntax failure should trigger rollback and output error JSON."""
        from scripts.i18n.commands.apply import cmd_apply

        # Create translation map
        map_file = tmp_path / 'zh-CN.json'
        map_data = {
            "_meta": {"cli_version": "2.1.92"},
            "translations": {"Permission denied": "权限被拒绝"},
        }
        map_file.write_text(json.dumps(map_data, ensure_ascii=False), encoding='utf-8')
        skip_file = tmp_path / 'skip-words.json'
        skip_file.write_text('{"skip": []}', encoding='utf-8')

        with patch('scripts.i18n.commands.apply.get_cli_dir', return_value=mock_cli_dir):
            with patch('scripts.i18n.commands.apply.get_data_dir', return_value=tmp_path):
                with patch('scripts.i18n.commands.apply.handle_version_change') as mock_ver:
                    mock_ver.return_value = {"changed": False}

                    with patch('scripts.i18n.commands.apply.verify_syntax') as mock_verify:
                        mock_verify.return_value = {"ok": False, "error": "SyntaxError: unexpected token"}

                        with patch('scripts.i18n.commands.apply.BackupManager') as MockBM:
                            mock_bm = MagicMock()
                            mock_bm.ensure_backup.return_value = {"ok": True}
                            mock_bm.restore.return_value = {"ok": True, "action": "restored"}
                            MockBM.return_value = mock_bm

                            cmd_apply()

        captured = capsys.readouterr()
        result = json.loads(captured.out)
        assert result["ok"] is False
        assert "Syntax validation failed" in result["error"]
        assert result["rollback"] is True
        # Restore should be called twice: once for clean state, once for rollback
        assert mock_bm.restore.call_count == 2


class TestApplyVersionChange:
    """Apply with version mismatch handling."""

    def test_apply_version_change(self, mock_cli_dir, tmp_path, capsys):
        """Version mismatch should trigger backup recreation."""
        from scripts.i18n.commands.apply import cmd_apply

        map_file = tmp_path / 'zh-CN.json'
        map_data = {
            "_meta": {"cli_version": "2.1.90"},
            "translations": {"Permission denied": "权限被拒绝"},
        }
        map_file.write_text(json.dumps(map_data, ensure_ascii=False), encoding='utf-8')
        skip_file = tmp_path / 'skip-words.json'
        skip_file.write_text('{"skip": []}', encoding='utf-8')

        with patch('scripts.i18n.commands.apply.get_cli_dir', return_value=mock_cli_dir):
            with patch('scripts.i18n.commands.apply.get_data_dir', return_value=tmp_path):
                with patch('scripts.i18n.commands.apply.handle_version_change') as mock_ver:
                    mock_ver.return_value = {"changed": True, "old": "2.1.90", "new": "2.1.92", "backup_recreated": True}

                    with patch('scripts.i18n.commands.apply.verify_syntax') as mock_verify:
                        mock_verify.return_value = {"ok": True, "error": None}

                        cmd_apply()

        captured = capsys.readouterr()
        result = json.loads(captured.out)
        assert result["ok"] is True
        assert result["action"] == "applied"
