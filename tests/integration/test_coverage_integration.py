"""Integration tests: coverage command end-to-end.

Tests the coverage subcommand against a realistic mock environment,
verifying that apply + coverage workflow produces correct metrics.
"""

import hashlib
import json
import shutil
from pathlib import Path
from unittest.mock import patch

import pytest

FIXTURES_DIR = Path(__file__).parent.parent / 'fixtures'


@pytest.fixture
def coverage_env(tmp_path):
    """Set up integration environment for coverage tests.

    Creates:
    - mock CLI directory with cli.js + package.json
    - pristine backup (cli.bak.en.js) with hash
    - data directory with zh-CN.json translation map
    - skip-words.json
    """
    # Create mock CLI installation directory
    cli_dir = tmp_path / 'claude-code'
    cli_dir.mkdir()
    shutil.copy2(FIXTURES_DIR / 'sample_cli.js', cli_dir / 'cli.js')
    shutil.copy2(FIXTURES_DIR / 'sample_package.json', cli_dir / 'package.json')

    # Create pristine backup from sample cli.js
    cli_js = cli_dir / 'cli.js'
    backup = cli_dir / 'cli.bak.en.js'
    backup.write_text(cli_js.read_text(encoding='utf-8'), encoding='utf-8')

    # Create hash file for backup integrity
    h = hashlib.sha256(backup.read_bytes()).hexdigest()
    (cli_dir / 'cli.backup.hash').write_text(h, encoding='utf-8')

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


def _extract_json(output: str) -> dict:
    """Extract the JSON output from mixed stdout (table + JSON)."""
    idx = output.rfind('{\n  "ok"')
    if idx == -1:
        raise ValueError(f"No JSON found in output: {output[:200]}...")
    return json.loads(output[idx:])


class TestCoverageIntegration:
    """Coverage command integration tests."""

    def test_coverage_after_apply(self, coverage_env, capsys):
        """After apply, coverage should show translated > 0 and percentage > 0."""
        from scripts.i18n.commands.apply import cmd_apply
        from scripts.i18n.commands.coverage import cmd_coverage

        cli_dir = coverage_env["cli_dir"]
        map_dir = coverage_env["map_dir"]

        # Step 1: Apply translations first
        with patch('scripts.i18n.commands.apply.get_cli_dir', return_value=cli_dir), \
             patch('scripts.i18n.commands.apply.get_data_dir', return_value=map_dir), \
             patch('scripts.i18n.commands.apply.handle_version_change', return_value={"changed": False}), \
             patch('scripts.i18n.commands.apply.verify_syntax', return_value={"ok": True, "error": None}):
            cmd_apply()

        capsys.readouterr()  # consume apply output

        # Step 2: Run coverage command
        with patch('scripts.i18n.commands.coverage.get_cli_dir', return_value=cli_dir), \
             patch('scripts.i18n.commands.coverage.get_data_dir', return_value=map_dir):
            cmd_coverage()

        captured = capsys.readouterr()
        result = _extract_json(captured.out)

        assert result["ok"] is True
        assert result["translated"] > 0
        assert result["percentage"] != "0.0%"

        # Parse percentage string to verify > 0
        pct = float(result["percentage"].rstrip('%'))
        assert pct > 0

    def test_coverage_no_map(self, tmp_path, capsys):
        """Without translation map, coverage should output translated=0."""
        from scripts.i18n.commands.coverage import cmd_coverage

        cli_dir = tmp_path / 'claude-code'
        cli_dir.mkdir()
        (cli_dir / 'cli.js').write_text('// mock cli', encoding='utf-8')
        (cli_dir / 'package.json').write_text(
            json.dumps({"name": "@anthropic-ai/claude-code", "version": "1.0.0"}),
            encoding='utf-8'
        )

        data_dir = tmp_path / 'maps'
        data_dir.mkdir()
        # No zh-CN.json created

        with patch('scripts.i18n.commands.coverage.get_cli_dir', return_value=cli_dir), \
             patch('scripts.i18n.commands.coverage.get_data_dir', return_value=data_dir):
            cmd_coverage()

        captured = capsys.readouterr()
        result = _extract_json(captured.out)

        assert result["ok"] is True
        assert result["translated"] == 0

    def test_coverage_shows_categories(self, coverage_env, capsys):
        """Coverage output should include long/medium/short categories."""
        from scripts.i18n.commands.coverage import cmd_coverage

        cli_dir = coverage_env["cli_dir"]
        map_dir = coverage_env["map_dir"]

        with patch('scripts.i18n.commands.coverage.get_cli_dir', return_value=cli_dir), \
             patch('scripts.i18n.commands.coverage.get_data_dir', return_value=map_dir):
            cmd_coverage()

        captured = capsys.readouterr()
        result = _extract_json(captured.out)

        cats = result["categories"]
        assert "long" in cats
        assert "medium" in cats
        assert "short" in cats

        # Each category should have required fields
        for cat_name in ["long", "medium", "short"]:
            cat = cats[cat_name]
            assert "translated" in cat
            assert "untranslated" in cat
            assert "total" in cat
            assert "percentage" in cat

        # Verify table output contains category headers
        output = captured.out
        assert "长字符串" in output or "long" in output
        assert "中字符串" in output or "medium" in output
        assert "短字符串" in output or "short" in output

    def test_coverage_table_format(self, coverage_env, capsys):
        """Coverage table should contain separator lines and percentage markers."""
        from scripts.i18n.commands.coverage import cmd_coverage

        cli_dir = coverage_env["cli_dir"]
        map_dir = coverage_env["map_dir"]

        with patch('scripts.i18n.commands.coverage.get_cli_dir', return_value=cli_dir), \
             patch('scripts.i18n.commands.coverage.get_data_dir', return_value=map_dir):
            cmd_coverage()

        captured = capsys.readouterr()
        output = captured.out

        # Table should contain standard markers
        assert "翻译覆盖率报告" in output
        assert "%" in output
        assert "=" * 10 in output  # separator line
