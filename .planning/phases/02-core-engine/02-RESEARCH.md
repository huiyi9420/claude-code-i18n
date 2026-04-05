# Phase 2: Core Engine - Research

**Researched:** 2026-04-05
**Domain:** 三级替换引擎 / 字符串扫描提取 / 语法验证 / 版本检测 / CLI 汉化核心逻辑
**Confidence:** HIGH

## Summary

Phase 2 是整个汉化工具的核心，实现从翻译映射表驱动的安全字符串替换引擎。需要在 13MB minified JavaScript 文件上执行三级策略替换（长字符串精确替换、中字符串引号边界替换、短字符串受控替换），替换后通过 `node --check` 验证语法完整性，失败自动回滚。同时需要实现从纯净备份提取可翻译字符串的扫描器（信号评分系统）、版本变更检测、以及完整的 status/apply/extract CLI 命令。

关键挑战：翻译映射表有 834 条条目（603 长字符串、131 中等字符串、100 短字符串），目标文件 13MB minified JS。替换策略必须在覆盖率和安全性之间取得平衡 -- 短字符串（如 "Running"、"Loading"）极易误伤代码逻辑，必须受控。Phase 1 已解决备份纯净性和原子写入，Phase 2 专注于替换逻辑本身。

**Primary recommendation:** 按照 ROADMAP 的 4-plan 结构实现：先 Translation Map 加载/Scanner，再 Replacement Engine，再 Verification/Version，最后 Extract/Status Commands。每个 plan 对应独立可测试的模块。

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
All implementation choices are at Claude's discretion -- autonomous execution mode. Use ROADMAP phase goal, success criteria, Phase 1 established patterns, and codebase conventions to guide decisions.

**Key constraints:**
- Python 3.8+, zero external dependencies
- Enhanced regex (NOT AST) for string replacement
- All output as JSON
- Atomic writes for all file operations
- Must use Path Resolver and Backup Manager from Phase 1
- Translation map format: JSON with _meta header

### Claude's Discretion
All implementation choices.

### Deferred Ideas (OUT OF SCOPE)
None -- autonomous execution.
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| APPLY-01 | Apply reads from pristine backup (not current cli.js) as source | BackupManager.restore() + read from backup; ARCHITECTURE.md data flow |
| APPLY-02 | Long strings (>20 chars) use global replacement with exact match | Python str.replace(); v3.0 proven; 603 entries in current map |
| APPLY-03 | Medium strings (10-20 chars) use quote-boundary constrained replacement | re with lookbehind/lookahead `(?<=[\"'])...(?=[\"'])`; 131 entries |
| APPLY-04 | Short strings (<10 chars) use word-boundary + whitelist + frequency cap | Skip-words.json (45 entries) + cap mechanism; 100 entries, HIGH RISK |
| APPLY-05 | All replacements proceed longest-first to prevent partial matches | sorted(key=len, reverse=True); v3.0 already does this correctly |
| APPLY-06 | Replacement count tracked per category (long/medium/short/skipped) | Stats dict pattern from v3.0; extend with skipped reason |
| APPLY-07 | After all replacements, `node --check` validates syntax | subprocess.run(["node","--check",path], timeout=10); v3.0 proven |
| APPLY-08 | On syntax validation failure, automatic rollback to backup | BackupManager.restore() + atomic_write flow |
| APPLY-09 | Hook/template string patterns replaced via precise context-aware regex | NOT sed; Python re with context patterns; PLATFORM concern |
| APPLY-10 | Apply outputs JSON result with ok/replacements/stats/entries | output_json() pattern from Phase 1 |
| EXTRACT-01 | Extract reads from pristine backup only | BackupManager ensures backup is pristine; read backup content |
| EXTRACT-02 | Extract uses strong/weak signal indicator system to score candidates | STRONG_INDICATORS (19 items) + WEAK_INDICATORS (26 items) from v3.0 |
| EXTRACT-03 | Extract filters out code-like strings (identifiers, URLs, protocol keywords) | NOISE_KW/NOISE_RE (65+ patterns) from v3.0; migrate to filters/ module |
| EXTRACT-04 | Extract outputs JSON with strong/weak candidates, scores, and occurrence counts | v3.0 extract output format; extend with scores |
| EXTRACT-05 | Extract correctly excludes already-translated and already-skipped strings | Load translations + skip-words, filter against them |
| EXTRACT-06 | Extract never outputs strings containing Chinese characters | CJK_PATTERN regex check on each candidate |
| VER-01 | Engine reads CLI version from package.json | json.loads(pkg_json.read_text())["version"]; Phase 1 pattern |
| VER-02 | Engine compares CLI version with translation map's `_meta.cli_version` | Load _meta.cli_version from zh-CN.json; compare strings |
| VER-03 | On version mismatch, engine deletes stale backup and re-creates from new cli.js | BackupManager re-create; delete old backup first |
| VER-04 | Version change reported to user with old->new version numbers | JSON output with old_version/new_version fields |
| STATUS-01 | `status` command outputs JSON with version, localized state, entry count, backup integrity | Extend Phase 1 cmd_status; add localized detection + entry count |
| STATUS-02 | `version` command outputs current CLI version | Phase 1 cmd_version already implemented |
| STATUS-03 | All commands output JSON format for script integration | output_json() from Phase 1 |
| STATUS-04 | Human-readable summary printed after apply (version, replacements, verification result) | JSON output + optional summary field |
| MAP-01 | Translation map uses JSON format with `_meta` header | Current zh-CN.json format; _meta with version/cli_version |
| MAP-02 | Map loaded from `~/.claude/scripts/i18n/zh-CN.json` by default | Path resolution; default to SCRIPTS dir |
| MAP-03 | Skip words loaded from `~/.claude/scripts/i18n/skip-words.json` | Current skip-words.json format; {"skip": [...]} |
| MAP-04 | Map entries with identical en/zh values are automatically skipped | 5 entries in current map have en==zh; skip in apply loop |
| PLAT-01 | All file paths use `pathlib.Path` (no hardcoded OS-specific separators) | Phase 1 pattern; pathlib throughout |
| PLAT-02 | No hardcoded user paths -- all resolved dynamically | Phase 1 find_cli_install_dir() |
| PLAT-03 | `sed -i` in Hook replacements uses platform-appropriate syntax (macOS vs Linux) | Use Python re instead of sed; cross-platform by design |
</phase_requirements>

