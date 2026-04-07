"""Context detection module for Claude Code i18n engine.

Identifies functional regions within cli.js content by pattern matching,
enabling context-aware translation (same English string can have different
Chinese translations depending on which component it belongs to).

Usage:
    index = build_context_index(cli_js_content)
    tags = detect_context(index, match_position)
    # tags is like ["tools", "permission"]
"""

import re

# Context patterns: (compiled regex, tag name)
# Each pattern identifies a functional region in cli.js
CONTEXT_PATTERNS = [
    (re.compile(r'tool_name|toolResult|tool_use'), "tools"),
    (re.compile(r'auth|login|token|credential'), "auth"),
    (re.compile(r'mcp_server|mcp_tool|McpServer'), "mcp"),
    (re.compile(r'status_bar|StatusItem'), "status"),
    (re.compile(r'config|settings|preference'), "config"),
    (re.compile(r'permission|approve|deny'), "permission"),
    (re.compile(r'agent|subagent|worker'), "agent"),
    (re.compile(r'commit|git|branch'), "git"),
    (re.compile(r'plan|yolo|auto_mode'), "mode"),
    (re.compile(r'cost|usage|billing'), "billing"),
]

# Sliding window size for expanding match points into regions
# Each match is expanded by WINDOW_HALF on each side
WINDOW_HALF = 512

# Merge threshold: adjacent same-tag regions within this distance are merged
MERGE_THRESHOLD = 2048


def build_context_index(content: str) -> list:
    """Scan content and identify functional regions by pattern matching.

    Finds all CONTEXT_PATTERNS matches, expands each match point into a
    region using a sliding window, then merges adjacent same-tag regions.

    Args:
        content: The full cli.js source content string.

    Returns:
        List of region dicts, each with:
        - tag: str (context label, e.g. "tools", "auth")
        - start: int (start position in content, inclusive)
        - end: int (end position in content, exclusive)
    """
    if not content:
        return []

    raw_regions = []

    for pattern, tag in CONTEXT_PATTERNS:
        for match in pattern.finditer(content):
            # Expand match position into a window region
            center = match.start()
            start = max(0, center - WINDOW_HALF)
            end = min(len(content), match.end() + WINDOW_HALF)
            raw_regions.append({"tag": tag, "start": start, "end": end})

    if not raw_regions:
        return []

    # Group by tag and merge adjacent regions
    by_tag = {}
    for r in raw_regions:
        by_tag.setdefault(r["tag"], []).append(r)

    merged = []
    for tag, regions in by_tag.items():
        # Sort by start position
        regions.sort(key=lambda x: x["start"])
        # Merge overlapping/adjacent regions
        current = {"tag": tag, "start": regions[0]["start"], "end": regions[0]["end"]}
        for r in regions[1:]:
            # If within merge threshold, extend current region
            if r["start"] <= current["end"] + MERGE_THRESHOLD:
                current["end"] = max(current["end"], r["end"])
            else:
                merged.append(current)
                current = {"tag": tag, "start": r["start"], "end": r["end"]}
        merged.append(current)

    # Sort final index by start position
    merged.sort(key=lambda x: x["start"])
    return merged


def detect_context(index: list, position: int) -> list:
    """Determine context tags for a given position in the content.

    Checks which regions in the pre-built index contain the position.
    A position may fall within multiple overlapping regions.

    Args:
        index: Pre-built context index from build_context_index().
        position: Character position in the original content.

    Returns:
        List of context tag strings. Returns ["default"] if position
        does not fall within any known region.
    """
    tags = []
    for region in index:
        if region["start"] <= position <= region["end"]:
            tags.append(region["tag"])

    return tags if tags else ["default"]
