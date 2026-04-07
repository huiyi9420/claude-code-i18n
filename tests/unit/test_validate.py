"""Unit tests for the validate command (translation quality validation).

Tests three quality checks:
1. chinese_english_mixing — untranslated English words mixed into Chinese
2. synonym_inconsistency — same canonical English mapped to different Chinese
3. placeholder_missing — format placeholders lost in translation
"""

import json
from pathlib import Path

import pytest

from scripts.i18n.commands.validate import (
    check_chinese_english_mixing,
    check_synonym_inconsistency,
    check_placeholder_missing,
    validate_translations,
    cmd_validate,
)
from scripts.i18n.io.translation_map import load_translation_map


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def simple_map_file(tmp_path):
    """Create a minimal translation map file with clean entries."""
    data = {
        "_meta": {"version": "1.0.0", "cli_version": "1.0.0"},
        "translations": {
            "Loading files": "正在加载文件",
            "Error occurred": "发生错误",
            "Delete item": "删除项目",
        }
    }
    path = tmp_path / "zh-CN.json"
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


@pytest.fixture
def mixed_map_file(tmp_path):
    """Translation map with Chinese-English mixing issues."""
    data = {
        "_meta": {"version": "1.0.0"},
        "translations": {
            "Loading files": "正在Loading文件",
            "Processing data": "正在Processing数据",
            "Pure Chinese": "纯中文翻译",
            "Using API key": "使用 API 密钥",  # API is whitelisted
            "Open IDE": "打开 IDE 编辑器",  # IDE is whitelisted
        }
    }
    path = tmp_path / "zh-CN.json"
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


@pytest.fixture
def synonym_map_file(tmp_path):
    """Translation map with synonym inconsistency issues."""
    data = {
        "_meta": {"version": "1.0.0"},
        "translations": {
            "Not found": "未找到",
            "Not Found": "找不到",
            "Delete item": "删除项目",
            "delete item": "移除项目",
        }
    }
    path = tmp_path / "zh-CN.json"
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


@pytest.fixture
def placeholder_map_file(tmp_path):
    """Translation map with missing placeholder issues."""
    data = {
        "_meta": {"version": "1.0.0"},
        "translations": {
            "Found %s items": "找到 %s 个项目",
            "User %s not found": "用户未找到",  # missing %s
            "Hello ${name}": "你好 ${name}",
            "Welcome ${user}": "欢迎",  # missing ${user}
            "Value: {0}": "值: {0}",
            "Count: {count}": "计数",  # missing {count}
            "No placeholders": "无占位符",
        }
    }
    path = tmp_path / "zh-CN.json"
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


@pytest.fixture
def empty_map_file(tmp_path):
    """Empty translation map."""
    data = {
        "_meta": {"version": "1.0.0"},
        "translations": {}
    }
    path = tmp_path / "zh-CN.json"
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


# ---------------------------------------------------------------------------
# Test 1 & 2: Chinese-English mixing detection
# ---------------------------------------------------------------------------

class TestChineseEnglishMixing:
    """Tests for check_chinese_english_mixing."""

    def test_detects_mixed_english_in_chinese(self, mixed_map_file):
        """Test 1: '正在Loading文件' should be flagged as chinese_english_mixing."""
        map_data = load_translation_map(mixed_map_file)
        issues = check_chinese_english_mixing(map_data["translations"])
        mixing_keys = [i["key"] for i in issues]
        assert "Loading files" in mixing_keys
        assert "Processing data" in mixing_keys
        # Verify issue type
        for issue in issues:
            assert issue["type"] == "chinese_english_mixing"
            assert "detail" in issue
            assert "value" in issue

    def test_no_false_positives_for_clean_chinese(self, mixed_map_file):
        """Test 2: Pure Chinese translations should not be flagged."""
        map_data = load_translation_map(mixed_map_file)
        issues = check_chinese_english_mixing(map_data["translations"])
        clean_keys = [i["key"] for i in issues]
        assert "Pure Chinese" not in clean_keys
        assert "Using API key" not in clean_keys  # API is whitelisted
        assert "Open IDE" not in clean_keys  # IDE is whitelisted


# ---------------------------------------------------------------------------
# Test 3 & 4: Synonym inconsistency detection
# ---------------------------------------------------------------------------