## Standard Stack

### Core (Python Standard Library Only)

| Module | Version | Purpose | Why Standard |
|--------|---------|---------|--------------|
| `re` | 3.8+ | 正则匹配引擎 -- 三级替换策略的核心 | 支持所有需要的高级特性：lookbehind/lookahead/word boundary/`re.compile()` |
| `json` | 3.8+ | 翻译映射表读写、skip-words 加载、JSON 输出 | `ensure_ascii=False` 保留中文 |
| `pathlib.Path` | 3.8+ | 所有文件路径操作 | Phase 1 模式，跨平台 |
| `subprocess` | 3.8+ | `node --check` 语法验证 | `capture_output=True, timeout=10`，不用 `shell=True` |
| `hashlib` | 3.8+ | 备份完整性校验 | Phase 1 已实现 |
| `os` | 3.8+ | `os.replace()` 原子重命名、环境变量 | Phase 1 已实现 |

### Phase 1 Dependencies (已存在，必须使用)

| Module | Path | Purpose |
|--------|------|---------|
| `paths.py` | `scripts/i18n/config/paths.py` | find_cli_install_dir(), validate_cli_dir() |
| `constants.py` | `scripts/i18n/config/constants.py` | PKG_NAME, BACKUP_NAME, HASH_NAME |
| `backup.py` | `scripts/i18n/io/backup.py` | BackupManager (ensure_backup, restore, _is_pristine_file) |
| `file_io.py` | `scripts/i18n/io/file_io.py` | atomic_write_text(), atomic_copy() |
| `cli.py` | `scripts/i18n/cli.py` | output_json(), output_error(), get_cli_dir(), build_parser() |
| `restore.py` | `scripts/i18n/commands/restore.py` | cmd_restore() -- 参考模式 |

### Alternatives Considered (全部排除)

| Instead of | Could Use | Why Not |
|------------|-----------|---------|
| `re` (stdlib) | `regex` (PyPI) | 标准 re 满足所有需求；额外依赖无收益 |
| `str.replace()` + `re` | Aho-Corasick (`pyahocorasick`) | 834 条翻译 x 13MB 文件，预估 ~20-26 秒，在 30 秒预算内；Phase 2+ 再优化 |
| `argparse` | `click`/`typer` | Phase 1 已用 argparse；只有 6 个子命令 |
| Python 正则 | `sed` 做替换 | sed 对 UTF-8 中文不可靠；无 lookbehind/lookahead；APPLY-09 用 Python re 代替 |

**Installation:**
```bash
# 零安装 -- 全部是 Python 标准库 + Phase 1 已有模块
# 开发依赖
pip install pytest  # pytest 9.0.2 已安装
```

