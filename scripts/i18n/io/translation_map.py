"""Translation map loader for Claude Code i18n engine.

Loads zh-CN.json translation maps and skip-words.json files.
Handles both v4 (string values) and v5 (dict values with "zh" key) formats.
"""

import json
from pathlib import Path


def load_translation_map(map_path: Path) -> dict:
    """Load translation map from a JSON file.

    Args:
        map_path: Path to the translation map JSON file (e.g. zh-CN.json).

    Returns:
        dict with "meta" and "translations" keys.
        - meta: the _meta object from the file (version, cli_version, etc.)
        - translations: dict mapping English strings to Chinese translations.
          Dict values (v5 format) are flattened to extract the "zh" key.

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
    raw_translations = raw.get("translations", {})

    # Flatten dict values: {"zh": "..."} -> "..."
    translations = {}
    for key, value in raw_translations.items():
        if isinstance(value, dict):
            translations[key] = value.get("zh", "")
        else:
            translations[key] = value

    return {"meta": meta, "translations": translations}


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
