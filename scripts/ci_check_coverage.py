#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""CI translation coverage regression check.

Standalone script that reads zh-CN.json and compares the translation
entry count against a stored baseline. Used in CI to prevent PRs from
accidentally reducing translation coverage.

Exit codes:
    0 — coverage is at or above baseline (or baseline missing, first run)
    1 — coverage has regressed below baseline
"""

import argparse
import json
import sys
from pathlib import Path


def count_translations(map_path: Path) -> dict:
    """Count translation entries from zh-CN.json.

    Reads the translation map and categorizes entries by English key length:
    - long: key length > 20 characters
    - medium: key length 10-20 characters
    - short: key length < 10 characters

    Args:
        map_path: Path to the zh-CN.json translation map.

    Returns:
        dict with keys: total, long, medium, short, meta_version.
    """
    raw = json.loads(map_path.read_text(encoding="utf-8"))
    meta = raw.get("_meta", {})
    translations = raw.get("translations", {})

    long_count = 0
    medium_count = 0
    short_count = 0

    for key in translations:
        key_len = len(key)
        if key_len > 20:
            long_count += 1
        elif key_len >= 10:
            medium_count += 1
        else:
            short_count += 1

    return {
        "total": len(translations),
        "long": long_count,
        "medium": medium_count,
        "short": short_count,
        "meta_version": meta.get("version", "unknown"),
    }


def load_baseline(baseline_path: Path) -> dict:
    """Load coverage baseline from a JSON file.

    Args:
        baseline_path: Path to the coverage-baseline.json file.

    Returns:
        dict with baseline data, or None if the file does not exist.
    """
    if not baseline_path.exists():
        return None
    return json.loads(baseline_path.read_text(encoding="utf-8"))


def compare_coverage(current: dict, baseline: dict) -> dict:
    """Compare current translation counts against a baseline.

    Args:
        current: Output from count_translations().
        baseline: Output from load_baseline().

    Returns:
        dict with keys:
        - ok: bool — True if current.total >= baseline.translated_count
        - current: the current stats dict
        - baseline: the baseline dict (normalized)
        - diff: dict of differences (current - baseline)
    """
    baseline_total = baseline.get("translated_count", 0)
    ok = current["total"] >= baseline_total

    diff = {
        "total": current["total"] - baseline_total,
        "long": current["long"] - baseline.get("long", 0),
        "medium": current["medium"] - baseline.get("medium", 0),
        "short": current["short"] - baseline.get("short", 0),
    }

    return {
        "ok": ok,
        "current": current,
        "baseline": baseline,
        "diff": diff,
    }


def main(argv=None):
    """CLI entry point for coverage regression check."""
    parser = argparse.ArgumentParser(
        description="Check translation coverage regression against baseline"
    )
    parser.add_argument(
        "--baseline-path",
        default=".planning/coverage-baseline.json",
        help="Path to coverage baseline JSON (default: .planning/coverage-baseline.json)",
    )
    parser.add_argument(
        "--map-path",
        default="scripts/zh-CN.json",
        help="Path to translation map JSON (default: scripts/zh-CN.json)",
    )
    args = parser.parse_args(argv)

    map_path = Path(args.map_path)
    baseline_path = Path(args.baseline_path)

    current = count_translations(map_path)
    baseline = load_baseline(baseline_path)

    if baseline is None:
        result = {
            "ok": True,
            "warning": f"Baseline file not found: {baseline_path}. First run — skipping regression check.",
            "current": current,
        }
    else:
        result = compare_coverage(current, baseline)

    print(json.dumps(result, ensure_ascii=False, indent=2))
    sys.exit(0 if result["ok"] else 1)


if __name__ == "__main__":
    main()