## Architecture Patterns

### Recommended Project Structure (Phase 2 新增/修改)

```
scripts/i18n/
  commands/
    apply.py        # [NEW] Apply 命令编排
    extract.py      # [NEW] Extract 命令
    status.py       # [MODIFY] 增强 cmd_status (Phase 2 版本)
    restore.py      # [EXISTING] Phase 1 已完成
  core/
    scanner.py      # [NEW] 字符串扫描器 -- 信号评分 + 噪声过滤
    replacer.py     # [NEW] 三级替换引擎
    verifier.py     # [NEW] node --check 验证 + 回滚逻辑
    version.py      # [NEW] 版本检测与变更处理
  io/
    translation_map.py  # [NEW] 翻译映射表加载/验证
  filters/
    noise_filter.py     # [NEW] 噪声过滤 (NOISE_KW/NOISE_RE 迁移)
    ui_indicator.py     # [NEW] UI 指标评分 (STRONG/WEAK_INDICATORS 迁移)
  config/
    constants.py    # [MODIFY] 可能增加映射表相关常量
  cli.py           # [MODIFY] 注册 apply/extract 子命令，接入 Phase 2 实现
```

### Pattern 1: 三级替换策略 (Tiered Replacement)

**What:** 根据英文源字符串长度分三级，使用不同精度的替换方式。
**When:** 替换 minified JS 中的字符串时必须用此策略。
**Example:**
```python
# 长字符串 (>20 chars): 精确全文替换
# 603 entries, risk: 极低
count = content.count(en)
if count > 0:
    content = content.replace(en, zh)
    stats["long"] += count

# 中等字符串 (10-20 chars): 引号边界约束
# 131 entries, risk: 低
pattern = f'(?<=[\'"]){re.escape(en)}(?=[\'"])'
matches = list(re.finditer(pattern, content))
for m in reversed(matches):
    content = content[:m.start()] + zh + content[m.end():]
stats["medium"] += len(matches)

# 短字符串 (<10 chars): 词边界 + skip 白名单 + 频率上限
# 100 entries, risk: 中等-高，必须受控
# 1. 必须不在 skip-words.json 中
# 2. 使用词边界 \b...\\b
# 3. 每个短字符串最多替换 N 次 (cap)
pattern = f'(?<=[\'"\\s>])\\b{re.escape(en)}\\b(?=[\'"\\s<])'
matches = list(re.finditer(pattern, content))
cap = min(len(matches), MAX_SHORT_CAP)
for m in reversed(matches[:cap]):
    content = content[:m.start()] + zh + content[m.end():]
```

### Pattern 2: 逆序替换 (Reverse Order Replacement)

**What:** 在同一个字符串内容上执行多次替换时，从后往前替换。
**When:** 任何涉及 regex match 对象的 in-place 替换（中等和短字符串）。
**Why:** 从末尾替换不影响前面 match 的位置偏移，避免偏移重算。
**Example:**
```python
# v3.0 已验证的模式 -- 直接沿用
matches = list(re.finditer(pattern, content))
for m in reversed(matches):
    content = content[:m.start()] + zh + content[m.end():]
```

### Pattern 3: 翻译映射表驱动 (Map-Driven Replacement)

**What:** 替换操作完全由 JSON 映射表驱动，引擎是通用的。
**When:** 所有替换操作。
**Example:**
```python
# 加载映射表
data = json.loads(map_path.read_text(encoding='utf-8'))
translations = data.get('translations', {})
# 按长度降序排序
items = sorted(translations.items(), key=lambda x: len(x[0]), reverse=True)
# 遍历并替换
for en, zh_val in items:
    if isinstance(zh_val, str):
        zh = zh_val  # v4 兼容
    elif isinstance(zh_val, dict):
        zh = zh_val.get('zh', '')  # v5 结构化
    if not zh or en == zh:
        continue  # MAP-04: en==zh 自动跳过
```

### Pattern 4: 信号评分系统 (Signal Scoring)

**What:** 提取字符串时用强/弱信号指标评分，区分 UI 文本和代码字符串。
**When:** extract 命令提取候选字符串时。
**Example:**
```python
# 从 v3.0 迁移的信号指标
STRONG_INDICATORS = [
    "claude code", "plan mode", "yolo mode", "auto mode",
    "extended thinking", "context window", "mcp server",
    # ... 19 项
]
WEAK_INDICATORS = [
    "permission", "allow", "deny", "agent", "tool",
    "please", "cannot", "loading", "not found",
    # ... 26 项
]
# 评分：强信号 * 1000 + 出现次数
score = (1000 if any(kw in text.lower() for kw in STRONG_INDICATORS) else 0) + count
```

