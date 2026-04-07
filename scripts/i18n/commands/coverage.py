"""Coverage command: 翻译覆盖率报告.

输出翻译覆盖率表格，显示已翻译/未翻译/跳过的条目数量和百分比。
按字符串长度分组显示覆盖率（长>20 / 中10-20 / 短<10）。
"""

from scripts.i18n.cli import get_cli_dir, output_json, output_error
from scripts.i18n.config.constants import MAP_FILE, SKIP_FILE
from scripts.i18n.config.paths import get_data_dir
from scripts.i18n.io.translation_map import load_translation_map, load_skip_words
from scripts.i18n.io.backup import BackupManager
from scripts.i18n.core.scanner import scan_candidates
from scripts.i18n.filters.noise_filter import NOISE_RE


def _classify_length(s: str) -> str:
    """按字符串长度分类: long(>20) / medium(10-20) / short(<10)."""
    n = len(s)
    if n > 20:
        return "long"
    elif n >= 10:
        return "medium"
    else:
        return "short"


def format_coverage_table(
    translated: int,
    untranslated: int,
    skipped: int,
    total: int,
    percentage: str,
    categories: dict,
) -> str:
    """格式化终端友好的覆盖率表格（纯文本，零外部依赖）.

    Args:
        translated: 已翻译条目数
        untranslated: 未翻译条目数
        skipped: 跳过条目数
        total: 总条目数
        percentage: 总覆盖率百分比字符串
        categories: 分组覆盖率数据

    Returns:
        多行表格字符串
    """
    lines = []
    lines.append("=" * 60)
    lines.append("  翻译覆盖率报告")
    lines.append("=" * 60)
    lines.append("")
    lines.append(f"  {'类别':<14} {'已翻译':>8} {'未翻译':>8} {'总计':>8} {'覆盖率':>10}")
    lines.append(f"  {'-' * 14} {'-' * 8} {'-' * 8} {'-' * 8} {'-' * 10}")

    cat_names = {"long": "长字符串(>20)", "medium": "中字符串(10-20)", "short": "短字符串(<10)"}
    for key in ["long", "medium", "short"]:
        cat = categories[key]
        name = cat_names[key]
        lines.append(
            f"  {name:<14} {cat['translated']:>8} {cat['untranslated']:>8} "
            f"{cat['total']:>8} {cat['percentage']:>10}"
        )

    lines.append(f"  {'-' * 14} {'-' * 8} {'-' * 8} {'-' * 8} {'-' * 10}")
    lines.append(
        f"  {'总计':<14} {translated:>8} {untranslated:>8} "
        f"{translated + untranslated:>8} {percentage:>10}"
    )
    lines.append("")
    lines.append(f"  跳过条目: {skipped}")
    lines.append(f"  全部条目: {total}")
    lines.append("=" * 60)

    return "\n".join(lines)


def cmd_coverage() -> None:
    """输出翻译覆盖率报告.

    计算已翻译/未翻译/跳过的条目数量，按字符串长度分组，
    输出 JSON 和终端友好的表格。
    """
    cli_dir = get_cli_dir()

    # 加载翻译映射表
    map_path = get_data_dir() / MAP_FILE
    skip_path = get_data_dir() / SKIP_FILE

    existing = set()
    if map_path.exists():
        map_data = load_translation_map(map_path)
        existing = set(map_data["translations"].keys())
    else:
        map_data = {"meta": {}, "translations": {}}

    skipped = load_skip_words(skip_path) if skip_path.exists() else set()
    skipped_count = len(skipped)

    # 确保备份存在并从中扫描未翻译候选
    untranslated = 0
    untranslated_list = []

    bm = BackupManager(cli_dir)
    backup_result = bm.ensure_backup()

    if backup_result["ok"] and bm.backup.exists():
        content = bm.backup.read_text(encoding="utf-8")
        candidates = scan_candidates(content, existing, skipped, NOISE_RE)
        untranslated_list = [c["en"] for c in candidates]
        untranslated = len(untranslated_list)

    # 计算总量
    translated = len(existing)
    total_translatable = translated + untranslated
    if total_translatable > 0:
        percentage = f"{translated / total_translatable * 100:.1f}%"
    else:
        percentage = "0.0%"

    # 按长度分类
    categories = {"long": {"translated": 0, "untranslated": 0, "total": 0, "percentage": "0.0%"},
                  "medium": {"translated": 0, "untranslated": 0, "total": 0, "percentage": "0.0%"},
                  "short": {"translated": 0, "untranslated": 0, "total": 0, "percentage": "0.0%"}}

    # 统计已翻译条目的分类
    for key in existing:
        cat = _classify_length(key)
        categories[cat]["translated"] += 1

    # 统计未翻译候选的分类
    for key in untranslated_list:
        cat = _classify_length(key)
        categories[cat]["untranslated"] += 1

    # 计算每个分类的总计和百分比
    for cat in categories.values():
        cat["total"] = cat["translated"] + cat["untranslated"]
        if cat["total"] > 0:
            cat["percentage"] = f"{cat['translated'] / cat['total'] * 100:.1f}%"
        else:
            cat["percentage"] = "N/A"

    total = translated + untranslated + skipped_count

    # 输出表格到 stdout
    table = format_coverage_table(
        translated=translated,
        untranslated=untranslated,
        skipped=skipped_count,
        total=total,
        percentage=percentage,
        categories=categories,
    )
    print(table)

    # 输出 JSON
    output_json({
        "ok": True,
        "translated": translated,
        "untranslated": untranslated,
        "skipped": skipped_count,
        "total": total,
        "percentage": percentage,
        "categories": categories,
    })
