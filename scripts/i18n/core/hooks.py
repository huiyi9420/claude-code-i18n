"""Hook replacement engine for Claude Code CLI i18n.

Applies unconstrained substring replacements (like sed) for hook UI messages
that are template-concatenated in the minified JS and cannot be handled by
the quote-boundary replacement engine.

Runs as a separate pass after apply_translations() to ensure node --check
covers all modifications.
"""

from typing import Dict, Tuple

# Hook replacement map -- unconstrained substring replacements (equivalent to sed).
# These are template-concatenated strings (e.g., hookName + " says: " + content)
# that lack consistent quote boundaries, so they must use str.replace() directly.
HOOK_REPLACEMENTS: Dict[str, str] = {
    ' says: ': ' 说道：',
    'hook returned blocking error': 'hook 返回了阻塞错误',
    ' hook error': ' hook 错误',
    ' hook warning': ' hook 警告',
    'hook stopped continuation: ': 'hook 停止了继续执行：',
    ' deferred ': ' 推迟了 ',
    'resume with -p --resume to continue': '使用 -p --resume 恢复继续',
    'Allowed by ': '已允许（由 ',
    'Denied by ': '已拒绝（由 ',
    'Async hook ': '异步钩子 ',
    ' completed': ' 已完成',
    'Ran ': '运行了 ',
}


def apply_hook_replacements(content: str) -> Tuple[str, dict]:
    """Apply hook-related string replacements to CLI content.

    Performs unconstrained substring replacements for hook UI messages.
    These are template-concatenated strings that cannot be handled by the
    quote-boundary replacement engine.

    Args:
        content: JavaScript source text (already processed by apply_translations).

    Returns:
        Tuple of (modified_content, stats_dict).
        Stats: {"hook_replacements": N, "details": {en_str: count}}
    """
    stats = {"hook_replacements": 0, "details": {}}
    for en, zh in HOOK_REPLACEMENTS.items():
        count = content.count(en)
        if count > 0:
            content = content.replace(en, zh)
            stats["hook_replacements"] += count
            stats["details"][en] = count
    return content, stats