### Anti-Patterns to Avoid

- **Anti-Pattern 1: 从已汉化 cli.js 读取/提取**: 必须从备份 (cli.bak.en.js) 读取，BackupManager 确保纯净。
- **Anti-Pattern 2: 短字符串全局 `str.replace()`**: `"Error"` 全局替换破坏代码逻辑。必须用三级策略。
- **Anti-Pattern 3: 替换后不验证**: 每次批量替换后必须 `node --check`。失败自动回滚。
- **Anti-Pattern 4: 正序替换导致偏移混乱**: 用 `reversed(matches)` 逆序替换。
- **Anti-Pattern 5: 直接覆盖写 cli.js**: 用 `atomic_write_text()` 写临时文件再 rename。
- **Anti-Pattern 6: 用 sed 做 Hook 替换**: APPLY-09 和 PLAT-03 决定用 Python re 而非 sed，跨平台一致性。

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| 备份管理 | 自定义备份逻辑 | Phase 1 BackupManager | 已实现 SHA-256 + CJK 检测 + 原子操作 |
| 原子写入 | 自定义文件写入 | Phase 1 atomic_write_text() | 已处理 tempfile + os.replace + 异常清理 |
| 路径检测 | 硬编码路径 | Phase 1 find_cli_install_dir() | 已实现 5 级级联检测 |
| JSON 输出 | print 格式化 | Phase 1 output_json()/output_error() | 已实现 ensure_ascii=False + stderr 错误 |
| 正则编译 | 每次循环重新编译 | `re.compile()` 预编译缓存 | 性能优化，标准做法 |

**Key insight:** Phase 1 提供了完善的基础设施层。Phase 2 的核心任务是在这些基础设施之上构建业务逻辑（scanner、replacer、verifier），而不是重新实现基础设施。

## Common Pitfalls

### Pitfall 1: 短字符串替换破坏代码逻辑 (CRITICAL)

**What goes wrong:** "Error"、"Running"、"OK" 等短字符串出现在 UI 文本和代码逻辑中。全局替换会改变条件判断、异常处理等代码行为。
**Why it happens:** minified JS 中短字符串无法通过简单的引号上下文区分 UI vs 代码。
**How to avoid:** (1) 短字符串默认跳过，除非在 skip-words.json 白名单中；(2) 使用词边界 + 引号边界双重约束；(3) 设置每个短字符串的替换频率上限。
**Warning signs:** 替换后 `node --check` 通过但 CLI 运行时行为异常。

### Pitfall 2: 替换顺序导致级联错误 (HIGH)

**What goes wrong:** "Extended thinking" 必须在 "Extended" 之前替换。如果短字符串先替换，可能破坏长字符串的匹配。
**Why it happens:** `content.replace()` 和 `re.sub()` 修改内容后影响后续匹配。
**How to avoid:** 始终按长度降序排序 (`sorted(key=len, reverse=True)`)。v3.0 已验证此策略有效。

### Pitfall 3: 逆序替换索引越界 (HIGH)

**What goes wrong:** 对 `re.finditer()` 的结果执行 `reversed()` 后切片替换，如果 `matches` 为空或 `cap=0` 则无替换，但如果 `content` 在循环中被修改（不是真正的 in-place），后续索引可能失效。
**Why it happens:** Python 字符串不可变，每次切片赋值创建新字符串。`reversed()` 的 match 对象的 `.start()/.end()` 仍然是原始 content 中的位置。
**How to avoid:** 逆序替换天然解决这个问题 -- 后面的替换不影响前面的位置。但必须确保每次替换都基于原始 content 的 match 位置，不重新扫描。

### Pitfall 4: node --check 通过但语义错误 (MEDIUM)

**What goes wrong:** `node --check` 只验证语法，不验证语义。替换可能改变字符串比较的值（如 `if(x==="Error")` 变成 `if(x==="错误")`），语法正确但运行时行为改变。
**Why it happens:** 三级策略的短字符串和中等字符串可能在代码逻辑字符串中命中。
**How to avoid:** (1) 中等字符串用引号边界约束降低风险；(2) 短字符串用白名单 + 频率上限；(3) 无法完全避免，但可控制在可接受范围内。

### Pitfall 5: 翻译映射表格式兼容性 (MEDIUM)

