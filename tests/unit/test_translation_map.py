"""Tests for translation map loader and skip words (MAP-01~04)."""

import json
from pathlib import Path

import pytest

FIXTURES = Path(__file__).parent.parent / "fixtures"


class TestLoadTranslationMap:
    """Tests for load_translation_map function."""

    def test_load_map_success(self):
        """MAP-01: Loads sample_zh_cn.json and checks meta + translations."""
        from scripts.i18n.io.translation_map import load_translation_map

        result = load_translation_map(FIXTURES / "sample_zh_cn.json")
        assert "meta" in result
        assert "translations" in result
        assert result["meta"]["version"] == "1.0.0"
        assert result["meta"]["cli_version"] == "2.1.92"
        assert isinstance(result["translations"], dict)
        assert len(result["translations"]) == 5

    def test_load_map_flatten_dict_value(self, tmp_path):
        """MAP-04: Entry with dict {"zh": "..."} flattened to string value."""
        from scripts.i18n.io.translation_map import load_translation_map

        data = {
            "_meta": {"version": "1.0"},
            "translations": {
                "Plan Mode": {"zh": "规划模式"},
                "Auto mode": "自动模式",
            },
        }
        p = tmp_path / "mixed.json"
        p.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")

        result = load_translation_map(p)
        assert result["translations"]["Plan Mode"] == "规划模式"
        assert result["translations"]["Auto mode"] == "自动模式"

    def test_load_map_skip_identical(self):
        """MAP-02: Entries with en==zh still present but identifiable."""
        from scripts.i18n.io.translation_map import load_translation_map

        result = load_translation_map(FIXTURES / "sample_zh_cn.json")
        # "Loading" -> "Loading" is an identical entry
        assert "Loading" in result["translations"]
        assert result["translations"]["Loading"] == "Loading"

    def test_load_map_file_not_found(self):
        """MAP-01: FileNotFoundError with clear message."""
        from scripts.i18n.io.translation_map import load_translation_map

        with pytest.raises(FileNotFoundError, match="Translation map"):
            load_translation_map(Path("/nonexistent/path/zh-CN.json"))

    def test_load_map_invalid_json(self, tmp_path):
        """MAP-01: ValueError on invalid JSON."""
        from scripts.i18n.io.translation_map import load_translation_map

        p = tmp_path / "bad.json"
        p.write_text("not valid json{{{", encoding="utf-8")

        with pytest.raises(ValueError, match="Invalid JSON"):
            load_translation_map(p)

    def test_load_map_preserves_meta_as_is(self):
        """MAP-01: _meta field preserved as-is including all sub-fields."""
        from scripts.i18n.io.translation_map import load_translation_map

        result = load_translation_map(FIXTURES / "sample_zh_cn.json")
        meta = result["meta"]
        assert meta["name"] == "Claude Code Test Map"
        assert meta["description"] == "Sample translation map for unit testing"


class TestLoadSkipWords:
    """Tests for load_skip_words function (MAP-03)."""

    def test_load_skip_words_success(self):
        """MAP-03: Returns set from 'skip' key."""
        from scripts.i18n.io.translation_map import load_skip_words

        result = load_skip_words(FIXTURES / "sample_skip.json")
        assert isinstance(result, set)
        assert "Error" in result
        assert "Warning" in result
        assert "Success" in result
        assert len(result) == 3

    def test_load_skip_words_empty(self, tmp_path):
        """MAP-03: Returns empty set for {"skip": []}."""
        from scripts.i18n.io.translation_map import load_skip_words

        p = tmp_path / "empty_skip.json"
        p.write_text(json.dumps({"skip": []}), encoding="utf-8")

        result = load_skip_words(p)
        assert isinstance(result, set)
        assert len(result) == 0

    def test_load_skip_words_file_not_found(self):
        """MAP-03: FileNotFoundError when file doesn't exist."""
        from scripts.i18n.io.translation_map import load_skip_words

        with pytest.raises(FileNotFoundError, match="Skip words"):
            load_skip_words(Path("/nonexistent/skip.json"))
