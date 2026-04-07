"""Auto-update command: one-click self-evolution for CLI localization.

Orchestrates the full pipeline:
1. Detect CLI installation + load translation map + skip words
2. Version change detection (rebuild backup if needed)
3. Ensure pristine backup
4. Scan backup for new candidates
5. Diff against previous snapshot
6. Auto-translate high-confidence candidates
7. Merge into translation map
8. Save snapshot + translation map
9. Restore from backup + apply translations + hook replacements
10. Verify syntax (auto-rollback on failure)
11. Output comprehensive JSON report
"""


from scripts.i18n.cli import get_cli_dir, output_json, output_error
from scripts.i18n.config.constants import MAP_FILE, SKIP_FILE, SNAPSHOT_FILE
from scripts.i18n.io.backup import BackupManager
from scripts.i18n.io.file_io import atomic_write_text
from scripts.i18n.io.translation_map import (
    load_translation_map,
    load_skip_words,
    save_translation_map,
    merge_translations,
    save_skip_words,
)
from scripts.i18n.io.extract_snapshot import (
    save_extract_snapshot,
    load_extract_snapshot,
    diff_extractions,
)
from scripts.i18n.core.scanner import scan_candidates
from scripts.i18n.core.auto_translate import auto_translate_candidates
from scripts.i18n.core.replacer import apply_translations
from scripts.i18n.core.hooks import apply_hook_replacements
from scripts.i18n.core.verifier import verify_syntax
from scripts.i18n.core.version import handle_version_change, get_cli_version
from scripts.i18n.config.paths import get_data_dir
from scripts.i18n.filters.noise_filter import NOISE_RE



def cmd_auto_update() -> None:
    """One-click: detect version, extract, translate, merge, apply."""
    cli_dir = get_cli_dir()

    # --- 1. Load existing data ---
    map_path = get_data_dir() / MAP_FILE
    skip_path = get_data_dir() / SKIP_FILE
    snapshot_path = get_data_dir() / SNAPSHOT_FILE

    if map_path.exists():
        map_data = load_translation_map(map_path)
    else:
        map_data = {"meta": {"version": "0.0.0"}, "translations": {}}

    skip_words = load_skip_words(skip_path) if skip_path.exists() else set()
    existing_translations = map_data["translations"]
    existing_keys = set(existing_translations.keys())

    # --- 2. Version change ---
    old_version = map_data["meta"].get("cli_version", "unknown")
    version_result = handle_version_change(cli_dir, map_data["meta"])

    # --- 3. Ensure backup ---
    bm = BackupManager(cli_dir)
    backup_result = bm.ensure_backup()
    if not backup_result["ok"]:
        output_error(
            f"Backup creation failed: {backup_result.get('error', 'unknown')}",
            hint=backup_result.get('hint', ''),
        )
        return

    # --- 4. Scan backup for candidates ---
    content = bm.backup.read_text(encoding='utf-8')
    candidates = scan_candidates(content, existing_keys, skip_words, NOISE_RE)

    # --- 5. Diff with previous snapshot ---
    prev_snap = load_extract_snapshot(snapshot_path)
    prev_candidates = prev_snap.get("candidates", [])
    diff = diff_extractions(prev_candidates, candidates)

    current_version = get_cli_version(cli_dir)

    # --- 6. Auto-translate ---
    auto_result = auto_translate_candidates(
        candidates,
        existing_translations,
        score_threshold=1000,
        dict_path=get_data_dir() / 'auto-translate-dict.json',
    )

    # --- 7. Merge translations ---
    if auto_result["translated"]:
        merge_result = merge_translations(
            existing_translations,
            auto_result["translated"],
            map_data["meta"],
            current_version,
        )
        merged = merge_result["merged"]
    else:
        merged = dict(existing_translations)
        merge_result = {"added": [], "updated": [], "unchanged": list(existing_keys)}

    # --- 8. Save snapshot + translation map ---
    save_extract_snapshot(snapshot_path, current_version, candidates)
    save_translation_map(map_path, map_data["meta"], merged)

    # Update skip words with newly skipped items
    new_skipped = {c["en"] for c in auto_result["skipped"]}
    if new_skipped:
        save_skip_words(skip_path, skip_words | new_skipped)

    # --- 9. Restore + apply ---
    restore_result = bm.restore()
    if not restore_result["ok"]:
        output_error(
            f"Restore from backup failed: {restore_result.get('error', 'unknown')}",
            hint=restore_result.get('hint', ''),
        )
        return

    cli_js = cli_dir / 'cli.js'
    source = cli_js.read_text(encoding='utf-8')

    modified, stats = apply_translations(source, merged, skip_words)
    modified, hook_stats = apply_hook_replacements(modified)
    stats["hook"] = hook_stats

    # --- 10. Write + verify ---
    atomic_write_text(cli_js, modified)
    verify_result = verify_syntax(cli_js)

    if not verify_result["ok"]:
        bm.restore()
        output_json({
            "ok": False,
            "action": "auto-update",
            "error": f"Syntax validation failed, rolled back: {verify_result['error']}",
            "rollback": True,
        })
        return

    # --- 11. Report ---
    total = stats["long"] + stats["medium"] + stats["short"] + stats["hook"]["hook_replacements"]

    review_items = []
    for item in auto_result["review"]:
        entry = {
            "en": item["en"] if isinstance(item, dict) else item,
            "score": item.get("score", 0) if isinstance(item, dict) else 0,
        }
        review_items.append(entry)

    output_json({
        "ok": True,
        "action": "auto-update",
        "version": {
            "old": old_version,
            "new": current_version,
            "changed": version_result.get("changed", False),
        },
        "extraction": {
            "candidates_found": len(candidates),
            "new": len(diff["new"]),
            "changed": len(diff["changed"]),
            "removed": len(diff["removed"]),
        },
        "translation": {
            "auto_translated": len(auto_result["translated"]),
            "needs_review": len(auto_result["review"]),
            "total_entries": len(merged),
            "added": len(merge_result["added"]),
            "updated": len(merge_result["updated"]),
        },
        "apply": {
            "replacements": total,
            "stats": stats,
        },
        "verification": verify_result,
        "review_items": review_items,
    })