**What goes wrong:** 当前 zh-CN.json 的 translations 值是字符串 (`"Accept edits": "接受编辑"`)，但如果未来改为对象格式 (`"Error": {"zh": "错误", "scope": "quoted-only"}`)，引擎需要同时支持两种格式。
**How to avoid:** 加载映射表时检查值类型：字符串按 v4 处理，字典按 v5 处理。映射表格式不变更（Phase 2 保持 v4 格式）。

### Pitfall 6: extract 从已汉化文件提取 (CRITICAL -- v3.0 已存在的 Bug)

**What goes wrong:** v3.0 的 extract 命令 `src = BACKUP if BACKUP.exists() else CLI_FILE`。如果备份被污染（含中文），提取结果包含中文"新字符串"。
**How to avoid:** (1) Phase 1 已解决备份纯净性（BackupManager._is_pristine()）；(2) extract 必须通过 BackupManager 获取备份路径，验证纯净性后再读取。

### Pitfall 7: 版本检测时机 (MEDIUM)

**What goes wrong:** 在 apply 之前不检查版本变化，可能导致翻译映射表与 CLI 版本不匹配。
**How to avoid:** apply 命令开始时先执行版本检测：比较 package.json 版本与 _meta.cli_version。不匹配时删除旧备份、从新 cli.js 重建备份。

### Pitfall 8: PLATFORM sed 跨平台问题 (MEDIUM)

**What goes wrong:** APPLY-09 提到 Hook/template 替换。如果用 `sed -i` 实现，macOS 和 Linux 的 `sed -i` 语法不同（macOS 需要 `sed -i ''`，Linux 需要 `sed -i`）。
**How to avoid:** 不用 sed。用 Python re 实现所有替换，天然跨平台。PLAT-03 的正确答案是 "不用 sed"。

## Code Examples

### Translation Map Loader

```python
# Source: 基于 v3.0 格式 + MAP-01~04 需求
# 文件: scripts/i18n/io/translation_map.py

import json
from pathlib import Path
from typing import Dict, Tuple, Set

def load_translation_map(map_path: Path) -> dict:
    """Load translation map from JSON file.

    Returns dict with:
    - meta: _meta dict (version, cli_version, etc.)
    - translations: dict of en -> zh (flat string values)
    """
    data = json.loads(map_path.read_text(encoding='utf-8'))
    meta = data.get('_meta', {})
    raw = data.get('translations', {})

    # Flatten structured entries to en -> zh strings
    translations = {}
    for en, val in raw.items():
        if isinstance(val, str):
            translations[en] = val
        elif isinstance(val, dict):
            translations[en] = val.get('zh', '')

    return {"meta": meta, "translations": translations}

def load_skip_words(skip_path: Path) -> Set[str]:
    """Load skip words list from JSON file."""
    data = json.loads(skip_path.read_text(encoding='utf-8'))
    return set(data.get('skip', []))
```

### Three-Tier Replacer

```python
# Source: 基于 v3.0 lines 162-193 + ARCHITECTURE.md Pattern 1
# 文件: scripts/i18n/core/replacer.py

import re
from typing import Dict, List, Tuple

def classify_entry(en: str) -> str:
    """Classify string length tier: 'long', 'medium', or 'short'."""
    n = len(en)
    if n > 20:
        return 'long'
    elif n > 10:
        return 'medium'
    else:
        return 'short'

def apply_translations(
    content: str,
    translations: Dict[str, str],
    skip_words: set,
    max_short_cap: int = 50,
) -> Tuple[str, dict]:
    """Apply all translations to content using three-tier strategy.

    Returns (modified_content, stats_dict).
    """
    stats = {"long": 0, "medium": 0, "short": 0, "skipped": 0, "skip_reasons": {}}
    items = sorted(translations.items(), key=lambda x: len(x[0]), reverse=True)

    for en, zh in items:
        # MAP-04: skip identical entries
        if en == zh:
            stats["skipped"] += 1
            continue

        tier = classify_entry(en)

        if tier == 'long':
            count = content.count(en)
            if count > 0:
                content = content.replace(en, zh)
                stats["long"] += count

        elif tier == 'medium':
            pattern = f'(?<=[\'"]){re.escape(en)}(?=[\'"])'
            matches = list(re.finditer(pattern, content))
            if matches:
                for m in reversed(matches):
                    content = content[:m.start()] + zh + content[m.end():]
                stats["medium"] += len(matches)

        else:  # short
            if en in skip_words:
                stats["skipped"] += 1
                continue
            pattern = f'(?<=[\'"\\s>])\\b{re.escape(en)}\\b(?=[\'"\\s<])'
            matches = list(re.finditer(pattern, content))
            if matches:
                cap = min(len(matches), max_short_cap)
                for m in reversed(matches[:cap]):
                    content = content[:m.start()] + zh + content[m.end():]
                stats["short"] += cap

    return content, stats
```

