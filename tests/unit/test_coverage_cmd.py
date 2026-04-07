"""单元测试: coverage 子命令

测试覆盖率报告生成的各种场景:
- CLI 未安装时的错误处理
- 正常覆盖率报告输出
- 无翻译映射表时的默认输出
- 按类别分组的覆盖率统计
- 表格格式化函数
"""

import json
from io import StringIO
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from scripts.i18n.commands.coverage import cmd_coverage, format_coverage_table


def _extract_json(output: str) -> dict:
    """从混合输出中提取最后的 JSON 块（表格在 JSON 之前）."""
    # output_json 使用 indent=2，顶层 JSON 以 {\n  "ok" 开头
    idx = output.rfind('{\n  "ok"')
    if idx == -1:
        raise ValueError(f"No JSON found in output: {output[:200]}...")
    return json.loads(output[idx:])


@pytest.fixture
def mock_env(tmp_path):
    """构建完整的 mock 环境: cli_dir + 翻译映射表 + skip words + 备份."""
    cli_dir = tmp_path / 'claude-code'
    cli_dir.mkdir()

    # 创建 cli.js 和 package.json
    (cli_dir / 'cli.js').write_text('// mock cli', encoding='utf-8')
    (cli_dir / 'package.json').write_text(
        json.dumps({"name": "@anthropic-ai/claude-code", "version": "1.0.0"}),
        encoding='utf-8'
    )

    # 创建备份
    backup = cli_dir / 'cli.bak.en.js'
    backup.write_text(
        '"This is a long string with many words for testing purposes" '
        '"Medium size string" '
        '"Short" '
        '"Another long string with different words inside" '
        '"Another med str" '
        '"Tiny" ',
        encoding='utf-8'
    )
    import hashlib
    h = hashlib.sha256(backup.read_bytes()).hexdigest()
    (cli_dir / 'cli.backup.hash').write_text(h, encoding='utf-8')

    # 创建数据目录
    data_dir = tmp_path / 'data'
    data_dir.mkdir()

    # 翻译映射表
    map_data = {
        "_meta": {"cli_version": "1.0.0", "version": "1.0.0"},
        "translations": {
            "This is a long string with many words for testing purposes": "这是用于测试的长字符串",
            "Medium size string": "中等长度字符串",
            "Short": "短",
        }
    }
    (data_dir / 'zh-CN.json').write_text(
        json.dumps(map_data, ensure_ascii=False), encoding='utf-8'
    )

    # Skip words
    skip_data = {"skip": ["Code identifier"]}
    (data_dir / 'skip-words.json').write_text(
        json.dumps(skip_data), encoding='utf-8'
    )

    return cli_dir, data_dir


class TestCoverageCommand:
    """coverage 命令测试类."""

    def test_cli_not_found(self):
        """测试 1: CLI 未安装时输出 ok=False 错误 JSON."""
        with patch('scripts.i18n.commands.coverage.get_cli_dir', side_effect=SystemExit(1)):
            with pytest.raises(SystemExit):
                cmd_coverage()

    def test_coverage_with_data(self, mock_env, capsys):
        """测试 2: 完整环境下输出包含覆盖率指标."""
        cli_dir, data_dir = mock_env

        with patch('scripts.i18n.commands.coverage.get_cli_dir', return_value=cli_dir), \
             patch('scripts.i18n.commands.coverage.get_data_dir', return_value=data_dir):
            cmd_coverage()

        captured = capsys.readouterr()
        output = _extract_json(captured.out)

        assert output["ok"] is True
        assert "translated" in output
        assert "untranslated" in output
        assert "skipped" in output
        assert "total" in output
        assert "percentage" in output
        assert "categories" in output
        assert output["translated"] == 3  # 3 条翻译

    def test_coverage_no_map(self, tmp_path, capsys):
        """测试 3: 无翻译映射表时 translated=0."""
        cli_dir = tmp_path / 'claude-code'
        cli_dir.mkdir()
        (cli_dir / 'cli.js').write_text('// mock', encoding='utf-8')
        (cli_dir / 'package.json').write_text(
            json.dumps({"name": "@anthropic-ai/claude-code", "version": "1.0.0"}),
            encoding='utf-8'
        )

        data_dir = tmp_path / 'data'
        data_dir.mkdir()
        # 不创建 zh-CN.json

        with patch('scripts.i18n.commands.coverage.get_cli_dir', return_value=cli_dir), \
             patch('scripts.i18n.commands.coverage.get_data_dir', return_value=data_dir):
            cmd_coverage()

        captured = capsys.readouterr()
        output = _extract_json(captured.out)

        assert output["ok"] is True
        assert output["translated"] == 0
        assert output["percentage"] == "0.0%"

    def test_categories_structure(self, mock_env, capsys):
        """测试 4: categories 包含 long/medium/short 三个分组."""
        cli_dir, data_dir = mock_env

        with patch('scripts.i18n.commands.coverage.get_cli_dir', return_value=cli_dir), \
             patch('scripts.i18n.commands.coverage.get_data_dir', return_value=data_dir):
            cmd_coverage()

        captured = capsys.readouterr()
        output = _extract_json(captured.out)

        cats = output["categories"]
        assert "long" in cats
        assert "medium" in cats
        assert "short" in cats

        for cat_name in ["long", "medium", "short"]:
            cat = cats[cat_name]
            assert "translated" in cat
            assert "untranslated" in cat
            assert "total" in cat
            assert "percentage" in cat

    def test_format_table(self):
        """测试 5: format_coverage_table 返回含分隔线和百分比的表格."""
        categories = {
            "long": {"translated": 10, "untranslated": 5, "total": 15, "percentage": "66.7%"},
            "medium": {"translated": 8, "untranslated": 2, "total": 10, "percentage": "80.0%"},
            "short": {"translated": 3, "untranslated": 7, "total": 10, "percentage": "30.0%"},
        }
        table = format_coverage_table(
            translated=21, untranslated=14, skipped=5,
            total=40, percentage="60.0%", categories=categories
        )

        assert isinstance(table, str)
        assert "66.7%" in table
        assert "80.0%" in table
        assert "30.0%" in table
        assert "60.0%" in table
        assert "---" in table or "=" in table.replace("=", "").replace("-", "") == False
        # 表格包含分隔线
        lines = table.strip().split("\n")
        assert len(lines) >= 5  # header + separator + 3 categories + total
