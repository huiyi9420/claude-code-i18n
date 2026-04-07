"""Tests for auto-update command."""

import json
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from scripts.i18n.commands.auto_update import cmd_auto_update

# find_cli_install_dir is imported by cli.py, so patch at that level
_FIND_CLI_PATCH = "scripts.i18n.cli.find_cli_install_dir"
_VERIFY_PATCH = "scripts.i18n.commands.auto_update.verify_syntax"


def _make_cli_env(tmp_path: Path) -> dict:
    """Create a minimal CLI installation environment for testing."""
    cli_dir = tmp_path / "cli-install"
    cli_dir.mkdir()
    (cli_dir / "cli.js").write_text(
        'console.log("Hello World");console.log("Loading");', encoding="utf-8"
    )
    (cli_dir / "package.json").write_text(
        json.dumps({"name": "@anthropic-ai/claude-code", "version": "2.1.92"}),
        encoding="utf-8",
    )
    return {"cli_dir": cli_dir}


class TestAutoUpdateNoCLI:
    """Auto-update with no CLI installed."""

    @patch(_FIND_CLI_PATCH, return_value=(None, "not_found"))
    def test_no_cli_found(self, mock_find):
        """Should exit with error when CLI not found."""
        with pytest.raises(SystemExit):
            cmd_auto_update()


class TestAutoUpdateSuccess:
    """Auto-update happy path."""

    @patch(_VERIFY_PATCH, return_value={"ok": True})
    @patch(_FIND_CLI_PATCH)
    def test_fresh_auto_update(self, mock_find, mock_verify, tmp_path, capsys):
        """Fresh auto-update should extract, auto-translate, apply."""
        env = _make_cli_env(tmp_path)
        mock_find.return_value = (env["cli_dir"], "test")

        cmd_auto_update()
        output = json.loads(capsys.readouterr().out)

        assert output["ok"] is True
        assert output["action"] == "auto-update"
        assert "version" in output
        assert "extraction" in output
        assert "translation" in output
        assert "apply" in output
        assert "verification" in output

    @patch(_VERIFY_PATCH, return_value={"ok": True})
    @patch(_FIND_CLI_PATCH)
    def test_with_existing_map(self, mock_find, mock_verify, tmp_path, capsys):
        """Auto-update with existing translation map should merge."""
        env = _make_cli_env(tmp_path)
        mock_find.return_value = (env["cli_dir"], "test")

        # Create existing translation map in scripts/ dir
        scripts_dir = tmp_path / "scripts"
        scripts_dir.mkdir()
        map_data = {
            "meta": {"version": "1.0.0", "cli_version": "2.1.91"},
            "translations": {"Hello World": "你好世界"},
        }
        map_path = scripts_dir / "zh-CN.json"
        map_path.write_text(json.dumps(map_data, ensure_ascii=False), encoding="utf-8")

        with patch("scripts.i18n.commands.auto_update.get_data_dir", return_value=scripts_dir):
            cmd_auto_update()
            output = json.loads(capsys.readouterr().out)

        assert output["ok"] is True
        assert output["translation"]["total_entries"] >= 1


class TestAutoUpdateRollback:
    """Auto-update rollback on syntax failure."""

    @patch(_VERIFY_PATCH, return_value={"ok": False, "error": "SyntaxError"})
    @patch(_FIND_CLI_PATCH)
    def test_rollback_on_syntax_failure(self, mock_find, mock_verify, tmp_path, capsys):
        """Should rollback when syntax verification fails."""
        env = _make_cli_env(tmp_path)
        mock_find.return_value = (env["cli_dir"], "test")

        cmd_auto_update()
        output = json.loads(capsys.readouterr().out)

        assert output["ok"] is False
        assert output.get("rollback") is True


class TestAutoUpdateBackupFailure:
    """Auto-update with backup creation failure."""

    @patch("scripts.i18n.commands.auto_update.BackupManager")
    @patch(_FIND_CLI_PATCH)
    def test_backup_failure(self, mock_find, mock_bm_class, tmp_path):
        """Should exit with error when backup creation fails."""
        env = _make_cli_env(tmp_path)
        mock_find.return_value = (env["cli_dir"], "test")

        mock_bm = MagicMock()
        mock_bm.ensure_backup.return_value = {"ok": False, "error": "disk full"}
        mock_bm_class.return_value = mock_bm

        with pytest.raises(SystemExit):
            cmd_auto_update()


class TestAutoUpdateJSONFormat:
    """Verify output JSON structure."""

    @patch(_VERIFY_PATCH, return_value={"ok": True})
    @patch(_FIND_CLI_PATCH)
    def test_output_has_required_fields(self, mock_find, mock_verify, tmp_path, capsys):
        """Output JSON should contain all required top-level fields."""
        env = _make_cli_env(tmp_path)
        mock_find.return_value = (env["cli_dir"], "test")

        cmd_auto_update()
        output = json.loads(capsys.readouterr().out)

        required = [
            "ok", "action", "version", "extraction",
            "translation", "apply", "verification", "review_items",
        ]
        for field in required:
            assert field in output, f"Missing field: {field}"

    @patch(_VERIFY_PATCH, return_value={"ok": True})
    @patch(_FIND_CLI_PATCH)
    def test_version_structure(self, mock_find, mock_verify, tmp_path, capsys):
        """Version field should have old/new/changed."""
        env = _make_cli_env(tmp_path)
        mock_find.return_value = (env["cli_dir"], "test")

        cmd_auto_update()
        output = json.loads(capsys.readouterr().out)

        assert "old" in output["version"]
        assert "new" in output["version"]
        assert "changed" in output["version"]

    @patch(_VERIFY_PATCH, return_value={"ok": True})
    @patch(_FIND_CLI_PATCH)
    def test_extraction_structure(self, mock_find, mock_verify, tmp_path, capsys):
        """Extraction field should have all diff categories."""
        env = _make_cli_env(tmp_path)
        mock_find.return_value = (env["cli_dir"], "test")

        cmd_auto_update()
        output = json.loads(capsys.readouterr().out)

        ext = output["extraction"]
        for key in ["candidates_found", "new", "changed", "removed"]:
            assert key in ext, f"Missing extraction key: {key}"