### Verifier

```python
# Source: 基于 v3.0 lines 199-215 + APPLY-07/08
# 文件: scripts/i18n/core/verifier.py

import subprocess
from pathlib import Path

def verify_syntax(js_path: Path, timeout: int = 10) -> dict:
    """Verify JavaScript syntax with node --check.

    Returns {"ok": bool, "error": str or None}.
    """
    try:
        r = subprocess.run(
            ["node", "--check", str(js_path)],
            capture_output=True, text=True, timeout=timeout,
        )
        if r.returncode == 0:
            return {"ok": True, "error": None}
        return {"ok": False, "error": r.stderr.strip()}
    except subprocess.TimeoutExpired:
        return {"ok": False, "error": "node --check timed out"}
    except FileNotFoundError:
        return {"ok": False, "error": "node not found"}
```

### Version Detection

```python
# Source: VER-01~04
# 文件: scripts/i18n/core/version.py

import json
from pathlib import Path

def get_cli_version(cli_dir: Path) -> str:
    """Read CLI version from package.json."""
    pkg = cli_dir / 'package.json'
    if not pkg.exists():
        return "unknown"
    data = json.loads(pkg.read_text(encoding='utf-8'))
    return data.get('version', 'unknown')

def check_version_change(cli_dir: Path, map_meta: dict) -> dict:
    """Compare CLI version with translation map's _meta.cli_version.

    Returns {"changed": bool, "old": str, "new": str}.
    """
    current = get_cli_version(cli_dir)
    expected = map_meta.get('cli_version', 'unknown')
    return {
        "changed": current != expected and current != "unknown",
        "old": expected,
        "new": current,
    }
```

### Scanner (Extract Core)

```python
# Source: 基于 v3.0 lines 227-322 + EXTRACT-01~06
# 文件: scripts/i18n/core/scanner.py

import re
from typing import Dict, List, Set

# 从 v3.0 迁移的常量 -- 迁移到 filters/ 模块
STRONG_INDICATORS = [
    "claude code", "claude.md", "claude ", ".claude",
    "anthropic", "plan mode", "yolo mode", "auto mode", "fast mode",
    "extended thinking", "context window",
    "bypass permission", "permission mode", "sandbox",
    "mcp server", "mcp tool", "mcp ",
    "agent type", "agent tool", "agent idle", "agent abort",
    "worktree", "subagent",
    "accept terms", "help improve claude",
    "auto-allow", "autoallow",
]

WEAK_INDICATORS = [
    "permission", "allow", "deny", "approve", "reject",
    "agent", "tool", "skill", "hook", "plugin",
    "commit", "branch", "merge", "pull request",
    "please", "cannot", "must be", "is required", "confirm",
    "loading", "saving", "processing", "idle",
    "not found", "already exist", "unable to",
    "session", "model", "token", "cost",
    "config", "setting", "marketplace",
    "install", "uninstall", "enable", "disable",
    "new version", "update available",
]

def score_candidate(text: str, count: int) -> dict:
    """Score a candidate string for UI relevance.

    Returns {"score": int, "type": "strong"|"weak"|"none"}.
    """
    tl = text.lower()
    is_strong = any(kw in tl for kw in STRONG_INDICATORS)
    is_weak = any(kw in tl for kw in WEAK_INDICATORS)

    if is_strong:
        return {"score": 1000 + count, "type": "strong"}
    elif is_weak:
        return {"score": count, "type": "weak"}
    return {"score": 0, "type": "none"}

def scan_candidates(
    content: str,
    existing: Set[str],
    skipped: Set[str],
    noise_re: re.Pattern,
) -> List[dict]:
    """Scan content for translatable string candidates.

    Returns list of {"en", "count", "score", "type"} sorted by score desc.
    """
    # EXTRACT: 提取双引号内的英文字符串
    candidates = re.findall(r'"([A-Z][A-Za-z][^"]{4,120})"', content)

    results = []
    seen = set()

    for s in candidates:
        if s in seen:
            continue
        seen.add(s)

        # EXTRACT-05: 排除已翻译/已跳过
        if s in existing or s in skipped:
            continue

        # 必须包含空格（自然语言特征）
        if " " not in s:
            continue

        # 跳过代码片段
        if any(c in s for c in ["=>", "${", "===", "!==", "async ", "function ", ".prototype.", "()"]):
            continue
        sl = s.lower()
        if "http://" in sl or "https://" in sl:
            continue
        if s == s.upper() and len(s) > 5:
            continue

        # EXTRACT-03: 噪声过滤
        if noise_re.search(s):
            continue

        # 评分
        count = content.count(f'"{s}"')
        result = score_candidate(s, count)
        if result["type"] == "none":
            continue

        results.append({"en": s, "count": count, "score": result["score"], "type": result["type"]})

    results.sort(key=lambda x: x["score"], reverse=True)
    return results
```

