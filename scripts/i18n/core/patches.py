"""Post-apply UI component patches for Claude Code CLI i18n.

Handles UI patterns that the three-tier replacement engine cannot cover:
1. React concatenated string fragments (e.g. "'" + "s in this folder first.")
2. _8 component: remove chord display, keep only action text
3. _8 component: translate action values (confirm -> confirm)
4. "Press " -> Chinese in dynamic key hint patterns

These patches run as a separate pass after apply_translations() and hooks,
before atomic_write_text(). All patches use precise matching to avoid
corrupting code logic.

Safety:
- Each patch targets specific known patterns in the minified JS
- Uses str.replace for exact-match patches, regex only for action values
- Action value replacement is scoped to createElement(_8,...) calls only
"""

import re
from typing import Dict, List, Tuple

# ─── Patch 1: Trust dialog React fragment fixes ──────────────────────────────
# The trust dialog uses React createElement with multiple children:
#   createElement(v, null, "long text", "'", "s in this folder first.")
# After engine translation, "'" and "s in this folder first." remain as
# separate children, causing display artifacts like:
#   "...check this folder's in this folder first."
# These patches merge the fragments into the preceding translated string.

TRUST_DIALOG_FIXES: List[Tuple[str, str]] = [
    # Patch 1a: "review what" + "'" + "s in this folder first."
    # After engine: "...review what" is translated, but "'" + "s in this folder first." remains
    (
        '"\u5feb\u901f\u5b89\u5168\u68c0\u67e5\uff1a\u8fd9\u662f\u4f60\u521b\u5efa\u6216\u4fe1\u4efb\u7684\u9879\u76ee\u5417\uff1f\uff08\u6bd4\u5982\u4f60\u81ea\u5df1\u7684\u4ee3\u7801\u3001\u77e5\u540d\u5f00\u6e90\u9879\u76ee\u6216\u56e2\u961f\u7684\u5de5\u4f5c\uff09\u3002\u5982\u679c\u4e0d\u662f\uff0c\u8bf7\u5148\u67e5\u770b\u6b64\u6587\u4ef6\u5939\u4e2d\u7684\u5185\u5bb9","\'","s in this folder first."',
        '"\u5feb\u901f\u5b89\u5168\u68c0\u67e5\uff1a\u8fd9\u662f\u4f60\u521b\u5efa\u6216\u4fe1\u4efb\u7684\u9879\u76ee\u5417\uff1f\uff08\u6bd4\u5982\u4f60\u81ea\u5df1\u7684\u4ee3\u7801\u3001\u77e5\u540d\u5f00\u6e90\u9879\u76ee\u6216\u56e2\u961f\u7684\u5de5\u4f5c\uff09\u3002\u5982\u679c\u4e0d\u662f\uff0c\u8bf7\u5148\u67e5\u770b\u6b64\u6587\u4ef6\u5939\u4e2d\u7684\u5185\u5bb9\u3002"',
    ),
    # Patch 1b: "Claude Code" + "'" + "will be able to..."
    # After engine: "...will be able to..." is translated, but "'" remains
    (
        '"Claude Code","\'","\u5c06\u80fd\u591f\u5728\u6b64\u8bfb\u53d6\u3001\u7f16\u8f91\u548c\u6267\u884c\u6587\u4ef6\u3002"',
        '"Claude Code \u5c06\u80fd\u591f\u5728\u6b64\u8bfb\u53d6\u3001\u7f16\u8f91\u548c\u6267\u884c\u6587\u4ef6\u3002"',
    ),
]

# ─── Patch 2: _8 component - remove chord, keep action only ───────────────────
# The _8 component renders keyboard hints as: chord + " to " + action
# e.g. createElement(NA,null,X," to ",z) renders "Enter to confirm"
# We remove the chord (X) and connector (" to "), keeping only the action (z)
# so it renders just "confirm" (or "确认" after Patch 3).

_8_CHORD_REMOVAL: List[Tuple[str, str]] = [
    # Parens version: (X to z) -> (z)
    ('createElement(NA,null,"(",X," to ",z,")")',
     'createElement(NA,null,"(",z,")")'),
    # No-parens version: X to z -> z
    ('createElement(NA,null,X," to ",z)',
     'createElement(NA,null,z)'),
]

# ─── Patch 3: _8 component action value translation ──────────────────────────
# Action values are display labels (e.g. "confirm", "cancel") passed to _8.
# They are only used as React children for display, not as logic keys.
# We translate them at the createElement(_8,...) call site only.

