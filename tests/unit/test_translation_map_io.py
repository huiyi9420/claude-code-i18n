"""Tests for translation map read/write operations."""

import json
from pathlib import Path

import pytest

from scripts.i18n.io.translation_map import (
    load_translation_map,
    save_translation_map,
    merge_translations,
    save_skip_words,
    load_skip_words,
)


class TestSaveTranslationMap:
    """Test save_translation_map function."""

    def test_save_and_load_roundtrip(self, tmp_path):
        """Saved map should be loadable with identical content."""
        map_path = tmp_path / "zh-CN.json"
        meta = {"version": "4.2.0", "cli_version": "2.1.92"}
        translations = {"Hello": "你好", "World": "世界"}

        save_translation_map(map_path, meta, translations)
        result = load_translation_map(map_path)

        assert result["meta"]["version"] == "4.2.0"
        assert result["translations"]["Hello"] == "你好"
        assert result["translations"]["World"] == "世界"

    def test_save_preserves_chinese(self, tmp_path):
        """Chinese characters should not be escaped in output."""
        map_path = tmp_path / "zh-CN.json"
        save_translation_map(map_path, {"version": "1"}, {"Test": "测试"})
        raw = map_path.read_text(encoding="utf-8")
        assert "测试" in raw
        assert "\\u" not in raw


class TestMergeTranslations:
    """Test merge_translations function."""

    def test_adds_new_entries(self):
        """New entries should be added to merged result."""
        existing = {"Hello": "你好"}
        new = {"World": "世界"}
        meta = {"version": "1.0.0", "cli_version": "old"}

        result = merge_translations(existing, new, meta, "2.0.0")
        assert "World" in result["merged"]
        assert "World" in result["added"]
        assert len(result["added"]) == 1

    def test_updates_existing(self):
        """Changed values should be updated."""
        existing = {"Hello": "你好"}
        new = {"Hello": "您好"}
        meta = {"version": "1.0.0"}

        result = merge_translations(existing, new, meta, "2.0.0")
        assert result["merged"]["Hello"] == "您好"
        assert "Hello" in result["updated"]

    def test_unchanged_detection(self):
        """Same values should be detected as unchanged."""
        existing = {"Hello": "你好"}
        new = {"Hello": "你好"}
        meta = {"version": "1.0.0"}

        result = merge_translations(existing, new, meta, "2.0.0")
        assert "Hello" in result["unchanged"]

    def test_version_increment(self):
        """Patch version should auto-increment."""
        meta = {"version": "4.2.0"}
        merge_translations({}, {}, meta, "2.0.0")
        assert meta["version"] == "4.2.1"

    def test_cli_version_updated(self):
        """cli_version should be updated to current."""
        meta = {"cli_version": "old"}
        merge_translations({}, {}, meta, "2.1.93")
        assert meta["cli_version"] == "2.1.93"

    def test_mixed_operations(self):
        """Add, update, and unchanged in one merge."""
        existing = {"A": "a", "B": "b"}
        new = {"A": "a", "B": "b2", "C": "c"}
        meta = {"version": "1.0.0"}

        result = merge_translations(existing, new, meta, "2.0.0")
        assert len(result["added"]) == 1
        assert len(result["updated"]) == 1
        assert len(result["unchanged"]) == 1


class TestSaveSkipWords:
    """Test save_skip_words function."""

    def test_save_and_load_roundtrip(self, tmp_path):
        """Saved skip words should be loadable."""
        skip_path = tmp_path / "skip-words.json"
        skip_set = {"OK", "Run", "Cancel"}

        save_skip_words(skip_path, skip_set)
        loaded = load_skip_words(skip_path)

        assert loaded == skip_set

    def test_save_sorted(self, tmp_path):
        """Skip words should be saved in sorted order."""
        skip_path = tmp_path / "skip-words.json"
        save_skip_words(skip_path, {"Z", "A", "M"})

        raw = json.loads(skip_path.read_text(encoding="utf-8"))
        assert raw["skip"] == ["A", "M", "Z"]
