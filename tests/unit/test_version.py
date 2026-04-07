"""Tests for version detection module (VER-01~04)."""

import json
import os
import stat
from pathlib import Path

import pytest

from scripts.i18n.core.version import get_cli_version, check_version_change, handle_version_change


class TestGetCliVersion:
    """Test get_cli_version function (VER-01)."""

    def test_get_version_success(self, mock_cli_dir):
        """Valid package.json returns correct version string."""
        result = get_cli_version(mock_cli_dir)
        assert result == "2.1.92"

    def test_get_version_custom(self, tmp_path):
        """Custom version in package.json is returned correctly."""
        cli_dir = tmp_path / "custom-cli"
        cli_dir.mkdir()
        pkg = cli_dir / "package.json"
        pkg.write_text(json.dumps({"name": "@anthropic-ai/claude-code", "version": "3.0.0"}), encoding="utf-8")
        result = get_cli_version(cli_dir)
        assert result == "3.0.0"

    def test_get_version_missing_pkg(self, tmp_path):
        """Missing package.json returns 'unknown'."""
        empty_dir = tmp_path / "empty"
        empty_dir.mkdir()
        result = get_cli_version(empty_dir)
        assert result == "unknown"

    def test_get_version_invalid_json(self, tmp_path):
        """Invalid JSON in package.json returns 'unknown'."""
        cli_dir = tmp_path / "bad-json"
        cli_dir.mkdir()
        pkg = cli_dir / "package.json"
        pkg.write_text("{invalid json", encoding="utf-8")
        result = get_cli_version(cli_dir)
        assert result == "unknown"

    def test_get_version_no_version_field(self, tmp_path):
        """package.json without version field returns 'unknown'."""
        cli_dir = tmp_path / "no-version"
        cli_dir.mkdir()
        pkg = cli_dir / "package.json"
        pkg.write_text(json.dumps({"name": "some-package"}), encoding="utf-8")
        result = get_cli_version(cli_dir)
        assert result == "unknown"


class TestCheckVersionChange:
    """Test check_version_change function (VER-02)."""

    def test_check_version_no_change(self, mock_cli_dir):
        """Same version returns changed=False."""
        map_meta = {"cli_version": "2.1.92"}
        result = check_version_change(mock_cli_dir, map_meta)
        assert result["changed"] is False
        assert result["old"] == "2.1.92"
        assert result["new"] == "2.1.92"

    def test_check_version_changed(self, mock_cli_dir):
        """Different version returns changed=True with old/new."""
        map_meta = {"cli_version": "1.0.0"}
        result = check_version_change(mock_cli_dir, map_meta)
        assert result["changed"] is True
        assert result["old"] == "1.0.0"
        assert result["new"] == "2.1.92"

    def test_check_version_unknown_cli(self, tmp_path):
        """CLI version 'unknown' returns changed=False even if different."""
        empty_dir = tmp_path / "no-pkg"
        empty_dir.mkdir()
        map_meta = {"cli_version": "2.1.92"}
        result = check_version_change(empty_dir, map_meta)
        assert result["changed"] is False
        assert result["new"] == "unknown"

    def test_check_version_missing_meta(self, mock_cli_dir):
        """Missing cli_version in meta defaults to 'unknown'."""
        result = check_version_change(mock_cli_dir, {})
        assert result["old"] == "unknown"
        assert result["new"] == "2.1.92"
        assert result["changed"] is True


class TestHandleVersionChange:
    """Test handle_version_change function (VER-03/04)."""

    def test_handle_version_no_change(self, mock_cli_dir):
        """No version change returns backup_recreated=False."""
        map_meta = {"cli_version": "2.1.92"}
        result = handle_version_change(mock_cli_dir, map_meta)
        assert result["changed"] is False
        assert result["backup_recreated"] is False

    def test_handle_version_changed(self, tmp_path):
        """Version changed deletes old backup, creates new one."""
        # Set up a CLI directory with cli.js and package.json
        cli_dir = tmp_path / "claude-code"
        cli_dir.mkdir()
        cli_js = cli_dir / "cli.js"
        cli_js.write_text("var x = 1;", encoding="utf-8")
        pkg = cli_dir / "package.json"
        pkg.write_text(json.dumps({"name": "@anthropic-ai/claude-code", "version": "3.0.0"}), encoding="utf-8")

        # Create old backup and hash files (simulating stale backup)
        backup = cli_dir / "cli.bak.en.js"
        backup.write_text("old content", encoding="utf-8")
        os.chmod(backup, stat.S_IRUSR | stat.S_IRGRP | stat.S_IROTH)  # read-only

        hash_file = cli_dir / "cli.backup.hash"
        hash_file.write_text("fakehash", encoding="utf-8")

        # Verify old files exist before handle
        assert backup.exists()
        assert hash_file.exists()

        map_meta = {"cli_version": "2.0.0"}
        result = handle_version_change(cli_dir, map_meta)

        assert result["changed"] is True
        assert result["old"] == "2.0.0"
        assert result["new"] == "3.0.0"
        assert result["backup_recreated"] is True

        # Verify backup was recreated (content should match cli.js now)
        new_backup = cli_dir / "cli.bak.en.js"
        assert new_backup.exists()
        assert new_backup.read_text(encoding="utf-8") == "var x = 1;"

    def test_handle_version_no_existing_backup(self, tmp_path):
        """Version changed with no existing backup creates new backup."""
        cli_dir = tmp_path / "claude-code"
        cli_dir.mkdir()
        cli_js = cli_dir / "cli.js"
        cli_js.write_text("var x = 1;", encoding="utf-8")
        pkg = cli_dir / "package.json"
        pkg.write_text(json.dumps({"name": "@anthropic-ai/claude-code", "version": "3.0.0"}), encoding="utf-8")

        # No backup files exist
        backup = cli_dir / "cli.bak.en.js"
        hash_file = cli_dir / "cli.backup.hash"
        assert not backup.exists()
        assert not hash_file.exists()

        map_meta = {"cli_version": "2.0.0"}
        result = handle_version_change(cli_dir, map_meta)

        assert result["changed"] is True
        assert result["backup_recreated"] is True

        # New backup was created
        assert backup.exists()
        assert backup.read_text(encoding="utf-8") == "var x = 1;"

    def test_handle_version_returns_old_and_new(self, mock_cli_dir):
        """Result always contains old, new, changed, backup_recreated keys."""
        map_meta = {"cli_version": "2.1.92"}
        result = handle_version_change(mock_cli_dir, map_meta)
        assert "old" in result
        assert "new" in result
        assert "changed" in result
        assert "backup_recreated" in result
