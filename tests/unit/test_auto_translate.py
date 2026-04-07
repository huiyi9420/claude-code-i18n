"""Tests for auto-translate rule engine."""

from pathlib import Path

import pytest

from scripts.i18n.core.auto_translate import auto_translate_candidates


class TestDictionaryMatch:
    """Test known phrase dictionary matching."""

    def test_dictionary_match(self, tmp_path):
        """Strings in the dictionary should be auto-translated."""
        dict_path = tmp_path / "dict.json"
        import json
        dict_path.write_text(json.dumps({"Loading": "加载中"}), encoding="utf-8")

        candidates = [{"en": "Loading", "score": 1002, "count": 5}]
        result = auto_translate_candidates(
            candidates, {}, dict_path=dict_path,
        )
        assert "Loading" in result["translated"]
        assert result["translated"]["Loading"] == "加载中"
        assert result["rules_used"]["Loading"] == "dictionary"

    def test_no_dictionary_file(self):
        """Missing dictionary file should not error."""
        candidates = [{"en": "Test", "score": 1002, "count": 1}]
        result = auto_translate_candidates(
            candidates, {}, dict_path=Path("/nonexistent"),
        )
        assert len(result["translated"]) == 0


class TestExactMatch:
    """Test exact match in existing translations."""

    def test_exact_match(self):
        """Strings already in existing translations should be reused."""
        existing = {"Hello World": "你好世界"}
        candidates = [{"en": "Hello World", "score": 1002, "count": 3}]

        result = auto_translate_candidates(candidates, existing)
        assert result["translated"]["Hello World"] == "你好世界"
        assert result["rules_used"]["Hello World"] == "exact_match"


class TestUITemplates:
    """Test UI sentence pattern templates."""

    def test_failed_to_pattern(self):
        """'Failed to X' should match template."""
        candidates = [{"en": "Failed to connect", "score": 1002, "count": 1}]
        result = auto_translate_candidates(candidates, {})
        assert "Failed to connect" in result["translated"]
        # Template produces "connect失败" — captures the verb as-is
        assert "失败" in result["translated"]["Failed to connect"]

    def test_please_pattern(self):
        """'Please X' should match template."""
        candidates = [{"en": "Please wait", "score": 1002, "count": 1}]
        result = auto_translate_candidates(candidates, {})
        # "Please wait" is in dictionary, so it should match there first
        # But if not, the template should catch it
        assert len(result["review"]) == 0 or "Please wait" in result["translated"]

    def test_no_match_goes_to_review(self):
        """Strings that don't match any rule should go to review."""
        candidates = [{"en": "Some random string xyz", "score": 1002, "count": 1}]
        result = auto_translate_candidates(candidates, {})
        assert len(result["review"]) == 1
        assert result["review"][0]["en"] == "Some random string xyz"


class TestScoreThreshold:
    """Test score threshold filtering."""

    def test_below_threshold_skipped(self):
        """Low-score candidates should be skipped."""
        candidates = [{"en": "Test", "score": 500, "count": 1}]
        result = auto_translate_candidates(
            candidates, {}, score_threshold=1000,
        )
        assert len(result["skipped"]) == 1
        assert len(result["translated"]) == 0

    def test_at_threshold_included(self):
        """Candidates at threshold should be processed."""
        candidates = [{"en": "Failed to load", "score": 1000, "count": 1}]
        result = auto_translate_candidates(
            candidates, {}, score_threshold=1000,
        )
        assert len(result["skipped"]) == 0


class TestEmptyInput:
    """Test empty input handling."""

    def test_empty_candidates(self):
        """Empty candidates list should return empty results."""
        result = auto_translate_candidates([], {})
        assert len(result["translated"]) == 0
        assert len(result["review"]) == 0
        assert len(result["skipped"]) == 0
