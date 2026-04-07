"""Tests for three-tier replacement engine (APPLY-01~06, APPLY-09~10)."""

import re
from pathlib import Path

import pytest

from scripts.i18n.core.replacer import classify_entry, apply_translations

FIXTURES_DIR = Path(__file__).parent.parent / "fixtures"


def _load_fixture(name: str) -> str:
    return (FIXTURES_DIR / name).read_text(encoding="utf-8")


# ── Tier classification (APPLY-02/03/04 boundaries) ──────────────


class TestClassifyEntry:
    def test_classify_long(self):
        assert classify_entry("An unexpected error occurred in the system") == "long"

    def test_classify_medium(self):
        assert classify_entry("Permission denied") == "medium"

    def test_classify_short(self):
        assert classify_entry("OK") == "short"

    def test_classify_boundary_exactly_10(self):
        # len == 10 -> short (not > 10)
        assert classify_entry("1234567890") == "short"

    def test_classify_boundary_exactly_20(self):
        # len == 20 -> medium (not > 20)
        assert classify_entry("12345678901234567890") == "medium"

    def test_classify_boundary_21(self):
        # len == 21 -> long
        assert classify_entry("123456789012345678901") == "long"


# ── Long string replacement (APPLY-02) ───────────────────────────


class TestLongReplacement:
    def test_long_replace_global(self):
        content = _load_fixture("sample_replacer_content.js")
        translations = {
            "An unexpected error occurred while processing your request.": "处理请求时发生意外错误。"
        }
        new_content, stats = apply_translations(content, translations, set())
        assert "处理请求时发生意外错误。" in new_content
        assert "An unexpected error occurred while processing your request." not in new_content

    def test_long_count_tracking(self):
        content = _load_fixture("sample_replacer_content.js")
        # "An unexpected error occurred..." appears 2 times in fixture
        translations = {
            "An unexpected error occurred while processing your request.": "处理请求时发生意外错误。"
        }
        _, stats = apply_translations(content, translations, set())
        assert stats["long"] == 2

    def test_long_replaces_all_occurrences(self):
        content = 'var a="Permission denied for user";var b="Permission denied for user";'
        translations = {"Permission denied for user": "权限被拒绝"}
        new_content, stats = apply_translations(content, translations, set())
        assert new_content.count("权限被拒绝") == 2
        assert stats["long"] == 2


# ── Medium string replacement (APPLY-03) ─────────────────────────


class TestMediumReplacement:
    def test_medium_quote_boundary(self):
        content = _load_fixture("sample_replacer_content.js")
        translations = {"Permission denied": "权限被拒绝"}
        new_content, stats = apply_translations(content, translations, set())
        assert "权限被拒绝" in new_content

    def test_medium_preserves_outside_quote(self):
        # "Permission denied" inside quotes should be replaced,
        # but bare text outside quotes should not
        content = 'var x="Permission denied";PermissionDenied();'
        translations = {"Permission denied": "权限被拒绝"}
        new_content, stats = apply_translations(content, translations, set())
        assert '"权限被拒绝"' in new_content
        assert "PermissionDenied()" in new_content  # outside quotes preserved

    def test_medium_reverse_order(self):
        # Multiple occurrences in different positions
        content = 'var a="Permission denied";var b="Permission denied";var c="Permission denied";'
        translations = {"Permission denied": "权限被拒绝"}
        new_content, stats = apply_translations(content, translations, set())
        assert new_content.count("权限被拒绝") == 3
        assert stats["medium"] == 3

    def test_medium_single_quote(self):
        content = "var x='Permission denied';"
        translations = {"Permission denied": "权限被拒绝"}
        new_content, stats = apply_translations(content, translations, set())
        assert "'权限被拒绝'" in new_content


# ── Short string replacement (APPLY-04) ──────────────────────────


class TestShortReplacement:
    def test_short_word_boundary(self):
        content = _load_fixture("sample_replacer_content.js")
        translations = {"OK": "好的"}
        new_content, stats = apply_translations(content, translations, set())
        assert stats["short"] > 0

    def test_short_skip_words_excluded(self):
        content = 'var x="Error";var y="Error";'
        translations = {"Error": "错误"}
        skip_words = {"Error"}
        new_content, stats = apply_translations(content, translations, skip_words)
        assert stats["short"] == 0
        assert stats["skipped"] == 1
        assert '"Error"' in new_content  # unchanged

    def test_short_frequency_cap(self):
        # Create content with many "Ready" occurrences
        content = "".join(f'var x{i}="Ready";' for i in range(100))
        translations = {"Ready": "就绪"}
        new_content, stats = apply_translations(content, translations, set(), max_short_cap=10)
        assert stats["short"] == 10

    def test_short_in_skip_words_counted(self):
        content = 'var x="Stop";'
        translations = {"Stop": "停止"}
        skip_words = {"Stop"}
        _, stats = apply_translations(content, translations, skip_words)
        assert stats["skipped"] >= 1
        assert stats["short"] == 0

    def test_short_no_match_no_error(self):
        content = 'var x="hello";'
        translations = {"Ready": "就绪"}
        new_content, stats = apply_translations(content, translations, set())
        assert new_content == content
        assert stats["short"] == 0


