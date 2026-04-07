"""Translation quality validation command for Claude Code i18n engine.

Detects three categories of translation quality issues:
1. chinese_english_mixing — untranslated English words mixed into Chinese text
2. synonym_inconsistency — same canonical English with different Chinese translations
3. placeholder_missing — format placeholders lost during translation

Usage:
    python3 scripts/engine.py validate

Output: JSON report to stdout with issue counts and details.
"""

import re
from pathlib import Path
from typing import Dict, List

from scripts.i18n.cli import output_json, get_cli_dir
from scripts.i18n.config.constants import MAP_FILE
from scripts.i18n.config.paths import get_data_dir
from scripts.i18n.io.translation_map import load_translation_map

# English words commonly used as technical terms that should NOT be flagged
# as chinese_english_mixing. Case-insensitive matching.
ENGLISH_WHITELIST = frozenset({
    "claude", "code", "mcp", "api", "cli", "url", "ssh", "git", "sdk",
    "json", "html", "css", "node", "npm", "lsp", "sse", "ide", "pdf",
    "dxt", "nan", "oauth", "id", "ui", "cpu", "gpu", "ram", "tcp", "udp",
    "http", "https", "dns", "ssl", "tls", "uri", "ip", "mac", "ios",
    "android", "linux", "macos", "windows", "unix", "sql", "no", "sql",
})

# Regex to find consecutive English letter sequences (3+ chars) in translation values
_ENGLISH_WORD_RE = re.compile(r'[a-zA-Z]{3,}')

# Regex to extract format placeholders from source strings
_PLACEHOLDER_RE = re.compile(r'%[sdifo]|\$\{[^}]+\}|\{[^}]+\}')


def check_chinese_english_mixing(translations: Dict[str, str]) -> List[dict]:
    """Detect untranslated English words mixed into Chinese translations.

    Scans each translation value for consecutive English letter sequences
    of length 3 or more that are not in the whitelist.

    Args:
        translations: Dict of {english_source: chinese_translation}.

    Returns:
        List of issue dicts with type, key, value, and detail.
    """
    issues = []
    for en_key, zh_value in translations.items():
        # Skip non-string values
        if not isinstance(zh_value, str):
            continue

        english_matches = _ENGLISH_WORD_RE.findall(zh_value)
        flagged_words = []
        for word in english_matches:
            if word.lower() not in ENGLISH_WHITELIST:
                flagged_words.append(word)

        if flagged_words:
            issues.append({
                "type": "chinese_english_mixing",
                "key": en_key,
                "value": zh_value,
                "detail": f"翻译中包含未翻译的英文片段: {', '.join(repr(w) for w in flagged_words)}",
            })

    return issues


def check_synonym_inconsistency(translations: Dict[str, str]) -> List[dict]:
    """Detect inconsistent Chinese translations for same canonical English.

    Canonicalizes English source keys by lowercasing and stripping
    punctuation. If the same canonical form maps to different Chinese
    translations, flags as an issue.

    Args:
        translations: Dict of {english_source: chinese_translation}.

    Returns:
        List of issue dicts with type, canonical form, and entries.
    """
    # Build canonical -> [(original_key, translation)] mapping
    canonical_map: Dict[str, List[dict]] = {}
    for en_key, zh_value in translations.items():
        # Canonicalize: lowercase + strip punctuation
        canonical = re.sub(r'[^\w\s]', '', en_key.lower()).strip()
        canonical = re.sub(r'\s+', ' ', canonical)
        if canonical not in canonical_map:
            canonical_map[canonical] = []
        canonical_map[canonical].append({"en": en_key, "zh": zh_value})

    issues = []
    for canonical, entries in canonical_map.items():
        # Find entries with different Chinese translations
        if len(entries) < 2:
            continue

        unique_zh = set()
        for entry in entries:
            unique_zh.add(entry["zh"])

        if len(unique_zh) > 1:
            issues.append({
                "type": "synonym_inconsistency",
                "canonical": canonical,
                "entries": entries,
            })

    return issues


def check_placeholder_missing(translations: Dict[str, str]) -> List[dict]:
    """Detect format placeholders present in source but missing in translation.

    Checks for printf-style (%s, %d, etc.), template literal (${var}),
    and brace-style ({0}, {name}) placeholders.

    Args:
        translations: Dict of {english_source: chinese_translation}.

    Returns:
        List of issue dicts with type, key, value, and detail.
    """
    issues = []
    for en_key, zh_value in translations.items():
        if not isinstance(en_key, str) or not isinstance(zh_value, str):
            continue

        source_placeholders = _PLACEHOLDER_RE.findall(en_key)
        if not source_placeholders:
            continue

        # Check which placeholders are missing from the translation
        missing = []
        for ph in source_placeholders:
            if ph not in zh_value:
                missing.append(ph)

        if missing:
            issues.append({
                "type": "placeholder_missing",
                "key": en_key,
                "value": zh_value,
                "detail": f"原文占位符 {repr(missing)} 在翻译中丢失",
            })

    return issues


def validate_translations(translations: Dict[str, str]) -> dict:
    """Run all quality checks and produce a validation report.

    Args:
        translations: Dict of {english_source: chinese_translation}.

    Returns:
        Validation report dict with ok, total_entries, issues_found,
        issues_by_type, and issues fields.
    """
    all_issues = []

    all_issues.extend(check_chinese_english_mixing(translations))
    all_issues.extend(check_synonym_inconsistency(translations))
    all_issues.extend(check_placeholder_missing(translations))

    # Count by type
    issues_by_type = {}
    for issue in all_issues:
        t = issue["type"]
        issues_by_type[t] = issues_by_type.get(t, 0) + 1

    return {
        "ok": len(all_issues) == 0,
        "total_entries": len(translations),
        "issues_found": len(all_issues),
        "issues_by_type": issues_by_type,
        "issues": all_issues,
    }


def cmd_validate() -> None:
    """CLI entry point for the validate command.

    Loads the translation map and outputs a JSON quality report.
    """
    data_dir = get_data_dir()
    map_path = data_dir / MAP_FILE

    if not map_path.exists():
        from scripts.i18n.cli import output_error
        output_error(
            f"Translation map not found: {map_path}",
            hint="Run 'extract' first to generate the translation map.",
        )
        return

    map_data = load_translation_map(map_path)
    report = validate_translations(map_data["translations"])
    output_json(report)