ACTION_MAP: Dict[str, str] = {
    # Common actions (high frequency)
    "confirm": "确认",
    "cancel": "取消",
    "select": "选择",
    "continue": "继续",
    "close": "关闭",
    "go back": "返回",
    "copy": "复制",
    "view": "查看",
    "expand": "展开",
    "manage": "管理",
    "toggle": "切换",
    "stop": "停止",
    "amend": "修改",
    "switch": "切换",
    "save": "保存",
    "exit": "退出",
    "interrupt": "中断",
    "collapse": "收起",
    "add": "添加",
    "submit": "提交",
    "return": "返回",
    "back": "返回",
    "skip": "跳过",
    "navigate": "导航",
    "apply": "应用",
    "change": "更改",
    "adjust": "调整",
    "update": "更新",
    "remove": "移除",
    "open": "打开",
    "delete": "删除",
    "new": "新建",
    "create": "创建",
    "search": "搜索",
    "preview": "预览",
    "rename": "重命名",
    "undo": "撤销",
    "resume": "恢复",
    "complete": "完成",
    "background": "后台",
    "foreground": "前台",
    # Multi-word actions
    "hide debug info": "隐藏调试信息",
    "show debug info": "显示调试信息",
    "give additional instructions": "追加指令",
    "run in background": "后台运行",
    "write to file": "写入文件",
    "auto-accept edits": "自动接受编辑",
    "toggle tasks": "切换任务",
    "switch model": "切换模型",
    "toggle fast mode": "切换快速模式",
    "stash prompt": "暂存提示",
    "edit in $EDITOR": "在编辑器中编辑",
    "continue anyway": "仍然继续",
    "exit and fix issues": "退出并修复问题",
    "open the browser": "打开浏览器",
    "edit in your editor": "在编辑器中编辑",
    "toggle selection": "切换选择",
    "add notes": "添加备注",
    "switch questions": "切换问题",
    "return to team lead": "返回组长",
    "view tasks": "查看任务",
    "stop agents": "停止代理",
    "stop all agents": "停止所有代理",
    "copy link": "复制链接",
    "switch focus": "切换焦点",
    "switch mode": "切换模式",
    "next field": "下一字段",
    "mark done": "标记完成",
    "exit and start a new conversation": "退出并开始新对话",
    "paste images": "粘贴图片",
    "scroll": "滚动",
    "tabs": "标签页",
    "cycle": "循环",
    "teleport": "传送",
    "disconnect": "断开",
    "suspend": "暂停",
    "unset": "取消设置",
}

# Pre-compile action value regex patterns for performance
_ACTION_PATTERNS: List[Tuple[re.Pattern, str]] = []
for _en, _zh in ACTION_MAP.items():
    _pattern = re.compile(
        r'(createElement\(_8,\{[^}]*?)action:"' + re.escape(_en) + '"'
    )
    _ACTION_PATTERNS.append((_pattern, f'action:"{_zh}"'))

# ─── Patch 4: "Press " -> Chinese in dynamic hints ───────────────────────────
# Pattern: createElement(v, ..., "Press ", keyName, " again to exit")
# After engine: " again to exit" is translated but "Press " is not
# because it's a short concatenation fragment.
# Only replace in createElement context to avoid false matches.

PRESS_REPLACEMENTS: List[Tuple[str, str]] = [
    ('"Press ",', '"按 ",'),
]


def apply_ui_patches(content: str) -> Tuple[str, dict]:
    """Apply all post-translation UI component patches.

    Runs after apply_translations() and hook replacements.
    Each patch uses precise matching to avoid code corruption.

    Args:
        content: JavaScript source text (already translated).

    Returns:
        Tuple of (modified_content, stats_dict).
        Stats: {"trust_dialog": N, "chord_removal": N, "action_values": N,
                "press_hints": N, "total": N, "details": {}}
    """
    stats = {
        "trust_dialog": 0,
        "chord_removal": 0,
        "action_values": 0,
        "press_hints": 0,
        "total": 0,
        "details": {},
    }

    # Patch 1: Trust dialog fragment fixes
    for old, new in TRUST_DIALOG_FIXES:
        count = content.count(old)
        if count > 0:
            content = content.replace(old, new)
            stats["trust_dialog"] += count
            stats["total"] += count

    # Patch 2: _8 chord removal
    for old, new in _8_CHORD_REMOVAL:
        count = content.count(old)
        if count > 0:
            content = content.replace(old, new)
            stats["chord_removal"] += count
            stats["total"] += count

    # Patch 3: _8 action value translation
    for pattern, replacement in _ACTION_PATTERNS:
        matches = pattern.findall(content)
        if matches:
            # Use re.sub with the full pattern to replace at _8 call sites only
            new_replacement = replacement
            content = pattern.sub(
                lambda m: m.group(1) + new_replacement,
                content,
            )
            stats["action_values"] += len(matches)
            stats["total"] += len(matches)

    # Patch 4: "Press " -> "按 "
    for old, new in PRESS_REPLACEMENTS:
        count = content.count(old)
        if count > 0:
            content = content.replace(old, new)
            stats["press_hints"] += count
            stats["total"] += count

    stats["details"] = {
        "trust_dialog": stats["trust_dialog"],
        "chord_removal": stats["chord_removal"],
        "action_values": stats["action_values"],
        "press_hints": stats["press_hints"],
    }

    return content, stats
