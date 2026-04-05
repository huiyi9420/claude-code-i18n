"""Tests for syntax verification module (APPLY-07, APPLY-08)."""

import subprocess
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from scripts.i18n.core.verifier import verify_syntax


class TestVerifySyntax:
    """Test verify_syntax function."""

    def test_verify_valid_js(self, tmp_path):
        """Valid JS file returns ok=True, error=None."""
        js_file = tmp_path / "valid.js"
        js_file.write_text("var x = 1;", encoding="utf-8")
        result = verify_syntax(js_file)
        assert result["ok"] is True
        assert result["error"] is None

    def test_verify_invalid_js(self, tmp_path):
        """Invalid JS file returns ok=False with error message."""
        js_file = tmp_path / "invalid.js"
        js_file.write_text("var x = ;", encoding="utf-8")
        result = verify_syntax(js_file)
        assert result["ok"] is False
        assert result["error"]  # non-empty error string
        assert isinstance(result["error"], str)

    def test_verify_missing_file(self, tmp_path):
        """Non-existent path returns ok=False with file-not-found error."""
        missing = tmp_path / "nonexistent.js"
        result = verify_syntax(missing)
        assert result["ok"] is False
        assert "not found" in result["error"].lower()

    def test_verify_timeout(self, tmp_path):
        """TimeoutExpired returns ok=False with timeout error message."""
        js_file = tmp_path / "slow.js"
        js_file.write_text("var x = 1;", encoding="utf-8")

        with patch("subprocess.run", side_effect=subprocess.TimeoutExpired(cmd="node", timeout=1)):
            result = verify_syntax(js_file, timeout=1)

        assert result["ok"] is False
        assert "timed out" in result["error"].lower()

    def test_verify_node_not_found(self, tmp_path):
        """FileNotFoundError (node not installed) returns ok=False."""
        js_file = tmp_path / "test.js"
        js_file.write_text("var x = 1;", encoding="utf-8")

        with patch("subprocess.run", side_effect=FileNotFoundError):
            result = verify_syntax(js_file)

        assert result["ok"] is False
        assert "node" in result["error"].lower()

    def test_verify_returns_dict(self, tmp_path):
        """verify_syntax always returns a dict with 'ok' and 'error' keys."""
        js_file = tmp_path / "test.js"
        js_file.write_text("var x = 1;", encoding="utf-8")
        result = verify_syntax(js_file)
        assert "ok" in result
        assert "error" in result

    def test_verify_custom_timeout(self, tmp_path):
        """Custom timeout value is passed to subprocess.run."""
        js_file = tmp_path / "test.js"
        js_file.write_text("var x = 1;", encoding="utf-8")

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stderr="")
            verify_syntax(js_file, timeout=30)
            _, kwargs = mock_run.call_args
            assert kwargs["timeout"] == 30
