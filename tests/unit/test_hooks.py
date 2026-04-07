"""Tests for hook replacement engine."""

from scripts.i18n.core.hooks import apply_hook_replacements, HOOK_REPLACEMENTS


class TestHookReplacements:
    """Test apply_hook_replacements function."""

    def test_all_patterns_replaced(self):
        """All hook patterns should be replaced in a combined string."""
        # Build a string containing all hook patterns
        parts = list(HOOK_REPLACEMENTS.keys())
        content = "|||".join(parts)
        modified, stats = apply_hook_replacements(content)
        assert stats["hook_replacements"] == len(parts)
        # Verify no English pattern remains
        for en in HOOK_REPLACEMENTS:
            assert en not in modified

    def test_empty_content(self):
        """Empty content should return empty with zero stats."""
        modified, stats = apply_hook_replacements("")
        assert modified == ""
        assert stats["hook_replacements"] == 0

    def test_no_matches(self):
        """Content without hook patterns should be unchanged."""
        content = 'var x = "Hello World"; console.log("test");'
        modified, stats = apply_hook_replacements(content)
        assert modified == content
        assert stats["hook_replacements"] == 0

    def test_multiple_occurrences(self):
        """Same pattern appearing multiple times should all be replaced."""
        content = ' says: '.join(["A", "B", "C"])  # 2 occurrences
        modified, stats = apply_hook_replacements(content)
        assert " says: " not in modified
        assert stats["hook_replacements"] == 2
        assert stats["details"][" says: "] == 2

    def test_idempotent(self):
        """Applying hook replacements twice should produce no additional changes."""
        content = 'hook returned blocking error and  says: hello'
        modified1, stats1 = apply_hook_replacements(content)
        modified2, stats2 = apply_hook_replacements(modified1)
        assert stats2["hook_replacements"] == 0
        assert modified2 == modified1

    def test_details_tracking(self):
        """Stats should track per-pattern replacement counts."""
        content = ' says: A says: B hook error hook error'
        modified, stats = apply_hook_replacements(content)
        assert " says: " in stats["details"]
        assert " hook error" in stats["details"]
        assert stats["details"][" says: "] == 2
        assert stats["details"][" hook error"] == 2

    def test_individual_patterns(self):
        """Each hook pattern should produce the correct Chinese replacement."""
        for en, zh in HOOK_REPLACEMENTS.items():
            content = f"before{en}after"
            modified, stats = apply_hook_replacements(content)
            assert zh in modified, f"Pattern '{en}' was not replaced with '{zh}'"
            assert en not in modified, f"Pattern '{en}' still present after replacement"
