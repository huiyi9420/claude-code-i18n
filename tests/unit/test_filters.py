"""Tests for noise filter and UI indicator scoring (EXTRACT-02/03)."""

import pytest


class TestNoiseFilter:
    """Tests for noise_filter module (EXTRACT-03)."""

    def test_noise_re_matches_known_noise(self):
        """EXTRACT-03: Known noise keywords match."""
        from scripts.i18n.filters.noise_filter import is_noise

        assert is_noise("azure authentication failed")
        assert is_noise("grpc connection error")
        assert is_noise("protobuf serialization error")
        assert is_noise("aws s3 bucket not found")
        assert is_noise("telemetry data")

    def test_noise_re_rejects_ui_string(self):
        """EXTRACT-03: UI strings like 'Plan Mode' do NOT match."""
        from scripts.i18n.filters.noise_filter import is_noise

        assert not is_noise("Plan Mode")
        assert not is_noise("Auto mode")
        assert not is_noise("Extended thinking")
        assert not is_noise("Accept edits")

    def test_noise_re_case_insensitive(self):
        """EXTRACT-03: Matching is case-insensitive."""
        from scripts.i18n.filters.noise_filter import is_noise

        assert is_noise("Azure Subscription")
        assert is_noise("GRPC Service")
        assert is_noise("AWS Region")

    def test_noise_compiled_pattern(self):
        """EXTRACT-03: NOISE_RE is a compiled regex pattern."""
        import re
        from scripts.i18n.filters.noise_filter import NOISE_RE

        assert isinstance(NOISE_RE, re.Pattern)


class TestUIIndicator:
    """Tests for ui_indicator module (EXTRACT-02)."""

    def test_strong_indicator_score(self):
        """EXTRACT-02: Strong indicator scores 1000 + count."""
        from scripts.i18n.filters.ui_indicator import score_candidate

        result = score_candidate("Extended thinking is enabled", 3)
        assert result["score"] == 1003
        assert result["type"] == "strong"

    def test_weak_indicator_score(self):
        """EXTRACT-02: Weak indicator scores 0 + count."""
        from scripts.i18n.filters.ui_indicator import score_candidate

        result = score_candidate("loading please wait", 5)
        assert result["score"] == 5
        assert result["type"] == "weak"

    def test_no_indicator_score(self):
        """EXTRACT-02: No indicator scores 0, type 'none'."""
        from scripts.i18n.filters.ui_indicator import score_candidate

        result = score_candidate("Random text here", 2)
        assert result["score"] == 0
        assert result["type"] == "none"

    def test_strong_overrides_weak(self):
        """EXTRACT-02: If both strong and weak indicators present, strong wins."""
        from scripts.i18n.filters.ui_indicator import score_candidate

        # "permission" is weak, "sandbox" is strong
        result = score_candidate("sandbox permission denied", 1)
        assert result["type"] == "strong"
        assert result["score"] == 1001

    def test_strong_indicators_count(self):
        """EXTRACT-02: STRONG_INDICATORS has expected count (from v3.0)."""
        from scripts.i18n.filters.ui_indicator import STRONG_INDICATORS

        assert len(STRONG_INDICATORS) >= 15
        # Verify key entries from v3.0
        indicators_lower = [s.lower() for s in STRONG_INDICATORS]
        assert "plan mode" in indicators_lower
        assert "extended thinking" in indicators_lower

    def test_weak_indicators_count(self):
        """EXTRACT-02: WEAK_INDICATORS has expected count (from v3.0)."""
        from scripts.i18n.filters.ui_indicator import WEAK_INDICATORS

        assert len(WEAK_INDICATORS) >= 20
        indicators_lower = [s.lower() for s in WEAK_INDICATORS]
        assert "loading" in indicators_lower
        assert "permission" in indicators_lower

    def test_score_candidate_zero_count(self):
        """EXTRACT-02: Zero count still gets base strong score."""
        from scripts.i18n.filters.ui_indicator import score_candidate

        result = score_candidate("Plan Mode activated", 0)
        assert result["score"] == 1000
        assert result["type"] == "strong"
