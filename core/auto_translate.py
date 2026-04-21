"""Rule-based auto-translation engine for new CLI string candidates.

Uses pattern matching (no external API) to automatically translate
high-confidence strings. Low-confidence strings are flagged for human review.

Rules:
1. Known phrase dictionary (auto-translate-dict.json)
2. Prefix/suffix match with existing translations
3. Common UI sentence patterns (regex templates)
4. Loading verb pattern ("XXing" -> "XX中")
"""

import json
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# UI sentence pattern templates: (english_regex, chinese_template)
# {action} and {noun} are placeholders extracted from the match
UI_TEMPLATES: List[Tuple[re.Pattern, str]] = [
    (re.compile(r'^Failed to (.+)$'), '{0}失败'),
    (re.compile(r'^Unable to (.+)$'), '无法{0}'),
    (re.compile(r'^Cannot (.+)$'), '无法{0}'),
    (re.compile(r'^Could not (.+)$'), '无法{0}'),
    (re.compile(r'^Please (.+) to continue$'), '请{0}以继续'),
    (re.compile(r'^Please (.+)$'), '请{0}'),
    (re.compile(r'^Are you sure you want to (.+)\?$'), '确定要{0}吗？'),
    (re.compile(r'^Do you want to (.+)\?$'), '要{0}吗？'),
    (re.compile(r'^Would you like to (.+)\?$'), '要{0}吗？'),
    (re.compile(r'^Click (.+) to (.+)$'), '点击{0}以{1}'),
    (re.compile(r'^Press (.+) to (.+)$'), '按{0}以{1}'),
    (re.compile(r'^Enter (.+) to (.+)$'), '输入{0}以{1}'),
    (re.compile(r'^(.+) is required$'), '{0}是必填项'),
    (re.compile(r'^(.+) is not (?:a )?valid (.+)$'), '{0}不是有效的{1}'),
    (re.compile(r'^(.+) has been (.+)$'), '{0}已被{1}'),
    (re.compile(r'^(.+) will be (.+)$'), '{0}将被{1}'),
    (re.compile(r'^No (.+) (?:was )?found$'), '未找到{0}'),
    (re.compile(r'^(.+) not found$'), '{0}未找到'),
    (re.compile(r'^(.+) already exists$'), '{0}已存在'),
    (re.compile(r'^Waiting for (.+)$'), '等待{0}'),
    (re.compile(r'^Connecting to (.+)$'), '正在连接{0}'),
    (re.compile(r'^Disconnecting from (.+)$'), '正在断开与{0}的连接'),
]

# Loading verb suffixes
_LOADING_VERB_RE = re.compile(r'^([A-Z][a-z]+)ing$')


def _load_dictionary(dict_path: Optional[Path]) -> Dict[str, str]:
    """Load the known phrase dictionary from JSON file."""
    if dict_path is None or not dict_path.exists():
        return {}
    try:
        return json.loads(dict_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}


def _try_prefix_suffix_match(
    en: str, existing_translations: Dict[str, str]
) -> Optional[str]:
    """Try to translate by finding longest common prefix/suffix match."""
    best_match = None
    best_overlap = 0

    for existing_en, existing_zh in existing_translations.items():
        # Find common prefix length
        prefix_len = 0
        for i in range(min(len(en), len(existing_en))):
            if en[i].lower() == existing_en[i].lower():
                prefix_len += 1
            else:
                break

        if prefix_len >= 10 and prefix_len > best_overlap:
            # Replace the differing suffix
            old_suffix = existing_en[prefix_len:]
            new_suffix = en[prefix_len:]
            if old_suffix and new_suffix:
                translated = existing_zh
                best_overlap = prefix_len
                best_match = translated

        # Find common suffix length
        suffix_len = 0
        for i in range(1, min(len(en), len(existing_en)) + 1):
            if en[-i].lower() == existing_en[-i].lower():
                suffix_len += 1
            else:
                break

        if suffix_len >= 10 and suffix_len > best_overlap:
            old_prefix = existing_en[:len(existing_en) - suffix_len]
            new_prefix = en[:len(en) - suffix_len]
            if old_prefix and new_prefix:
                translated = existing_zh
                best_overlap = suffix_len
                best_match = translated

    return best_match


def _try_ui_template(en: str) -> Optional[Tuple[str, str]]:
    """Try to match against UI sentence patterns.

    Returns (translated_string, template_name) or None.
    """
    for pattern, template in UI_TEMPLATES:
        m = pattern.match(en)
        if m:
            groups = m.groups()
            # Simple: use the captured groups as-is in template
            translated = template.format(*groups)
            return translated, f"ui_template:{pattern.pattern[:30]}"
    return None


def _try_loading_verb(en: str) -> Optional[Tuple[str, str]]:
    """Try to translate loading verb pattern (XXing -> XX中)."""
    m = _LOADING_VERB_RE.match(en)
    if m:
        base = m.group(1)
        return f"{base}中", "loading_verb"
    return None


def auto_translate_candidates(
    candidates: list,
    existing_translations: dict,
    score_threshold: int = 1000,
    dict_path: Optional[Path] = None,
) -> dict:
    """Auto-translate high-confidence string candidates.

    Args:
        candidates: List of candidate dicts from scan_candidates() or diff.
        existing_translations: Current translations dict for pattern reference.
        score_threshold: Minimum score for auto-translation (default 1000).
        dict_path: Path to auto-translate-dict.json.

    Returns:
        dict with:
        - translated: dict of {en: zh} for auto-translated entries.
        - review: list of candidate dicts needing human review.
        - skipped: list of candidate dicts that were too low-score.
        - rules_used: dict of {en: rule_name} showing which rule matched.
    """
    dictionary = _load_dictionary(dict_path)
    translated = {}
    review = []
    skipped = []
    rules_used = {}

    for cand in candidates:
        en = cand["en"] if isinstance(cand, dict) else cand
        score = cand.get("score", 0) if isinstance(cand, dict) else 0

        # Below threshold -> skip entirely
        if score < score_threshold:
            skipped.append(cand)
            continue

        # Rule 1: Dictionary match
        if en in dictionary:
            translated[en] = dictionary[en]
            rules_used[en] = "dictionary"
            continue

        # Rule 2: Exact match in existing translations
        if en in existing_translations:
            translated[en] = existing_translations[en]
            rules_used[en] = "exact_match"
            continue

        # Rule 3: UI template match
        template_result = _try_ui_template(en)
        if template_result:
            translated[en] = template_result[0]
            rules_used[en] = template_result[1]
            continue

        # Rule 4: Loading verb pattern
        verb_result = _try_loading_verb(en)
        if verb_result:
            translated[en] = verb_result[0]
            rules_used[en] = verb_result[1]
            continue

        # Rule 5: Prefix/suffix match (most complex, try last)
        prefix_result = _try_prefix_suffix_match(en, existing_translations)
        if prefix_result:
            translated[en] = prefix_result
            rules_used[en] = "prefix_suffix_match"
            continue

        # No rule matched -> review
        review.append(cand)

    return {
        "translated": translated,
        "review": review,
        "skipped": skipped,
        "rules_used": rules_used,
    }
