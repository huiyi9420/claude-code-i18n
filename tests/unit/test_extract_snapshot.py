"""Tests for extract snapshot persistence and diff."""

import json
from pathlib import Path

import pytest

from scripts.i18n.io.extract_snapshot import (
    save_extract_snapshot,
    load_extract_snapshot,
    diff_extractions,
)


class TestSaveLoadSnapshot:
    """Test snapshot save/load round-trip."""

    def test_roundtrip(self, tmp_path):
        """Saved snapshot should be loadable with identical data."""
        path = tmp_path / "extract-snapshot.json"
        candidates = [
            {"en": "Hello World", "score": 1002, "type": "strong", "count": 3},
            {"en": "Loading", "score": 1, "type": "weak", "count": 1},
        ]
        save_extract_snapshot(path, "2.1.92", candidates)
        result = load_extract_snapshot(path)

        assert result["cli_version"] == "2.1.92"
        assert len(result["candidates"]) == 2
        assert result["candidates"][0]["en"] == "Hello World"

    def test_load_nonexistent(self, tmp_path):
        """Loading nonexistent file should return empty candidates."""
        result = load_extract_snapshot(tmp_path / "nope.json")
        assert result["candidates"] == []

    def test_timestamp_present(self, tmp_path):
        """Snapshot should contain a timestamp."""
        path = tmp_path / "snap.json"
        save_extract_snapshot(path, "1.0", [])
        result = load_extract_snapshot(path)
        assert result["timestamp"] is not None


class TestDiffExtractions:
    """Test diff_extractions function."""

    def test_new_candidates(self):
        """Strings in current but not previous should be 'new'."""
        prev = [{"en": "A", "score": 1, "count": 1}]
        curr = [{"en": "A", "score": 1, "count": 1}, {"en": "B", "score": 2, "count": 1}]

        result = diff_extractions(prev, curr)
        assert len(result["new"]) == 1
        assert result["new"][0]["en"] == "B"

    def test_removed_candidates(self):
        """Strings in previous but not current should be 'removed'."""
        prev = [{"en": "A", "score": 1, "count": 1}, {"en": "B", "score": 2, "count": 1}]
        curr = [{"en": "A", "score": 1, "count": 1}]

        result = diff_extractions(prev, curr)
        assert len(result["removed"]) == 1
        assert result["removed"][0]["en"] == "B"

    def test_changed_candidates(self):
        """Same key but different score/count should be 'changed'."""
        prev = [{"en": "A", "score": 1, "count": 1}]
        curr = [{"en": "A", "score": 5, "count": 3}]

        result = diff_extractions(prev, curr)
        assert len(result["changed"]) == 1
        assert result["changed"][0]["score"] == 5

    def test_unchanged_candidates(self):
        """Identical entries should be 'unchanged'."""
        prev = [{"en": "A", "score": 1, "count": 1}]
        curr = [{"en": "A", "score": 1, "count": 1}]

        result = diff_extractions(prev, curr)
        assert len(result["unchanged"]) == 1
        assert len(result["new"]) == 0
        assert len(result["changed"]) == 0

    def test_empty_previous(self):
        """Empty previous means everything is new."""
        curr = [{"en": "A", "score": 1, "count": 1}]

        result = diff_extractions([], curr)
        assert len(result["new"]) == 1
        assert len(result["removed"]) == 0

    def test_empty_current(self):
        """Empty current means everything was removed."""
        prev = [{"en": "A", "score": 1, "count": 1}]

        result = diff_extractions(prev, [])
        assert len(result["removed"]) == 1
        assert len(result["new"]) == 0
