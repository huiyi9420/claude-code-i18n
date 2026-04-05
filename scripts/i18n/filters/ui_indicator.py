"""UI indicator scoring for Claude Code i18n string extraction.

Provides strong/weak signal detection to prioritize translatable strings.
Migrated from v3.0 localize.py STRONG_INDICATORS and WEAK_INDICATORS lists.
"""

STRONG_INDICATORS = [
    "claude code", "claude.md", "claude ", ".claude",
    "anthropic", "plan mode", "yolo mode", "auto mode", "fast mode",
    "extended thinking", "context window",
    "bypass permission", "permission mode", "sandbox",
    "mcp server", "mcp tool", "mcp ",
    "agent type", "agent tool", "agent idle", "agent abort",
    "worktree", "subagent",
    "accept terms", "help improve claude",
    "auto-allow", "autoallow",
]

WEAK_INDICATORS = [
    "permission", "allow", "deny", "approve", "reject",
    "agent", "tool", "skill", "hook", "plugin",
    "commit", "branch", "merge", "pull request",
    "please", "cannot", "must be", "is required", "confirm",
    "loading", "saving", "processing", "idle",
    "not found", "already exist", "unable to",
    "session", "model", "token", "cost",
    "config", "setting", "marketplace",
    "install", "uninstall", "enable", "disable",
    "new version", "update available",
]


def score_candidate(text: str, count: int) -> dict:
    """Score a candidate string based on UI indicator signals.

    Args:
        text: The candidate string to score.
        count: The number of occurrences in the source file.

    Returns:
        dict with "score" (int) and "type" ("strong"|"weak"|"none").
        Strong: score = 1000 + count
        Weak: score = count
        None: score = 0
    """
    lower = text.lower()

    is_strong = any(kw in lower for kw in STRONG_INDICATORS)
    is_weak = any(kw in lower for kw in WEAK_INDICATORS)

    if is_strong:
        return {"score": 1000 + count, "type": "strong"}
    elif is_weak:
        return {"score": count, "type": "weak"}
    else:
        return {"score": 0, "type": "none"}
