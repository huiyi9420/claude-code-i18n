"""Translate skill descriptions by applying AI-translated JSON to SKILL.md files.

Two modes:
1. --list: Output English descriptions as JSON for AI to translate.
2. --apply: Read translated JSON and write back to SKILL.md files.

Usage:
    python3 engine.py translate-skills --list [--source all] [--skill name1,name2]
    python3 engine.py translate-skills --apply translated.json
"""

import json
import re
from pathlib import Path
from typing import Dict, List, Optional

from scripts.i18n.cli import output_json, output_error


def _extract_frontmatter(content: str) -> tuple:
    """Extract YAML frontmatter boundaries from SKILL.md content.

    Returns (before_frontmatter, frontmatter_text, after_frontmatter).
    """
    if not content.startswith('---'):
        return '', '', content

    # Find closing ---
    end = content.find('---', 3)
    if end == -1:
        return '', '', content

    return content[:3], content[3:end], content[end + 3:]


def _replace_description(frontmatter: str, new_desc: str) -> str:
    """Replace description field in YAML frontmatter string.

    Handles quoted, single-quoted, and multi-line description formats.
    """
    # Pattern matches description: "..." or description: '...' or description: |
    pattern = re.compile(
        r'(description:\s*)(?:"[^"]*"|\'[^\']*\'|\|[^\n]*(?:\n[ \t]+[^\n]*)*)',
        re.MULTILINE,
    )

    # Check if original had description
    m = pattern.search(frontmatter)
    if not m:
        # No existing description, append it
        return frontmatter.rstrip('\n') + f'\ndescription: "{new_desc}"\n'

    # Use double quotes, escape ALL ASCII double quotes in the description
    escaped = new_desc.replace('"', '\\"')
    replacement = f'description: "{escaped}"'
    return pattern.sub(replacement, frontmatter)


def cmd_translate_skills(args) -> None:
    """Translate skill descriptions."""
    if args.apply:
        _cmd_apply(args.apply)
    else:
        # --list is default
        _cmd_list(args.source, args.skill)


def _cmd_list(source: str, skill: str = None) -> None:
    """Output English descriptions for translation."""
    from scripts.i18n.commands import scan_skills as smod

    skill_names = None
    if skill:
        skill_names = set(s.strip() for s in skill.split(','))

    all_skills = []

    user_skills = smod._scan_directory(smod.SKILLS_DIR, "user_skills")
    all_skills.extend(user_skills)

    if smod.PLUGINS_DIR.exists():
        for plugin_dir in smod.PLUGINS_DIR.iterdir():
            if not plugin_dir.is_dir():
                continue
            source_name = smod.plugin_sources.get(plugin_dir.name, plugin_dir.name)
            plugin_skills = smod._scan_directory(plugin_dir, source_name)
            all_skills.extend(plugin_skills)

    filtered = []
    for s in all_skills:
        if s["lang"] != "en":
            continue
        if source != "all" and s["source"] != source:
            continue
        if skill_names and s["name"] not in skill_names:
            continue
        filtered.append({
            "name": s["name"],
            "path": s["path"],
            "description": s["description"],
            "source": s["source"],
        })

    output_json({
        "ok": True,
        "count": len(filtered),
        "skills": filtered,
    })


def _cmd_apply(json_path: str) -> None:
    """Apply translated descriptions from JSON file to SKILL.md."""
    path = Path(json_path)
    if not path.exists():
        output_error(f"Translation file not found: {json_path}")
        return

    try:
        translations = json.loads(path.read_text(encoding='utf-8'))
    except (json.JSONDecodeError, OSError) as e:
        output_error(f"Failed to read translation file: {e}")
        return

    if not isinstance(translations, list):
        output_error("Expected JSON array of {name, path, description, translated}")
        return

    applied = 0
    failed = 0
    errors = []

    for item in translations:
        skill_path = Path(item.get("path", ""))
        translated = item.get("translated", "")

        if not skill_path.exists() or not translated:
            failed += 1
            errors.append(f"Skip: {item.get('name', '?')} (path missing or no translation)")
            continue

        try:
            content = skill_path.read_text(encoding='utf-8')

            # Replace description in frontmatter
            before, frontmatter, after = _extract_frontmatter(content)
            if not frontmatter:
                failed += 1
                errors.append(f"No frontmatter: {skill_path}")
                continue

            new_frontmatter = _replace_description(frontmatter, translated)
            new_content = f"---{new_frontmatter}---{after}"

            skill_path.write_text(new_content, encoding='utf-8')
            applied += 1

        except Exception as e:
            failed += 1
            errors.append(f"Error writing {skill_path}: {e}")

    output_json({
        "ok": True,
        "applied": applied,
        "failed": failed,
        "errors": errors[:20],
    })
