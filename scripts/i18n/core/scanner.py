"""String scanner for Claude Code i18n engine.

Extracts translatable string candidates from JavaScript source content.
Applies noise filtering, signal scoring, and CJK exclusion.
"""

import re
from typing import List, Set

from scripts.i18n.filters.ui_indicator import score_candidate

# CJK character range for exclusion (EXTRACT-06)
CJK_PATTERN = re.compile(r"[\u4e00-\u9fff]")

# Code fragment patterns to exclude (EXTRACT-03)
CODE_FRAGMENTS = ["=>", "${", "===", "!==", "async ", "function ", ".prototype.", "()"]


def scan_candidates(
    content: str,
    existing: Set[str],
    skipped: Set[str],
    noise_re: re.Pattern,
) -> List[dict]:
    """Scan content for translatable string candidates.

    Extracts double-quoted English strings, applies filtering rules,
    scores by signal strength, and returns sorted candidates.

    Args:
        content: The JavaScript source content to scan.
        existing: Set of already-translated strings to exclude.
        skipped: Set of already-skipped strings to exclude.
        noise_re: Compiled regex pattern for noise filtering.

    Returns:
        List of candidate dicts sorted by score descending.
        Each dict has: {"en": str, "count": int, "score": int, "type": str}
    """
    # Extract candidates: double-quoted strings starting with capital letter,
    # at least 3 chars of [A-Za-z...], total 6-122 chars
    candidates = re.findall(r'"([A-Z][A-Za-z][^"]{4,120})"', content)

    results = []
    seen = set()

    for s in candidates:
        # Deduplicate
        if s in seen:
            continue
        seen.add(s)

        # Exclude already-translated or already-skipped (EXTRACT-05)
        if s in existing or s in skipped:
            continue

        # Must contain space (natural language) (EXTRACT-03)
        if " " not in s:
            continue

        # Exclude code fragments (EXTRACT-03)
        if any(c in s for c in CODE_FRAGMENTS):
            continue

        # Exclude URLs (EXTRACT-03)
        sl = s.lower()
        if "http://" in sl or "https://" in sl:
            continue

        # Exclude ALL_CAPS strings > 5 chars (EXTRACT-03)
        if s == s.upper() and len(s) > 5:
            continue

        # Exclude noise matches (EXTRACT-03)
        if noise_re.search(s):
            continue

        # Exclude CJK characters (EXTRACT-06)
        if CJK_PATTERN.search(s):
            continue

        # Exclude underscore-only identifiers without natural punctuation (EXTRACT-03)
        if "_" in s and not any(c in s for c in " .,;:!?"):
            continue

        # Count exact quoted occurrences
        count = content.count(f'"{s}"')

        # Score candidate using UI indicators
        result = score_candidate(s, count)

        # Only include strings with signal (EXTRACT-02)
        if result["type"] == "none":
            continue

        results.append({
            "en": s,
            "count": count,
            "score": result["score"],
            "type": result["type"],
        })

    # Sort by score descending (EXTRACT-04)
    results.sort(key=lambda x: x["score"], reverse=True)
    return results
