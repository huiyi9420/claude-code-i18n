"""Three-tier replacement engine for applying translations to CLI JavaScript content.

Strategy:
- Long strings (>20 chars): global str.replace with exact match (APPLY-02)
- Medium strings (10-20 chars): quote-boundary regex replacement (APPLY-03)
- Short strings (<10 chars): word-boundary + whitelist + frequency cap (APPLY-04)
- All replacements proceed longest-first to prevent partial matches (APPLY-05)
- Context-aware: uses raw_translations + context_index to select per-position translations
"""

import re
from typing import Dict, List, Optional, Set, Tuple


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


def _find_all_positions(content: str, en: str, tier: str) -> List[int]:
    """Find all match positions for an English string in content.

    Uses tier-appropriate matching strategy:
    - long: plain string find (all occurrences)
    - medium: quote-boundary regex
    - short: quote-boundary regex (same as medium for safety)

    Short strings now use quote-boundary matching instead of word-boundary,
    which is much safer — only matches inside quoted strings ("..." or '...'),
    preventing false matches in code logic like variable names or keywords.

    Args:
        content: The content to search in.
        en: The English string to find.
        tier: The replacement tier ('long', 'medium', 'short').

    Returns:
        List of start positions for all matches.
    """
    if tier == "long":
        positions = []
        start = 0
        while True:
            idx = content.find(en, start)
            if idx == -1:
                break
            positions.append(idx)
            start = idx + 1
        return positions
    else:
        # Both medium and short use quote-boundary regex for safety.
        # This prevents matching code identifiers or keywords.
        pattern = f"(?<=[\'\"]){re.escape(en)}(?=[\'\"])"
        return [m.start() for m in re.finditer(pattern, content)]


def _resolve_contextual(
    en: str,
    position: int,
    translations: Dict[str, str],
    raw_translations: Optional[Dict],
    context_index: Optional[List[dict]],
) -> Tuple[str, bool]:
    """Resolve which translation to use for a match at a given position.

    Args:
        en: The English source string.
        position: Character position of the match in content.
        translations: Flat {en: zh} dict (backward compat).
        raw_translations: Raw translation entries (may have contexts).
        context_index: Pre-built context index from build_context_index().

    Returns:
        Tuple of (chinese_translation, is_contextual).
        is_contextual is True if a context-specific translation was selected.
    """
    if raw_translations is None or context_index is None:
        return translations.get(en, ""), False

    raw_entry = raw_translations.get(en)
    if raw_entry is None:
        return translations.get(en, ""), False

    # Plain string entry (v4 format normalized to {"zh": value})
    if isinstance(raw_entry, str):
        return raw_entry, False

    # Dict entry - check if it has contexts
    if isinstance(raw_entry, dict) and "contexts" in raw_entry:
        from scripts.i18n.core.context_detector import detect_context  # noqa: lazy import to avoid circular
        context_tags = detect_context(context_index, position)
        contexts = raw_entry.get("contexts", {})

        # Check each context tag in order; first match wins
        for tag in context_tags:
            if tag in contexts:
                return contexts[tag], True

    # No context match or no contexts key -> use global default
    if isinstance(raw_entry, dict):
        return raw_entry.get("zh", ""), False

    return translations.get(en, ""), False


def apply_translations(
    content: str,
    translations: Dict[str, str],
    skip_words: Set[str],
    max_short_cap: int = 50,
    raw_translations: Optional[Dict] = None,
    context_index: Optional[List[dict]] = None,
) -> Tuple[str, dict]:
    """Apply all translations to content using three-tier strategy.

    When raw_translations and context_index are provided, the engine resolves
    translations per-position: strings in a context-tagged region get the
    context-specific translation, others get the global default. When these
    parameters are None, behavior is identical to v3.0 (backward compatible).

    Args:
        content: JavaScript source text.
        translations: Dict of {english: chinese} translation pairs.
        skip_words: Set of short words to skip (loaded from skip-words.json).
        max_short_cap: Maximum number of short-string replacements per entry.
        raw_translations: Optional raw translation entries (may contain contexts).
        context_index: Optional pre-built context index for position-aware translation.

    Returns:
        Tuple of (modified_content, stats_dict).
        Stats: {"long": N, "medium": N, "short": N, "skipped": N,
                "skip_reasons": {}, "contextual": N}
    """
    stats = {
        "long": 0,
        "medium": 0,
        "short": 0,
        "skipped": 0,
        "skip_reasons": {},
        "contextual": 0,
    }

    # APPLY-05: Sort by length descending to prevent partial matches
    items = sorted(translations.items(), key=lambda x: len(x[0]), reverse=True)

    # Collect all planned replacements: (position, original_en, resolved_zh, tier, is_contextual)
    # We resolve translations against ORIGINAL content positions before any replacement.
    planned = []

    for en, zh in items:
        # MAP-04: Skip identical entries
        if en == zh:
            stats["skipped"] += 1
            stats["skip_reasons"][en] = "identical"
            continue

        tier = classify_entry(en)

        if tier == "short" and en in skip_words:
            stats["skipped"] += 1
            stats["skip_reasons"][en] = "skip_word"
            continue

        # Find all match positions in the ORIGINAL content
        positions = _find_all_positions(content, en, tier)

        if not positions:
            continue

        # Apply frequency cap for short strings
        if tier == "short" and len(positions) > max_short_cap:
            positions = positions[:max_short_cap]

        # Resolve translation for each position
        for pos in positions:
            resolved, is_ctx = _resolve_contextual(
                en, pos, translations, raw_translations, context_index
            )
            planned.append((pos, len(en), resolved, tier, is_ctx))

    # APPLY-05: Remove shorter matches that overlap with longer matches.
    # Process in order of descending string length so longer matches take priority.
    planned.sort(key=lambda x: x[1], reverse=True)  # sort by match length descending
    consumed_ranges = []  # list of (start, end) for accepted matches
    filtered = []
    for pos, en_len, zh, tier, is_ctx in planned:
        overlap = False
        for cs, ce in consumed_ranges:
            if pos < ce and pos + en_len > cs:
                overlap = True
                break
        if not overlap:
            filtered.append((pos, en_len, zh, tier, is_ctx))
            consumed_ranges.append((pos, pos + en_len))

    # Sort by position descending (reverse order) to preserve offsets during replacement
    filtered.sort(key=lambda x: x[0], reverse=True)

    # Execute replacements in reverse order
    for pos, en_len, zh, tier, is_ctx in filtered:
        content = content[:pos] + zh + content[pos + en_len:]
        stats[tier] += 1
        if is_ctx:
            stats["contextual"] += 1

    return content, stats
