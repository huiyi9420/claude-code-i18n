"""Three-tier replacement engine for applying translations to CLI JavaScript content.

Strategy:
- Long strings (>20 chars): global str.replace with exact match (APPLY-02)
- Medium strings (10-20 chars): quote-boundary regex replacement (APPLY-03)
- Short strings (<10 chars): word-boundary + whitelist + frequency cap (APPLY-04)
- All replacements proceed longest-first to prevent partial matches (APPLY-05)
"""

import re
from typing import Dict, Set, Tuple


def classify_entry(en: str) -> str:
    """Classify string length into replacement tier.

    Args:
        en: English source string.

    Returns:
        'long' if len > 20, 'medium' if len > 10, 'short' otherwise.
    """
    n = len(en)
    if n > 20:
        return "long"
    elif n > 10:
        return "medium"
    else:
        return "short"


def apply_translations(
    content: str,
    translations: Dict[str, str],
    skip_words: Set[str],
    max_short_cap: int = 50,
) -> Tuple[str, dict]:
    """Apply all translations to content using three-tier strategy.

    Args:
        content: JavaScript source text.
        translations: Dict of {english: chinese} translation pairs.
        skip_words: Set of short words to skip (loaded from skip-words.json).
        max_short_cap: Maximum number of short-string replacements per entry.

    Returns:
        Tuple of (modified_content, stats_dict).
        Stats: {"long": N, "medium": N, "short": N, "skipped": N, "skip_reasons": {}}
    """
    stats = {"long": 0, "medium": 0, "short": 0, "skipped": 0, "skip_reasons": {}}

    # APPLY-05: Sort by length descending to prevent partial matches
    items = sorted(translations.items(), key=lambda x: len(x[0]), reverse=True)

    for en, zh in items:
        # MAP-04: Skip identical entries
        if en == zh:
            stats["skipped"] += 1
            stats["skip_reasons"][en] = "identical"
            continue

        tier = classify_entry(en)

        if tier == "long":
            # APPLY-02: Global str.replace for long strings
            count = content.count(en)
            if count > 0:
                content = content.replace(en, zh)
                stats["long"] += count

        elif tier == "medium":
            # APPLY-03: Quote-boundary constrained replacement
            pattern = f"(?<=[\'\"]){re.escape(en)}(?=[\'\"])"
            matches = list(re.finditer(pattern, content))
            if matches:
                # Reverse order to preserve positions (Pattern 2)
                for m in reversed(matches):
                    content = content[: m.start()] + zh + content[m.end() :]
                stats["medium"] += len(matches)

        else:  # short
            # APPLY-04: Skip if in skip_words whitelist
            if en in skip_words:
                stats["skipped"] += 1
                stats["skip_reasons"][en] = "skip_word"
                continue

            # Word-boundary + context constraint
            pattern = f"(?<=[\'\"\\s>])\\b{re.escape(en)}\\b(?=[\'\"\\s<])"
            matches = list(re.finditer(pattern, content))
            if matches:
                cap = min(len(matches), max_short_cap)
                for m in reversed(matches[:cap]):
                    content = content[: m.start()] + zh + content[m.end() :]
                stats["short"] += cap

    return content, stats
