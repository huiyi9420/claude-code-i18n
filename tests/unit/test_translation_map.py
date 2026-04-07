"""Tests for translation map loader and skip words (MAP-01~04).

Extended with v6 context-aware format tests (CTX-01).
"""

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


# ============================================================
# v6 context-aware format tests (CTX-01)
# ============================================================


class TestLoadV6Format:
    """Tests for v6 format with context-aware translations."""

    def test_load_v6_format_with_contexts(self, tmp_path):
        """CTX-01: Load entries with contexts field."""
        from scripts.i18n.io.translation_map import load_translation_map

        data = {
            "_meta": {"version": "6.0.0"},
            "translations": {
                "Error": {
                    "zh": "错误",
                    "contexts": {
                        "tools": "工具错误",
                        "auth": "认证错误",
                    },
                },
            },
        }
        p = tmp_path / "v6.json"
        p.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")

        result = load_translation_map(p)
        # translations 仍然展平为 {en: zh}
        assert result["translations"]["Error"] == "错误"
        # raw_translations 保留完整结构
        assert "raw_translations" in result
        raw_error = result["raw_translations"]["Error"]
        assert raw_error["zh"] == "错误"
        assert raw_error["contexts"]["tools"] == "工具错误"
        assert raw_error["contexts"]["auth"] == "认证错误"

    def test_load_v4_string_backward_compat(self, tmp_path):
        """CTX-01: Pure string values treated as {zh: value}."""
        from scripts.i18n.io.translation_map import load_translation_map

        data = {
            "_meta": {"version": "4.0.0"},
            "translations": {
                "Loading": "加载中",
                "Plan Mode": "规划模式",
            },
        }
        p = tmp_path / "v4.json"
        p.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")

        result = load_translation_map(p)
        assert result["translations"]["Loading"] == "加载中"
        assert result["translations"]["Plan Mode"] == "规划模式"
        # raw_translations 中字符串值被规范化为 {"zh": value}
        assert result["raw_translations"]["Loading"] == {"zh": "加载中"}
        assert result["raw_translations"]["Plan Mode"] == {"zh": "规划模式"}

    def test_load_v5_dict_backward_compat(self, tmp_path):
        """CTX-01: Dict with only zh key (no contexts) works normally."""
        from scripts.i18n.io.translation_map import load_translation_map

        data = {
            "_meta": {"version": "5.0.0"},
            "translations": {
                "Auto mode": {"zh": "自动模式"},
            },
        }
        p = tmp_path / "v5.json"
        p.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")

        result = load_translation_map(p)
        assert result["translations"]["Auto mode"] == "自动模式"
        assert result["raw_translations"]["Auto mode"] == {"zh": "自动模式"}

    def test_mixed_format(self, tmp_path):
        """CTX-01: Mix of v4 (string), v5 (zh-only), v6 (with contexts)."""
        from scripts.i18n.io.translation_map import load_translation_map

        data = {
            "_meta": {"version": "6.0.0"},
            "translations": {
                "Loading": "加载中",
                "Auto mode": {"zh": "自动模式"},
                "Error": {
                    "zh": "错误",
                    "contexts": {
                        "tools": "工具错误",
                        "auth": "认证错误",
                    },
                },
            },
        }
        p = tmp_path / "mixed_v6.json"
        p.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")

        result = load_translation_map(p)
        assert result["translations"]["Loading"] == "加载中"
        assert result["translations"]["Auto mode"] == "自动模式"
        assert result["translations"]["Error"] == "错误"
        # raw_translations preserves full structure
        assert result["raw_translations"]["Loading"] == {"zh": "加载中"}
        assert result["raw_translations"]["Auto mode"] == {"zh": "自动模式"}
        assert result["raw_translations"]["Error"]["contexts"]["tools"] == "工具错误"


class TestResolveTranslation:
    """Tests for resolve_translation function."""

    def test_resolve_translation_exact_context(self):
        """CTX-01: Returns context-specific translation when tag matches."""
        from scripts.i18n.io.translation_map import resolve_translation

        entry = {
            "zh": "错误",
            "contexts": {
                "tools": "工具错误",
                "auth": "认证错误",
            },
        }
        assert resolve_translation(entry, ["tools"]) == "工具错误"
        assert resolve_translation(entry, ["auth"]) == "认证错误"

    def test_resolve_translation_fallback(self):
        """CTX-01: Falls back to zh default when no context matches."""
        from scripts.i18n.io.translation_map import resolve_translation

        entry = {
            "zh": "错误",
            "contexts": {
                "tools": "工具错误",
            },
        }
        assert resolve_translation(entry, ["unknown"]) == "错误"

    def test_resolve_translation_no_contexts(self):
        """CTX-01: Returns zh value directly when no contexts field."""
        from scripts.i18n.io.translation_map import resolve_translation

        entry = {"zh": "自动模式"}
        assert resolve_translation(entry, ["tools"]) == "自动模式"

    def test_resolve_translation_string_entry(self):
        """CTX-01: String entry returned as-is."""
        from scripts.i18n.io.translation_map import resolve_translation

        assert resolve_translation("加载中", ["tools"]) == "加载中"

    def test_resolve_translation_empty_tags(self):
        """CTX-01: Empty context tags returns default zh."""
        from scripts.i18n.io.translation_map import resolve_translation

        entry = {
            "zh": "错误",
            "contexts": {
                "tools": "工具错误",
            },
        }
        assert resolve_translation(entry, []) == "错误"

    def test_resolve_translation_multiple_tags_priority(self):
        """CTX-01: First matching context tag wins when multiple provided."""
        from scripts.i18n.io.translation_map import resolve_translation

        entry = {
            "zh": "错误",
            "contexts": {
                "tools": "工具错误",
                "auth": "认证错误",
            },
        }
        # 第一个匹配的 tag 优先
        assert resolve_translation(entry, ["tools", "auth"]) == "工具错误"
        assert resolve_translation(entry, ["auth", "tools"]) == "认证错误"


class TestSaveV6Format:
    """Tests for save_translation_map with v6 format."""

    def test_save_v6_format(self, tmp_path):
        """CTX-01: Saving with raw_translations preserves contexts."""
        from scripts.i18n.io.translation_map import (
            load_translation_map,
            save_translation_map,
        )

        raw_translations = {
            "Error": {
                "zh": "错误",
                "contexts": {
                    "tools": "工具错误",
                    "auth": "认证错误",
                },
            },
            "Loading": {"zh": "加载中"},
        }
        p = tmp_path / "save_v6.json"
        save_translation_map(p, {"version": "6.0.0"}, raw_translations)

        # 重新加载验证格式一致
        result = load_translation_map(p)
        assert result["translations"]["Error"] == "错误"
        assert result["translations"]["Loading"] == "加载中"
        assert result["raw_translations"]["Error"]["contexts"]["tools"] == "工具错误"
        assert result["raw_translations"]["Error"]["contexts"]["auth"] == "认证错误"

    def test_save_v6_preserves_string_values(self, tmp_path):
        """CTX-01: Saving plain string values round-trips correctly."""
        from scripts.i18n.io.translation_map import (
            load_translation_map,
            save_translation_map,
        )

        translations = {
            "Loading": "加载中",
            "Plan Mode": {"zh": "规划模式"},
        }
        p = tmp_path / "save_strings.json"
        save_translation_map(p, {"version": "6.0.0"}, translations)

        result = load_translation_map(p)
        assert result["translations"]["Loading"] == "加载中"
        assert result["translations"]["Plan Mode"] == "规划模式"