## State of the Art

| Old Approach (v3.0) | Current Approach (v4.0 Rewrite) | When Changed | Impact |
|---------------------|--------------------------------|--------------|--------|
| 硬编码路径 | Phase 1 PathResolver (5级级联) | Phase 1 | 任何用户都能使用 |
| 污染备份（含中文） | Phase 1 BackupManager (SHA-256+CJK检测) | Phase 1 | restore 可靠性保证 |
| 简单 `str.replace()` 全局替换 | 三级替换策略 (长/中/短) | Phase 2 | 减少误替换 |
| 从 `CLI_FILE` 或 `BACKUP` 提取 | 只从经过纯净验证的备份提取 | Phase 2 | 提取结果不含中文 |
| 无版本检测 | package.json vs _meta.cli_version 对比 | Phase 2 | 版本更新后自动处理 |
| sys.argv 手动解析 | argparse 子命令 | Phase 1 | 可扩展 CLI 框架 |

**Deprecated/outdated:**
- v3.0 的 `SKIP_WORDS` 内联集合: 迁移到 `skip-words.json` 文件
- v3.0 的 `NOISE_KW`/`NOISE_RE` 内联定义: 迁移到 `filters/noise_filter.py` 模块
- v3.0 的 `STRONG_INDICATORS`/`WEAK_INDICATORS` 内联: 迁移到 `filters/ui_indicator.py` 模块
- v3.0 的 `sed` 用法 (如果有): 完全用 Python re 替代

## Open Questions

1. **短字符串替换策略的最终决定**
   - What we know: 100 条短字符串翻译，45 条 skip-words。短字符串替换风险高。
   - What's unclear: MAP-04 说 "default skip"，但 APPLY-04 说 "word-boundary + whitelist + frequency cap"。到底哪些短字符串在白名单中？
   - Recommendation: 保持 v3.0 策略 -- 短字符串如果不在 skip-words 中，用引号+词边界约束替换，频率上限 50。映射表中已有的短字符串都是经过人工审核的，风险可控。

2. **APPLY-09 Hook/template 替换的具体需求**
   - What we know: 需求说 "Hook/template string patterns replaced via precise context-aware sed"。v3.0 代码中没有明确的 Hook 替换逻辑。
   - What's unclear: 哪些具体的 Hook/template 模式需要替换？
   - Recommendation: Phase 2 先不实现专门的 Hook 替换路径。三级策略已覆盖大部分情况。如果测试中发现特定模式未被覆盖，作为后续增强。

3. **翻译映射表加载路径**
   - What we know: MAP-02 说 "loaded from ~/.claude/scripts/i18n/zh-CN.json"。但开发时映射表在 `scripts/zh-CN.json`。
   - What's unclear: 是否需要支持多个搜索路径？
   - Recommendation: 默认路径为 SCRIPTS 目录（与 engine.py 同级），支持环境变量或参数覆盖。安装后路径变为 ~/.claude/scripts/i18n/。

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Python 3.8+ | 主引擎 | True | 3.14.3 | -- |
| Node.js | `node --check` 验证 | True | 22.22.0 | -- |
| pytest | 单元测试 | True | 9.0.2 | -- |
| Claude Code CLI | 集成测试目标 | Needs check | -- | 用 fixtures 模拟 |

**Missing dependencies with no fallback:**
- None -- 所有核心依赖都已就位。

**Missing dependencies with fallback:**
- Claude Code CLI 本体：集成测试用 `tests/fixtures/sample_cli.js` 模拟，不依赖真实安装。

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest 9.0.2 |
| Config file | 无 (使用默认 + conftest.py) |
| Quick run command | `python3 -m pytest tests/unit/test_scanner.py -x -q` |
| Full suite command | `python3 -m pytest tests/ -v` |

