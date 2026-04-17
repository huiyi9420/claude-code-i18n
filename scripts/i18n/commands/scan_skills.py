"""Scan installed skills and plugins for description language detection.

Scans SKILL.md files in:
- ~/.claude/skills/ (user-installed skills)
- ~/.claude/plugins/marketplaces/*/ (plugin skills)

Outputs JSON with per-skill info: name, path, description, language (zh/en).
"""

import json
import re
import sys
from pathlib import Path
from typing import Dict, List, Optional

from scripts.i18n.cli import output_json

HOME = Path.home()
CLAUDE_DIR = HOME / ".claude"
SKILLS_DIR = CLAUDE_DIR / "skills"
PLUGINS_DIR = CLAUDE_DIR / "plugins" / "marketplaces"

# Plugin directory name -> source identifier
plugin_sources = {
    "everything-claude-code": "ecc_plugin",
    "minimax-skills": "minimax_plugin",
    "claude-plugins-official": "official_plugin",
    "claude-code-lsps": "lsp_plugin",
}

# Chinese character detection
_ZH_RE = re.compile(r'[\u4e00-\u9fff]')

# YAML frontmatter description extraction
# Matches: description: "..." or description: '...' or description: |
#   multi-line...
_DESCRIPTION_RE = re.compile(
    r'^description:\s*(?:"([^"]*)"|\'([^\']*)\'|\|[\s]*\n((?:[ \t]+.*\n)*))',
    re.MULTILINE,
)


def _extract_description(content: str) -> Optional[str]:
    """Extract description from SKILL.md YAML frontmatter."""
    m = _DESCRIPTION_RE.search(content)
    if not m:
        return None
    # Three capture groups: double-quoted, single-quoted, multi-line
    for group in m.groups():
        if group is not None:
            return group.strip()
    return None


def _detect_lang(text: str) -> str:
    """Detect if text contains Chinese characters."""
    return "zh" if _ZH_RE.search(text) else "en"


def _scan_directory(base_dir: Path, source_name: str) -> List[Dict]:
    """Scan a directory for SKILL.md files and extract descriptions."""
    results = []
    if not base_dir.exists():
        return results

    for skill_md in base_dir.rglob("SKILL.md"):
        # Skip node_modules, .git, etc.
        parts = skill_md.relative_to(base_dir).parts
        if any(p in ('node_modules', '.git', '__pycache__', '.cursor', '.agents')
               for p in parts):
            continue

        try:
            content = skill_md.read_text(encoding='utf-8')
        except (OSError, UnicodeDecodeError):
            continue

        desc = _extract_description(content)
        if desc is None:
            continue

        # Extract skill name from frontmatter or directory name
        name = skill_md.parent.name
        name_match = re.search(r'^name:\s*(.+)$', content, re.MULTILINE)
        if name_match:
            name = name_match.group(1).strip()

        results.append({
            "name": name,
            "path": str(skill_md),
            "description": desc[:200],
            "lang": _detect_lang(desc),
            "source": source_name,
        })

    return results


def cmd_scan_skills() -> None:
    """Scan all installed skills and output language report."""
    all_skills = []
    source_stats = {}

    # Source 1: User-installed skills
    user_skills = _scan_directory(SKILLS_DIR, "user_skills")
    all_skills.extend(user_skills)

    # Source 2: Plugin marketplace skills
    if PLUGINS_DIR.exists():
        for plugin_dir in PLUGINS_DIR.iterdir():
            if not plugin_dir.is_dir():
                continue
            source_name = plugin_sources.get(plugin_dir.name, plugin_dir.name)
            plugin_skills = _scan_directory(plugin_dir, source_name)
            all_skills.extend(plugin_skills)

    # Deduplicate by path (prefer user_skills over plugin duplicates)
    seen_paths = set()
    unique_skills = []
    for skill in all_skills:
        if skill["path"] not in seen_paths:
            seen_paths.add(skill["path"])
            unique_skills.append(skill)

    # Compute stats
    total = len(unique_skills)
    zh_count = sum(1 for s in unique_skills if s["lang"] == "zh")
    en_count = sum(1 for s in unique_skills if s["lang"] == "en")

    by_source = {}
    for skill in unique_skills:
        src = skill["source"]
        if src not in by_source:
            by_source[src] = {"total": 0, "en": 0, "zh": 0}
        by_source[src]["total"] += 1
        by_source[src][skill["lang"]] += 1

    output_json({
        "ok": True,
        "summary": {
            "total": total,
            "chinese": zh_count,
            "english": en_count,
            "by_source": by_source,
        },
        "skills": unique_skills,
    })
