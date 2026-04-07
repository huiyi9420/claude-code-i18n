"""Extract snapshot persistence for diffing between CLI versions.

Saves and loads extraction results so the engine can diff new candidates
against previous runs, identifying new/changed/removed strings.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List

from scripts.i18n.io.file_io import atomic_write_text


def save_extract_snapshot(
    snapshot_path: Path,
    cli_version: str,
    candidates: List[dict],
) -> None:
    """Save extraction snapshot to JSON file.

    Args:
        snapshot_path: Path to extract-snapshot.json.
        cli_version: Current CLI version.
        candidates: List of candidate dicts from scan_candidates().
    """
    data = {
        "timestamp": datetime.now().isoformat(),
        "cli_version": cli_version,
        "candidates": candidates,
    }
    content = json.dumps(data, ensure_ascii=False, indent=2)
    atomic_write_text(snapshot_path, content)


def load_extract_snapshot(snapshot_path: Path) -> dict:
    """Load previous extraction snapshot.

    Args:
        snapshot_path: Path to extract-snapshot.json.

    Returns:
        dict with timestamp, cli_version, candidates.
        Returns {"candidates": []} if file doesn't exist.
    """
    if not snapshot_path.exists():
        return {"timestamp": None, "cli_version": None, "candidates": []}

    try:
        return json.loads(snapshot_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {"timestamp": None, "cli_version": None, "candidates": []}


def diff_extractions(previous: List[dict], current: List[dict]) -> dict:
    """Compare two extraction snapshots and categorize changes.

    Args:
        previous: Previous candidates list (list of dicts with "en" key).
        current: Current candidates list.

    Returns:
        dict with:
        - new: Candidates in current but not in previous.
        - removed: Candidates in previous but not in current.
        - changed: Candidates in both but with different score/count.
        - unchanged: Candidates identical in both.
    """
    prev_map: Dict[str, dict] = {c["en"]: c for c in previous}
    curr_map: Dict[str, dict] = {c["en"]: c for c in current}

    prev_keys = set(prev_map.keys())
    curr_keys = set(curr_map.keys())

    new_keys = curr_keys - prev_keys
    removed_keys = prev_keys - curr_keys
    common_keys = curr_keys & prev_keys

    new = [curr_map[k] for k in new_keys]
    removed = [prev_map[k] for k in removed_keys]
    changed = []
    unchanged = []

    for k in common_keys:
        p = prev_map[k]
        c = curr_map[k]
        if p.get("score") != c.get("score") or p.get("count") != c.get("count"):
            changed.append(c)
        else:
            unchanged.append(c)

    return {
        "new": new,
        "removed": removed,
        "changed": changed,
        "unchanged": unchanged,
    }