# ── Ordering (APPLY-05) ─────────────────────────────────────────


class TestOrdering:
    def test_longest_first(self):
        # "Extended thinking is enabled" must be replaced before "Extended"
        content = 'var x="Extended thinking is enabled";'
        translations = {
            "Extended thinking is enabled": "已启用扩展思考功能",
            "Extended": "扩展的",
        }
        new_content, stats = apply_translations(content, translations, set())
        assert "已启用扩展思考功能" in new_content
        assert "扩展的" not in new_content  # long match consumed it

    def test_no_partial_corruption(self):
        # Long string replacement should not break medium/short matches
        content = 'var a="Permission denied";var b="denied";'
        translations = {
            "Permission denied": "权限被拒绝",
            "denied": "被拒绝",
        }
        new_content, stats = apply_translations(content, translations, set())
        assert '"权限被拒绝"' in new_content
        assert '"被拒绝"' in new_content


# ── Stats tracking (APPLY-06) ───────────────────────────────────


class TestStats:
    def test_stats_all_zero_on_empty(self):
        content = _load_fixture("sample_replacer_content.js")
        _, stats = apply_translations(content, {}, set())
        assert stats["long"] == 0
        assert stats["medium"] == 0
        assert stats["short"] == 0
        assert stats["skipped"] == 0

    def test_stats_tracks_all_tiers(self):
        content = _load_fixture("sample_replacer_content.js")
        translations = {
            "An unexpected error occurred while processing your request.": "处理请求时发生意外错误。",
            "Permission denied": "权限被拒绝",
            "OK": "好的",
        }
        _, stats = apply_translations(content, translations, set())
        assert stats["long"] > 0
        assert stats["medium"] > 0
        assert stats["short"] > 0

    def test_identical_entry_skipped(self):
        content = 'var x="Permission denied";'
        translations = {"Permission denied": "Permission denied"}
        new_content, stats = apply_translations(content, translations, set())
        assert stats["skipped"] == 1
        assert stats["medium"] == 0
        assert "Permission denied" in new_content

    def test_skip_reasons_tracked(self):
        content = 'var x="Error";'
        translations = {"Error": "Error"}
        _, stats = apply_translations(content, translations, {"Error"})
        assert "Error" in stats["skip_reasons"]


# ── Hook/template replacement (APPLY-09) ─────────────────────────


class TestTemplateReplacement:
    def test_template_replacement_via_regex(self):
        # Python re handles template-like patterns (not sed)
        content = 'var x=`Template: ${name}`;var y="Template: name";'
        translations = {"Template: name": "模板: 名称"}
        new_content, stats = apply_translations(content, translations, set())
        assert "模板: 名称" in new_content

    def test_special_chars_escaped(self):
        content = 'var x="cost: $100";'
        translations = {"cost: $100": "费用: $100"}
        new_content, stats = apply_translations(content, translations, set())
        assert "费用: $100" in new_content


# ── Edge cases ───────────────────────────────────────────────────


class TestEdgeCases:
    def test_string_not_found(self):
        content = 'var x="hello";'
        translations = {"nonexistent string here": "不存在"}
        new_content, stats = apply_translations(content, translations, set())
        assert new_content == content
        assert stats["long"] == 0

    def test_empty_content(self):
        translations = {"hello": "你好"}
        new_content, stats = apply_translations("", translations, set())
        assert new_content == ""
        assert stats["short"] == 0


# ── Context-aware replacement (04-02) ─────────────────────────────


