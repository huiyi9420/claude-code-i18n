"""Extract command: extract translatable strings from pristine backup.

EXTRACT-01: Reads from pristine backup only (never from translated cli.js).
EXTRACT-02: Uses signal indicator system to score candidates.
EXTRACT-04: Outputs JSON with strong/weak candidates, scores, occurrence counts.
EXTRACT-05: Excludes already-translated and already-skipped strings.
EXTRACT-06: Never outputs strings containing Chinese characters.
"""

from pathlib import Path

from scripts.i18n.cli import get_cli_dir, output_json, output_error
from scripts.i18n.config.constants import MAP_FILE, SKIP_FILE
from scripts.i18n.config.paths import get_data_dir
from scripts.i18n.io.backup import BackupManager
from scripts.i18n.io.translation_map import load_translation_map, load_skip_words
from scripts.i18n.core.scanner import scan_candidates
from scripts.i18n.filters.noise_filter import NOISE_RE



def cmd_extract() -> None:
    """Extract translatable string candidates from pristine backup."""
    cli_dir = get_cli_dir()

    # Load translation data
    map_path = get_data_dir() / MAP_FILE
    skip_path = get_data_dir() / SKIP_FILE

    existing = set()
    if map_path.exists():
        map_data = load_translation_map(map_path)
        existing = set(map_data["translations"].keys())
    else:
        map_data = {"meta": {}, "translations": {}}

    skipped = load_skip_words(skip_path) if skip_path.exists() else set()

    # Ensure backup exists (EXTRACT-01: extract from pristine backup only)
    bm = BackupManager(cli_dir)
    backup_result = bm.ensure_backup()
    if not backup_result["ok"]:
        output_error(
            f"Backup required for extraction: {backup_result.get('error', 'unknown')}"
        )
        return

    # Read from backup (not cli.js!)
    content = bm.backup.read_text(encoding='utf-8')

    # Scan for candidates
    candidates = scan_candidates(content, existing, skipped, NOISE_RE)

    # Split into strong/weak buckets (EXTRACT-04)
    strong = [c for c in candidates if c["type"] == "strong"]
    weak = [c for c in candidates if c["type"] == "weak"]

    output_json({
        "ok": True,
        "strong_count": len(strong),
        "weak_count": len(weak),
        "existing_entries": len(existing),
        "skipped_entries": len(skipped),
        "strong": strong[:150],
        "weak": weak[:100],
    })
