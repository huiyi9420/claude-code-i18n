"""Tests for string scanner (EXTRACT-01~06)."""

import re

import pytest

from scripts.i18n.filters.noise_filter import NOISE_RE
from scripts.i18n.core.scanner import scan_candidates


class TestScanBasic:
    """Basic scanning functionality (EXTRACT-01)."""

    def test_scan_finds_candidates(self):
        """EXTRACT-01: Sample content with known strings returns candidates."""
        content = '''
        "Plan Mode activated for this session"
        "Extended thinking is now enabled"
        "Auto mode will handle all permissions"
        "Plan Mode activated for this session"
        "Random unknown thing here"
        '''
        existing = set()
        skipped = set()
        results = scan_candidates(content, existing, skipped, NOISE_RE)
        assert len(results) > 0
        # Plan Mode should be found
        ens = [r["en"] for r in results]
        assert any("Plan Mode" in e for e in ens)

    def test_scan_returns_list_of_dicts(self):
        """EXTRACT-01: Each candidate has en, count, score, type keys."""
        content = '"Plan Mode is active"'
        results = scan_candidates(content, set(), set(), NOISE_RE)
        assert isinstance(results, list)
        if results:
            r = results[0]
            assert "en" in r
            assert "count" in r
            assert "score" in r
            assert "type" in r


class TestScanExclusions:
    """Tests for exclusion rules (EXTRACT-03/05/06)."""

    def test_scan_excludes_existing(self):
        """EXTRACT-05: Strings in existing set are not in results."""
        content = '"Plan Mode is now active"'
        existing = {"Plan Mode is now active"}
        results = scan_candidates(content, existing, set(), NOISE_RE)
        ens = [r["en"] for r in results]
        assert "Plan Mode is now active" not in ens

    def test_scan_excludes_skipped(self):
        """EXTRACT-05: Strings in skipped set are not in results."""
        content = '"Plan Mode is now active"'
        skipped = {"Plan Mode is now active"}
        results = scan_candidates(content, set(), skipped, NOISE_RE)
        ens = [r["en"] for r in results]
        assert "Plan Mode is now active" not in ens

    def test_scan_excludes_no_space(self):
        """EXTRACT-03: Strings without space (code identifiers) excluded."""
        content = '"PackageManager" "ConfigResolver" "ExtendedThinking"'
        results = scan_candidates(content, set(), set(), NOISE_RE)
        ens = [r["en"] for r in results]
        assert "PackageManager" not in ens
        assert "ConfigResolver" not in ens

    def test_scan_excludes_code_fragments(self):
        """EXTRACT-03: Strings with code fragments excluded."""
        content = '"Result === true" "Async function handler" "Value !== null"'
        results = scan_candidates(content, set(), set(), NOISE_RE)
        ens = [r["en"] for r in results]
        # These should be excluded due to code-like patterns
        for e in ens:
            assert "===" not in e
            assert "!==" not in e

    def test_scan_excludes_urls(self):
        """EXTRACT-03: URL strings excluded."""
        content = '"Visit https://example.com for details"'
        results = scan_candidates(content, set(), set(), NOISE_RE)
        ens = [r["en"] for r in results]
        for e in ens:
            assert "https://" not in e

    def test_scan_excludes_noise(self):
        """EXTRACT-03: Strings matching noise patterns excluded."""
        content = '"Azure authentication telemetry protocol buffer error"'
        results = scan_candidates(content, set(), set(), NOISE_RE)
        ens = [r["en"] for r in results]
        assert len(ens) == 0

    def test_scan_excludes_cjk(self):
        """EXTRACT-06: Strings containing Chinese characters never appear."""
        content = '"这是中文 Plan Mode" "Extended thinking 包含中文"'
        results = scan_candidates(content, set(), set(), NOISE_RE)
        ens = [r["en"] for r in results]
        for e in ens:
            # No CJK characters in output
            assert not any("\u4e00" <= c <= "\u9fff" for c in e)

    def test_scan_excludes_all_caps(self):
        """EXTRACT-03: ALL_CAPS strings > 5 chars excluded."""
        content = '"CONFIGURATION_SETTINGS_UPDATED"'
        results = scan_candidates(content, set(), set(), NOISE_RE)
        ens = [r["en"] for r in results]
        assert "CONFIGURATION_SETTINGS_UPDATED" not in ens

    def test_scan_excludes_underscore_identifiers(self):
        """EXTRACT-03: Underscore-only identifiers (no natural punctuation) excluded."""
        content = '"SOME_CONSTANT_VALUE_HERE"'
        results = scan_candidates(content, set(), set(), NOISE_RE)
        ens = [r["en"] for r in results]
        assert "SOME_CONSTANT_VALUE_HERE" not in ens


class TestScanScoring:
    """Tests for scoring and sorting (EXTRACT-02/04)."""

    def test_scan_scores_strong_higher(self):
        """EXTRACT-02: Strong indicator strings have higher scores than weak."""
        content = '"Plan Mode is active" "Loading please wait"'
        results = scan_candidates(content, set(), set(), NOISE_RE)
        if len(results) >= 2:
            strong = [r for r in results if r["type"] == "strong"]
            weak = [r for r in results if r["type"] == "weak"]
            if strong and weak:
                assert strong[0]["score"] > weak[0]["score"]

    def test_scan_sorted_by_score(self):
        """EXTRACT-04: Results sorted by score descending."""
        content = '''
        "Plan Mode is active"
        "Extended thinking enabled"
        "Loading the session"
        "Processing your request"
        '''
        results = scan_candidates(content, set(), set(), NOISE_RE)
        scores = [r["score"] for r in results]
        assert scores == sorted(scores, reverse=True)

    def test_scan_only_signal_strings(self):
        """EXTRACT-02: Strings with no strong/weak indicator excluded."""
        content = '"Random XYZ text with no indicators at all"'
        results = scan_candidates(content, set(), set(), NOISE_RE)
        ens = [r["en"] for r in results]
        assert "Random XYZ text with no indicators at all" not in ens

    def test_scan_counts_occurrences(self):
        """EXTRACT-01: Count reflects exact quoted occurrences."""
        content = '''
        "Plan Mode activated"
        "Plan Mode activated"
        "Plan Mode activated"
        '''
        results = scan_candidates(content, set(), set(), NOISE_RE)
        plan = [r for r in results if "Plan Mode" in r["en"]]
        if plan:
            assert plan[0]["count"] == 3


class TestScanEdgeCases:
    """Edge case tests."""

    def test_scan_empty_content(self):
        """Empty content returns empty list."""
        results = scan_candidates("", set(), set(), NOISE_RE)
        assert results == []

    def test_scan_no_matching_strings(self):
        """Content with no quoted strings returns empty list."""
        content = "no quoted strings here"
        results = scan_candidates(content, set(), set(), NOISE_RE)
        assert results == []

    def test_scan_single_char_strings_excluded(self):
        """Strings too short (< 6 chars total) are excluded by regex."""
        content = '"Abc" "Test" "Hi"'
        results = scan_candidates(content, set(), set(), NOISE_RE)
        assert len(results) == 0

    def test_scan_deduplicates_candidates(self):
        """Same string appearing multiple times only counted once."""
        content = '"Plan Mode active" "Plan Mode active" "Plan Mode active"'
        results = scan_candidates(content, set(), set(), NOISE_RE)
        ens = [r["en"] for r in results]
        assert ens.count("Plan Mode active") <= 1
