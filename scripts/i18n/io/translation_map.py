"""Translation map loader and writer for Claude Code i18n engine.

Loads/saves zh-CN.json translation maps and skip-words.json files.
Handles v4 (string values), v5 (dict values with "zh" key), and
v6 (dict values with "zh" + "contexts") formats.
"""

import json
from pathlib import Path

from scripts.i18n.io.file_io import atomic_write_text


def load_translation_map(map_path: Path) -> dict:
    """Load translation map from a JSON file.

    Args:
        map_path: Path to the translation map JSON file (e.g. zh-CN.json).

    Returns:
        dict with "meta", "translations", and "raw_translations" keys.
        - meta: the _meta object from the file (version, cli_version, etc.)
        - translations: dict mapping English strings to Chinese translations.
          Dict values (v5/v6 format) are flattened to extract the "zh" key.
        - raw_translations: dict preserving full v6 structure including
          contexts. String values are normalized to {"zh": value}.

    Raises:
        FileNotFoundError: If map_path does not exist.
        ValueError: If the file contains invalid JSON.
    """
    if not map_path.exists():
        raise FileNotFoundError(
            f"Translation map not found: {map_path}"
        )

    try:
        raw = json.loads(map_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        raise ValueError(
            f"Invalid JSON in translation map {map_path}: {e}"
        )

    meta = raw.get("_meta", {})
    raw_translations_data = raw.get("translations", {})

    # Flatten dict values: {"zh": "..."} -> "..." for backward compat
    translations = {}
    for key, value in raw_translations_data.items():
        if isinstance(value, dict):
            translations[key] = value.get("zh", "")
        else:
            translations[key] = value

    # Preserve raw structure: normalize strings to {"zh": value}
    raw_translations = {}
    for key, value in raw_translations_data.items():
        if isinstance(value, dict):
            raw_translations[key] = value
        else:
            raw_translations[key] = {"zh": value}

    return {
        "meta": meta,
        "translations": translations,
        "raw_translations": raw_translations,
    }


def load_skip_words(skip_path: Path) -> set:
    """Load skip words from a JSON file.

    Args:
        skip_path: Path to the skip words JSON file (e.g. skip-words.json).

    Returns:
        set of strings from the "skip" key in the JSON file.

    Raises:
        FileNotFoundError: If skip_path does not exist.
    """
    if not skip_path.exists():
        raise FileNotFoundError(
            f"Skip words file not found: {skip_path}"
        )

    raw = json.loads(skip_path.read_text(encoding="utf-8"))
    return set(raw.get("skip", []))


def save_translation_map(map_path: Path, meta: dict, translations: dict) -> None:
    """Save translation map to JSON file atomically.

    Supports v6 format: if a translation value is a dict (with "zh" and
    optional "contexts"), it is written as-is. String values are written
    as plain strings for backward compatibility.

    Args:
        map_path: Path to zh-CN.json.
        meta: _meta dict (cli_version, version, etc.).
        translations: Dict of {english: chinese_str | dict} pairs.
    """
    data = {"_meta": meta, "translations": translations}
    content = json.dumps(data, ensure_ascii=False, indent=2)
    atomic_write_text(map_path, content)


def resolve_translation(entry, context_tags: list) -> str:
    """Resolve the best translation for an entry given context tags.

    Selects the most specific translation by checking context tags in order.
    The first matching context wins. Falls back to the global "zh" default.

    Args:
        entry: A translation entry, which can be:
            - str: plain Chinese string (v4 format)
            - dict with "zh" key: {"zh": "中文"} (v5 format)
            - dict with "zh" + "contexts": {"zh": "中文", "contexts": {...}} (v6)
        context_tags: Ordered list of context tag strings to match.
            First matching tag wins.

    Returns:
        The resolved Chinese translation string.
    """
    # v4 format: plain string
    if isinstance(entry, str):
        return entry

    # v5/v6 format: dict with "zh" key
    if isinstance(entry, dict):
        contexts = entry.get("contexts", {})
        # Check context tags in order; first match wins
        for tag in context_tags:
            if tag in contexts:
                return contexts[tag]
        # Fallback to global default
        return entry.get("zh", "")

    # Unknown format: return empty string
    return ""


def merge_translations(
    existing: dict,
    new_entries: dict,
    meta: dict,
    current_version: str,
) -> dict:
    """Merge new translation entries into existing translations.

    Args:
        existing: Current translations dict ({en: zh}).
        new_entries: New entries to merge ({en: zh}).
        meta: Current _meta dict (will be updated in-place).
        current_version: Current CLI version string.

    Returns:
        dict with:
        - merged: The merged translations dict.
        - added: List of newly added keys.
        - updated: List of updated keys (value changed).
        - unchanged: List of keys that already existed with same value.
    """
    merged = dict(existing)
    added = []
    updated = []
    unchanged = []

    for key, value in new_entries.items():
        if key not in merged:
            merged[key] = value
            added.append(key)
        elif merged[key] != value:
            merged[key] = value
            updated.append(key)
        else:
            unchanged.append(key)

    # Update meta
    meta["cli_version"] = current_version
    # Increment patch version
    version = meta.get("version", "0.0.0")
    parts = version.split(".")
    if len(parts) == 3:
        parts[2] = str(int(parts[2]) + 1)
        meta["version"] = ".".join(parts)

    return {
        "merged": merged,
        "added": added,
        "updated": updated,
        "unchanged": unchanged,
    }


def save_skip_words(skip_path: Path, skip_set: set) -> None:
    """Save skip words set to JSON file atomically.

    Args:
        skip_path: Path to skip-words.json.
        skip_set: Set of strings to save.
    """
    data = {"skip": sorted(skip_set)}
    content = json.dumps(data, ensure_ascii=False, indent=2)
    atomic_write_text(skip_path, content)