### Phase Requirements -> Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| APPLY-01 | Apply reads from pristine backup | integration | `pytest tests/integration/test_apply.py -x` | Wave 0 |
| APPLY-02 | Long strings global replace | unit | `pytest tests/unit/test_replacer.py::test_long_string_replace -x` | Wave 0 |
| APPLY-03 | Medium strings quote-boundary replace | unit | `pytest tests/unit/test_replacer.py::test_medium_string_replace -x` | Wave 0 |
| APPLY-04 | Short strings controlled replace | unit | `pytest tests/unit/test_replacer.py::test_short_string_replace -x` | Wave 0 |
| APPLY-05 | Longest-first ordering | unit | `pytest tests/unit/test_replacer.py::test_replacement_order -x` | Wave 0 |
| APPLY-06 | Stats tracking per category | unit | `pytest tests/unit/test_replacer.py::test_stats_tracking -x` | Wave 0 |
| APPLY-07 | node --check validation | unit | `pytest tests/unit/test_verifier.py::test_syntax_check -x` | Wave 0 |
| APPLY-08 | Auto-rollback on failure | integration | `pytest tests/integration/test_apply.py::test_rollback -x` | Wave 0 |
| APPLY-10 | JSON output format | unit | `pytest tests/unit/test_replacer.py::test_json_output -x` | Wave 0 |
| EXTRACT-01 | Extract from pristine backup only | unit | `pytest tests/unit/test_scanner.py::test_extract_from_backup -x` | Wave 0 |
| EXTRACT-02 | Signal scoring system | unit | `pytest tests/unit/test_scanner.py::test_scoring -x` | Wave 0 |
| EXTRACT-03 | Code-string filtering | unit | `pytest tests/unit/test_scanner.py::test_noise_filter -x` | Wave 0 |
| EXTRACT-05 | Exclude translated/skipped | unit | `pytest tests/unit/test_scanner.py::test_exclude_existing -x` | Wave 0 |
| EXTRACT-06 | No Chinese in output | unit | `pytest tests/unit/test_scanner.py::test_no_cjk_output -x` | Wave 0 |
| VER-01~04 | Version detection and change handling | unit | `pytest tests/unit/test_version.py -x` | Wave 0 |
| MAP-01~04 | Map loading and validation | unit | `pytest tests/unit/test_translation_map.py -x` | Wave 0 |

### Sampling Rate
- **Per task commit:** `python3 -m pytest tests/unit/ -x -q`
- **Per wave merge:** `python3 -m pytest tests/ -v`
- **Phase gate:** `python3 -m pytest tests/ -v --tb=short` 全部绿色

### Wave 0 Gaps
- [ ] `tests/unit/test_replacer.py` -- covers APPLY-02~06, APPLY-10
- [ ] `tests/unit/test_verifier.py` -- covers APPLY-07, APPLY-08
- [ ] `tests/unit/test_scanner.py` -- covers EXTRACT-01~06
- [ ] `tests/unit/test_version.py` -- covers VER-01~04
- [ ] `tests/unit/test_translation_map.py` -- covers MAP-01~04
- [ ] `tests/unit/test_filters.py` -- covers noise_filter + ui_indicator
- [ ] `tests/integration/test_apply.py` -- covers APPLY-01, APPLY-08 (round-trip)
- [ ] `tests/fixtures/sample_zh_cn.json` -- 测试用翻译映射表 fixture
- [ ] `tests/fixtures/sample_skip.json` -- 测试用跳过列表 fixture

## Sources

### Primary (HIGH confidence)
- ARCHITECTURE.md -- 组件职责、数据流、三级策略设计
- PITFALLS.md -- 15 个已知陷阱和缓解策略
- STACK.md -- 技术栈决策（零外部依赖、Python 标准库）
- localize.py (v3.0) -- 当前实现参考，三级策略已验证
- Phase 1 代码: paths.py, backup.py, file_io.py, cli.py, restore.py

### Secondary (MEDIUM confidence)
- Python `re` module docs -- 正则 API 和性能特性
- Python `subprocess` docs -- node --check 调用模式
- v3.0 实际运行数据: 834 翻译条目分布 (603 long / 131 medium / 100 short)

### Tertiary (LOW confidence)
- 性能预估 (20-26 秒) -- 需要实测验证

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH -- 全部是 Python 标准库 + Phase 1 已有模块，零不确定性
- Architecture: HIGH -- ROADMAP 已规划 4-plan 结构，ARCHITECTURE.md 有详细设计
- Pitfalls: HIGH -- PITFALLS.md 详列 15 个陷阱，v3.0 代码提供了真实案例
- Performance: MEDIUM -- 预估在 30 秒预算内，但需实测确认

**Research date:** 2026-04-05
**Valid until:** 2026-05-05 (stable -- 标准库和既定架构，不会快速变化)
