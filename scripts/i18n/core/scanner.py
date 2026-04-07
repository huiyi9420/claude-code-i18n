"""String scanner for Claude Code i18n engine.

Extracts translatable string candidates from JavaScript source content.
Applies noise filtering, signal scoring, and CJK exclusion.
"""

import re
from typing import List, Optional, Set

from scripts.i18n.core.context_detector import detect_context
from scripts.i18n.filters.ui_indicator import score_candidate

# CJK character range for exclusion (EXTRACT-06)
CJK_PATTERN = re.compile(r"[\u4e00-\u9fff]")

# Code fragment patterns to exclude (EXTRACT-03)
CODE_FRAGMENTS = ["=>", "${", "===", "!==", "async ", "function ", ".prototype.", "()"]

# Regex pattern for extracting double-quoted candidate strings
_CANDIDATE_RE = re.compile(r'"([A-Z][A-Za-z][^"]{4,120})"')


def scan_candidates(
    content: str,
    existing: Set[str],
    skipped: Set[str],
    noise_re: re.Pattern,
    context_index: Optional[list] = None,
) -> List[dict]:
    """Scan content for translatable string candidates.

    Extracts double-quoted English strings, applies filtering rules,
    scores by signal strength, and returns sorted candidates.

    Args:
        content: The JavaScript source content to scan.
        existing: Set of already-translated strings to exclude.
        skipped: Set of already-skipped strings to exclude.
        noise_re: Compiled regex pattern for noise filtering.
        context_index: Pre-built context index from build_context_index().
            When provided, each candidate includes a "contexts" field
            listing the component regions where the string appears.

    Returns:
        List of candidate dicts sorted by score descending.
        Each dict has: {"en": str, "count": int, "score": int, "type": str,
                        "contexts": list[str]}
        contexts is empty list when context_index is None (backward compat).
        contexts is ["default"] when string not in any known region.
        contexts lists sorted tag names when string is in known regions.
    """
    # Extract candidates using finditer to preserve position info
    candidate_matches = list(_CANDIDATE_RE.finditer(content))

    # Build position lookup: string -> list of match positions
    string_positions = {}
    for m in candidate_matches:
        s = m.group(1)
        string_positions.setdefault(s, []).append(m.start())

    results = []

    for s, positions in string_positions.items():
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

        # Determine context tags from positions
        if context_index is not None:
            all_tags = set()
            for pos in positions:
                tags = detect_context(context_index, pos)
                all_tags.update(tags)
            ctx = sorted(all_tags) if all_tags else ["default"]
        else:
            ctx = []

        results.append({
            "en": s,
            "count": count,
            "score": result["score"],
            "type": result["type"],
            "contexts": ctx,
        })

    # Sort by score descending (EXTRACT-04)
    results.sort(key=lambda x: x["score"], reverse=True)
    return results
