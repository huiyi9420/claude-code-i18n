"""Unit tests for CI coverage regression check script.

Tests the ci_check_coverage.py module which validates that translation
entry counts do not fall below a stored baseline.
"""

import json
import sys
from pathlib import Path

import pytest

# Import the module under test
from scripts.ci_check_coverage import (
    compare_coverage,
    count_translations,
    load_baseline,
    main,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def sample_map(tmp_path):
    """Create a sample zh-CN.json translation map file."""
    data = {
        "_meta": {
            "name": "Claude Code 中文汉化",
            "version": "4.4.0",
            "cli_version": "2.1.92",
        },
        "translations": {
            # long strings (>20 chars)
            "This is a very long English string for testing": "这是一个很长的英文字符串用于测试",
            "Another long English string that exceeds twenty": "另一个超过二十个字符的英文长字符串",
            "Yet another long string for the long category test": "又一个长类别测试的长字符串",
            # medium strings (10-20 chars)
            "Medium str1!!": "中等字符串1",
            "Medium str2!!": "中等字符串2",
            "Medium str3!!": "中等字符串3",
            # short strings (<10 chars)
            "Short": "短",
            "Tiny": "小",
            "Error": "错误",
            # dict-style translation (v6 format)
            "A dict translation entry": {"zh": "字典翻译条目"},
        },
    }
    map_file = tmp_path / "zh-CN.json"
    map_file.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    return map_file


@pytest.fixture
def sample_baseline(tmp_path):
    """Create a sample coverage-baseline.json file."""
    baseline = {
        "translated_count": 10,
        "long": 3,
        "medium": 3,
        "short": 3,
        "updated_at": "2026-04-07",
        "zh-CN_meta_version": "4.4.0",
    }
    bl_file = tmp_path / "coverage-baseline.json"
    bl_file.write_text(json.dumps(baseline, ensure_ascii=False), encoding="utf-8")
    return bl_file


# ---------------------------------------------------------------------------
# count_translations tests
# ---------------------------------------------------------------------------

class TestCountTranslations:
    """Tests for count_translations function."""

    def test_counts_total_correctly(self, sample_map):
        result = count_translations(sample_map)
        assert result["total"] == 10  # 10 translation entries

    def test_classifies_long_strings(self, sample_map):
        """Strings with English key length > 20 are 'long'."""
        result = count_translations(sample_map)
        assert result["long"] == 4  # 3 plain + 1 dict entry, all > 20 chars

    def test_classifies_medium_strings(self, sample_map):
        """Strings with English key length 10-20 are 'medium'."""
        result = count_translations(sample_map)
        assert result["medium"] == 3

    def test_classifies_short_strings(self, sample_map):
        """Strings with English key length < 10 are 'short'."""
        result = count_translations(sample_map)
        assert result["short"] == 3

    def test_includes_meta_version(self, sample_map):
        result = count_translations(sample_map)
        assert result["meta_version"] == "4.4.0"

    def test_empty_translations(self, tmp_path):
        data = {"_meta": {"version": "1.0.0"}, "translations": {}}
        f = tmp_path / "zh-CN.json"
        f.write_text(json.dumps(data), encoding="utf-8")
        result = count_translations(f)
        assert result["total"] == 0
        assert result["long"] == 0
        assert result["medium"] == 0
        assert result["short"] == 0


# ---------------------------------------------------------------------------
# load_baseline tests
# ---------------------------------------------------------------------------

class TestLoadBaseline:
    """Tests for load_baseline function."""

    def test_loads_valid_baseline(self, sample_baseline):
        result = load_baseline(sample_baseline)
        assert result is not None
        assert result["translated_count"] == 10
        assert result["long"] == 3

    def test_returns_none_for_missing_file(self, tmp_path):
        missing = tmp_path / "nonexistent.json"
        result = load_baseline(missing)
        assert result is None


# ---------------------------------------------------------------------------
# compare_coverage tests
# ---------------------------------------------------------------------------

class TestCompareCoverage:
    """Tests for compare_coverage function."""

    def test_ok_when_current_gte_baseline(self):
        current = {"total": 10, "long": 3, "medium": 3, "short": 3}
        baseline = {"translated_count": 10, "long": 3, "medium": 3, "short": 3}
        result = compare_coverage(current, baseline)
        assert result["ok"] is True

    def test_ok_when_current_exceeds_baseline(self):
        current = {"total": 15, "long": 5, "medium": 5, "short": 5}
        baseline = {"translated_count": 10, "long": 3, "medium": 3, "short": 3}
        result = compare_coverage(current, baseline)
        assert result["ok"] is True

    def test_fails_when_current_below_baseline(self):
        current = {"total": 8, "long": 2, "medium": 3, "short": 3}
        baseline = {"translated_count": 10, "long": 3, "medium": 3, "short": 3}
        result = compare_coverage(current, baseline)
        assert result["ok"] is False

    def test_diff_contains_negative_values_when_below(self):
        current = {"total": 8, "long": 2, "medium": 3, "short": 3}
        baseline = {"translated_count": 10, "long": 3, "medium": 3, "short": 3}
        result = compare_coverage(current, baseline)
        assert result["diff"]["total"] == -2
        assert result["diff"]["long"] == -1

    def test_diff_zero_when_equal(self):
        current = {"total": 10, "long": 3, "medium": 3, "short": 3}
        baseline = {"translated_count": 10, "long": 3, "medium": 3, "short": 3}
        result = compare_coverage(current, baseline)
        assert result["diff"]["total"] == 0

    def test_includes_current_and_baseline_in_result(self):
        current = {"total": 10, "long": 3, "medium": 3, "short": 3}
        baseline = {"translated_count": 10, "long": 3, "medium": 3, "short": 3}
        result = compare_coverage(current, baseline)
        assert result["current"] == current
        assert result["baseline"]["translated_count"] == 10


# ---------------------------------------------------------------------------
# main (CLI) tests
# ---------------------------------------------------------------------------

class TestMain:
    """Tests for the main() CLI entry point."""

    def test_full_pass_flow(self, sample_map, sample_baseline, capsys):
        """When current >= baseline, exits 0 and outputs JSON with ok=true."""
        with pytest.raises(SystemExit) as exc_info:
            main([
                "--map-path", str(sample_map),
                "--baseline-path", str(sample_baseline),
            ])
        assert exc_info.value.code == 0
        output = json.loads(capsys.readouterr().out)
        assert output["ok"] is True

    def test_full_fail_flow(self, sample_map, tmp_path, capsys):
        """When current < baseline, exits 1 and outputs JSON with ok=false."""
        high_baseline = {
            "translated_count": 99999,
            "long": 99999,
            "medium": 99999,
            "short": 99999,
            "updated_at": "2026-04-07",
            "zh-CN_meta_version": "4.4.0",
        }
        bl_file = tmp_path / "high_baseline.json"
        bl_file.write_text(json.dumps(high_baseline), encoding="utf-8")

        with pytest.raises(SystemExit) as exc_info:
            main([
                "--map-path", str(sample_map),
                "--baseline-path", str(bl_file),
            ])
        assert exc_info.value.code == 1
        output = json.loads(capsys.readouterr().out)
        assert output["ok"] is False

    def test_no_baseline_still_passes(self, sample_map, tmp_path, capsys):
        """When baseline file does not exist, exits 0 (first-run scenario)."""
        missing_baseline = tmp_path / "nonexistent.json"
        with pytest.raises(SystemExit) as exc_info:
            main([
                "--map-path", str(sample_map),
                "--baseline-path", str(missing_baseline),
            ])
        assert exc_info.value.code == 0
        output = json.loads(capsys.readouterr().out)
        assert output["ok"] is True
        assert "warning" in output