class TestContextAwareReplacement:
    """Tests for context-aware translation selection in apply_translations."""

    def test_apply_with_context_exact_match(self):
        """Entry with contexts: in matching region, use context translation."""
        # "tools" region is at position 50-200 (simulated)
        content = (
            'var x="default text";'
            'tool_name="Permission denied";'
            'toolResult="Permission denied";'
        )
        translations = {"Permission denied": "权限被拒绝"}
        raw_translations = {
            "Permission denied": {
                "zh": "权限被拒绝",
                "contexts": {"tools": "工具权限不足"},
            }
        }
        context_index = [
            {"tag": "tools", "start": 19, "end": 72},
        ]
        new_content, stats = apply_translations(
            content, translations, set(),
            raw_translations=raw_translations,
            context_index=context_index,
        )
        # In "tools" region: "Permission denied" -> "工具权限不足"
        assert "工具权限不足" in new_content
        assert stats["contextual"] >= 1

    def test_apply_with_context_fallback(self):
        """Entry with contexts: in non-matching region, use global default."""
        content = 'var x="Permission denied";'
        translations = {"Permission denied": "权限被拒绝"}
        raw_translations = {
            "Permission denied": {
                "zh": "权限被拒绝",
                "contexts": {"tools": "工具权限不足"},
            }
        }
        # No context index region covers position 7-26
        context_index = [
            {"tag": "auth", "start": 100, "end": 200},
        ]
        new_content, stats = apply_translations(
            content, translations, set(),
            raw_translations=raw_translations,
            context_index=context_index,
        )
        # No matching context -> fallback to global "权限被拒绝"
        assert "权限被拒绝" in new_content
        # "工具权限不足" should NOT appear
        assert "工具权限不足" not in new_content

    def test_apply_without_context_index(self):
        """Without context_index, behavior is identical to v3.0."""
        content = 'var x="Permission denied for user account access";'
        translations = {"Permission denied for user account access": "权限被拒绝"}
        raw_translations = {
            "Permission denied for user account access": {
                "zh": "权限被拒绝",
                "contexts": {"auth": "认证权限不足"},
            }
        }
        new_content, stats = apply_translations(
            content, translations, set(),
            raw_translations=raw_translations,
            context_index=None,
        )
        # No context_index -> always use global default
        assert "权限被拒绝" in new_content
        assert "认证权限不足" not in new_content

    def test_apply_mixed_context_and_plain(self):
        """Mix of entries with and without context annotations."""
        content = (
            'var a="Permission denied";'
            'var b="An unexpected error occurred in system";'
            'tool_name="Permission denied";'
        )
        translations = {
            "Permission denied": "权限被拒绝",
            "An unexpected error occurred in system": "系统发生意外错误",
        }
        raw_translations = {
            "Permission denied": {
                "zh": "权限被拒绝",
                "contexts": {"tools": "工具权限不足"},
            },
            # "An unexpected error..." is a plain string (v4 format)
            "An unexpected error occurred in system": "系统发生意外错误",
        }
        context_index = [
            {"tag": "tools", "start": 59, "end": 96},
        ]
        new_content, stats = apply_translations(
            content, translations, set(),
            raw_translations=raw_translations,
            context_index=context_index,
        )
        # First "Permission denied" at pos 7 (not in tools region) -> global "权限被拒绝"
        # "An unexpected error..." is long tier -> global "系统发生意外错误"
        # Second "Permission denied" at pos ~74 (in tools region) -> "工具权限不足"
        assert "权限被拒绝" in new_content
        assert "系统发生意外错误" in new_content
        assert "工具权限不足" in new_content

    def test_contextual_stats(self):
        """Stats include 'contextual' counter."""
        content = 'tool_name="Permission denied";'
        translations = {"Permission denied": "权限被拒绝"}
        raw_translations = {
            "Permission denied": {
                "zh": "权限被拒绝",
                "contexts": {"tools": "工具权限不足"},
            }
        }
        context_index = [
            {"tag": "tools", "start": 0, "end": 50},
        ]
        _, stats = apply_translations(
            content, translations, set(),
            raw_translations=raw_translations,
            context_index=context_index,
        )
        assert "contextual" in stats
        assert stats["contextual"] >= 1

    def test_apply_no_raw_translations(self):
        """Without raw_translations, use translations dict directly (v3 compat)."""
        content = 'var x="Permission denied";'
        translations = {"Permission denied": "权限被拒绝"}
        new_content, stats = apply_translations(
            content, translations, set(),
            raw_translations=None,
            context_index=None,
        )
        assert "权限被拒绝" in new_content
        assert stats["contextual"] == 0

    def test_long_string_context_aware(self):
        """Long strings: each occurrence independently selects translation by context."""
        # Two occurrences of same long string in different regions
        content = (
            'auth_token("An unexpected error occurred in processing");'
            'tool_name="An unexpected error occurred in processing";'
        )
        translations = {"An unexpected error occurred in processing": "处理中发生意外错误"}
        raw_translations = {
            "An unexpected error occurred in processing": {
                "zh": "处理中发生意外错误",
                "contexts": {"auth": "认证处理错误"},
            }
        }
        context_index = [
            {"tag": "auth", "start": 0, "end": 53},
            {"tag": "tools", "start": 53, "end": 110},
        ]
        new_content, stats = apply_translations(
            content, translations, set(),
            raw_translations=raw_translations,
            context_index=context_index,
        )
        # First occurrence in auth region -> "认证处理错误"
        assert "认证处理错误" in new_content
        # Second occurrence in tools region (no tools context) -> global fallback
        assert "处理中发生意外错误" in new_content
        assert stats["contextual"] >= 1

    def test_existing_tests_backward_compatible(self):
        """Verify that existing tests still pass with new params defaulting to None."""
        content = _load_fixture("sample_replacer_content.js")
        translations = {
            "An unexpected error occurred while processing your request.": "处理请求时发生意外错误。",
            "Permission denied": "权限被拒绝",
            "OK": "好的",
        }
        new_content, stats = apply_translations(content, translations, set())
        assert stats["long"] > 0
        assert stats["medium"] > 0
        assert stats["short"] > 0