class TestSynonymInconsistency:
    """Tests for check_synonym_inconsistency."""

    def test_detects_inconsistent_translations(self, synonym_map_file):
        """Test 3: 'Not found' and 'Not Found' with different translations
        should be flagged as synonym_inconsistency."""
        map_data = load_translation_map(synonym_map_file)
        issues = check_synonym_inconsistency(map_data["translations"])
        # Should detect at least the 'not found' canonical group
        canonical_forms = [i["canonical"] for i in issues]
        assert "not found" in canonical_forms
        # Verify structure
        for issue in issues:
            assert issue["type"] == "synonym_inconsistency"
            assert "canonical" in issue
            assert "entries" in issue
            assert len(issue["entries"]) >= 2

    def test_no_false_positives_for_consistent(self, simple_map_file):
        """Test 4: Consistent translations should not be flagged."""
        map_data = load_translation_map(simple_map_file)
        issues = check_synonym_inconsistency(map_data["translations"])
        # simple_map has no canonical-key collisions
        assert len(issues) == 0


# ---------------------------------------------------------------------------
# Test 5, 6, 7: Placeholder missing detection
# ---------------------------------------------------------------------------

class TestPlaceholderMissing:
    """Tests for check_placeholder_missing."""

    def test_detects_printf_placeholder_missing(self, placeholder_map_file):
        """Test 5: Missing %s in translation should be flagged."""
        map_data = load_translation_map(placeholder_map_file)
        issues = check_placeholder_missing(map_data["translations"])
        missing_keys = [i["key"] for i in issues]
        assert "User %s not found" in missing_keys

    def test_detects_template_literal_placeholder_missing(self, placeholder_map_file):
        """Test 6: Missing ${var} in translation should be flagged."""
        map_data = load_translation_map(placeholder_map_file)
        issues = check_placeholder_missing(map_data["translations"])
        missing_keys = [i["key"] for i in issues]
        assert "Welcome ${user}" in missing_keys

    def test_detects_format_brace_placeholder_missing(self, placeholder_map_file):
        """Test 7: Missing {0}/{var} in translation should be flagged."""
        map_data = load_translation_map(placeholder_map_file)
        issues = check_placeholder_missing(map_data["translations"])
        missing_keys = [i["key"] for i in issues]
        assert "Count: {count}" in missing_keys

    def test_preserved_placeholders_not_flagged(self, placeholder_map_file):
        """Placeholders that are correctly preserved should not be flagged."""
        map_data = load_translation_map(placeholder_map_file)
        issues = check_placeholder_missing(map_data["translations"])
        missing_keys = [i["key"] for i in issues]
        assert "Found %s items" not in missing_keys  # %s preserved
        assert "Hello ${name}" not in missing_keys  # ${name} preserved
        assert "Value: {0}" not in missing_keys  # {0} preserved
        assert "No placeholders" not in missing_keys  # no placeholders at all


# ---------------------------------------------------------------------------
# Test 8: Empty map handling
# ---------------------------------------------------------------------------

class TestEmptyMap:
    """Tests for edge case: empty translation map."""

    def test_empty_map_no_crash(self, empty_map_file):
        """Test 8: Empty translation map should return ok=True, issues=[]."""
        map_data = load_translation_map(empty_map_file)
        result = validate_translations(map_data["translations"])
        assert result["ok"] is True
        assert result["issues_found"] == 0
        assert result["issues"] == []
        assert result["total_entries"] == 0


# ---------------------------------------------------------------------------
# Test 9: Full cmd_validate flow
# ---------------------------------------------------------------------------

class TestCmdValidate:
    """Tests for the cmd_validate entry point."""

    def test_cmd_validate_outputs_json_report(self, simple_map_file, monkeypatch, capsys):
        """Test 9: cmd_validate loads map and outputs JSON report."""
        monkeypatch.setattr(
            "scripts.i18n.commands.validate.get_data_dir",
            lambda: simple_map_file.parent,
        )
        monkeypatch.setattr(
            "scripts.i18n.commands.validate.get_cli_dir",
            lambda: None,  # validate doesn't need CLI dir
        )
        cmd_validate()
        captured = capsys.readouterr()
        report = json.loads(captured.out)
        assert report["ok"] is True
        assert "total_entries" in report
        assert "issues_found" in report
        assert "issues_by_type" in report
        assert "issues" in report
        assert report["total_entries"] == 3
